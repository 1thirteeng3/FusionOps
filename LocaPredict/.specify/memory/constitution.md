<!--
Sync Impact Report (temporary review scratch, remove before commit):
- Version change: 1.0.0 -> 1.1.0 (MINOR: new validation-integrity principle + materially expanded XAI/forecast/clustering/calibration/causal/security guidance)
- Modified Principles:
  * I. Ground-Truth Realism & Anti-Mock Fidelity -> I. Ground-Truth Realism, Label Honesty & Anti-Mock Fidelity (expanded: synthetic ola_breached disclosure, KPI-real reporting, P1 n=1 disclosure, cluster-count consistency)
  * II. Explainable & Actionable AI (XAI First) -> III. Real Explainability with Verified SHAP (expanded: bans fixed-weight pseudo-SHAP, mandates TreeExplainer + fidelity tests)
  * III. Proactive Shift-Left & Capacity Alignment -> IV. Forecasting & Clustering Evidence Standards (expanded: bans sinusoidal-as-Prophet and keyword-rules-as-HDBSCAN, mandates backtest + DBCV)
  * IV. MLOps Observability & Continuous Drift Monitoring -> VI. MLOps Observability with Multiplicity Control (expanded: FDR/Bonferroni, symmetric windows, bans hardcoded p-values)
  * V. Zero-Trust RBAC & Immutable Auditability -> VII. Zero-Trust Auth & Immutable Auditability (hardened: bans anonymous fallback, passwordless login, committed secrets)
- Added Sections/Principles:
  * II. Honest Validation & Anti-Resubstitution (new, NON-NEGOTIABLE: bans train-as-test AUC 0.989 pattern, mandates stratified CV + temporal holdout + PR-AUC + calibration)
  * V. Calibrated Risk & Causal-Claim Discipline (new: bans affine heuristic as probability, bans -38.5%/-21.4% as causal without RCT/DiD/ITS)
  * Quality Gates 4-7 (validation, XAI fidelity, forecast backtest, security hardening)
- Removed Sections: none
- Follow-up TODOs: none (all tokens resolved; ACR-001..ACR-007 thresholds require product-owner sign-off in Next Actions specs)
-->

# LocaPredict SLA Guard v3 (FusionOps) Constitution

## Core Principles

### I. Ground-Truth Realism, Label Honesty & Anti-Mock Fidelity (NON-NEGOTIABLE)
Every risk score, cluster assignment, and forecast MUST derive from the real
122,543-record Locaweb ITSM dataset via genuine inference pipelines. Mock or
random generation for core ML metrics is prohibited. The synthetic
`ola_breached` rule (duration over SLA limit) MUST be labeled as synthetic and
reported alongside the observed KPI-violated rate (0.20%), never as observed
breach alone. The single P1 exemplar (n=1) MUST be disclosed wherever P1
metrics appear, and no P1-generalization claim is permitted. Cluster counts
served by the API MUST reconcile with the dataset loader within 1%; the known
cluster-1 divergence (55,171 vs. 100,634) MUST NOT recur.

### II. Honest Validation & Anti-Resubstitution (NON-NEGOTIABLE)
Train-as-test evaluation is prohibited. The resubstitution AUC pattern
(train 0.989 reported as generalization; honest 5-fold CV 0.849) MUST NOT
recur. Every classifier claim MUST report stratified K-fold CV plus a
pre-registered temporal holdout, PR-AUC under 5.16% prevalence, DeLong 95%
CIs, and confusion matrices by priority stratum. Acceptance thresholds
(ACR-001: ROC-AUC, ACR-002: Recall, ACR-003: WAPE) MUST be frozen before
seeing test data. Any single-fold 0.884 MUST be reported with fold variance,
never as a point guarantee.

### III. Real Explainability with Verified SHAP (NON-NEGOTIABLE)
A prediction without actionable diagnosis MUST NOT reach NOC operators, and
no fixed-weight table SHALL be presented as SHAP. Every high/critical OLA
risk MUST carry TreeExplainer-derived Shapley attributions over the true
55-dimension TF-IDF plus meta-feature space, with base value, sign, and
feature-value strings. Explanations MUST pass top-k removal fidelity checks
and guide reassignment, escalation, or auto-resolution. The former
hardcoded-factor module is banned as evidence of explainability.

### IV. Forecasting & Clustering Evidence Standards
No deterministic sinusoid SHALL be labeled Prophet, and no keyword rule list
SHALL be labeled HDBSCAN/NLP-semantic. Demand forecasts (D+1/D+7 with
Gaussian 95% intervals) MUST come from a fitted temporal model with
rolling-origin backtest, WAPE computed on holdout against seasonal-naive
baselines, and Diebold-Mariano comparison. Semantic clusters MUST come from
a density or neural-topic model with DBCV, bootstrap stability, and
false-positive rates measured per cluster, not asserted. Forecast WAPE
constants and hardcoded cluster sizes are prohibited.

### V. Calibrated Risk & Causal-Claim Discipline
Risk scores 0-100 MUST be calibrated probabilities (reliability diagram plus
Brier score) with a justified decision threshold, not the banned affine
heuristic (55p plus priority bonus plus group delta with clipping). Effect
claims (-38.5% FP, -21.4% MTTR, -25% to -45% benefit table) MUST be labeled
projection until measured by a controlled pilot (RCT, difference-in-
differences, or interrupted time series with intention-to-treat). No
t-test non-significance SHALL be presented as equivalence; transfers
require pre-specified TOST margins.

**Addendum 2026-10-06 (Fases 1-7, still MINOR v1.1.0 scope):** the operating
threshold is economic, τ* = argmin C_FP·FP + C_FN·FN (defaults R$30/R$600 via
env), fitted on temporal-validation blocks only, with the frozen recall floor
(ACR-002) enforced as a disclosed PASS/BLOCKED gate — never silently
overridden. Walk-forward temporal validation (no shuffle anywhere), causal
past-only features with purging, Grouped TreeSHAP by causal coalitions, PSI
drift plus prediction_audit with 24h rollup and >20% auto-block are mandatory;
MTTR ships as conditional median (quantile) with disclosed MdAPE because the
acceptance metric is median-based and the Tweedie mean is incompatible with it
under ×254 skew. Promotion requires every Fase-7 acceptance gate PASS.

### VI. MLOps Observability with Multiplicity Control
Production models MUST NEVER run unmonitored. Drift MUST use two-sample
Kolmogorov-Smirnov tests on adequate symmetric windows with Bonferroni or
FDR correction across the six-feature panel, versioned references, and
idempotent deterministic retraining. Hardcoded p-values, uncorrected
multiplicity (26% false-alarm rate per cycle), and reference-vs-n-50
comparisons without power disclosure are prohibited. Alerts at p below 0.05
(warning) and 0.01 (critical) MUST trigger documented triage, not silent
decay.

### VII. Zero-Trust Auth & Immutable Auditability (NON-NEGOTIABLE)
All interactions MUST enforce HMAC-SHA256 JWT RBAC (Admin, Operator,
Viewer) with Viewer barred from mutations. Anonymous-operator fallback,
passwordless login accepting any username, committed default secrets,
missing revocation/refresh, and absent rate limiting are prohibited.
Secrets MUST come from vault or environment, never source. Every mutation
(reassign, escalate, regime override, retrain) MUST append timestamp, actor,
before/after params to the SQLite audit trail, verified by auth and audit
integration tests.

## Technical & Architectural Constraints

- **Backend Architecture**: Python 3.10+ and FastAPI with async non-blocking
  I/O for WebSocket telemetry and REST standards; dynamic root-relative data
  paths for bare-metal, VM, and Docker portability.
- **Frontend Architecture**: React 18, TypeScript, Vite with the cohesive
  accessible Glassmorphic system; WCAG-compliant contrast and responsive
  layouts; no arbitrary external UI libraries.
- **ML Stack Discipline**: scikit-learn TF-IDF plus Random Forest
  (B=60, balanced weights) as baseline; scipy KS; real SHAP TreeExplainer;
  fitted forecaster; density/topic clusterer. Dependency additions
  (e.g. Prophet/HDBSCAN native) require portability justification.
- **Persistence & Audit**: SQLite ACID with append-only audit_logs and
  operational_state; CSV exports capped at 1,000 rows with sanitized
  headers.
- **Security & Network**: Strict CORS whitelist with credentials, no
  wildcard in auth routes; `X-Content-Type-Options: nosniff` on exports;
  vault-backed JWT secret with rotation; rate limits on auth and retrain.

## Development Workflow & Quality Gates

- **Quality Gate 1 (Automated Testing)**: 100% `pytest` pass across auth,
  API, inference, drift, and persistence; no merge or release on failure.
- **Quality Gate 2 (Type Integrity & Build)**: `tsc && vite build` with
  zero type errors before distribution.
- **Quality Gate 3 (Packaging & Delivery)**: `.zip` artifacts contain
  sanitized trees, datasets, requirements, Docker, and docs; exclude
  `node_modules` and `__pycache__`.
- **Quality Gate 4 (Validation Integrity)**: Stratified CV plus temporal
  holdout, PR-AUC, DeLong CIs, and calibration artifacts required; bans
  resubstitution metrics and post hoc thresholds.
- **Quality Gate 5 (XAI & Forecast Evidence)**: SHAP fidelity report plus
  forecast backtest vs. naive baselines required; bans pseudo-SHAP,
  sinusoidal forecasts, and rule-list clusters.
- **Quality Gate 6 (Security Hardening)**: Secret-scan, anonymous-fallback
  absence test, passwordless-login rejection test, RBAC matrix test, and
  audit-completeness test required before production.
- **Quality Gate 7 (Claim Review)**: Every external metric (AUC, WAPE,
  FP/MTTR reduction) MUST cite frozen criteria, sample, window, and
  reproduction script; projections labeled as projections.

## Governance

This Constitution is the supreme architectural and operational standard
for LocaPredict SLA Guard (FusionOps). It supersedes ad hoc practices.
All PRs and reviews MUST verify compliance gate by gate; complexity and
deviations MUST be justified in writing with a migration plan.

- **MAJOR**: Removal or redefinition of core principles.
- **MINOR**: New principle, constraint, or quality gate; materially
  expanded guidance.
- **PATCH**: Clarifications, wording, and non-semantic refinements.
- Amendments require documentation, semantic versioning, and regression
  validation; the Sync Impact Report header MUST be removed before commit.
- Compliance is reviewed at each release; violations block promotion until
  remediated or formally waived with expiry.

**Version**: 1.1.0 | **Ratified**: 2026-09-24 | **Last Amended**: 2026-09-24
