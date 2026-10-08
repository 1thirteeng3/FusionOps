import asyncio
import pytest
from fastapi import HTTPException
from backend.api.routes import (
    get_health, list_incidents, get_incident,
    get_forecast, get_regime, get_clusters,
    get_drift_and_mlops, get_metrics_overview,
    assign_incident, escalate_incident, export_incidents_csv,
    login, get_demo_token, logout,
    predict_full, post_resolution_feedback, get_drift_metrics, get_model_audit,
)
from backend.models.schemas import (
    AssignRequest, EscalateRequest, LoginRequest, PredictRequest,
    FeedbackResolution,
)
from backend.services.itsm_data import itsm_store
from backend.services.ml_engine import ml_engine
from backend.db.database import DatabaseRepository

OP_USER = {"sub": "test-operator", "role": "operator"}
from backend.auth.security import get_current_user, require_role

DEV_PASSWORD = "dev-only-operator-passphrase-change-me"

def test_api_health():
    health = get_health()
    assert health["status"] == "healthy"
    assert health["version"] == "3.0.0"

def test_api_auth_login():
    resp = login(LoginRequest(username="test_admin", password="dev-only-admin-passphrase-change-me", role="admin"))
    assert resp.access_token != ""
    assert resp.user["role"] == "admin"

def test_api_auth_login_rejects_passwordless():
    with pytest.raises(Exception):
        login(LoginRequest(username="test_admin", role="admin"))

def test_api_auth_login_rejects_wrong_password():
    with pytest.raises(HTTPException) as exc:
        login(LoginRequest(username="test_admin", password="wrong-password-xyz", role="admin"))
    assert exc.value.status_code == 401

def test_api_no_anonymous_fallback():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_current_user(None))
    assert exc.value.status_code == 401

def test_api_rbac_viewer_blocked_from_mutation():
    checker = require_role(["admin", "operator"])
    with pytest.raises(HTTPException) as exc:
        asyncio.run(checker({"sub": "viewer-1", "role": "viewer"}))
    assert exc.value.status_code == 403

def test_api_demo_token():
    resp = get_demo_token(role="operator")
    assert resp.access_token != ""
    assert resp.user["role"] == "operator"

def test_api_list_incidents():
    incs = list_incidents(user=OP_USER)
    assert len(incs) >= 20
    assert incs[0].risk_score >= incs[-1].risk_score

def test_api_filter_priority():
    p1_incs = list_incidents(priority="P1", user=OP_USER)
    for inc in p1_incs:
        assert inc.priority == "P1"

def test_api_get_single_incident():
    inc = get_incident("INC8654273", user=OP_USER)
    assert inc.id == "INC8654273"
    assert inc.config_item.startswith("IC")

def test_api_calibrated_provenance_on_incident():
    inc = get_incident("INC8654273", user=OP_USER)
    assert inc.label_source == "synth_rule"
    assert inc.p_calibrated is not None
    assert inc.risk_score == max(1, min(99, int(round(inc.p_calibrated * 100.0))))

def test_api_assign_and_persistence():
    user = {"sub": "test-operator", "role": "operator"}
    before = itsm_store.get_incident("INC8654273").risk_score
    assigned = assign_incident("INC8654273", AssignRequest(group="Team07 (NOC)", notes="Teste automatizado"), user=user)
    assert assigned.group == "Team07 (NOC)"
    assert assigned.status == "in_progress"
    assert assigned.p_calibrated is not None
    assert assigned.risk_score == max(1, min(99, int(round(assigned.p_calibrated * 100.0))))

    # Verify persistence in store
    retrieved = itsm_store.get_incident("INC8654273")
    assert retrieved.group == "Team07 (NOC)"

def test_api_metrics_overview_projection_labels():
    metrics = get_metrics_overview(user=OP_USER)
    assert metrics.total_active_incidents >= 20
    assert metrics.fp_claim_label == "projection"
    assert metrics.mttr_claim_label == "projection"

def test_api_export_csv():
    user = {"sub": "test-admin", "role": "admin"}
    response = export_incidents_csv(limit=50, user=user)
    assert response.status_code == 200
    assert b"INC8654273" in response.body
    assert response.headers.get("X-Content-Type-Options") == "nosniff"

def test_api_retrain_idempotent_and_audited():
    admin = {"sub": "test-admin", "role": "admin"}
    from backend.api.routes import retrain_model
    first = retrain_model(user=admin)
    second = retrain_model(user=admin)
    assert first["status"] == "success"
    assert second["status"] == "success"
    assert first["model_version"] == second["model_version"]
    assert "artifact_hash" in first and "threshold_tau" in first


def _op():
    return {"sub": "test-operator", "role": "operator"}


def test_api_predict_full_contract():
    import time
    payload = PredictRequest(title="Apache Busy Workers no web9", priority="P2",
                             group="Team14", product="Hosting Linux",
                             config_item="IC00001", hour=14)
    t0 = time.perf_counter()
    out = predict_full(payload, user=_op())
    dt_ms = (time.perf_counter() - t0) * 1000
    assert 0.0 <= out.calibrated_risk_score <= 1.0
    assert out.risk_score == max(1, min(99, int(round(out.calibrated_risk_score * 100.0))))
    assert out.risk_category == ml_engine.risk_category(out.calibrated_risk_score)
    assert out.threshold_tau_star == ml_engine.threshold_tau
    assert out.estimated_mttr_minutes > 0
    assert len(out.grouped_shap_explanations) == 3
    assert {g.group for g in out.grouped_shap_explanations} == {
        "sobrecarga_turno", "capacidade_tecnica", "severidade_semantica"}
    assert len(out.shap_factors) >= 4
    print(f"\n/predict latency: {dt_ms:.1f} ms (aceite 45 ms)")
    assert dt_ms < 5000, "trava de sanidade contra hangs"


def test_api_feedback_and_drift_metrics():
    import time as _t
    suffix = int(_t.time_ns() % 1_000_000)
    DatabaseRepository.clear_prediction_audit()
    # Linhas bem calibradas: o rollup NÃO deve bloquear (cobre o caminho saudável).
    DatabaseRepository.record_prediction(f"TEST-TICKET-1-{suffix}", 0.95, 35.0)
    out = post_resolution_feedback(
        FeedbackResolution(ticket_id=f"TEST-TICKET-1-{suffix}", actual_sla_violado=True,
                           actual_resolution_time=61.0), user=_op())
    assert out["matched_prediction"] is True
    out2 = post_resolution_feedback(
        FeedbackResolution(ticket_id=f"TEST-TICKET-GHOST-{suffix}", actual_sla_violado=False,
                           actual_resolution_time=5.0), user=_op())
    assert out2["matched_prediction"] is False
    drift = get_drift_metrics(user={"sub": "v", "role": "viewer"})
    assert isinstance(drift.psi_panel, list) and len(drift.psi_panel) > 0
    assert drift.auto_block is False
    audit = get_model_audit(user={"sub": "v", "role": "viewer"})
    assert audit.brier_gate in ("PASS", "BLOCKED")
    DatabaseRepository.clear_prediction_audit()


def test_api_auto_block_on_degradation():
    import time as _t
    suffix = int(_t.time_ns() % 1_000_000)
    DatabaseRepository.clear_prediction_audit()
    for i in range(10):
        DatabaseRepository.record_prediction(f"TEST-BAD-{suffix}-{i}", 0.99, 10.0)
        DatabaseRepository.record_resolution(f"TEST-BAD-{suffix}-{i}", False, 12.0)
    try:
        roll = ml_engine.rollup_audit_job()
        assert roll["status"] == "ok" and roll["auto_block"] is True
        import pytest as _pt
        with _pt.raises(Exception) as exc:
            predict_full(PredictRequest(title="x y z apache", priority="P3",
                                        group="Team14", product="Hosting Linux",
                                        config_item="IC00001", hour=10), user=_op())
        assert exc.value.status_code == 503
    finally:
        DatabaseRepository.clear_prediction_audit()
        ml_engine.auto_block = False
        ml_engine.auto_block_reason = ""
