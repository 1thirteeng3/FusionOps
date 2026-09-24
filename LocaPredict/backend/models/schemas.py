from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import html

class SHAPFactor(BaseModel):
    feature: str = Field(..., max_length=100)
    value: float
    impact: Literal['positive', 'negative']
    display_name: Optional[str] = Field(None, max_length=150)
    feature_value_str: Optional[str] = Field(None, max_length=150)
    # Provenance for verified SHAP (Constitution III, Gate 5, T006)
    base_value: Optional[float] = None
    explainer: Optional[str] = Field(None, max_length=64)
    explainer_version: Optional[str] = Field(None, max_length=64)
    fidelity_topk: Optional[float] = None

class IncidentBase(BaseModel):
    id: str = Field(..., max_length=50)
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=3, max_length=2000)
    category: str = Field(..., max_length=100)
    priority: Literal['P1', 'P2', 'P3', 'P4']
    group: str = Field(..., max_length=100)
    product: str = Field(..., max_length=100)
    config_item: str = Field(..., max_length=50)
    opened_by: str = Field(default="Monitoramento", max_length=100)
    status: Literal['open', 'in_progress', 'escalated', 'resolved']
    risk_score: int = Field(ge=0, le=100)
    sla_deadline: str
    sla_remaining_minutes: int
    estimated_violation: Optional[str] = Field(None, max_length=100)
    cluster_id: Optional[str] = Field(None, max_length=50)
    cluster_name: Optional[str] = Field(None, max_length=150)
    shap_factors: List[SHAPFactor] = []
    similar_tickets: List[str] = []
    is_automated_fp: bool = False
    duration_seconds: Optional[int] = None
    created_at: str
    updated_at: str
    # Honesty provenance (Constitution I/V, Gate 7, T006)
    label_source: Optional[Literal['synth_rule', 'kpi_obs']] = None
    p_raw: Optional[float] = None
    p_calibrated: Optional[float] = None
    threshold_tau: Optional[float] = None
    claim_label: Optional[Literal['measured', 'projection']] = None
    p1_n1_warning: Optional[str] = None

    @field_validator('title', 'description', 'group', 'product', mode='before')
    @classmethod
    def sanitize_strings(cls, v: Any) -> Any:
        if isinstance(v, str):
            clean = html.escape(v.strip())
            return clean
        return v

class Incident(IncidentBase):
    pass

class DataPoint(BaseModel):
    timestamp: str
    label: str
    value: float

class Forecast(BaseModel):
    historical: List[DataPoint]
    predicted: List[DataPoint]
    confidence_lower: List[float]
    confidence_upper: List[float]
    horizon: Literal['D+1', 'D+7']
    generated_at: str
    peak_value: float
    peak_date: str
    capacity_threshold: float
    is_over_capacity: bool
    wape_accuracy: float
    breakdown_by_group: Optional[Dict[str, List[DataPoint]]] = None
    breakdown_by_product: Optional[Dict[str, List[DataPoint]]] = None
    # Forecast provenance (Constitution IV, Gate 5, T006)
    model_id: Optional[str] = Field(None, max_length=64)
    wape_holdout: Optional[float] = None
    wape_baseline: Optional[float] = None
    dm_pvalue: Optional[float] = None
    claim_label: Optional[Literal['measured', 'projection']] = None

class Regime(BaseModel):
    current: Literal['normal', 'stress', 'saturation', 'crisis', 'recovery']
    confidence: float
    previous: Optional[str] = None
    changed_at: str
    trend: Literal['improving', 'stable', 'worsening']
    active_triggers: List[str] = []
    description: Optional[str] = None
    recent_history: List[Dict[str, Any]] = []

class Cluster(BaseModel):
    id: str
    name: str
    incident_count: int = Field(default=0, alias="incident_count")
    avg_risk_score: float
    top_features: List[str]
    trend: Literal['growing', 'stable', 'declining']
    false_positive_rate: float
    p1_count: int
    p2_count: int
    p3_count: int
    p4_count: int
    incident_ids: List[str]
    sample_description: str
    recommended_action: str
    # Cluster provenance (Constitution IV, Gate 5, T006)
    algorithm: Optional[str] = Field(None, max_length=64)
    dbcv: Optional[float] = None
    stability: Optional[float] = None
    claim_label: Optional[Literal['measured', 'projection']] = None

    model_config = ConfigDict(populate_by_name=True)

class DriftMetric(BaseModel):
    feature_name: str
    p_value: float
    statistic: float
    status: Literal['stable', 'warning', 'drifted']
    reference_mean: float
    current_mean: float
    drift_detected: bool
    # Multiplicity provenance (Constitution VI, Gate 6, T006)
    p_adjusted: Optional[float] = None
    reference_version: Optional[str] = Field(None, max_length=64)
    window_n: Optional[int] = None

class MLOpsStatus(BaseModel):
    model_version: str
    last_trained: str
    roc_auc: float
    recall: float
    precision: float
    f1_score: float
    wape: float
    drift_status: Literal['healthy', 'warning', 'critical']
    overall_drift_score: float
    feature_drifts: List[DriftMetric]
    retraining_in_progress: bool = False
    samples_in_training: int
    samples_in_inference: int

class MetricsOverview(BaseModel):
    total_active_incidents: int
    critical_risk_count: int
    sla_warning_count: int
    sla_breached_count: int
    avg_risk_score: float
    projected_volume_next_period: int
    fp_reduction_rate: float
    mttr_reduction_pct: float
    operational_regime: str
    active_drift_alerts: int
    last_updated: str
    # Claim discipline (Constitution V, Gate 7, T006): aggregates below are
    # projections until measured by a controlled pilot.
    fp_claim_label: Literal['measured', 'projection'] = 'projection'
    mttr_claim_label: Literal['measured', 'projection'] = 'projection'
    # Validated operating point: risk >= this value means "flagged positive"
    # at the recall-constrained threshold tau (replaces the dead >=80 rule).
    operating_point_risk: int = 4

class AssignRequest(BaseModel):
    group: str = Field(..., max_length=100)
    notes: Optional[str] = Field(None, max_length=500)

class EscalateRequest(BaseModel):
    priority: Optional[Literal['P1', 'P2', 'P3']] = None
    reason: str = Field(..., min_length=3, max_length=500)
    target_group: Optional[str] = Field(None, max_length=100)

class RegimeOverrideRequest(BaseModel):
    regime: Literal['normal', 'stress', 'saturation', 'crisis', 'recovery', 'auto']

# Auth Schemas
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=200)
    role: Optional[Literal['admin', 'operator', 'viewer']] = 'operator'

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in_minutes: int
    user: Dict[str, Any]
