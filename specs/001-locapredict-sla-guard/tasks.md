# Tasks: LocaPredict SLA Guard v3 — Remediation to Constitution v1.1.0

**Input**: Design documents from `/specs/001-locapredict-sla-guard/`
**Prerequisites**: plan.md (remediation), spec.md (US1-US5), research.md (R-01..R-07), data-model.md, contracts/api_contracts.md
**Status**: Ready for Implementation
**Tests**: Included — explicitly required by SC-005 and Quality Gate 1 (100% pytest) plus Gates 4-7.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1..US5 mapping to spec.md stories
- Exact file paths included in every task.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Remediation project initialization.

- [X] T001 Add `shap`, `hdbscan` (or `bertopic`) with portability justification in `LocaPredict/requirements.txt`
- [X] T002 [P] Remove committed JWT default secret, require vault/env secret with startup fail-closed in `LocaPredict/backend/core/config.py`
- [X] T003 [P] Configure pytest paths and markers for calibration/fidelity/backtest/security/audit suites in `LocaPredict/pytest.ini`
- [X] T004 Freeze ACR-001 (ROC-AUC), ACR-002 (Recall), ACR-003 (WAPE) thresholds in `specs/001-locapredict-sla-guard/plan.md` before any test-window evaluation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Dual labels, provenance schema, audit, honest validation harness. BLOCKS all stories.

- [X] T005 Implement dual-label ingestion (`ola_breached_synth` rule vs `kpi_violado_obs` observed 0.20%), P1 n=1 flag, and cluster-count reconciliation within 1% in `LocaPredict/backend/services/dataset_loader.py`
- [X] T006 [P] Extend Pydantic v2 schemas with `label_source` ENUM(`synth_rule`,`kpi_obs`), `p_raw`, `p_calibrated`, `threshold_tau`, `claim_label` ENUM(`measured`,`projection`), SHAP/forecast/cluster/drift provenance in `LocaPredict/backend/models/schemas.py`
- [X] T007 [P] Harden SQLite append-only `audit_logs` and `operational_state` with actor plus before/after params in `LocaPredict/backend/db/database.py`
- [X] T008 Create frozen temporal split (train ≤ 2025-10-31, validate November, test December) plus stratified K-fold, PR-AUC, DeLong CI, Brier harness in `LocaPredict/backend/services/validation_harness.py`
- [X] T009 Remove anonymous-operator fallback, require password credentials, add revocation metadata and rate-limit hooks in `LocaPredict/backend/auth/security.py`

**Checkpoint**: Foundation ready — dual labels, provenance schema, audit, and honest harness operational.

---

## Phase 3: User Story 1 - Triagem e Priorização Preditiva com Explicabilidade (Priority: P1) 🎯 MVP

**Goal**: Calibrated RF risk plus TreeExplainer SHAP with fidelity, recalculated on reassign/escalate.

**Independent Test**: Open Operations view, filter risk ≥ 80%, open INC8654273 modal and verify risk equals `round(100*p_calibrated)`, TreeExplainer base value plus version plus `fidelity_topk`, `label_source`, and P1 warning where applicable; reassign recalibrates plus audit; Viewer gets 403.

### Tests for User Story 1

- [X] T010 [P] [US1] Contract test for calibrated incident plus SHAP provenance in `LocaPredict/backend/tests/test_ml.py`
- [X] T011 [P] [US1] RBAC test for assign/escalate/simulate (Operator/Admin pass, Viewer 403, no-token 401) in `LocaPredict/backend/tests/test_api.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Train TF-IDF plus balanced Random Forest on frozen split and report CV plus holdout ROC-AUC/PR-AUC/DeLong/Brier in `LocaPredict/backend/services/ml_engine.py`
- [X] T013 [US1] Calibrate scores via Platt/Isotonic on validation fold and serve `p_calibrated` with `threshold_tau` in `LocaPredict/backend/services/ml_engine.py`
- [X] T014 [US1] Replace fixed-weight table with `shap.TreeExplainer` attributions plus top-k fidelity in `LocaPredict/backend/services/ml_engine.py`
- [X] T015 [US1] Recompute calibrated risk on reassign/escalate with audit before/after in `LocaPredict/backend/services/itsm_data.py`
- [X] T016 [US1] Enforce RBAC plus provenance responses on list/get/assign/escalate/notify/simulate in `LocaPredict/backend/api/routes.py`
- [X] T017 [P] [US1] Render calibrated risk, `claim_label`, TreeExplainer waterfall with version and fidelity in `LocaPredict/frontend/src/components/operations/SHAPWaterfallModal.tsx`
- [X] T018 [P] [US1] Gate incident cards and actions on role plus P1 n=1 disclosure in `LocaPredict/frontend/src/components/operations/OperationsView.tsx`

**Checkpoint**: US1 independently testable with calibrated, explainable, audited triage.

---

## Phase 4: User Story 2 - Planejamento Tático D+1/D+7 e Capacidade (Priority: P1)

**Goal**: Fitted forecaster with rolling backtest, holdout WAPE vs. naive plus Diebold-Mariano, capacity matrix labeled.

**Independent Test**: Toggle D+1/D+7, verify `model_id`, `wape_holdout` vs. `wape_baseline`, `dm_pvalue`, 95% envelope; Team14 saturation carries `claim_label=projection` until pilot.

### Tests for User Story 2

- [X] T019 [P] [US2] Backtest test asserting holdout WAPE computed per horizon against seasonal-naive in `LocaPredict/backend/tests/test_ml.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement fitted forecaster with rolling-origin backtest and Gaussian 95% intervals in `LocaPredict/backend/services/ml_engine.py`
- [X] T021 [US2] Serve `model_id`, `wape_holdout`, `wape_baseline`, `dm_pvalue`, `claim_label` on `GET /api/v1/forecast` in `LocaPredict/backend/api/routes.py`
- [X] T022 [P] [US2] Render history, prediction, confidence envelope plus backtest metadata in `LocaPredict/frontend/src/components/tactical/ForecastChart.tsx`
- [X] T023 [US2] Render capacity matrix with saturation prescriptions labeled projection in `LocaPredict/frontend/src/components/tactical/TacticalView.tsx`

**Checkpoint**: US1 and US2 independently functional.

---

## Phase 5: User Story 3 - Clusters Semânticos e Supressão de FP (Priority: P2)

**Goal**: Density/topic clusters with DBCV, stability, measured FP, reconciled counts.

**Independent Test**: Open cluster panel, verify per-cluster `algorithm`, `dbcv`, `stability`, measured FP, counts within 1% of loader; rule lists appear only as `baseline`.

### Tests for User Story 3

- [X] T024 [P] [US3] Cluster reconciliation plus DBCV/stability threshold test in `LocaPredict/backend/tests/test_ml.py`

### Implementation for User Story 3

- [X] T025 [US3] Implement HDBSCAN/BERTopic clustering with DBCV, bootstrap stability, measured FP in `LocaPredict/backend/services/ml_engine.py`
- [X] T026 [US3] Serve clusters with algorithm, DBCV, stability, measured FP, `claim_label` on `GET /api/v1/clusters` in `LocaPredict/backend/api/routes.py`
- [X] T027 [P] [US3] Render cluster metrics with drill-down plus baseline-vs-model provenance in `LocaPredict/frontend/src/components/engineering/ClusterPanel.tsx`

**Checkpoint**: US3 independently functional.

---

## Phase 6: User Story 4 - MLOps Drift e Retreinamento (Priority: P2)

**Goal**: Multiplicity-controlled KS drift plus versioned idempotent retrain with zero downtime.

**Independent Test**: Verify six-feature KS with `p_adjusted`, `reference_version`, `window_n`; trigger retrain as Admin and verify version plus CV/PR-AUC/DeLong/Brier plus audit; Viewer/Operator retrain gets 403.

### Tests for User Story 4

- [X] T028 [P] [US4] KS multiplicity test (Bonferroni/FDR, no hardcoded p, symmetric windows) in `LocaPredict/backend/tests/test_ml.py`
- [X] T029 [P] [US4] Idempotent versioned retrain plus audit test in `LocaPredict/backend/tests/test_api.py`

### Implementation for User Story 4

- [X] T030 [US4] Implement Bonferroni/FDR-corrected two-sample KS on symmetric versioned windows in `LocaPredict/backend/services/ml_engine.py`
- [X] T031 [US4] Implement idempotent versioned retrain returning CV/PR-AUC/DeLong/Brier/threshold/artifact hash in `LocaPredict/backend/services/ml_engine.py`
- [X] T032 [US4] Enforce Admin-only drift plus retrain endpoints with audit in `LocaPredict/backend/api/routes.py`
- [X] T033 [P] [US4] Render adjusted-p drift table plus retrain button with version metrics in `LocaPredict/frontend/src/components/engineering/DriftPanel.tsx`

**Checkpoint**: MLOps governance independently functional.

---

## Phase 7: User Story 5 - RBAC, Exportação e Auditoria (Priority: P3)

**Goal**: Vault-backed auth, RBAC matrix, capped sanitized export, complete audit.

**Independent Test**: Passwordless login yields 401; no-token yields 401; Viewer mutations yield 403; CSV export ≤1,000 rows with `nosniff` plus audit; every mutation has actor plus before/after.

### Tests for User Story 5

- [X] T034 [P] [US5] Passwordless-rejection, fallback-absence, RBAC-matrix, and secret-scan tests in `LocaPredict/backend/tests/test_auth.py`
- [X] T035 [P] [US5] CSV cap plus header plus audit-completeness test in `LocaPredict/backend/tests/test_api.py`

### Implementation for User Story 5

- [X] T036 [US5] Enforce vault/env JWT secret rotation, password verification, revocation, rate limits in `LocaPredict/backend/auth/security.py`
- [X] T037 [US5] Enforce RBAC plus audit on export and regime override in `LocaPredict/backend/api/routes.py`
- [X] T038 [P] [US5] Gate UI actions on role and surface auth/audit errors in `LocaPredict/frontend/src/components/common/Modals.tsx`

**Checkpoint**: Governance independently functional.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Claim review, validation docs, performance, packaging.

- [X] T039 Relabel README metrics (AUC/CV variance, WAPE holdout, FP/MTTR projections) with criteria, window, sample, script in `LocaPredict/README.md`
- [X] T040 [P] Verify inference plus TreeExplainer p95 < 150 ms and log budget evidence in `LocaPredict/backend/services/ml_engine.py`
- [X] T041 [P] Run `quickstart.md` Gate 4-7 validation and fix deviations in `specs/001-locapredict-sla-guard/quickstart.md`
- [X] T042 Regenerate sanitized delivery archive excluding transient dirs via `LocaPredict/scripts/create_final_zip.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all stories.
- **User Stories (Phase 3+)**: Depend on Foundational; then parallelizable by capacity or sequential P1 → P2 → P3.
- **Polish (Phase 8)**: Depends on all desired stories.

### User Story Dependencies

- **US1 (P1)**: After Foundational; no story dependencies; MVP scope.
- **US2 (P1)**: After Foundational; independently testable; reads US1 risk scale but does not block on it.
- **US3 (P2)**: After Foundational; independently testable.
- **US4 (P2)**: After Foundational; consumes US1-US3 model versions but testable via harness.
- **US5 (P3)**: After Foundational; RBAC/audit wraps all stories.

### Within Each Story

- Tests FAIL before implementation; models before services; services before endpoints; core before UI integration.

### Parallel Opportunities

- T002, T003 parallel (different files); T006, T007 parallel; T010, T011 parallel; T012 vs. T017/T018 parallel (backend vs. frontend); T019 vs. frontend T022/T023 parallel; T024 vs. T027 parallel; T028, T029 parallel; T034, T035 parallel; T040, T041 parallel.

---

## Parallel Example: User Story 1

```bash
# Tests in parallel (different files):
Task: "Contract test for calibrated incident plus SHAP provenance in LocaPredict/backend/tests/test_ml.py"
Task: "RBAC test for assign/escalate/simulate in LocaPredict/backend/tests/test_api.py"

# Backend model vs. frontend in parallel (different files):
Task: "Train TF-IDF plus balanced RF in LocaPredict/backend/services/ml_engine.py"
Task: "Render TreeExplainer waterfall in LocaPredict/frontend/src/components/operations/SHAPWaterfallModal.tsx"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1 Setup plus Phase 2 Foundational.
2. Complete Phase 3 US1 (calibrated risk plus verified SHAP).
3. STOP and VALIDATE per US1 independent test plus Gates 4, 6, 7.
4. Demo only; no production until Gates 4-7 pass.

### Incremental Delivery

1. Setup plus Foundational → harness ready.
2. Add US1 → test → demo (MVP).
3. Add US2 → test → demo; US3 → test → demo; US4 → test → demo; US5 → test → demo.
4. Polish Gate 7 claim review before any release.

---

## Notes

- [P] = different files, no incomplete dependencies.
- [USn] traceability mandatory for story phases.
- Quote data-model constraints verbatim (ENUMs, reconciliation within 1%, P1 n=1, p_adjusted, claim labels).
- Commit after each task; stop at any checkpoint for independent validation.
