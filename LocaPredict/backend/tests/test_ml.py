import pytest
from backend.services.ml_engine import ml_engine
from backend.services.itsm_data import itsm_store
from backend.services import dataset_loader


def test_ml_shap_verified_treeexplainer():
    incident = itsm_store.get_incident("INC8654273")
    assert incident is not None

    shap_factors = ml_engine.calculate_incident_shap(incident.model_dump())
    assert len(shap_factors) >= 4
    for factor in shap_factors:
        assert factor.feature != ""
        assert isinstance(factor.value, float)
        assert factor.impact in ["positive", "negative"]
        # Verified-SHAP provenance (Gate 5): no fixed-weight tables.
        assert factor.explainer == "shap.TreeExplainer"
        assert factor.base_value is not None
        assert factor.explainer_version
        assert factor.fidelity_topk is not None
        assert -1.0 <= factor.fidelity_topk <= 1.0


def test_honest_cv_metrics_no_resubstitution():
    # CV quantities must exist and resubstitution must never be reported.
    assert 0.0 < ml_engine.roc_auc <= 1.0
    assert ml_engine.roc_auc < 0.99, "resubstitution-range AUC indicates train-as-test"
    assert ml_engine.roc_auc >= 0.70
    assert 0.0 < ml_engine.cv_pr_auc <= 1.0
    assert len(ml_engine.auc_ci95) == 2
    assert ml_engine.auc_ci95[0] <= ml_engine.roc_auc <= ml_engine.auc_ci95[1]
    assert ml_engine.auc_ci_method == "bootstrap-1000"
    assert ml_engine.brier >= 0.0
    assert 0.02 <= ml_engine.threshold_tau <= 0.95


def test_forecast_fitted_with_backtest():
    fc = ml_engine.get_forecast(horizon="D+7")
    assert fc.horizon == "D+7"
    assert len(fc.historical) >= 14
    assert len(fc.predicted) == 7
    assert len(fc.confidence_lower) == 7
    assert len(fc.confidence_upper) == 7
    assert fc.peak_value > 0
    # Fitted-forecast provenance (Gate 5): holdout WAPE, baseline, DM test.
    assert fc.model_id
    assert fc.wape_holdout is not None and fc.wape_holdout > 0
    assert fc.wape_baseline is not None and fc.wape_baseline > 0
    assert fc.dm_pvalue is not None and 0.0 <= fc.dm_pvalue <= 1.0
    assert fc.claim_label == "measured"

def test_forecast_generation_d1():
    fc = ml_engine.get_forecast(horizon="D+1")
    assert fc.horizon == "D+1"
    assert len(fc.predicted) == 1
    assert len(fc.confidence_lower) == 1

def test_clusters_measured_and_reconciled():
    clusters = ml_engine.get_clusters()
    assert len(clusters) >= 5
    apache_cluster = next((c for c in clusters if "Apache" in c.name), None)
    assert apache_cluster is not None
    assert apache_cluster.algorithm in ("hdbscan", "keyword-baseline")
    # Measured counts reconcile with the loader within 1% (Gate 7).
    df = dataset_loader.get_or_create_processed_dataset()
    api_counts = {c.id: c.incident_count for c in clusters}
    ok, details = dataset_loader.reconcile_cluster_counts(api_counts, df, tol=0.01)
    assert ok, f"cluster count divergence: {details}"
    for c in clusters:
        assert 0.0 <= c.false_positive_rate <= 100.0
        assert c.claim_label in ("measured", "projection")

def test_ks_drift_with_multiplicity_control():
    drift = ml_engine.get_drift_and_mlops()
    assert drift.recall >= 0.80  # frozen ACR-002, recall-constrained tau
    assert len(drift.feature_drifts) >= 5
    for metric in drift.feature_drifts:
        assert 0.0 <= metric.p_value <= 1.0
        assert metric.p_adjusted is not None and 0.0 <= metric.p_adjusted <= 1.0
        assert metric.reference_version
        assert metric.window_n and metric.window_n > 0
        assert metric.status in ["stable", "warning", "drifted"]

def test_model_retraining_returns_evidence():
    result = ml_engine.retrain_model()
    assert result["status"] == "success"
    assert "v3" in result["model_version"]
    assert result["roc_auc"] >= 0.70
    assert "cv_pr_auc" in result and "auc_ci95" in result
    assert result["auc_ci_method"] == "bootstrap-1000"
    assert "brier" in result and "threshold_tau" in result
    assert "artifact_hash" in result and "wape_holdout" in result

def test_predict_incident_risk_calibrated():
    risk_p1, shap_p1 = ml_engine.predict_incident_risk(
        title="Apache Busy Workers saturation on IC00001",
        priority="P1",
        group="Team14",
        product="Hosting Linux",
        config_item="IC00001",
        hour=14,
        duration_seconds=14,
        is_fp=True
    )
    assert 1 <= risk_p1 <= 99
    assert len(shap_p1) >= 4

    # Ceteris-paribus priority monotonicity: same technical context, only the
    # priority differs. (Absolute P1-vs-P4 ordering across different contexts
    # is not asserted: calibrated breach probability is dominated by the FP
    # pattern, while contractual severity travels in the priority badge.)
    risk_p4_same, _ = ml_engine.predict_incident_risk(
        title="Apache Busy Workers saturation on IC00001",
        priority="P4",
        group="Team14",
        product="Hosting Linux",
        config_item="IC00001",
        hour=14,
        duration_seconds=14,
        is_fp=True
    )
    assert risk_p1 >= risk_p4_same
    # Calibration: risk equals round(100 * p_calibrated).
    p_raw, p_cal = ml_engine.predict_incident_proba(
        "Apache Busy Workers saturation on IC00001", "P1", "Team14",
        "Hosting Linux", "IC00001", 14)
    assert risk_p1 == max(1, min(99, int(round(p_cal * 100.0))))

def test_dual_labels_and_p1_disclosure():
    df = dataset_loader.get_or_create_processed_dataset()
    assert "ola_breached_synth" in df.columns
    assert "kpi_violado_obs" in df.columns
    assert "p1_n1_flag" in df.columns
    assert int(df["p1_n1_flag"].sum()) == 1
    assert float(df["kpi_violado_obs"].mean()) < 0.01


def test_group_vocabulary_matches_observed_data():
    # Filter-bug regression: metadata options must equal pool vocabulary.
    observed = dataset_loader.get_observed_groups()
    assert len(observed) >= 10
    for inc in itsm_store.get_all_incidents():
        assert inc.group in observed, f"phantom squad in pool: {inc.group}"
    # Unknown squads map to a dedicated bucket, never index 0.
    assert dataset_loader.group_index("__NOPE__") == float(len(observed))


def test_operating_point_exposed_and_consistent():
    from backend.api.routes import get_metrics_overview
    overview = get_metrics_overview(user={"sub": "t", "role": "viewer"})
    expected = max(1, min(99, int(round(ml_engine.threshold_tau * 100.0))))
    assert overview.operating_point_risk == expected
    flagged = [i for i in itsm_store.get_all_incidents() if i.risk_score >= expected]
    assert len(flagged) > 0, "operating point must flag at least one incident"


def test_reseed_rebuilds_canonical_pool():
    n = itsm_store.reseed_from_dataset()
    assert n >= 20
    observed = dataset_loader.get_observed_groups()
    for inc in itsm_store.get_all_incidents():
        assert inc.group in observed
    # Restore calibrated state for subsequent tests/sessions.
    result = ml_engine.retrain_model()
    assert result["status"] == "success"
    inc = itsm_store.get_incident("INC8654273")
    assert inc is not None and inc.p_calibrated is not None
