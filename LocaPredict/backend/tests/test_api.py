import asyncio
import pytest
from fastapi import HTTPException
from backend.api.routes import (
    get_health, list_incidents, get_incident,
    get_forecast, get_regime, get_clusters,
    get_drift_and_mlops, get_metrics_overview,
    assign_incident, escalate_incident, export_incidents_csv,
    login, get_demo_token, logout
)
from backend.models.schemas import AssignRequest, EscalateRequest, LoginRequest
from backend.services.itsm_data import itsm_store

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
