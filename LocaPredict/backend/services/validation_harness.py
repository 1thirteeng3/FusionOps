"""Honest validation harness (Constitution II/V, Gates 4-5, T008).

Frozen temporal windows, stratified K-fold evaluation with PR-AUC and bootstrap
95% CIs, Brier score, Platt/Isotonic calibration, and forecast backtest
utilities (WAPE, seasonal-naive baseline, Diebold-Mariano). No thresholds are
learned from test data here; ACR-001..ACR-003 live frozen in plan.md.
"""
import numpy as np
from typing import Dict, Any, Tuple
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
