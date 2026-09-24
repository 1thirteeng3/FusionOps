# Research & Engineering Decisions: LocaPredict SLA Guard v3 (Remediation, Constitution v1.1.0)

**Feature**: [spec.md](./spec.md)
**Status**: Completed (remediation revision)
**Date**: 2026-09-24

---

## R-01. Honest validation protocol (resubstitution → CV + holdout)

### Decision
Stratified 5-fold CV plus pre-registered temporal holdout (train ≤ 2025-10-31,
validate November, test December, no refit), PR-AUC under 5.16% prevalence,
DeLong 95% CIs for ROC-AUC, confusion matrices by priority stratum, frozen
ACR-001/ACR-002 before test. Train AUC 0.989 banned from reporting as
generalization; honest CV 0.849 reported with fold variance.

### Rationale
Reproduction proved 0.989 is resubstitution. Imbalanced data (P1 n=1, positives
5%) makes ROC-AUC alone misleading; PR-AUC plus calibration exposes the true
operating point and satisfies Principles I-II and Gate 4.

### Alternatives considered
- *Single split only*: rejected (high variance on rare class).
- *ROC-AUC point 0.884 as guarantee*: rejected (single favorable fold, no CI).
- *XGBoost/LightGBM now*: deferred; RF baseline retained until honest protocol passes.

## R-02. Explainability (pseudo-SHAP → TreeExplainer)

### Decision
`shap.TreeExplainer` over the true 55-dim TF-IDF plus meta-feature space, with
base value, per-feature attributions, and top-k removal fidelity checks. Fixed
weights (+0.34/+0.22/+0.18/-0.15/-0.08) banned as SHAP evidence.

### Rationale
Fixed tables violate Shapley efficiency/null-player/symmetry axioms and have zero
counterfactual fidelity. TreeExplainer cost is trivial at B=60 and meets the
<150 ms budget while satisfying Principle III and Gate 5.

### Alternatives considered
- *LIME*: rejected (stochastic perturbation latency/variance).
- *Global importances only*: rejected (no per-incident diagnosis for NOC action).

## R-03. Forecaster (sinusoid → fitted model + backtest)

### Decision
Fitted temporal model (seasonal baseline candidate: SARIMAX/ETS or LightGBM with
lags; Prophet optional with portability justification) with rolling-origin
backtest, holdout WAPE vs. seasonal-naive baselines, Diebold-Mariano test, and
Gaussian 95% intervals from residual variance. Constant WAPE 11.8% banned;
WAPE reported per horizon from backtest.

### Rationale
Deterministic sinusoid plus constant WAPE is circular. Only walk-forward
evaluation proves D+1/D+7 utility and satisfies Principles III-IV and Gate 5.

### Alternatives considered
- *Static moving average*: rejected (48-72 h peak lag).
- *Keep sinusoid as placeholder*: rejected (constitutional mislabeling ban).

## R-04. Clustering (keyword rules → density/topic + DBCV)

### Decision
HDBSCAN or BERTopic over TF-IDF/embeddings with DBCV, bootstrap stability, and
per-cluster measured FP rates. Keyword rules retained only as weak-label
baseline, never as HDBSCAN/NLP-semantic. Cluster counts must reconcile with
loader within 1%.

### Rationale
Substring matching is taxonomy, not density discovery, and produced the 55,171
vs. 100,634 divergence. DBCV plus stability plus measured FP rates satisfy
Principle IV and Gate 5.

### Alternatives considered
- *K-means with k=5*: rejected (spherical assumption, no noise model for 65% FP).
- *Rules as production clusters*: rejected (banned mislabeling).

## R-05. Risk calibration (affine heuristic → Platt/Isotonic)

### Decision
Calibrate Random Forest scores via Platt scaling or isotonic regression on
validation fold; report reliability diagram, Brier score, and justified
threshold τ. Affine formula (55p + priority bonus + group delta) banned as
probability.

### Rationale
Affine transform preserves within-priority order but destroys probabilistic
semantics claimed in US-01 independent test. Calibration satisfies Principle V
and Gate 4.

### Alternatives considered
- *Raw RF votes as percent*: rejected (uncalibrated under imbalance).
- *Threshold 0.5 by default*: rejected (requires cost-based justification).

## R-06. Causal claims (projections → controlled pilot)

### Decision
Label -38.5% FP, -21.4% MTTR, and -25% to -45% benefit table as projections.
Confirm via NOC pilot (RCT or difference-in-differences / interrupted time
series, intention-to-treat). Transfers require pre-specified TOST margins;
t-test p>0.05 never presented as equivalence.

### Rationale
No counterfactual design exists; arithmetic suppression is not causal evidence.
Satisfies Principle V and Gate 7.

### Alternatives considered
- *Before-after without control*: rejected (confounded by seasonality/load).
- *Keep as measured gains*: rejected (Gate 7 violation).

## R-07. Label honesty and regime/KS/auth hardening

### Decision
Dual labels (`ola_breached_synth`, `kpi_violado_obs`), P1 n=1 disclosure, KS
with Bonferroni/FDR over six features on symmetric windows (no hardcoded
p-values, power disclosed), regime thresholds versioned with hysteresis
backlog, auth via vault secret + password + revocation + rate limits with RBAC
matrix tests. Anonymous fallback and committed default secret removed.

### Rationale
Bundles the remaining I/VI/VII violations into single hardening track; each
sub-item maps to Gates 4/6/7 and unblocks production promotion.

### Alternatives considered
- *Single synthetic label*: rejected (construct leakage).
- *Uncorrected KS*: rejected (~26% false-alarm rate per cycle).
- *Demo-token in prod*: rejected (RBAC bypass).
