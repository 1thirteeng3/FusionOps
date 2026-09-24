export type Priority = 'P1' | 'P2' | 'P3' | 'P4';
export type IncidentStatus = 'open' | 'in_progress' | 'escalated' | 'resolved';
export type OperationalRegimeType = 'normal' | 'stress' | 'saturation' | 'crisis' | 'recovery';
export type TrendType = 'growing' | 'stable' | 'declining' | 'improving' | 'worsening';
export type DashboardMode = 'operations' | 'tactical' | 'engineering';

export interface SHAPFactor {
  feature: string;
  value: number;
  impact: 'positive' | 'negative';
  display_name?: string;
  feature_value_str?: string;
  base_value?: number;
  explainer?: string;
  explainer_version?: string;
  fidelity_topk?: number;
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  category: string;
  priority: Priority;
  group: string;
  product: string;
  config_item: string;
  opened_by: string;
  status: IncidentStatus;
  risk_score: number; // 0-100
  sla_deadline: string;
  sla_remaining_minutes: number;
  estimated_violation?: string;
  cluster_id?: string;
  cluster_name?: string;
  shap_factors: SHAPFactor[];
  similar_tickets?: string[];
  is_automated_fp?: boolean;
  duration_seconds?: number;
  created_at: string;
  updated_at: string;
  label_source?: 'synth_rule' | 'kpi_obs';
  p_raw?: number;
  p_calibrated?: number;
  threshold_tau?: number;
  claim_label?: 'measured' | 'projection';
  p1_n1_warning?: string;
}

export interface DataPoint {
  timestamp: string;
  label: string;
  value: number;
}

export interface Forecast {
  historical: DataPoint[];
  predicted: DataPoint[];
  confidence_lower: number[];
  confidence_upper: number[];
  horizon: 'D+1' | 'D+7';
  generated_at: string;
  peak_value: number;
  peak_date: string;
  capacity_threshold: number;
  is_over_capacity: boolean;
  wape_accuracy: number;
  breakdown_by_group?: Record<string, DataPoint[]>;
  breakdown_by_product?: Record<string, DataPoint[]>;
  model_id?: string;
  wape_holdout?: number;
  wape_baseline?: number;
  dm_pvalue?: number;
  claim_label?: 'measured' | 'projection';
}

export interface Regime {
  current: OperationalRegimeType;
  confidence: number;
  previous?: string;
  changed_at: string;
  trend: TrendType;
  active_triggers: string[];
  description?: string;
  recent_history?: Array<{ time: string; regime: string }>;
}

export interface Cluster {
  id: string;
  name: string;
  incident_count: number;
  avg_risk_score: number;
  top_features: string[];
  trend: TrendType;
  false_positive_rate: number;
  p1_count: number;
  p2_count: number;
  p3_count: number;
  p4_count: number;
  incident_ids: string[];
  sample_description: string;
  recommended_action: string;
  algorithm?: string;
  dbcv?: number | null;
  stability?: number | null;
  claim_label?: 'measured' | 'projection';
}

export interface DriftMetric {
  feature_name: string;
  p_value: number;
  statistic: number;
  status: 'stable' | 'warning' | 'drifted';
  reference_mean: number;
  current_mean: number;
  drift_detected: boolean;
  p_adjusted?: number;
  reference_version?: string;
  window_n?: number;
}

export interface MLOpsStatus {
  model_version: string;
  last_trained: string;
  roc_auc: number;
  recall: number;
  precision: number;
  f1_score: number;
  wape: number;
  drift_status: 'healthy' | 'warning' | 'critical';
  overall_drift_score: number;
  feature_drifts: DriftMetric[];
  retraining_in_progress: boolean;
  samples_in_training: number;
  samples_in_inference: number;
}

export interface MetricsOverview {
  total_active_incidents: number;
  critical_risk_count: number;
  sla_warning_count: number;
  sla_breached_count: number;
  avg_risk_score: number;
  projected_volume_next_period: number;
  fp_reduction_rate: number;
  mttr_reduction_pct: number;
  operational_regime: string;
  active_drift_alerts: number;
  last_updated: string;
  fp_claim_label?: 'measured' | 'projection';
  mttr_claim_label?: 'measured' | 'projection';
  operating_point_risk?: number;
}

export interface FilterState {
  search: string;
  priority: string;
  group: string;
  product: string;
  status: string;
  minRisk: number;
  maxRisk: number;
  clusterId?: string;
  sortBy: 'risk_desc' | 'risk_asc' | 'sla_asc' | 'created_desc';
}

export interface ToastMessage {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  duration?: number;
}
