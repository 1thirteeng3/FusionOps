# Quickstart & Validation Guide: LocaPredict SLA Guard v3 (Remediation, Constitution v1.1.0)

**Feature**: [spec.md](./spec.md)
**Status**: Completed
**Date**: 2026-09-24

---

## 1. Pré-Requisitos

- Python 3.10+, Node.js 18+, navegador moderno.
- Vault/env `JWT_SECRET` configurado; perfil prod desabilita `/demo-token`.
- Dataset `LocaPredict/data/locaweb_clean.parquet` presente.

---

## 2. Inicialização

```cmd
start_all.bat
```

Backend `http://localhost:8000`, frontend `http://localhost:5173`. Para
serviços separados, ver README (uvicorn + `npm run dev`).

---

## 3. Roteiro de Validação Honesta (Gate 4-7)

### Cenário 1: Triagem calibrada + SHAP real (US-01)
1. Abra a Visão Operacional; localize `INC8654273`.
2. **Esperado**: risco = `100*p_calibrated` com `threshold_tau`, `label_source`,
   `p1_n1_warning` onde aplicável; modal SHAP com `base_value`,
   TreeExplainer `version`, `fidelity_topk`; sem pesos fixos.
3. Reatribua/escale como Operator; **esperado**: risco recalibrado + AuditLog
   com ator e before/after. Como Viewer, **esperado**: 403.

### Cenário 2: Forecast com backtest (US-02)
1. Abra Tático; alterne D+1/D+7.
2. **Esperado**: `model_id`, `wape_holdout` vs. `wape_baseline`, `dm_pvalue`,
   envelope 95%; pico +2d somente se vier do backtest; Team14 120% com
   `claim_label=projection` até piloto.

### Cenário 3: Clusters + drift + retrain (US-03/US-04)
1. Em Engenharia, verifique 5 clusters com `algorithm`, `dbcv`, `stability`,
   FP medido e reconciliação ±1% (cluster-1 sem divergência).
2. Em MLOps, verifique KS com `p_adjusted`, `reference_version`, `window_n`;
   sem p hardcodado.
3. Como Admin, retreine; **esperado**: nova versão + CV/PR-AUC/bootstrap-IC95/Brier
   + audit. Como Viewer/Operator, **esperado**: 403.

### Cenário 4: Segurança e auditoria (US-05)
1. Login sem senha → 401; sem token → 401 (sem fallback anônimo).
2. Exporte CSV (≤1,000 linhas); **esperado**: 200 + `nosniff` + audit + colunas
   de claim rotuladas.

---

## 4. Testes

```bash
pytest
```

**Esperado**: 100% pass incluindo matriz RBAC, rejeição passwordless, ausência
de fallback, calibração/Brier, fidelidade SHAP, backtest forecast, DBCV/
estabilidade, reconciliação de clusters, completude de auditoria e secret-scan.
`tsc && vite build` com zero erros. Qualquer métrica externa sem critérios
congelados, janela, amostra e script de reprodução reprova o Gate 7.
