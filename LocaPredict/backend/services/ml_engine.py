"""LocaPredict honest ML engine — fases 1-5 da reformulação matemática.

Arquitetura de duas cabeças sobre GBM (Fase 3):
  Cabeça 1 (MTTR): LightGBM Tweedie p=1.5 (fallback: log-alvo + correção de viés).
  Cabeça 2 (SLA): LightGBM com Focal Loss customizada (γ=2, α=taxa negativa).
Validação: walk-forward temporal expansivo, sem shuffle em nenhum ponto (Fase 1).
Calibração: isotônica ajustada no bloco de calibração da dobra (Fase 4).
Limiar: τ* econômico C_FP·FP + C_FN·FN com piso de recall divulgado (Fase 4).
Explicação: Grouped TreeSHAP por coalizões causais (Fase 5).

Compatibilidade preservada: predict_incident_risk/proba, calculate_incident_shap,
get_forecast/regime/clusters/drift/mlops/metrics/overview, retrain_model.
"""
import math
import time
import threading
import hashlib
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import roc_auc_score, recall_score, precision_score, f1_score
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, average_precision_score
from scipy import stats

import shap

from backend.models.schemas import (
    SHAPFactor, Forecast, DataPoint, Regime, Cluster,
    DriftMetric, MLOpsStatus, MetricsOverview
)
from backend.services.itsm_data import itsm_store, PRODUCTS
from backend.services import dataset_loader
from backend.services.dataset_loader import (
    sanitize_technical_text, HybridTextPipeline, BayesianTargetEncoder,
    add_causal_temporal_features, vif_filter,
)
from backend.services.validation_harness import (
    wape, diebold_mariano_pvalue,
    walk_forward_folds, purge_overlaps, optimize_cost_threshold,
    population_stability_index, bootstrap_auc_ci,
)
from backend.core.config import settings
from backend.db.database import DatabaseRepository
from backend.utils.logger import logger

SHAP_VERSION = getattr(shap, "__version__", "unknown")

try:
    import lightgbm as lgb
    LGBM_AVAILABLE = True
except Exception:
    lgb = None
    LGBM_AVAILABLE = False

META_NAMES = ["prioridade", "squad_responsavel", "produto", "hora_abertura", "item_configuracao"]
META_DISPLAY = {
    "prioridade": "Prioridade do chamado",
    "squad_responsavel": "Squad responsável (backlog)",
    "produto": "Produto afetado",
    "hora_abertura": "Janela de horário de abertura",
    "item_configuracao": "Item de configuração (reincidência)",
}

REGIME_THRESHOLD_VERSION = "regime-v1"
DRIFT_REF_VERSION = "ref-train-sample-v1"
FORECAST_MODEL_ID = "weekly-seasonal-fitted-v1"
ENGINE_MODEL_VERSION = "v4.0.0-walkforward-focal-tweedie"
PREDICT_BUDGET_MS = 45.0  # aceite: pré-processamento+LGBM+calibração+SHAP ≤ 45 ms

TE_COLS = ["prio_clean", "grupo_clean", "produto_clean", "ic_clean"]
NUM_BASE = ["hour", "wd", "title_len", "queue_volume_24h", "arrive_15m",
            "arrive_60m", "arrive_240m", "group_pending_24h", "load_ratio"]

C_FP = float(os.getenv("LOCAPREDICT_C_FP", "30.0"))
C_FN = float(os.getenv("LOCAPREDICT_C_FN", "600.0"))


# ======================================================================
# Fase 3 — Focal Loss binária customizada (3.2)
# ======================================================================
def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(np.asarray(x, dtype=float), -30.0, 30.0)))


def focal_objective(y_pred: np.ndarray, dataset, gamma: float = 2.0,
                    alpha: Optional[float] = None):
    """L = -α_t (1-p_t)^γ ln(p_t). Retorna (grad, hess) no espaço raw.

    p = sigmoid(raw); p_t = p se y=1 senão 1-p; α_t análogo. Estável via clip.
    """
    y = dataset.get_label()
    if alpha is None:
        neg_rate = float((y == 0).mean()) if len(y) else 0.95
        alpha = neg_rate
    raw = np.asarray(y_pred, dtype=float)
    p = 1.0 / (1.0 + np.exp(-np.clip(raw, -30.0, 30.0)))
    p = np.clip(p, 1e-7, 1 - 1e-7)
    yy = np.asarray(y, dtype=float)
    pt = p * yy + (1 - p) * (1 - yy)
    at = alpha * yy + (1 - alpha) * (1 - yy)
    s = 2 * yy - 1.0  # dp_t/dp
    logpt = np.log(pt)
    ompt = 1 - pt
    dfl_dpt = -at * (gamma * ompt ** (gamma - 1) * (-1.0) * logpt + ompt ** gamma / pt)
    dfl_dp = dfl_dpt * s
    dpdraw = p * (1 - p)
    grad = dfl_dp * dpdraw
    # Hessiana: d²/dp²·[p(1-p)]² + d/dp·p(1-p)(1-2p), com d² numérico estável.
    d2fl_dpt2 = -at * (gamma * (gamma - 1) * ompt ** (gamma - 2) * logpt
                       - 2 * gamma * ompt ** (gamma - 1) / pt
                       - ompt ** gamma / (pt ** 2))
    d2fl_dp2 = d2fl_dpt2 * (s ** 2)
    hess = d2fl_dp2 * (dpdraw ** 2) + dfl_dp * dpdraw * (1 - 2 * p)
    hess = np.clip(hess, 1e-6, None)
    return grad, hess


def focal_logloss_eval(y_pred: np.ndarray, dataset):
    y = dataset.get_label()
    p = np.clip(1.0 / (1.0 + np.exp(-np.asarray(y_pred, dtype=float))), 1e-7, 1 - 1e-7)
    yy = np.asarray(y, dtype=float)
    loss = -(yy * np.log(p) + (1 - yy) * np.log(1 - p)).mean()
    return "focal_logloss", float(loss), False


class MLEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self.model_version = ENGINE_MODEL_VERSION
        self.last_trained = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        self.regime_override: Optional[str] = None
        self.training_in_progress = False

        # Métricas honestas (walk-forward). Nunca ressubstituição.
        self.roc_auc = 0.0
        self.cv_pr_auc = 0.0
        self.auc_ci95 = [0.0, 0.0]
        self.auc_ci_method = "bootstrap-1000"
        self.brier = 0.0
        self.brier_gate = "UNKNOWN"
        self.decile_max_err = 1.0
        self.recall = 0.0
        self.precision = 0.0
        self.f1_score = 0.0
        self.threshold_tau = 0.5   # τ* econômico (Fase 4), piso de recall divulgado
        self.tau_report: Dict[str, Any] = {}
        self.cost_baseline_05 = 0.0
        self.wape = 0.0
        self.wape_baseline = 0.0
        self.dm_pvalue = 1.0
        self.mdape_mttr = 1.0      # MdAPE do MTTR na dobra cega
        self.mttr_sigma2 = 0.0     # variância residual p/ correção de viés (via log)
        self.mttr_cap = 0.0        # winsorização p99.9 do treino (divulgada)
        self.last_inference_ms: float = 0.0

        # Artefatos de produção (janelas da última dobra, determinísticos).
        self.text_pipe: Optional[HybridTextPipeline] = None
        self.text_dim = 0
        self.te_encoder: Optional[BayesianTargetEncoder] = None
        self.vif_kept: List[str] = []
        self.vif_report: Dict[str, Any] = {}
        self.feature_names: List[str] = []
        self.coalitions: Dict[str, List[int]] = {}
        self.classifier = None     # LGBM focal (ou fallback sklearn)
        self.regressor = None      # mediana condicional (quantile α=0.5)
        self.mean_regressor = None  # média Tweedie p=1.5 (diagnóstico)
        self.reg_is_log = False    # True se via secundária logarítmica
        self.calibrator = None     # isotônica no bloco de calibração
        self.explainer = None
        self.walk_report: List[Dict[str, Any]] = []

        # KS refs legadas (compat) + PSI refs (Fase 6).
        self.ref_backlogs: np.ndarray = np.array([])
        self.ref_hours: np.ndarray = np.array([])
        self.ref_durations: np.ndarray = np.array([])
        self.ref_recurrences: np.ndarray = np.array([])
        self.ref_product_idx: np.ndarray = np.array([])
        self.ref_title_len: np.ndarray = np.array([])
        self.psi_refs: Dict[str, np.ndarray] = {}
        self.validation_brier = 0.0
        self.auto_block = False    # Fase 6: bloqueio >20% degradação
        self.auto_block_reason = ""

        # Forecaster legado (módulo preservado).
        self._daily_index: List[str] = []
        self._daily_values: np.ndarray = np.array([])
        self._weekday_profile: np.ndarray = np.zeros(7)
        self._drift_per_day: float = 0.0
        self._residual_sigma: float = 1.0
        self._cluster_report: Optional[Dict[str, Any]] = None

        # Compat: vetorizador legado (aponta p/ pipeline de texto pós-treino).
        self.vectorizer = TfidfVectorizer(max_features=50, stop_words=['de', 'a', 'o', 'em', 'no', 'na', 'para', 'com', 'da', 'do', 'por'])

        self._train_initial_models()

    # ------------------------------------------------------------------
    # Compat: extração legada (mantida p/ chamadas antigas; motor usa _row_X)
    # ------------------------------------------------------------------
    def _extract_features(self, text: str, prio: str, group: str, prod: str, ic: str, hour: int) -> np.ndarray:
        try:
            text_vec = self.vectorizer.transform([text]).toarray()[0]
        except Exception:
            text_vec = np.zeros(50)
        prio_num = 4.0 if prio == "P1" else (3.0 if prio == "P2" else (2.0 if prio == "P3" else 1.0))
        group_idx = dataset_loader.group_index(group)
        prod_idx = float(PRODUCTS.index(prod) if prod in PRODUCTS else 0)
        hour_norm = float(hour) / 24.0
        ic_num = 1.0
        try:
            ic_num = float(ic.replace("IC", "")) / 100.0
        except Exception:
            pass
        return np.concatenate([text_vec, np.array([prio_num, group_idx, prod_idx, hour_norm, ic_num])])

    # ------------------------------------------------------------------
    # Construção do frame honesto (Fases 1-2)
    # ------------------------------------------------------------------
    def _build_frame(self) -> pd.DataFrame:
        df = dataset_loader.get_or_create_processed_dataset().copy()
        df["dt_aberto"] = pd.to_datetime(df["aberto"], errors="coerce")
        df = df.dropna(subset=["dt_aberto"]).reset_index(drop=True)
        df["hour"] = df["dt_aberto"].dt.hour.fillna(14).astype(int)
        df["wd"] = df["dt_aberto"].dt.weekday.fillna(2).astype(int)
        df["title_len"] = df["titulo_clean"].astype(str).str.len().astype(float)
        df["title_text"] = (df["titulo_clean"].astype(str) + " " + df["produto_clean"].astype(str)
                            + " squad " + df["grupo_clean"].astype(str)
                            + " prioridade " + df["prio_clean"].astype(str))
        df["y_breach"] = df["ola_breached_synth"].astype(int) if "ola_breached_synth" in df.columns else df["ola_breached"].astype(int)
        df["y_minutes"] = (pd.to_numeric(df["duracao_sec"], errors="coerce").fillna(14) / 60.0).clip(lower=1.0 / 60.0)
        df["t_end"] = df["dt_aberto"] + pd.to_timedelta(df["duracao_sec"], unit="s")
        df, _ = add_causal_temporal_features(df)
        return df.sort_values("dt_aberto").reset_index(drop=True)

    def _fit_fold_pipeline(self, dft: pd.DataFrame, ytr: np.ndarray):
        """Ajusta texto+TE+VIF só no treino da dobra. Retorna (Xtr, meta)."""
        tp = HybridTextPipeline(k=50)
        tp.fit(dft["title_text"].tolist())
        Xt = tp.transform(dft["title_text"].tolist())
        te = BayesianTargetEncoder(m=10.0)
        te.fit(dft, TE_COLS, pd.Series(ytr, index=dft.index))
        Xte = te.transform(dft, TE_COLS)
        num = dft[NUM_BASE].copy()
        kept, vrep = vif_filter(num)
        cols = [f"lsa_{i}" for i in range(Xt.shape[1])] + [c + "__te" for c in TE_COLS] + kept
        X = np.concatenate([Xt, Xte.values, dft[kept].values.astype(float)], axis=1)
        meta = {"text_dim": Xt.shape[1], "te_cols": [c + "__te" for c in TE_COLS],
                "num_kept": kept, "vif": vrep}
        return X, meta, tp, te

    def _apply_fold_pipeline(self, dfx: pd.DataFrame, tp, te, meta) -> np.ndarray:
        Xt = tp.transform(dfx["title_text"].tolist())
        if Xt.shape[1] != meta["text_dim"]:
            # Dimensão estável por construção (SVD k fixo); guarda honesta.
            raise RuntimeError(f"Dimensão textual divergente: {Xt.shape[1]} != {meta['text_dim']}")
        Xte = te.transform(dfx, TE_COLS)
        return np.concatenate([Xt, Xte.values, dfx[meta["num_kept"]].values.astype(float)], axis=1)

    def _feature_names(self, meta) -> List[str]:
        return ([f"lsa_{i}" for i in range(meta["text_dim"])] + meta["te_cols"] + meta["num_kept"])

    def _coalitions(self, names: List[str]) -> Dict[str, List[int]]:
        """Coalizões causais fechadas sobre os nomes finais (Fase 5)."""
        idx = {n: i for i, n in enumerate(names)}
        sobrecarga = [n for n in names if n in ("hour", "wd", "queue_volume_24h", "arrive_15m",
                                                "arrive_60m", "arrive_240m")]
        capacidade = [n for n in names if n.endswith("__te") or n in ("load_ratio", "group_pending_24h")]
        severidade = [n for n in names if n.startswith("lsa_")] + ([n for n in names if n == "title_len"] if "title_len" in idx else [])
        return {"sobrecarga_turno": [idx[n] for n in sobrecarga],
                "capacidade_tecnica": [idx[n] for n in capacidade],
                "severidade_semantica": [idx[n] for n in severidade]}

    # ------------------------------------------------------------------
    # Treino walk-forward + artefatos de produção (Fases 1,3,4)
    # ------------------------------------------------------------------
    def _lgbm_clf(self, Xtr, ytr, Xva, yva):
        dtrain = lgb.Dataset(Xtr, label=ytr)
        dvalid = lgb.Dataset(Xva, label=yva, reference=dtrain)
        params = {"objective": focal_objective, "metric": "None", "verbosity": -1,
                  "learning_rate": 0.05, "num_leaves": 31, "min_data_in_leaf": 50,
                  "feature_pre_filter": False, "seed": settings.RANDOM_SEED,
                  "deterministic": True, "num_threads": 1}
        return lgb.train(params, dtrain, num_boost_round=400, valid_sets=[dvalid],
                         feval=focal_logloss_eval,
                         callbacks=[lgb.early_stopping(30, verbose=False), lgb.log_evaluation(-1)])

    def _lgbm_reg(self, Xtr, ytr, Xva, yva):
        """MTTR: mediana condicional (quantile α=0.5) como cabeça primária.

        Desvio documentado da Fase 3: o aceite (MdAPE<18%) é métrica MEDIANA;
        estimador de média (Tweedie) é matematicamente incompatível com ele
        sob assimetria ×254 (mediana 16min, média 4142min). A média Tweedie
        segue como diagnóstico secundário (planejamento de capacidade usa
        médias). Fallback: via logarítmica com correção de viés.
        """
        cap = float(np.quantile(ytr, 0.999))
        diag = {"tweedie_mean_ok": False}
        # Diagnóstico Tweedie p=1.5 (média) — melhor esforço, nunca fatal.
        try:
            dtr = lgb.Dataset(Xtr, label=np.clip(ytr, None, cap))
            dva = lgb.Dataset(Xva, label=np.asarray(yva), reference=dtr)
            pm = {"objective": "tweedie", "tweedie_variance_power": 1.5,
                  "metric": "tweedie", "verbosity": -1, "learning_rate": 0.05,
                  "num_leaves": 31, "min_data_in_leaf": 50, "seed": settings.RANDOM_SEED,
                  "deterministic": True, "num_threads": 1}
            mean_model = lgb.train(pm, dtr, num_boost_round=400, valid_sets=[dva],
                                   callbacks=[lgb.early_stopping(30, verbose=False), lgb.log_evaluation(-1)])
            diag["tweedie_mean_ok"] = True
        except Exception as e:
            logger.warning(f"Tweedie diagnóstico falhou (não-fatal): {e}")
            mean_model = None
        # Cabeça primária: mediana condicional.
        try:
            dtr = lgb.Dataset(Xtr, label=np.asarray(ytr, dtype=float))
            dva = lgb.Dataset(Xva, label=np.asarray(yva, dtype=float), reference=dtr)
            pq = {"objective": "quantile", "alpha": 0.5, "metric": "quantile",
                  "verbosity": -1, "learning_rate": 0.05,
                  "num_leaves": 31, "min_data_in_leaf": 50, "seed": settings.RANDOM_SEED,
                  "deterministic": True, "num_threads": 1}
            med = lgb.train(pq, dtr, num_boost_round=400, valid_sets=[dva],
                            callbacks=[lgb.early_stopping(30, verbose=False), lgb.log_evaluation(-1)])
            return (med, mean_model), False, 0.0, cap, diag
        except Exception as e:
            logger.warning(f"Quantile falhou; via logarítmica secundária: {e}")
            ytr_c = np.clip(ytr, None, cap)
            ztr = np.log(ytr_c + 1.0)
            dtr = lgb.Dataset(Xtr, label=ztr)
            dva = lgb.Dataset(Xva, label=np.log(np.asarray(yva) + 1.0), reference=dtr)
            pr = {"objective": "regression", "metric": "l2", "verbosity": -1,
                  "learning_rate": 0.05, "num_leaves": 31, "min_data_in_leaf": 50,
                  "seed": settings.RANDOM_SEED, "deterministic": True, "num_threads": 1}
            booster = lgb.train(pr, dtr, num_boost_round=400, valid_sets=[dva],
                                callbacks=[lgb.early_stopping(30, verbose=False), lgb.log_evaluation(-1)])
            resid = ztr - booster.predict(Xtr)
            return (booster, mean_model), True, float(np.var(resid)), cap, diag

    def _train_initial_models(self):
        with self._lock:
            t0 = time.perf_counter()
            logger.info("Treino walk-forward (fases 1-5): sem shuffle, purging, focal+tweedie...")
            if not LGBM_AVAILABLE:
                logger.warning("LightGBM ausente: fallback sklearn será usado (sem focal/custom).")
            df = self._build_frame()
            dates = df["dt_aberto"].values
            folds = walk_forward_folds(dates, n_folds=3, min_train_months=3)
            folds = [f for f in folds if not f["skipped"]]
            if not folds:
                raise RuntimeError("Sem dobras temporais viáveis: dados insuficientes.")

            fold_reports = []
            calib_pool_p, calib_pool_y = [], []
            for f in folds:
                dft = df[f["train"]].copy()
                dfc = df[f["calib"]].copy()
                dftst = df[f["test"]].copy()
                # Purging (López de Prado): treino exclui linhas cujo desfecho
                # (t_end) invade o período de calibração/teste — rótulos
                # realizados no futuro não treinam o passado.
                cut = dfc["dt_aberto"].min()
                mask, n_purged = purge_overlaps(np.ones(len(dft), dtype=bool),
                                                dft["t_end"].values, np.array([cut]))
                dft = dft[mask].reset_index(drop=True)
                ytr = dft["y_breach"].values.astype(int)
                yva = dfc["y_breach"].values.astype(int)
                yte = dftst["y_breach"].values.astype(int)
                if yte.sum() < 5 or ytr.sum() < 10:
                    fold_reports.append({"test_month": f["test_month"], "skipped": "few positives"})
                    continue
                Xtr, meta, tp, te = self._fit_fold_pipeline(dft, ytr)
                Xva = self._apply_fold_pipeline(dfc, tp, te, meta)
                Xte = self._apply_fold_pipeline(dftst, tp, te, meta)
                names = self._feature_names(meta)

                if LGBM_AVAILABLE:
                    clf = self._lgbm_clf(Xtr, ytr, Xva, yva)
                    # Com objetivo customizado, predict() retorna RAW margin:
                    # converter para probabilidade antes de calibrar/avaliar.
                    s_va = _sigmoid(clf.predict(Xva))
                    s_te_raw = _sigmoid(clf.predict(Xte))
                    (med, _mean), reg_is_log, sigma2, cap, _diag = self._lgbm_reg(
                        Xtr, dft["y_minutes"].values, Xva, dfc["y_minutes"].values)
                    if reg_is_log:
                        mttr_te = np.exp(med.predict(Xte) + sigma2 / 2.0) - 1.0
                    else:
                        mttr_te = np.maximum(med.predict(Xte), 1.0 / 60.0)
                else:
                    from sklearn.ensemble import HistGradientBoostingClassifier
                    from sklearn.linear_model import TweedieRegressor
                    clf = HistGradientBoostingClassifier(class_weight="balanced", random_state=settings.RANDOM_SEED)
                    clf.fit(Xtr, ytr)
                    s_va = clf.predict_proba(Xva)[:, 1]
                    s_te_raw = clf.predict_proba(Xte)[:, 1]
                    reg = TweedieRegressor(power=1.5, alpha=0.5, max_iter=300)
                    reg.fit(Xtr, np.clip(dft["y_minutes"].values, None, float(np.quantile(dft["y_minutes"].values, 0.999))))
                    reg_is_log, sigma2 = False, 0.0
                    mttr_te = np.maximum(reg.predict(Xte), 1.0 / 60.0)

                iso = IsotonicRegression(out_of_bounds="clip")
                iso.fit(np.clip(s_va, 1e-6, 1 - 1e-6), yva)
                p_te = np.clip(iso.predict(np.clip(s_te_raw, 1e-6, 1 - 1e-6)), 0.0, 1.0)
                calib_pool_p.extend(np.clip(iso.predict(np.clip(s_va, 1e-6, 1 - 1e-6)), 0.0, 1.0).tolist())
                calib_pool_y.extend(yva.tolist())

                auc = round(float(roc_auc_score(yte, s_te_raw)), 4)
                bs = round(float(brier_score_loss(yte, p_te)), 4)
                ytm = dftst["y_minutes"].values
                mdape = float(np.median(np.abs(ytm - mttr_te) / np.maximum(ytm, 1e-9)))
                self._last_blind = (np.asarray(yte, dtype=int), np.asarray(p_te, dtype=float))
                fold_reports.append({
                    "test_month": f["test_month"], "n_train": f["n_train"],
                    "n_purged": int(n_purged), "roc_auc": auc,
                    "pr_auc": round(float(average_precision_score(yte, s_te_raw)), 4),
                    "brier_blind": bs, "mdape_mttr": round(mdape, 4),
                    "pos_rate_test": round(float(yte.mean()), 4),
                })
            self.walk_report = fold_reports
            ok = [r for r in fold_reports if "roc_auc" in r]
            if not ok:
                raise RuntimeError("Todas as dobras degeneradas; treino abortado.")
            last = ok[-1]

            # τ* econômico no pool de calibração (Fase 4) + gate de recall.
            tau = optimize_cost_threshold(np.array(calib_pool_y), np.array(calib_pool_p),
                                          c_fp=C_FP, c_fn=C_FN, recall_floor=0.80)
            self.tau_report = tau
            self.threshold_tau = float(tau["tau_star"])
            self.cost_baseline_05 = float(tau["cost_static_05"])

            # Métricas primárias = última dobra cega (aceite).
            self.roc_auc = float(last["roc_auc"])
            self.cv_pr_auc = float(last["pr_auc"])
            self.brier = float(last["brier_blind"])
            self.mdape_mttr = float(last["mdape_mttr"])
            self.validation_brier = self.brier
            preds = None  # (removido placeholder; métricas vêm do pool de calibração)
            # Recall/precision/F1 no pool de calibração em τ*.
            pc = np.array(calib_pool_p)
            yc = np.array(calib_pool_y)
            pp = (pc >= self.threshold_tau).astype(int)
            self.recall = round(float(recall_score(yc, pp, zero_division=0)), 3)
            self.precision = round(float(precision_score(yc, pp, zero_division=0)), 3)
            self.f1_score = round(float(f1_score(yc, pp, zero_division=0)), 3)
            # IC bootstrap do AUC: pool de calibração como aproximação divulgada
            # (a dobra cega não é reamostrada para não tocar no teste).
            try:
                _, lo, hi = bootstrap_auc_ci(yc, pc)
                self.auc_ci95 = [lo, hi]
            except Exception:
                pass
            self.auc_ci_method = "bootstrap-1000"
            self.brier_gate, self.decile_max_err = self._brier_gate(last)

            # Artefatos de produção = refit determinístico das janelas da última dobra.
            self._refit_production(df, fold_reports)
            # Refs KS legadas + PSI refs.
            self._build_refs()
            self._fit_forecaster()

            # Reseed versionado + recalibração do pool (compat T015).
            try:
                saved_seed = DatabaseRepository.get_state("seed_model_version")
                if saved_seed != self.model_version:
                    itsm_store.reseed_from_dataset()
                    DatabaseRepository.set_state("seed_model_version", self.model_version)
            except Exception as e:
                logger.warning(f"Pool reseed check skipped: {e}")
            try:
                itsm_store.recalibrate_pool(self.predict_incident_proba,
                                            self.calculate_incident_shap,
                                            self.threshold_tau,
                                            self.predict_mttr_minutes,
                                            self.risk_category)
            except Exception as e:
                logger.warning(f"Pool recalibration skipped: {e}")
            dt = time.perf_counter() - t0
            logger.info(
                f"Walk-forward treinado em {dt:.1f}s. Blind Dec: AUC {self.roc_auc}, "
                f"Brier {self.brier} (gate {self.brier_gate}), MdAPE {self.mdape_mttr}, "
                f"τ*={self.threshold_tau} (custo -{self.tau_report.get('cost_reduction_pct', 0)}%).")

    def _brier_gate(self, last: Dict[str, Any]):
        """Aceite: Brier ≤ 0.08 e erro decil < 5% na dobra cega (Fase 4)."""
        bs = float(last["brier_blind"])
        max_err = 1.0
        try:
            yte, p_te = self._last_blind
            qs = np.quantile(p_te, np.linspace(0, 1, 11))
            errs = []
            for b in range(10):
                m = (p_te >= qs[b]) & (p_te <= qs[b + 1] if b < 9 else p_te <= 1.0)
                if m.sum() >= 10:
                    errs.append(abs(float(p_te[m].mean()) - float(yte[m].mean())))
            max_err = round(float(max(errs)) if errs else 1.0, 4)
        except Exception:
            pass
        gate = "PASS" if (bs <= 0.08 and max_err < 0.05) else "BLOCKED"
        return gate, max_err

    def _refit_production(self, df: pd.DataFrame, folds: List[Dict[str, Any]]):
        """Refit determinístico nas janelas da última dobra (treino+calib)."""
        f = [x for x in folds if "roc_auc" in x][-1]
        # Recupera máscaras da última dobra válida.
        dates = df["dt_aberto"].values
        allf = walk_forward_folds(dates, n_folds=3, min_train_months=3)
        target = [x for x in allf if x["test_month"] == f["test_month"]][0]
        dft = df[target["train"]].copy()
        dfc = df[target["calib"]].copy()
        cutoff_end = dft["dt_aberto"].max()
        mask, _ = purge_overlaps(np.ones(len(dft), dtype=bool), dft["t_end"].values, np.array([cutoff_end]))
        dft = dft[mask].reset_index(drop=True)
        ytr = dft["y_breach"].values.astype(int)
        yva = dfc["y_breach"].values.astype(int)
        Xtr, meta, tp, te = self._fit_fold_pipeline(dft, ytr)
        Xva = self._apply_fold_pipeline(dfc, tp, te, meta)
        names = self._feature_names(meta)
        if LGBM_AVAILABLE:
            clf = self._lgbm_clf(Xtr, ytr, Xva, yva)
            s_va = _sigmoid(clf.predict(Xva))
            (med, mean_model), reg_is_log, sigma2, cap, _diag = self._lgbm_reg(
                Xtr, dft["y_minutes"].values, Xva, dfc["y_minutes"].values)
            reg, mean_reg = med, mean_model
        else:
            from sklearn.ensemble import HistGradientBoostingClassifier
            from sklearn.linear_model import TweedieRegressor
            clf = HistGradientBoostingClassifier(class_weight="balanced", random_state=settings.RANDOM_SEED)
            clf.fit(Xtr, ytr)
            s_va = clf.predict_proba(Xva)[:, 1]
            reg = TweedieRegressor(power=1.5, alpha=0.5, max_iter=300)
            cap = float(np.quantile(dft["y_minutes"].values, 0.999))
            reg.fit(Xtr, np.clip(dft["y_minutes"].values, None, cap))
            reg_is_log, sigma2 = False, 0.0
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(np.clip(s_va, 1e-6, 1 - 1e-6), yva)
        # IC bootstrap do AUC: usa OOF da calibração (aproximação divulgada).
        try:
            from backend.services.validation_harness import bootstrap_auc_ci
            _, lo, hi = bootstrap_auc_ci(yva, np.clip(s_va, 0.0, 1.0))
            self.auc_ci95 = [lo, hi]
        except Exception:
            pass
        self.text_pipe, self.text_dim = tp, tp.dim
        self.te_encoder = te
        self.vif_kept, self.vif_report = meta["num_kept"], {"vif": meta["vif"]}
        self.feature_names = names
        self.coalitions = self._coalitions(names)
        self.classifier = clf
        self.regressor = reg
        self.mean_regressor = mean_reg  # Tweedie-média p/ diagnóstico de capacidade
        self.reg_is_log = reg_is_log
        self.mttr_sigma2 = float(sigma2)
        self.mttr_cap = float(cap)
        self.calibrator = ("isotonic-blind", iso)
        self.vectorizer.fit(dft["title_text"].head(2000).tolist() if "title_text" in dft.columns else ["risco ola backlog"])
        # TreeExplainer path-dependent: exato no raw-margin e rápido (sem
        # background interventional, que estouraria o orçamento de 45 ms).
        self.explainer = shap.TreeExplainer(self.classifier, feature_perturbation="tree_path_dependent")
        # PSI refs: distribuições do treino de produção por feature final.
        self.psi_refs = {n: np.asarray(Xtr[:, i], dtype=float) for i, n in enumerate(names)}

    # ------------------------------------------------------------------
    # Inferência: probabilidade calibrada + MTTR + SHAP (Fases 3-5)
    # ------------------------------------------------------------------
    def _row_frame(self, title: str, priority: str, group: str, product: str,
                   config_item: str, hour: int, now: Optional[datetime] = None) -> pd.DataFrame:
        """Linha de inferência com contexto vivo (aproximação divulgada).

        queue/arrive/load usam o pool ativo + baselines do loader (Seção F1):
        aproximação operacional, não valores históricos exatos.
        """
        now = now or datetime.now()
        live = itsm_store.get_all_incidents()
        t_now = now
        opens = []
        for inc in live:
            try:
                opens.append(pd.Timestamp(inc.created_at))
            except Exception:
                pass
        opens = pd.DatetimeIndex(opens) if opens else pd.DatetimeIndex([])
        q24 = int(((opens >= t_now - timedelta(hours=24)) & (opens <= t_now)).sum())
        a15 = int(((opens >= t_now - timedelta(minutes=15)) & (opens <= t_now)).sum())
        a60 = int(((opens >= t_now - timedelta(minutes=60)) & (opens <= t_now)).sum())
        a240 = int(((opens >= t_now - timedelta(minutes=240)) & (opens <= t_now)).sum())
        gpend = int(sum(1 for inc in live if inc.group == group))
        row = {
            "title_text": sanitize_technical_text(
                f"{title} {product} squad {group} prioridade {priority}"),
            "prio_clean": priority, "grupo_clean": group, "produto_clean": product,
            "ic_clean": config_item, "hour": int(hour), "wd": int(now.weekday()),
            "title_len": float(len(str(title))),
            "queue_volume_24h": float(q24), "arrive_15m": float(a15),
            "arrive_60m": float(a60), "arrive_240m": float(a240),
            "group_pending_24h": float(gpend), "load_ratio": 1.0,
        }
        return pd.DataFrame([row])

    def _row_X(self, row: pd.DataFrame) -> np.ndarray:
        Xt = self.text_pipe.transform(row["title_text"].tolist())
        Xte = self.te_encoder.transform(row, TE_COLS)
        return np.concatenate([Xt, Xte.values, row[self.vif_kept].values.astype(float)], axis=1)

    def predict_incident_proba(self, title: str, priority: str, group: str,
                               product: str, config_item: str,
                               hour: int = 14) -> Tuple[float, float]:
        """(p_raw, p_calibrada). Só p_calibrada pode ser exibida (Fase 4)."""
        if self.classifier is None or self.calibrator is None:
            return 0.50, 0.50
        X = self._row_X(self._row_frame(title, priority, group, product, config_item, hour))
        if LGBM_AVAILABLE:
            raw = float(self.classifier.predict(X)[0])
            p_raw = float(_sigmoid(np.array([raw]))[0])
        else:
            p_raw = float(self.classifier.predict_proba(X)[0][1])
        _, iso = self.calibrator
        p_cal = float(np.clip(iso.predict(np.clip([p_raw], 1e-6, 1 - 1e-6))[0], 0.0, 1.0))
        return round(p_raw, 4), round(p_cal, 4)

    def predict_mttr_minutes(self, title: str, priority: str, group: str,
                             product: str, config_item: str, hour: int = 14) -> float:
        """MTTR em minutos: Tweedie direta ou log-alvo com correção (Fase 3)."""
        if self.regressor is None:
            return 15.0
        X = self._row_X(self._row_frame(title, priority, group, product, config_item, hour))
        if LGBM_AVAILABLE:
            out = float(self.regressor.predict(X)[0])
            if self.reg_is_log:
                out = float(np.exp(out + self.mttr_sigma2 / 2.0) - 1.0)
            return round(max(out, 1.0 / 60.0), 2)
        return round(float(max(self.regressor.predict(X)[0], 1.0 / 60.0)), 2)

    def risk_category(self, p_cal: float) -> str:
        """CRITICAL p≥τ*; WARNING [τ*/4, τ*); SAFE abaixo (Fase 4/7)."""
        tau = max(self.threshold_tau, 1e-9)
        if p_cal >= tau:
            return "CRITICAL"
        if p_cal >= tau / 4.0:
            return "WARNING"
        return "SAFE"

    def predict_incident_risk(
        self,
        title: str,
        priority: str,
        group: str,
        product: str,
        config_item: str,
        hour: int = 14,
        duration_seconds: int = 14,
        is_fp: bool = False
    ) -> Tuple[int, List[SHAPFactor]]:
        """Risco calibrado 0-100 + SHAP verificado (compat T013)."""
        with self._lock:
            t0 = time.perf_counter()
            if self.auto_block:
                raise RuntimeError(f"Inferência automática bloqueada: {self.auto_block_reason}")
            p_raw, p_cal = self.predict_incident_proba(
                title, priority, group, product, config_item, hour)
            risk_score = max(1, min(99, int(round(p_cal * 100.0))))
            shap_factors = self.calculate_incident_shap({
                "title": title, "priority": priority, "group": group,
                "product": product, "config_item": config_item, "hour": hour,
                "duration_seconds": duration_seconds, "is_automated_fp": is_fp,
                "p_raw": p_raw, "p_calibrated": p_cal,
            })
            self.last_inference_ms = round((time.perf_counter() - t0) * 1000, 2)
            if self.last_inference_ms > PREDICT_BUDGET_MS:
                logger.warning(f"Orçamento de inferência excedido: {self.last_inference_ms} ms > {PREDICT_BUDGET_MS} ms.")
            return risk_score, shap_factors

    def _shap_row(self, X: np.ndarray):
        """Valores de Shapley no espaço raw-margin + base (Fase 5)."""
        if self.explainer is None:
            raise RuntimeError("SHAP explainer is not fitted; Gate 5 blocks inference.")
        sv = np.asarray(self.explainer.shap_values(X.reshape(1, -1) if X.ndim == 1 else X))
        if sv.ndim == 3:
            sv = sv[0, :, 1] if sv.shape[2] > 1 else sv[0, :, 0]
        elif sv.ndim == 2 and sv.shape[0] == 1:
            sv = sv[0]
        sv = np.asarray(sv, dtype=float).ravel()
        ev = self.explainer.expected_value
        if isinstance(ev, (list, np.ndarray)):
            arr = np.asarray(ev).ravel()
            ev = float(arr[1] if arr.size > 1 else arr[0])
        else:
            ev = float(ev)
        return sv, ev

    def grouped_shap(self, X: np.ndarray) -> Tuple[List[Dict[str, Any]], float, np.ndarray, float]:
        """Φ_G = Σ φ_j por coalizão causal + fechamento aditivo (Fase 5)."""
        sv, ev = self._shap_row(X)
        groups = []
        for gname, idxs in self.coalitions.items():
            phi = round(float(sv[idxs].sum()) if idxs else 0.0, 4)
            members = sorted(((self.feature_names[i], round(float(sv[i]), 4)) for i in idxs),
                             key=lambda kv: -abs(kv[1]))[:5]
            groups.append({"group": gname, "phi": phi, "members": members})
        groups.sort(key=lambda g: -abs(g["phi"]))
        return groups, ev, sv, ev

    def calculate_incident_shap(self, incident_dict: Dict[str, Any]) -> List[SHAPFactor]:
        """Fatores flat (compat) com grupo causal + proveniência; soma fecha no raw."""
        title = str(incident_dict.get("title", ""))
        prio = incident_dict.get("priority", incident_dict.get("prio", "P3"))
        group = incident_dict.get("group", "Team14")
        prod = incident_dict.get("product", incident_dict.get("prod", "Hosting Linux"))
        ic = incident_dict.get("config_item", incident_dict.get("ic", "IC00001"))
        hour = int(incident_dict.get("hour", 14))
        X = self._row_X(self._row_frame(title, prio, group, prod, ic, hour))
        groups, ev, sv, _ = self.grouped_shap(X)
        g_of = {}
        for g in groups:
            for name, _ in g["members"]:
                g_of.setdefault(name, g["group"])
        # Fidelidade top-k por remoção mascarada.
        order = np.argsort(-np.abs(sv))[:5]
        topk = order[:3]
        bg = np.zeros(X.shape[1])
        masked = X.copy().reshape(1, -1)
        masked[0, topk] = bg[topk]
        try:
            if LGBM_AVAILABLE:
                f = lambda M: float(1.0 / (1.0 + np.exp(-self.classifier.predict(M)[0])))
                fidelity = round(float(np.clip(f(X.reshape(1, -1)) - f(masked), -1.0, 1.0)), 3)
            else:
                f = lambda M: float(self.classifier.predict_proba(M)[0][1])
                fidelity = round(float(np.clip(f(X.reshape(1, -1)) - f(masked), -1.0, 1.0)), 3)
        except Exception:
            fidelity = 0.0
        factors: List[SHAPFactor] = []
        for dim in order:
            v = round(float(sv[dim]), 4)
            fname = self.feature_names[dim] if dim < len(self.feature_names) else f"dim-{dim}"
            factors.append(SHAPFactor(
                feature=fname, value=v,
                impact="positive" if v >= 0 else "negative",
                display_name=self._shap_display_name(fname),
                feature_value_str=f"contribuição local no raw-margin",
                base_value=round(ev, 4),
                explainer="shap.TreeExplainer",
                explainer_version=SHAP_VERSION,
                fidelity_topk=fidelity,
                group=g_of.get(fname, "outros"),
            ))
        return factors

    def _shap_display_name(self, fname: str) -> str:
        if fname.startswith("lsa_"):
            return f"Severidade semântica ({fname})"
        if fname.endswith("__te"):
            return f"Capacidade codificada ({fname[:-4]})"
        pt = {"hour": "Hora de abertura", "wd": "Dia da semana",
              "title_len": "Tamanho do título", "queue_volume_24h": "Volume concorrente (24h)",
              "arrive_15m": "Chegadas 15m", "arrive_60m": "Chegadas 60m",
              "arrive_240m": "Chegadas 240m", "group_pending_24h": "Pendentes do grupo",
              "load_ratio": "Carga relativa do grupo"}
        if fname in pt:
            return pt[fname]
        return META_DISPLAY.get(fname, fname.replace("_", " "))

    # ------------------------------------------------------------------
    # Refs KS legadas + forecaster + regime + clusters + drift + métricas
    # (módulos preservados; limiares passam a τ*)
    # ------------------------------------------------------------------
    def _build_refs(self):
        backlog_samples, hour_samples, duration_samples = [], [], []
        recurrence_samples, product_samples, titlelen_samples = [], [], []
        for rec in itsm_store.historical_archive:
            hour = rec.get("hour", 14)
            dur = float(rec.get("duration_minutes", 15))
            is_fp = rec.get("is_fp", False)
            backlog_samples.append(dur / 4.0)
            hour_samples.append(float(hour))
            duration_samples.append(dur)
            recurrence_samples.append(1.0 if is_fp else 3.0)
            prod = rec.get("product", "Hosting Linux")
            product_samples.append(float(PRODUCTS.index(prod) if prod in PRODUCTS else 0))
            titlelen_samples.append(float(rec.get("title_len", 30)))
        self.ref_backlogs = np.array(backlog_samples) if backlog_samples else np.array([20.0])
        self.ref_hours = np.array(hour_samples) if hour_samples else np.array([14.0])
        self.ref_durations = np.array(duration_samples) if duration_samples else np.array([14.0])
        self.ref_recurrences = np.array(recurrence_samples) if recurrence_samples else np.array([1.0])
        self.ref_product_idx = np.array(product_samples) if product_samples else np.array([0.0])
        self.ref_title_len = np.array(titlelen_samples) if titlelen_samples else np.array([30.0])

    def _fit_forecaster(self):
        try:
            df = dataset_loader.get_or_create_processed_dataset()
            daily = df.groupby("date_str").size().sort_index()
            self._daily_index = list(daily.index)
            self._daily_values = daily.values.astype(float)
            y = self._daily_values
            n = len(y)
            tail = 28
            prof = np.zeros(7)
            counts = np.zeros(7)
            for i in range(max(0, n - tail), n):
                wd = pd.Timestamp(self._daily_index[i]).weekday()
                prof[wd] += y[i]
                counts[wd] += 1
            counts[counts == 0] = 1
            self._weekday_profile = prof / counts
            self._drift_per_day = float(np.mean(np.diff(y[-tail:]))) if n >= tail + 1 else 0.0
            errs = []
            for i in range(max(0, n - tail), n):
                wd = pd.Timestamp(self._daily_index[i]).weekday()
                errs.append(y[i] - (self._weekday_profile[wd]))
            self._residual_sigma = float(np.std(errs)) if len(errs) > 1 else 1.0
            e_model_all, e_base_all = [], []
            per_h, per_h_base = [], []
            for o in range(n - 28, n):
                for h in range(1, 8):
                    if o + h - 1 >= n:
                        continue
                    yt = y[o + h - 1]
                    yp = self._predict_at(o, h)
                    yb = float(np.mean(y[max(0, o - 28):o]))
                    e_model_all.append(yt - yp)
                    e_base_all.append(yt - yb)
            for h in range(1, 8):
                num = den = numb = 0.0
                for o in range(n - 28, n):
                    if o + h - 1 >= n:
                        continue
                    yt = y[o + h - 1]
                    num += abs(yt - self._predict_at(o, h))
                    numb += abs(yt - float(np.mean(y[max(0, o - 28):o])))
                    den += abs(yt)
                per_h.append(num / den if den else float("nan"))
                per_h_base.append(numb / den if den else float("nan"))
            self.wape = round(float(np.nanmean(per_h)), 4)
            self.wape_baseline = round(float(np.nanmean(per_h_base)), 4)
            self.dm_pvalue = diebold_mariano_pvalue(np.array(e_model_all), np.array(e_base_all))
        except Exception as e:
            logger.warning(f"Forecaster fitting failed; forecast gated: {e}")
            self.wape, self.wape_baseline, self.dm_pvalue = 0.0, 0.0, 1.0

    def _predict_at(self, origin_idx: int, h: int) -> float:
        wd = pd.Timestamp(self._daily_index[origin_idx + h - 1]).weekday()
        return float(self._weekday_profile[wd] + self._drift_per_day * h * 0.5)

    def get_forecast(self, horizon: str = "D+7") -> Forecast:
        now = datetime.now()
        n = len(self._daily_values)
        historical: List[DataPoint] = []
        for i in range(max(0, n - 14), n):
            dt = pd.Timestamp(self._daily_index[i])
            day_name = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][dt.weekday()]
            historical.append(DataPoint(
                timestamp=self._daily_index[i],
                label=f"{day_name} {dt.strftime('%d/%m')}",
                value=round(float(self._daily_values[i]), 1)))
        num_steps = 1 if horizon == "D+1" else 7
        predicted: List[DataPoint] = []
        conf_lower: List[float] = []
        conf_upper: List[float] = []
        peak_val, peak_date = 0.0, ""
        last_dt = pd.Timestamp(self._daily_index[-1]) if self._daily_index else now
        for step in range(1, num_steps + 1):
            f_dt = last_dt + timedelta(days=step)
            day_name = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][f_dt.weekday()]
            wd = f_dt.weekday()
            f_val = round(float(self._weekday_profile[wd] + self._drift_per_day * step * 0.5), 1) \
                if len(self._weekday_profile) == 7 else 0.0
            if f_val > peak_val:
                peak_val, peak_date = f_val, f"+{step}d ({day_name})"
            predicted.append(DataPoint(
                timestamp=f_dt.strftime("%Y-%m-%d"),
                label=f"+{step}d ({day_name})",
                value=f_val))
            margin = 1.96 * self._residual_sigma * math.sqrt(1 + step * 0.25)
            conf_lower.append(round(max(0.0, f_val - margin), 1))
            conf_upper.append(round(f_val + margin, 1))
        cap_window = self._daily_values[-90:] if n >= 90 else self._daily_values
        capacity_threshold = round(float(np.mean(cap_window)), 1) if len(cap_window) else 95.0
        group_breakdown, product_breakdown = self._measured_shares(predicted)
        return Forecast(
            historical=historical,
            predicted=predicted,
            confidence_lower=conf_lower,
            confidence_upper=conf_upper,
            horizon=horizon,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            peak_value=round(peak_val, 1),
            peak_date=peak_date,
            capacity_threshold=capacity_threshold,
            is_over_capacity=peak_val > capacity_threshold,
            wape_accuracy=round((1.0 - min(self.wape, 1.0)) * 100, 1),
            breakdown_by_group=group_breakdown,
            breakdown_by_product=product_breakdown,
            model_id=FORECAST_MODEL_ID,
            wape_holdout=self.wape,
            wape_baseline=self.wape_baseline,
            dm_pvalue=self.dm_pvalue,
            claim_label="measured",
        )

    def _measured_shares(self, predicted: List[DataPoint]):
        try:
            df = dataset_loader.get_or_create_processed_dataset()
            tail_dates = sorted(df["date_str"].unique())[-30:]
            tail = df[df["date_str"].isin(tail_dates)]
            gshares = (tail.groupby("grupo_clean").size() / max(1, len(tail))).to_dict()
            pshares = (tail.groupby("produto_clean").size() / max(1, len(tail))).to_dict()
        except Exception:
            gshares, pshares = {"Team14": 0.75}, {"Hosting Linux": 0.64}
        group_breakdown = {}
        for grp in ["Team14", "Team11", "Team05", "Team09"]:
            ratio = float(gshares.get(grp, 0.0))
            group_breakdown[grp] = [DataPoint(timestamp=p.timestamp, label=p.label,
                                              value=round(p.value * ratio, 1)) for p in predicted]
        product_breakdown = {}
        for prod in ["Hosting Linux", "Cloud VPS", "Email Corporativo", "Criador de Sites"]:
            ratio = float(pshares.get(prod, 0.0))
            product_breakdown[prod] = [DataPoint(timestamp=p.timestamp, label=p.label,
                                                 value=round(p.value * ratio, 1)) for p in predicted]
        return group_breakdown, product_breakdown

    def get_operational_regime(self) -> Regime:
        now = datetime.now()
        incidents = itsm_store.get_all_incidents()
        op_risk = max(1, min(99, int(round(self.threshold_tau * 100.0))))
        critical_count = sum(1 for inc in incidents if (inc.p_calibrated is not None and inc.p_calibrated >= self.threshold_tau) or inc.risk_score >= op_risk)
        p1_count = sum(1 for inc in incidents if inc.priority == "P1")
        active_count = len(incidents)
        if self.regime_override and self.regime_override != "auto":
            current_regime = self.regime_override
        elif critical_count >= 8 or p1_count >= 5:
            current_regime = "crisis"
        elif critical_count >= 4 or active_count >= 25:
            current_regime = "saturation"
        elif critical_count >= 2 or active_count >= 18:
            current_regime = "stress"
        else:
            current_regime = "normal"
        triggers = []
        if critical_count > 0:
            triggers.append(f"{critical_count} incidentes sinalizados no ponto operacional (risco ≥ {op_risk}%)")
        if p1_count > 0:
            triggers.append(f"{p1_count} chamados P1 em atendimento simultâneo")
        if active_count >= 18:
            triggers.append(f"Volume ativo de {active_count} chamados acima do limiar tático")
        confidence = round(min(0.95, 0.70 + 0.05 * len(triggers) + 0.01 * min(critical_count, 10)), 2)
        descriptions = {
            "normal": "Operação equilibrada. Backlog dentro da capacidade nominal e SLA sob controle.",
            "stress": "Demanda acima da média (+28%). Volume em squads de Hosting e VPS requer atenção de triagem.",
            "saturation": "Saturação de capacidade em Team14 e NOC. Fila com risco de violação em chamados P2.",
            "crisis": "Regime crítico detectado! Incidentes P1/P2 com risco calibrado no ponto operacional e iminência de quebra de OLA.",
            "recovery": "Fase de recuperação ativa. Backlog em queda acelerada após contenção de surto de rede."
        }
        return Regime(
            current=current_regime,
            confidence=confidence,
            previous="normal" if current_regime != "normal" else "recovery",
            changed_at=(now - timedelta(minutes=45)).strftime("%H:%M"),
            trend="worsening" if current_regime in ["stress", "saturation", "crisis"] else "stable",
            active_triggers=triggers,
            description=f"[{REGIME_THRESHOLD_VERSION}] {descriptions.get(current_regime)}",
            recent_history=[
                {"time": (now - timedelta(hours=3)).strftime("%H:%M"), "regime": "normal"},
                {"time": (now - timedelta(hours=2)).strftime("%H:%M"), "regime": "normal"},
                {"time": (now - timedelta(minutes=45)).strftime("%H:%M"), "regime": current_regime}
            ]
        )

    def set_regime_override(self, regime_str: str):
        self.regime_override = regime_str
        DatabaseRepository.set_state("regime_override", regime_str)

    def _run_hdbscan_validation(self) -> Dict[str, Any]:
        from hdbscan import HDBSCAN
        from hdbscan.validity import validity_index
        from sklearn.metrics import adjusted_rand_score
        df = dataset_loader.get_or_create_processed_dataset()
        sample = df.sample(min(3000, len(df)), random_state=settings.RANDOM_SEED)
        titles = sample["titulo_clean"].astype(str).tolist()
        vec = TfidfVectorizer(max_features=100)
        X = vec.fit_transform(titles).toarray()
        labels = HDBSCAN(min_cluster_size=50, min_samples=5).fit_predict(X)
        try:
            dbcv = round(float(validity_index(X, labels)), 4)
        except Exception:
            dbcv = None
        aris = []
        rng = np.random.RandomState(settings.RANDOM_SEED + 1)
        for _ in range(2):
            idx = rng.choice(len(X), size=len(X), replace=True)
            lab2 = HDBSCAN(min_cluster_size=50, min_samples=5).fit_predict(X[idx])
            try:
                aris.append(adjusted_rand_score(labels[idx], lab2))
            except Exception:
                pass
        stability = round(float(np.mean(aris)), 4) if aris else None
        rule = sample["cluster_id"].astype(str).values
        overlaps = {}
        for fam in sorted(set(rule)):
            mask = rule == fam
            best = 0.0
            for c in sorted(set(labels)):
                if c == -1:
                    continue
                cmask = labels == c
                inter = np.logical_and(mask, cmask).sum()
                union = np.logical_or(mask, cmask).sum()
                best = max(best, inter / union if union else 0.0)
            overlaps[fam] = round(float(best), 3)
        noise_rate = round(float((labels == -1).mean()), 4)
        median_overlap = float(np.median(list(overlaps.values()))) if overlaps else 0.0
        algorithm = "hdbscan" if median_overlap >= 0.4 else "keyword-baseline"
        return {"algorithm": algorithm, "dbcv": dbcv, "stability": stability,
                "overlaps": overlaps, "noise_rate": noise_rate,
                "median_overlap": round(median_overlap, 3)}

    def _get_cluster_report(self) -> Dict[str, Any]:
        with self._lock:
            if self._cluster_report is None:
                try:
                    self._cluster_report = self._run_hdbscan_validation()
                except Exception as e:
                    logger.warning(f"HDBSCAN validation failed; honest baseline fallback: {e}")
                    self._cluster_report = {"algorithm": "keyword-baseline", "dbcv": None,
                                            "stability": None, "overlaps": {},
                                            "noise_rate": None, "median_overlap": 0.0}
            return self._cluster_report

    def get_clusters(self) -> List[Cluster]:
        incidents = itsm_store.get_all_incidents()
        report = self._get_cluster_report()
        try:
            df = dataset_loader.get_or_create_processed_dataset()
            dist = dataset_loader.get_cluster_distribution(df)
            prio = df.groupby(["cluster_id", "prio_clean"]).size().unstack(fill_value=0)
        except Exception:
            dist, prio = {}, None

        def counts_for(cid: str):
            if prio is not None and cid in prio.index:
                row = prio.loc[cid]
                return (int(row.get("P1", 0)), int(row.get("P2", 0)),
                        int(row.get("P3", 0)), int(row.get("P4", 0)))
            return (0, 0, 0, 0)

        avg_risk = {}
        try:
            full = dataset_loader.get_or_create_processed_dataset()
            sample = full.sample(min(2000, len(full)), random_state=settings.RANDOM_SEED)
            for cid, sub in sample.groupby("cluster_id"):
                probs = []
                for _, r in sub.iterrows():
                    _, pc = self.predict_incident_proba(
                        str(r["titulo_clean"]), str(r["prio_clean"]),
                        str(r["grupo_clean"]), str(r["produto_clean"]),
                        str(r["ic_clean"]), int(r["hour"]))
                    probs.append(pc)
                avg_risk[str(cid)] = round(float(np.mean(probs)) * 100, 1) if probs else 0.0
        except Exception:
            avg_risk = {}

        c1_tickets = [inc.id for inc in incidents if "Apache" in inc.title or "web9" in inc.title or inc.id == "INC8654273"]
        c2_tickets = [inc.id for inc in incidents if "DNS" in inc.title or "Anycast" in inc.title]
        c3_tickets = [inc.id for inc in incidents if "MySQL" in inc.title or "Pool" in inc.title]
        c4_tickets = [inc.id for inc in incidents if "SMTP" in inc.title or "Email" in inc.title or "E-mail" in inc.title]
        c5_tickets = [inc.id for inc in incidents if "Storage" in inc.title or "Inode" in inc.title or "Disk" in inc.title]

        algo = report["algorithm"]
        claim = "measured" if algo == "hdbscan" else "projection"

        def fam(cid: str, name: str, tickets: List[str], trend: str,
                sample_desc: str, action: str) -> Cluster:
            info = dist.get(cid, {})
            p1, p2, p3, p4 = counts_for(cid)
            return Cluster(
                id=cid, name=name,
                incident_count=info.get("incident_count", 0),
                avg_risk_score=avg_risk.get(cid, 0.0),
                top_features=[f"hdb_overlap={report['overlaps'].get(cid, 0.0)}",
                              f"noise_rate={report['noise_rate']}"],
                trend=trend,
                false_positive_rate=info.get("false_positive_rate", 0.0),
                p1_count=p1, p2_count=p2, p3_count=p3, p4_count=p4,
                incident_ids=tickets if tickets else [incidents[0].id] if incidents else [],
                sample_description=f"[{algo}|DBCV={report['dbcv']}|stability={report['stability']}] {sample_desc}",
                recommended_action=action,
                algorithm=algo, dbcv=report["dbcv"], stability=report["stability"],
                claim_label=claim)

        return [
            fam("cluster-1", "Apache Busy Workers Recorrente",
                c1_tickets, "growing",
                "Alarmes transitórios de workers encerrados sem intervenção humana.",
                "Automatizar triagem com auto-resolução para chamados < 30s sem impacto."),
            fam("cluster-2", "DNS Resolution Failure pós-deploy",
                c2_tickets, "declining",
                "Falha de resolução autoritativa pós-deploy com impacto em zonas Anycast.",
                "Rollback preventivo de regras BGP Anycast e ativação de cache secundário."),
            fam("cluster-3", "DB Connection Pool Exhaustion",
                c3_tickets, "stable",
                "Saturação do pool de threads MySQL em cluster compartilhado DB-04.",
                "Aumentar temporariamente max_connections e isolar queries pesadas em réplicas."),
            fam("cluster-4", "SMTP Spool Latency & TLS Handshake",
                c4_tickets, "stable",
                "Atraso na entrega de mensagens corporativas com fila em spool retido.",
                "Rotacionar IPs de saída nos pools de relay e purgar rejeitadas por SPF."),
            fam("cluster-5", "Storage & Inode Limit Breaches",
                c5_tickets, "declining",
                "Bloqueio de gravação temporária por exaustão de inodes de logs antigos.",
                "Limpeza de sessões PHP órfãs e sugestão de upgrade de plano."),
        ]

    # ------------------------------------------------------------------
    # Drift KS + PSI (Fase 6) e auditoria contínua
    # ------------------------------------------------------------------
    @staticmethod
    def _incident_hour(inc) -> float:
        try:
            return float(pd.Timestamp(inc.created_at).hour)
        except Exception:
            return 14.0

    @staticmethod
    def _holm_bonferroni(pvals: List[float]) -> List[float]:
        m = len(pvals)
        order = np.argsort(pvals)
        adj = np.empty(m)
        for rank, idx in enumerate(order):
            adj[idx] = min(1.0, (m - rank) * pvals[idx])
        sorted_adj = np.maximum.accumulate(adj[order])
        out = np.empty(m)
        out[order] = sorted_adj
        return [round(float(v), 4) for v in out]

    def _symmetric_sample(self, ref: np.ndarray, n_cur: int, cap: int = 500) -> np.ndarray:
        n_ref = min(len(ref), max(200, 4 * max(1, n_cur)), cap)
        rng = np.random.RandomState(settings.RANDOM_SEED)
        idx = rng.choice(len(ref), size=min(n_ref, len(ref)), replace=False)
        return ref[idx]

    def psi_panel(self) -> List[Dict[str, Any]]:
        """PSI por feature final vs. referência de treino (Fase 6.1)."""
        incidents = itsm_store.get_all_incidents()
        if not incidents or not self.psi_refs or self.feature_names is None:
            return []
        rows = []
        for inc in incidents:
            try:
                X = self._row_X(self._row_frame(
                    inc.title, inc.priority, inc.group, inc.product,
                    inc.config_item, self._incident_hour(inc)))
                rows.append(X.reshape(-1))
            except Exception:
                continue
        if not rows:
            return []
        cur = np.asarray(rows)
        out = []
        for j, name in enumerate(self.feature_names):
            ref = np.asarray(self.psi_refs.get(name, []), dtype=float)
            if len(ref) < 20:
                continue
            res = population_stability_index(
                ref, cur[:, j] if cur.shape[1] > j else np.zeros(len(cur)))
            out.append({"feature_name": name, **res,
                        "reference_version": DRIFT_REF_VERSION})
        return out

    def get_drift_and_mlops(self) -> MLOpsStatus:
        incidents = itsm_store.get_all_incidents()
        cur_backlogs = np.array([float((inc.p_calibrated if inc.p_calibrated is not None else inc.risk_score / 100.0)) * 30.0 for inc in incidents])
        cur_hours = np.array([self._incident_hour(inc) for inc in incidents])
        cur_durations = np.array([float(inc.duration_seconds or 14) for inc in incidents])
        cur_recurrences = np.array([1.0 if inc.is_automated_fp else 3.0 for inc in incidents])
        cur_products = np.array([float(PRODUCTS.index(inc.product) if inc.product in PRODUCTS else 0) for inc in incidents])
        cur_titlelen = np.array([float(len(inc.title or "")) for inc in incidents])
        refs = [self.ref_backlogs, self.ref_hours, self.ref_durations,
                self.ref_recurrences, self.ref_product_idx, self.ref_title_len]
        curs = [cur_backlogs, cur_hours, cur_durations, cur_recurrences, cur_products, cur_titlelen]
        names = ["backlog_squad_team14", "horario_pico_dist", "ticket_duration_122k",
                 "reincidencia_ic_rate", "product_distribution", "title_length_proxy"]
        n_cur = len(incidents)
        raw_p, statistics, ref_means, cur_means, win = [], [], [], [], []
        for ref, cur in zip(refs, curs):
            r = self._symmetric_sample(np.asarray(ref, dtype=float), n_cur)
            c = np.asarray(cur, dtype=float) if len(cur) else np.array([0.0])
            res = stats.ks_2samp(r, c)
            raw_p.append(float(res.pvalue))
            statistics.append(float(res.statistic))
            ref_means.append(float(np.mean(r)))
            cur_means.append(float(np.mean(c)))
            win.append((len(r), len(c)))
        adj_p = self._holm_bonferroni(raw_p)
        drift_metrics: List[DriftMetric] = []
        drift_count = 0
        for i, name in enumerate(names):
            p_adj = adj_p[i]
            is_drift = p_adj < 0.05
            status = "drifted" if p_adj < 0.01 else ("warning" if is_drift else "stable")
            if is_drift:
                drift_count += 1
            drift_metrics.append(DriftMetric(
                feature_name=name,
                p_value=round(raw_p[i], 4),
                statistic=round(statistics[i], 3),
                status=status,
                reference_mean=round(ref_means[i], 2),
                current_mean=round(cur_means[i], 2),
                drift_detected=is_drift,
                p_adjusted=p_adj,
                reference_version=DRIFT_REF_VERSION,
                window_n=win[i][0] + win[i][1],
            ))
        overall_status = "warning" if drift_count >= 1 else "healthy"
        return MLOpsStatus(
            model_version=self.model_version,
            last_trained=self.last_trained,
            roc_auc=self.roc_auc,
            recall=self.recall,
            precision=self.precision,
            f1_score=self.f1_score,
            wape=self.wape,
            drift_status=overall_status,
            overall_drift_score=round(float(np.mean([m.statistic for m in drift_metrics])), 3),
            feature_drifts=drift_metrics,
            retraining_in_progress=self.training_in_progress,
            samples_in_training=122543,
            samples_in_inference=len(incidents),
            brier_gate=self.brier_gate,
            psi_overall=round(float(np.mean([p["psi"] for p in self.psi_panel() if isinstance(p.get("psi"), (int, float))])), 4) if self.psi_panel() else 0.0,
        )

    def rollup_audit_job(self) -> Dict[str, Any]:
        """Job de auditoria contínua (Fase 6.2): Brier móvel 7d + MdAE MTTR.

        Degradação >20% vs. base de validação → auto_block + log + notificação.
        """
        rows = DatabaseRepository.list_resolved_predictions(days=30)
        now = datetime.now().isoformat()
        if not rows:
            return {"status": "no-data", "auto_block": self.auto_block, "at": now}
        df = pd.DataFrame(rows)
        recent = df[df["timestamp_resolution"].fillna("") >= (datetime.now() - timedelta(days=7)).isoformat()]
        out: Dict[str, Any] = {"at": now, "n_30d": len(df), "n_7d": len(recent)}
        if len(recent):
            brier_roll = float((((recent["predicted_risk"].values - recent["actual_sla_violated"].values) ** 2).mean()))
            mdae = float(np.median(np.abs(recent["actual_resolution_time"].values - recent["predicted_time"].values)))
            out["brier_rolling_7d"] = round(brier_roll, 4)
            out["mdae_mttr_7d"] = round(mdae, 2)
            base = max(self.validation_brier, 1e-9)
            degr = (brier_roll - base) / base
            out["degradation_vs_validation"] = round(float(degr), 4)
            if degr > 0.20:
                self.auto_block = True
                self.auto_block_reason = f"Brier móvel {brier_roll:.4f} degradou {degr:.1%} vs. validação {base:.4f}"
                DatabaseRepository.log_audit("AUTO_BLOCK", "system", None,
                                             {"reason": self.auto_block_reason})
                logger.warning(f"AUTO-BLOCK de inferência: {self.auto_block_reason}")
            else:
                self.auto_block = False
                self.auto_block_reason = ""
        DatabaseRepository.set_state("last_audit_rollup", out)
        return {"status": "ok", "auto_block": self.auto_block, **out}

    def acceptance_gates(self) -> Dict[str, Dict[str, Any]]:
        """Gates de aceite da Fase 7: cada critério PASS/BLOCKED com valor medido.

        Promoção a homologação exige todos PASS. BLOCKED honesto não é falha
        de teste — é o gate funcionando (documenta o que falta).
        """
        rec = float(self.tau_report.get("recall_at_star", 0.0))
        cost_red = float(self.tau_report.get("cost_reduction_pct", 0.0))
        return {
            "brier": {"threshold": "BS≤0.08 e decil<5%",
                      "value": {"brier": self.brier, "decile_max_err": self.decile_max_err},
                      "status": "PASS" if (self.brier <= 0.08 and self.decile_max_err < 0.05) else "BLOCKED"},
            "mdape_mttr": {"threshold": "MdAPE<18%",
                           "value": self.mdape_mttr,
                           "status": "PASS" if self.mdape_mttr < 0.18 else "BLOCKED"},
            "cost": {"threshold": "redução≥35% vs corte 0.5",
                     "value": cost_red,
                     "status": "PASS" if cost_red >= 35.0 else "BLOCKED"},
            "recall_floor": {"threshold": "recall@τ*≥0.80",
                             "value": rec,
                             "status": "PASS" if rec >= 0.80 else "BLOCKED"},
        }

    def retrain_model(self) -> Dict[str, Any]:
        with self._lock:
            self.training_in_progress = True
            self.last_trained = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.model_version = f"v4.0.1-walkforward-{datetime.now().strftime('%m%d')}"
            self._cluster_report = None
            self.auto_block = False
            self.auto_block_reason = ""
            self._train_initial_models()
            self.training_in_progress = False
            artifact = hashlib.sha1(
                f"{self.model_version}{self.roc_auc}{self.threshold_tau}".encode()).hexdigest()[:12]
            return {
                "status": "success",
                "model_version": self.model_version,
                "trained_at": self.last_trained,
                "roc_auc": self.roc_auc,
                "cv_pr_auc": self.cv_pr_auc,
                "auc_ci95": self.auc_ci95,
                "auc_ci_method": self.auc_ci_method,
                "brier": self.brier,
                "brier_gate": self.brier_gate,
                "threshold_tau": self.threshold_tau,
                "tau_report": self.tau_report,
                "recall": self.recall,
                "mdape_mttr": self.mdape_mttr,
                "wape_holdout": self.wape,
                "wape_baseline": self.wape_baseline,
                "dm_pvalue": self.dm_pvalue,
                "walk_folds": self.walk_report,
                "acceptance": self.acceptance_gates(),
                "artifact_hash": artifact,
                "samples_trained": 122543,
                "message": "Retreinamento walk-forward concluído (focal+quantile+isotônica).",
            }

    def get_metrics_overview(self) -> MetricsOverview:
        incidents = itsm_store.get_all_incidents()
        op_risk = max(1, min(99, int(round(self.threshold_tau * 100.0))))
        critical_count = sum(1 for inc in incidents if (inc.p_calibrated is not None and inc.p_calibrated >= self.threshold_tau) or inc.risk_score >= op_risk)
        sla_warn_count = sum(1 for inc in incidents if 0 < inc.sla_remaining_minutes <= 45)
        sla_breached = sum(1 for inc in incidents if inc.sla_remaining_minutes <= 0)
        avg_risk = sum(inc.risk_score for inc in incidents) / max(1, len(incidents))
        regime = self.get_operational_regime()
        return MetricsOverview(
            total_active_incidents=len(incidents),
            critical_risk_count=critical_count,
            sla_warning_count=sla_warn_count,
            sla_breached_count=sla_breached,
            avg_risk_score=round(avg_risk, 1),
            projected_volume_next_period=int(round(self._weekday_profile.mean() * 7)) if len(self._weekday_profile) == 7 else 120,
            fp_reduction_rate=38.5,
            mttr_reduction_pct=21.4,
            operational_regime=regime.current,
            active_drift_alerts=sum(1 for _ in [regime] if regime.current in ["saturation", "crisis"]),
            last_updated=datetime.now().strftime("%H:%M:%S"),
            fp_claim_label="projection",
            mttr_claim_label="projection",
            operating_point_risk=op_risk,
        )


ml_engine = MLEngine()
