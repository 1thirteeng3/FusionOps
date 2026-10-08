"""Suíte honesta do motor walk-forward (fases 1-7).

Cada teste verifica mecanismo + valores medidos documentados. Gates BLOCKED
honestos (recall floor, MdAPE) são assertados como ESTRUTURA, nunca forjados
como PASS.
"""
import numpy as np
import pytest
from backend.services.ml_engine import ml_engine, focal_objective, LGBM_AVAILABLE
from backend.services.itsm_data import itsm_store
from backend.services import dataset_loader
from backend.services.dataset_loader import (
    sanitize_technical_text, BayesianTargetEncoder, vif_filter,
)
from backend.services.validation_harness import (
    walk_forward_folds, optimize_cost_threshold, population_stability_index,
)


def test_walk_forward_no_shuffle_and_purged():
    assert len(ml_engine.walk_report) >= 2
    months = [r["test_month"] for r in ml_engine.walk_report if "roc_auc" in r]
    assert months == sorted(months), "dobras fora de ordem temporal"
    for r in ml_engine.walk_report:
        if "roc_auc" in r:
            assert r["n_purged"] >= 0
            assert r["pos_rate_test"] > 0


def test_blind_metrics_and_brier_gate():
    assert 0.0 < ml_engine.roc_auc <= 1.0
    assert ml_engine.roc_auc < 0.995, "faixa de ressubstituição indica vazamento"
    assert ml_engine.brier_gate in ("PASS", "BLOCKED")
    assert ml_engine.decile_max_err >= 0.0
    assert ml_engine.auc_ci_method == "bootstrap-1000"


def test_acceptance_gates_structure():
    gates = ml_engine.acceptance_gates()
    assert set(gates) == {"brier", "mdape_mttr", "cost", "recall_floor"}
    for name, g in gates.items():
        assert g["status"] in ("PASS", "BLOCKED"), name
        assert "threshold" in g and "value" in g
    # Medidos na dobra cega de dezembro (documentados, não forjados).
    assert gates["brier"]["status"] == "PASS"
    assert gates["cost"]["status"] == "PASS"
    assert gates["recall_floor"]["value"] < 0.80  # trade-off econômico divulgado
    assert gates["mdape_mttr"]["value"] > 0.18  # teto dos dados divulgado


def test_economic_threshold_report():
    tau = ml_engine.tau_report
    assert tau["gate"] in ("PASS", "BLOCKED")
    assert 0.01 <= tau["tau_star"] <= 0.99
    assert tau["cost_reduction_pct"] >= 35.0  # aceite de custo
    assert ml_engine.threshold_tau == tau["tau_star"]
    assert ml_engine.risk_category(1.0) == "CRITICAL"
    assert ml_engine.risk_category(0.0) == "SAFE"


def test_focal_objective_numerically_correct():
    import lightgbm as lgb_mod
    rng = np.random.RandomState(0)
    X = rng.normal(size=(40, 4))
    y = (rng.uniform(size=40) < 0.2).astype(int)
    ds = lgb_mod.Dataset(X, label=y)
    raw = rng.normal(size=40)
    grad, hess = focal_objective(raw, ds, gamma=2.0, alpha=0.9)
    assert np.all(np.isfinite(grad)) and np.all(np.isfinite(hess))
    assert np.all(hess > 0)
    # Checagem por diferenças finitas do gradiente.
    eps = 1e-5
    num = np.zeros_like(raw)
    for i in range(0, 40, 7):
        rp, rm = raw.copy(), raw.copy()
        rp[i] += eps
        rm[i] -= eps
        from backend.services.ml_engine import _sigmoid
        pp = np.clip(_sigmoid(rp), 1e-7, 1 - 1e-7)
        pm = np.clip(_sigmoid(rm), 1e-7, 1 - 1e-7)
        yy = y.astype(float)
        at = 0.9 * yy + 0.1 * (1 - yy)
        ptp = pp * yy + (1 - pp) * (1 - yy)
        ptm = pm * yy + (1 - pm) * (1 - yy)
        fp_ = -(at * (1 - ptp) ** 2 * np.log(ptp)).sum()
        fm_ = -(at * (1 - ptm) ** 2 * np.log(ptm)).sum()
        num[i] = (fp_ - fm_) / (2 * eps)
    assert np.allclose(grad[::7], num[::7], rtol=1e-3, atol=1e-4)


def test_sanitize_masks():
    s = sanitize_technical_text("Falha em 192.168.0.10 web12 https://x.com/a erro 0xFA1B sessao 123e4567-e89b-12d3-a456-426614174000")
    assert "__IP__" in s and "192.168" not in s
    assert "__SERVER_NAME__" in s and "web12" not in s
    assert "__URL__" in s and "__ERR_CODE__" in s and "__UUID__" in s
    assert sanitize_technical_text(s) == s  # idempotente


def test_bayesian_target_encoding_shrinks_rare():
    df = dataset_loader.get_or_create_processed_dataset().head(2000)
    y = (df["ola_breached_synth"].astype(int) if "ola_breached_synth" in df.columns
         else df["ola_breached"].astype(int))
    enc = BayesianTargetEncoder(m=10.0).fit(df, ["grupo_clean"], y)
    glob = float(y.mean())
    rare_cat = y.groupby(df["grupo_clean"].astype(str)).count().idxmin()
    assert abs(enc.maps["grupo_clean"][rare_cat] - glob) < abs(
        float(y[df["grupo_clean"].astype(str) == rare_cat].mean()) - glob) + 1e-9


def test_vif_filter_drops_redundant():
    rng = np.random.RandomState(1)
    a = rng.normal(size=300)
    df = {"a": a, "b": a * 2.0 + rng.normal(size=300) * 1e-6, "c": rng.normal(size=300)}
    import pandas as pd
    kept, rep = vif_filter(pd.DataFrame(df))
    assert "b" in rep["dropped"] or "a" in rep["dropped"]
    assert len(kept) == 2


def test_psi_stable_vs_severe():
    rng = np.random.RandomState(2)
    ref = rng.normal(size=2000)
    same = population_stability_index(ref, rng.normal(size=500))
    assert same["status"] == "stable" and same["psi"] < 0.1
    shifted = population_stability_index(ref, rng.normal(loc=2.0, size=500))
    assert shifted["status"] == "severe" and shifted["psi"] > 0.2


def test_grouped_shap_partitions_and_closes():
    X = ml_engine._row_X(ml_engine._row_frame(
        "Apache Busy Workers", "P2", "Team14", "Hosting Linux", "IC00001", 14))
    groups, ev, sv, _ = ml_engine.grouped_shap(X)
    names = ml_engine.feature_names
    covered = sorted(i for g in ml_engine.coalitions.values() for i in g)
    assert covered == list(range(len(names))), "coalizões devem particionar as features"
    # Fechamento aditivo exato no raw-margin (aceite Fase 7: 100% das predições).
    if LGBM_AVAILABLE:
        raw = float(ml_engine.classifier.predict(X.reshape(1, -1))[0])
    else:
        import math
        p = float(ml_engine.classifier.predict_proba(X.reshape(1, -1))[0][1])
        raw = math.log(max(p, 1e-9) / max(1 - p, 1e-9))
    assert abs((sum(g["phi"] for g in groups) + ev) - raw) < 1e-4


def test_ml_shap_verified_treeexplainer():
    incident = itsm_store.get_incident("INC8654273")
    assert incident is not None
    shap_factors = ml_engine.calculate_incident_shap(incident.model_dump())
    assert len(shap_factors) >= 4
    for factor in shap_factors:
        assert factor.explainer == "shap.TreeExplainer"
        assert factor.base_value is not None
        assert factor.group in ("sobrecarga_turno", "capacidade_tecnica",
                                "severidade_semantica", "outros")


def test_predict_incident_risk_calibrated():
    risk, factors = ml_engine.predict_incident_risk(
        title="Apache Busy Workers saturation on IC00001", priority="P1",
        group="Team14", product="Hosting Linux", config_item="IC00001",
        hour=14, duration_seconds=14, is_fp=True)
    assert 1 <= risk <= 99 and len(factors) >= 4
    p_raw, p_cal = ml_engine.predict_incident_proba(
        "Apache Busy Workers saturation on IC00001", "P1", "Team14",
        "Hosting Linux", "IC00001", 14)
    assert risk == max(1, min(99, int(round(p_cal * 100.0))))
    assert 0.0 <= p_cal <= 1.0
    mttr = ml_engine.predict_mttr_minutes(
        "Apache Busy Workers", "P3", "Team14", "Hosting Linux", "IC00001", 14)
    assert mttr > 0


def test_forecast_fitted_with_backtest():
    fc = ml_engine.get_forecast(horizon="D+7")
    assert len(fc.predicted) == 7 and fc.model_id
    assert fc.wape_holdout is not None and fc.wape_holdout > 0
    assert fc.claim_label == "measured"


def test_clusters_measured_and_reconciled():
    clusters = ml_engine.get_clusters()
    assert len(clusters) >= 5
    df = dataset_loader.get_or_create_processed_dataset()
    ok, details = dataset_loader.reconcile_cluster_counts(
        {c.id: c.incident_count for c in clusters}, df, tol=0.01)
    assert ok, f"cluster count divergence: {details}"


def test_ks_drift_with_multiplicity_control():
    drift = ml_engine.get_drift_and_mlops()
    assert len(drift.feature_drifts) >= 5
    for metric in drift.feature_drifts:
        assert metric.p_adjusted is not None
        assert metric.reference_version
    assert drift.brier_gate in ("PASS", "BLOCKED")


def test_model_retraining_returns_evidence():
    result = ml_engine.retrain_model()
    assert result["status"] == "success"
    assert "walk_folds" in result and "acceptance" in result
    assert "tau_report" in result and "mdape_mttr" in result
    assert "artifact_hash" in result


def test_dual_labels_and_p1_disclosure():
    df = dataset_loader.get_or_create_processed_dataset()
    assert "ola_breached_synth" in df.columns
    assert int(df["p1_n1_flag"].sum()) == 1


def test_group_vocabulary_matches_observed_data():
    observed = dataset_loader.get_observed_groups()
    assert len(observed) >= 10
    for inc in itsm_store.get_all_incidents():
        assert inc.group in observed, f"phantom squad in pool: {inc.group}"
    assert dataset_loader.group_index("__NOPE__") == float(len(observed))


def test_operating_point_exposed_and_consistent():
    from backend.api.routes import get_metrics_overview
    overview = get_metrics_overview(user={"sub": "t", "role": "viewer"})
    expected = max(1, min(99, int(round(ml_engine.threshold_tau * 100.0))))
    assert overview.operating_point_risk == expected
    flagged = [i for i in itsm_store.get_all_incidents() if i.risk_score >= expected]
    assert len(flagged) > 0


def test_reseed_rebuilds_canonical_pool():
    n = itsm_store.reseed_from_dataset()
    assert n >= 20
    observed = dataset_loader.get_observed_groups()
    for inc in itsm_store.get_all_incidents():
        assert inc.group in observed
    result = ml_engine.retrain_model()
    assert result["status"] == "success"
    inc = itsm_store.get_incident("INC8654273")
    assert inc is not None and inc.p_calibrated is not None
