# Implementation Plan: LocaPredict SLA Guard v3 — FusionOps Intelligence Platform

**Branch**: `001-locapredict-sla-guard` | **Date**: 2026-09-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-locapredict-sla-guard/spec.md`

---

## Summary

Remediation plan to bring LocaPredict SLA Guard v3 into compliance with
Constitution v1.1.0. The prior plan (v1.0.0, 100% approval) is void: independent
audit proved resubstitution AUC, pseudo-SHAP, sinusoidal forecast, rule-list
clusters, uncalibrated risk, projection-as-effect claims, synthetic-label
conflation, and auth bypass. This plan keeps the working full-stack skeleton
(FastAPI + React + SQLite + TF-IDF/RF + KS) and replaces each non-compliant
module with an evidence-gated equivalent. No new product scope; no production
promotion until Gates 4-7 pass.

---

## Technical Context

**Language/Version**: Python 3.10+ (Backend), TypeScript 5.7+ / Node.js 18+ (Frontend).

**Primary Dependencies**:
- *Backend*: FastAPI 0.139+, Uvicorn, Scikit-Learn 1.9+, Pandas 3.0+, PyArrow 25.0+, SciPy 1.18+, Pydantic 2.13+, shap (TreeExplainer), hdbscan or bertopic (portability-justified).
- *Frontend*: React 18.3+, Lucide React 0.475+, Vite 6.1+.

**Storage**: SQLite 3 ACID (`incidents`, `audit_logs`, `operational_state`) plus
Apache Parquet/Excel ingestion of 122,543 records. Dual-label columns required:
`ola_breached_synth` (rule) and `kpi_violado_obs` (observed 0.20%).

**Testing**: Pytest 9.1+ (routes, JWT/RBAC matrix, inference, KS drift,
calibration, fidelity, backtest, secret-scan, audit completeness). Frontend
`tsc && vite build` zero-error.

**Target Platform**: Linux / Windows / Docker (Python slim + Nginx).

**Project Type**: Corporate web application (REST + async WebSockets + SPA
glassmorphic).

**Performance Goals**:
- Inference risk + TreeExplainer: < 150 ms p95 local.
- SPA view transition: < 1 s local (SC-004).
- WebSocket event lag: < 50 ms.

**Constraints**:
- Local-first portability; dynamic root-relative data paths.
- Frozen thresholds before test (frozen 2026-09-24, T004): ACR-001 ROC-AUC ≥ 0.85
  on temporal holdout (Dec 2025) with DeLong 95% CI; ACR-002 Recall ≥ 0.80 on
  holdout; ACR-003 WAPE < 15% per horizon from rolling-origin backtest vs.
  seasonal-naive baseline. No threshold changes after seeing test data.
- P1 n=1 disclosure; no P1-generalization.
- Secrets via vault/env only; no committed default; no anonymous fallback.
- Projections labeled as projections until controlled pilot.

**Scale/Scope**:
- 122,543 historical records; 5 squads; 9 products; 5 clusters (counts must
  reconcile within 1%; cluster-1 55,171 vs 100,634 divergence banned).
- 6-feature KS panel with multiplicity correction.

No NEEDS CLARIFICATION remains; all unknowns resolved in research.md (Phase 0).

---

## Constitution Check

*GATE: Mandatory validation against Constitution v1.1.0. Prior v1.0.0 approval is superseded.*

| Principle | Status | Evidence / Remediation |
|---|---|---|
| I. Ground-Truth, Label Honesty & Anti-Mock | **FAIL → REMEDIATE** | Synthetic `ola_breached` (5.16%) conflated with observed KPI (0.20%); P1 n=1 generalized; cluster-1 count divergence. Remediation: dual-label schema, disclosure strings, 1% reconciliation test. |
| II. Honest Validation & Anti-Resubstitution | **FAIL → REMEDIATE** | Train-as-test AUC 0.989 reported; honest CV 0.849. Remediation: stratified K-fold + temporal holdout + PR-AUC + DeLong CI + frozen ACR thresholds. |
| III. Real Explainability with Verified SHAP | **FAIL → REMEDIATE** | Fixed-weight table presented as SHAP. Remediation: TreeExplainer over 55-dim space + top-k fidelity gate. |
| IV. Forecasting & Clustering Evidence | **FAIL → REMEDIATE** | Sinusoid labeled Prophet; keyword rules labeled HDBSCAN. Remediation: fitted forecaster + rolling backtest + Diebold-Mariano; density/topic clusterer + DBCV/stability. |
| V. Calibrated Risk & Causal Discipline | **FAIL → REMEDIATE** | Affine heuristic as probability; -38.5%/-21.4% as causal. Remediation: Platt/Isotonic + Brier/reliability; pilot RCT/DiD/ITS; TOST for transfers. |
| VI. MLOps Observability with Multiplicity Control | **PARTIAL → REMEDIATE** | Genuine KS but uncorrected multiplicity (~26% false alarms), asymmetric n, 2 hardcoded p-values. Remediation: Bonferroni/FDR, symmetric windows, power disclosure. |
| VII. Zero-Trust Auth & Auditability | **FAIL → REMEDIATE** | Anonymous fallback, passwordless login, committed secret, no revocation/rate-limit. Remediation: remove fallback, require credentials, vault secret, RBAC matrix + audit tests. |

*Gate result*: **BLOCKED for production. Proceed to remediation Phases 0-1; implementation gated on Gates 4-7.**

---

## Project Structure

### Documentation (this feature)

```text
specs/001-locapredict-sla-guard/
├── spec.md                  # Especificação funcional e critérios de aceite
├── plan.md                  # Este plano de remediação (Constitution v1.1.0)
├── research.md              # Decisões de engenharia e alternativas (Fase 0, reescrito)
├── data-model.md            # Entidades + proveniência e calibração (Fase 1, reescrito)
├── contracts/
│   └── api_contracts.md     # Contratos REST/WebSocket + proveniência (Fase 1, reescrito)
├── quickstart.md            # Guia de validação honesta (Fase 1, reescrito)
└── checklists/
    └── requirements.md      # Validação de qualidade de requisitos
```

### Source Code (repository root)

```text
LocaPredict/
├── backend/
│   ├── api/routes.py        # Endpoints + RBAC estrito + rótulos projection/measured
│   ├── auth/security.py     # JWT vault-backed, sem fallback, com senha e revogação
│   ├── core/config.py       # CORS whitelist, sem segredo default
│   ├── db/database.py       # SQLite + audit_logs append-only
│   ├── models/schemas.py    # Pydantic v2 + label_source, calibration, provenance
│   ├── services/
│   │   ├── dataset_loader.py# Dual-label + reconciliação de clusters
│   │   ├── itsm_data.py     # Pool com risco calibrado
│   │   └── ml_engine.py     # RF honesto + TreeExplainer + forecaster + clusterer + KS corrigido
│   ├── tests/               # test_api, test_auth, test_ml + fidelity/backtest/security/audit
│   └── main.py              # FastAPI + WebSocket
├── frontend/src/            # Operations/Tactical/Engineering + claim labels + RBAC UI
├── data/                    # locaweb_clean.parquet + LW-DATASET.xlsx
└── requirements.txt         # Inclui shap, hdbscan/bertopic justificados
```

---

## Complexity Tracking

No complexity waiver granted. Added dependencies (shap, density clusterer,
forecaster) are justified per ML Stack Discipline and gated by portability
review. Alternative of keeping pseudo-modules was rejected as constitutional
violation (Principles II-V). Single-responsibility modules retained; provenance
fields add schema cost but are required by Gate 7 claim review.
