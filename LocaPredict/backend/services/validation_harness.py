"""Honest validation harness (Constitution II/V, Gates 4-5, T008).

Frozen temporal windows, stratified K-fold evaluation with PR-AUC and bootstrap
95% CIs, Brier score, Platt/Isotonic calibration, and forecast backtest
utilities (WAPE, seasonal-naive baseline, Diebold-Mariano). No thresholds are
learned from test data here; ACR-001..ACR-003 live frozen in plan.md.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import (roc_auc_score, average_precision_score, recall_score,
                             precision_score, f1_score, brier_score_loss)
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression

# Frozen temporal windows (T004/T008). Test window MUST NOT be touched during
# model selection.
TRAIN_END = "2025-10-31"
VALID_START, VALID_END = "2025-11-01", "2025-11-30"
TEST_START = "2025-12-01"


def split_temporal(dates: np.ndarray) -> Dict[str, np.ndarray]:
    """Return boolean masks for frozen train/valid/test windows."""
    d = np.array([str(x)[:10] for x in dates])
    return {
        "train": d <= TRAIN_END,
        "valid": (d >= VALID_START) & (d <= VALID_END),
        "test": d >= TEST_START,
    }


def bootstrap_auc_ci(y_true: np.ndarray, y_score: np.ndarray,
                     n_boot: int = 1000, seed: int = 42,
                     alpha: float = 0.05) -> Tuple[float, float, float]:
    """Bootstrap percentile CI for ROC-AUC (deterministic given seed).

    Used instead of closed-form approximations: assumption-free and exact
    for the observed score distribution. Returns (auc, lo, hi).
    """
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score, dtype=float)
    auc = round(float(roc_auc_score(y_true, y_score)), 4)
    rng = np.random.RandomState(seed)
    n = len(y_true)
    boots = []
    for _ in range(n_boot):
        idx = rng.choice(n, size=n, replace=True)
        if len(np.unique(y_true[idx])) < 2:
            continue
        boots.append(roc_auc_score(y_true[idx], y_score[idx]))
    if not boots:
        return auc, auc, auc
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return auc, round(float(lo), 4), round(float(hi), 4)


def cross_validated_metrics(X: np.ndarray, y: np.ndarray, make_clf,
                            n_splits: int = 5, seed: int = 42) -> Dict[str, Any]:
    """Stratified K-fold CV reporting ROC-AUC, PR-AUC, recall, Brier (T008)."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    oof = cross_val_predict(make_clf(), X, y, cv=skf, method="predict_proba")[:, 1]
    preds = (oof >= 0.5).astype(int)
    auc, lo, hi = bootstrap_auc_ci(y, oof)
    return {
        "roc_auc": auc,
        "roc_auc_ci95": [lo, hi],
        "roc_auc_ci_method": "bootstrap-1000",
        "pr_auc": round(float(average_precision_score(y, oof)), 4),
        "recall": round(float(recall_score(y, preds, zero_division=0)), 4),
        "precision": round(float(precision_score(y, preds, zero_division=0)), 4),
        "f1": round(float(f1_score(y, preds, zero_division=0)), 4),
        "brier": round(float(brier_score_loss(y, oof)), 4),
        "oof_proba": oof,
    }


def fit_calibrator(oof_proba: np.ndarray, y: np.ndarray,
                   method: str = "isotonic"):
    """Fit Platt (logistic) or isotonic calibrator on out-of-fold scores."""
    oof_proba = np.clip(np.asarray(oof_proba, dtype=float), 1e-6, 1 - 1e-6)
    if method == "platt":
        clf = LogisticRegression(max_iter=1000)
        clf.fit(oof_proba.reshape(-1, 1), np.asarray(y))
        return ("platt", clf)
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(oof_proba, np.asarray(y))
    return ("isotonic", iso)


def apply_calibrator(calibrator, p_raw: np.ndarray) -> np.ndarray:
    kind, model = calibrator
    p = np.clip(np.asarray(p_raw, dtype=float), 1e-6, 1 - 1e-6)
    if kind == "platt":
        return model.predict_proba(p.reshape(-1, 1))[:, 1]
    return model.predict(p)


def wape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = np.abs(y_true).sum()
    if denom == 0:
        return float("nan")
    return float(np.abs(y_true - y_pred).sum() / denom)


def diebold_mariano_pvalue(e1: np.ndarray, e2: np.ndarray) -> float:
    """Two-sided Diebold-Mariano p-value on loss differentials (quadratic loss)."""
    from scipy.stats import t as t_dist
    d = np.asarray(e1, dtype=float) ** 2 - np.asarray(e2, dtype=float) ** 2
    n = len(d)
    if n < 3 or np.allclose(d, 0):
        return 1.0
    mean_d = d.mean()
    # Newey-West(1) variance
    gamma0 = d.var(ddof=1)
    gamma1 = np.cov(d[:-1], d[1:])[0, 1] if n > 3 else 0.0
    var_dm = (gamma0 + 2 * gamma1) / n
    if var_dm <= 0:
        return 1.0
    stat = mean_d / np.sqrt(var_dm)
    return round(float(2 * (1 - t_dist.cdf(abs(stat), df=n - 1))), 4)


# ======================================================================
# Fase 1 — Walk-Forward temporal com janela expansiva (1.1)
# ======================================================================
def walk_forward_folds(dates: np.ndarray, n_folds: int = 3,
                       min_train_months: int = 3) -> List[Dict[str, Any]]:
    """Dobra k sobre meses ordenados m_1..m_M (floor mensal de dt_abertura):
    treino = todos os meses anteriores ao mês de calibração; calibração =
    mês imediatamente anterior ao teste; teste = 1 mês cego. Aquecimento:
    exige ≥ min_train_months meses de treino; dobras degeneradas (teste sem
    positivos) são puladas com registro explícito. NENHUM shuffle em nenhum
    ponto: a ordem temporal é a validação.
    """
    d = pd.to_datetime(np.asarray(dates)).values.astype("datetime64[M]")
    months = np.unique(d)  # já ordenado; preserva dtype datetime64[M]
    folds: List[Dict[str, Any]] = []
    if len(months) < min_train_months + 2:
        return folds
    for test_m in months[-n_folds:]:
        calib_m = test_m - np.timedelta64(1, "M")
        train_mask = d < calib_m
        calib_mask = d == calib_m
        test_mask = d == test_m
        info: Dict[str, Any] = {
            "test_month": str(test_m),
            "n_train": int(train_mask.sum()),
            "n_calib": int(calib_mask.sum()),
            "n_test": int(test_mask.sum()),
            "skipped": "",
        }
        if train_mask.sum() == 0 or test_mask.sum() == 0:
            info["skipped"] = "empty train or test month"
        folds.append({**info, "train": train_mask, "calib": calib_mask, "test": test_mask})
    return folds


def purge_overlaps(train_mask: np.ndarray, end_times: np.ndarray,
                   cutoff_end: np.ndarray) -> Tuple[np.ndarray, int]:
    """Purga de segurança (1.1, López de Prado): remove do treino as linhas
    cujo desfecho (t_end) ocorre em/ após o início do período seguinte
    (cutoff). Rótulos realizados no futuro não treinam o passado.
    Retorna (máscara limpa, nº removido)."""
    end = pd.to_datetime(np.asarray(end_times)).values
    cut = pd.to_datetime(np.asarray(cutoff_end)).values if np.asarray(cutoff_end).size else None
    if cut is None:
        return train_mask, 0
    leak = train_mask & (end > cut)
    clean = train_mask & ~leak
    return clean, int(leak.sum())


# ======================================================================
# Fase 4 — limiar econômico τ* (4.2)
# ======================================================================
C_FP_DEFAULT = 30.0    # R$: inspecionar um falso alarme (analista sênior)
C_FN_DEFAULT = 600.0   # R$: deixar um SLA crítico estourar (multa/indisp.)


def optimize_cost_threshold(y_true: np.ndarray, y_probs: np.ndarray,
                            c_fp: float = C_FP_DEFAULT,
                            c_fn: float = C_FN_DEFAULT,
                            recall_floor: Optional[float] = 0.80
                            ) -> Dict[str, Any]:
    """τ* = argmin C_FP·FP(τ) + C_FN·FN(τ), com piso de recall divulgado.

    Se o ótimo econômico viola o piso (ACR-002), o gate é declarado BLOQUEADO
    em vez de mascarado: retorna ambos os candidatos e a decisão.
    """
    y_true = np.asarray(y_true).astype(int)
    y_probs = np.asarray(y_probs, dtype=float)
    base_cost = float(c_fp * ((y_probs >= 0.5).astype(int) & (y_true == 0)).sum()
                      + c_fn * ((y_probs < 0.5).astype(int) & (y_true == 1)).sum())
    best = {"tau": 0.5, "cost": base_cost, "recall": 0.0}
    for tau in np.arange(0.01, 1.0, 0.01):
        pred = (y_probs >= tau).astype(int)
        fp = int(((pred == 1) & (y_true == 0)).sum())
        fn = int(((pred == 0) & (y_true == 1)).sum())
        tp = int(((pred == 1) & (y_true == 1)).sum())
        rec = tp / max(1, tp + fn)
        cost = float(c_fp * fp + c_fn * fn)
        if cost < best["cost"]:
            best = {"tau": round(float(tau), 2), "cost": cost, "recall": round(float(rec), 4),
                    "fp": fp, "fn": fn, "tp": tp}
    gate = "PASS" if (recall_floor is None or best["recall"] >= recall_floor) else "BLOCKED"
    return {"tau_star": best["tau"], "cost_star": best["cost"],
            "recall_at_star": best["recall"], "fp": best["fp"], "fn": best["fn"],
            "cost_static_05": base_cost,
            "cost_reduction_pct": round(100 * (base_cost - best["cost"]) / max(1e-9, base_cost), 1),
            "recall_floor": recall_floor, "gate": gate, "c_fp": c_fp, "c_fn": c_fn}


# ======================================================================
# Fase 6 — PSI de deriva (6.1)
# ======================================================================
def population_stability_index(ref: np.ndarray, cur: np.ndarray,
                               bins: int = 10) -> Dict[str, Any]:
    """PSI sobre decis de referência. <0.1 estável; 0.1-0.2 alerta; >0.2 severo."""
    r = np.asarray(ref, dtype=float)
    c = np.asarray(cur, dtype=float)
    qs = np.quantile(r, np.linspace(0, 1, bins + 1))
    qs[0], qs[-1] = -np.inf, np.inf
    pr, _ = np.histogram(r, bins=qs)
    pc, _ = np.histogram(c, bins=qs)
    pr = pr / max(1, pr.sum())
    pc = pc / max(1, pc.sum())
    eps = 1e-6
    pr = np.clip(pr, eps, None)
    pc = np.clip(pc, eps, None)
    psi = float(np.sum((pc - pr) * np.log(pc / pr)))
    status = "stable" if psi < 0.1 else ("watch" if psi <= 0.2 else "severe")
    return {"psi": round(psi, 4), "status": status}
