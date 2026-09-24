# Interface & API Contracts: LocaPredict SLA Guard v3 (Remediation, Constitution v1.1.0)

**Feature**: [spec.md](../spec.md)
**Status**: Completed
**Date**: 2026-09-24

---

## 1. RESTful API Specification (`/api/v1`)

### 1.1 Autenticação & Sessão

#### `POST /api/v1/auth/login`
Requires username + password + role; vault-backed HMAC-SHA256 JWT.
Anonymous fallback removed; committed default secret banned.
- **Request**: `{"username": "operador_noc", "password": "••••", "role": "operator"}`
- **Response 200**: `{"access_token": "eyJ...","token_type": "bearer","expires_in_minutes": 1440,"user": {...}}`
- **Errors**: `401` credentials invalid/expired, `429` rate-limited.
- Contract test: passwordless body MUST yield 401; missing token MUST NOT default to operator.

#### `POST /api/v1/auth/demo-token`
Development-only. MUST be disabled in production profile (404 or 403).

### 1.2 Telemetria & Fila

#### `GET /api/v1/metrics/overview`
Adds `claim_label` to every aggregate; projections never served as measured.
- **Response 200**: `{..., "fp_reduction_rate": {"value": 38.5, "claim_label": "projection"}, "mttr_reduction_pct": {"value": 21.4, "claim_label": "projection"}, "model_version": "vX.Y.Z", "threshold_tau": 0.5, ...}`

#### `GET /api/v1/incidents` / `GET /api/v1/incidents/{id}`
Incident objects include `p_calibrated`, `label_source`, `threshold_tau`,
`shap_provenance {explainer, version, fidelity_topk}`, and `p1_n1_warning`
when priority P1. Fixed-weight SHAP responses are contract violations.

#### `POST /api/v1/incidents/{id}/assign` | `/escalate` | `/notify` | `/simulate`
Require Operator/Admin; Viewer gets 403; every mutation appends AuditLog with
actor + before/after. Simulate runs genuine calibrated inference (no random risk).

### 1.3 Planejamento Tático

#### `GET /api/v1/forecast?horizon={D+1|D+7}`
Returns `{historical, predicted, confidence_lower/upper (95%), model_id,
wape_holdout, wape_baseline, dm_pvalue, claim_label}`. Constant-WAPE or
sinusoid provenance fails contract.

#### `GET /api/v1/regime` | `POST /api/v1/regime/override`
Regime includes `threshold_version`, calibrated `confidence`, triggers, history.
Override requires Admin + reason; logged.

### 1.4 Engenharia & Governança

#### `GET /api/v1/clusters`
Each cluster includes `algorithm, dbcv, stability, incident_count,
false_positive_rate (measured), claim_label`. Rule-list provenance labeled
`baseline` only; HDBSCAN label requires DBCV artifact.

#### `GET /api/v1/drift`
Each metric includes `statistic, p_value, p_adjusted, status (by adjusted p),
reference_version, window_n, power_note`. Hardcoded p-values fail contract.

#### `POST /api/v1/models/retrain` (Admin)
Idempotent versioned retrain; returns `{model_version, cv_auc, cv_prauc,
delong_ci, brier, threshold_tau, artifact_hash}`. Unauthenticated/duplicate
side effects banned.

#### `GET /api/v1/export?limit={100..1000}`
Sanitized CSV capped at 1,000 rows, `X-Content-Type-Options: nosniff`,
RBAC-enforced, audit-logged. Exported claim columns carry `claim_label`.

---

## 2. WebSocket (`/ws`)

- Server → Client `CONNECTED {regime, overview (with claim_labels, model_version)}`.
- Server → Client `NEW_INCIDENT {incident (calibrated + provenance)}`.
- Client → Server `PING → PONG`; `SIMULATE_TICKET` (Operator/Admin only) → broadcast.
- Broken auth MUST close socket (no anonymous subscribe in production).
