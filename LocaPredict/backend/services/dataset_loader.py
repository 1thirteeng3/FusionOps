import os
import re
import sqlite3
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from backend.utils.logger import logger
from backend.models.schemas import SHAPFactor

from pathlib import Path

# Resolve project directories dynamically relative to this file
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

PRIMARY_PARQUET = DATA_DIR / "locaweb_clean.parquet"
PRIMARY_EXCEL = DATA_DIR / "LW-DATASET.xlsx"

# Search candidates in priority order (local project folder first, then environment variable, then fallbacks)
PARQUET_CANDIDATES = [
    Path(os.getenv("PARQUET_CACHE", "")) if os.getenv("PARQUET_CACHE") else None,
    PRIMARY_PARQUET,
    PROJECT_ROOT / "locaweb_clean.parquet",
    Path(r"c:\Users\giovanni.barcelos\Desktop\LocaPredict\data\locaweb_clean.parquet"),
]

EXCEL_CANDIDATES = [
    Path(os.getenv("DATASET_PATH", "")) if os.getenv("DATASET_PATH") else None,
    PRIMARY_EXCEL,
    PROJECT_ROOT / "LW-DATASET.xlsx",
    Path(r"c:\Users\giovanni.barcelos\Desktop\LocaPredict\data\LW-DATASET.xlsx"),
]

DATASET_PATH = str(next((p for p in EXCEL_CANDIDATES if p and p.exists()), PRIMARY_EXCEL))
PARQUET_CACHE = str(next((p for p in PARQUET_CANDIDATES if p and p.exists()), PRIMARY_PARQUET))
DB_PATH = os.getenv("DB_PATH", str(PROJECT_ROOT / "locapredict.db"))

PROD_MAP = {
    'lhco': 'Hosting Linux',
    'lhvp': 'Cloud VPS',
    'lcem': 'Email Corporativo',
    'lsin': 'Criador de Sites',
    'lrev': 'Revenda de Hospedagem',
    'lcho': 'Cloud Hosting Dedicado',
    'lcsi': 'Certificado SSL',
    'lsaa': 'SaaS & Apps',
    'lrel': 'Email Marketing'
}

PRIO_MAP = {
    '1 - Crítica': 'P1',
    '1 - Critica': 'P1',
    '2 - Alta': 'P2',
    '3 - Média': 'P3',
    '3 - Media': 'P3',
    '4 - Baixa': 'P4',
    '5 - Muito Baixa': 'P4'
}

def get_or_create_processed_dataset() -> pd.DataFrame:
    # Check if parquet cache exists in any candidate location
    for p_path in PARQUET_CANDIDATES:
        if p_path and p_path.exists():
            logger.info(f"Loading cached real dataset from {p_path}...")
            df = pd.read_parquet(p_path)
            return _ensure_label_columns(df)

    # Check if raw Excel exists in any candidate location
    target_excel = next((p for p in EXCEL_CANDIDATES if p and p.exists()), None)
    if not target_excel:
        logger.error(f"Excel dataset not found in candidates: {[str(p) for p in EXCEL_CANDIDATES if p]}")
        return pd.DataFrame()

    logger.info(f"Ingesting raw Excel dataset from {DATASET_PATH} (122k records)...")
    df = pd.read_excel(DATASET_PATH)

    col_names = [
        'numero', 'prioridade', 'produto', 'categoria', 'subcategoria',
        'grupo_designado', 'item_configuracao', 'aberto', 'resolvido',
        'encerrado', 'duracao', 'codigo_fechamento', 'descricao_resumida',
        'solucao', 'aberto_por', 'incidente_pai', 'status', 'entrou_kpi', 'kpi_violado'
    ]
    df.columns = col_names[:len(df.columns)]

    df['produto_clean'] = df['produto'].map(PROD_MAP).fillna('Hosting Linux')
    df['prio_clean'] = df['prioridade'].map(PRIO_MAP).fillna('P3')
    df['grupo_clean'] = df['grupo_designado'].fillna('Team14')
    df['titulo_clean'] = df['descricao_resumida'].fillna('Problem: Incident Detected')
    df['ic_clean'] = df['item_configuracao'].fillna('IC00001')
    df['aberto_por_clean'] = df['aberto_por'].fillna('Monitoramento')
    df['status_clean'] = df['status'].fillna('Sem Intervenção')

    df['duracao_sec'] = pd.to_numeric(df['duracao'], errors='coerce').fillna(14).astype(int)
    df['is_fp'] = (df['status_clean'] == 'Sem Intervenção') | (df['duracao_sec'] <= 30)
    df['kpi_violado_bool'] = (df['kpi_violado'] == 'SIM')

    sla_limits = {'P1': 14400, 'P2': 14400, 'P3': 43200, 'P4': 86400}
    df['sla_limit_sec'] = df['prio_clean'].map(sla_limits).fillna(43200)
    # Dual-label honesty (Constitution I, T005): the duration-rule label is
    # synthetic and MUST be named as such; the observed KPI label is separate.
    df['ola_breached_synth'] = df['kpi_violado_bool'] | ((df['duracao_sec'] > df['sla_limit_sec']) & (~df['is_fp']))
    df['kpi_violado_obs'] = df['kpi_violado_bool']
    df['ola_breached'] = df['ola_breached_synth']  # legacy alias, do not use for claims
    # P1 n=1 disclosure flag (Constitution I): exactly one P1 exemplar exists.
    df['p1_n1_flag'] = (df['prio_clean'] == 'P1')

    df['dt_aberto'] = pd.to_datetime(df['aberto'], errors='coerce')
    df['hour'] = df['dt_aberto'].dt.hour.fillna(14).astype(int)
    df['date_str'] = df['dt_aberto'].dt.strftime('%Y-%m-%d').fillna('2025-12-31')

    def assign_cluster(title: str, ic: str) -> Tuple[str, str]:
        t_low = str(title).lower()
        if 'apache' in t_low or 'busy workers' in t_low or 'web9' in t_low or ic == 'IC00001':
            return 'cluster-1', 'Apache Busy Workers Recorrente'
        elif 'dns' in t_low or 'anycast' in t_low or 'servfail' in t_low or 'zona' in t_low:
            return 'cluster-2', 'DNS Resolution Failure pós-deploy'
        elif 'mysql' in t_low or 'pool' in t_low or 'connection' in t_low or 'thread' in t_low:
            return 'cluster-3', 'DB Connection Pool Exhaustion'
        elif 'smtp' in t_low or 'email' in t_low or 'spool' in t_low or 'tls' in t_low:
            return 'cluster-4', 'SMTP Spool Latency & TLS Handshake'
        elif 'storage' in t_low or 'inode' in t_low or 'disk' in t_low or 'nvme' in t_low:
            return 'cluster-5', 'Storage & Inode Limit Breaches'
        return 'cluster-1', 'Apache Busy Workers Recorrente'

    cluster_info = [assign_cluster(t, ic) for t, ic in zip(df['titulo_clean'], df['ic_clean'])]
    df['cluster_id'] = [c[0] for c in cluster_info]
    df['cluster_name'] = [c[1] for c in cluster_info]

    # Save compact parquet cache
    try:
        df.to_parquet(PARQUET_CACHE, index=False)
        logger.info(f"Cached processed dataset to {PARQUET_CACHE}")
    except Exception as e:
        logger.warning(f"Could not write parquet cache: {e}")

    return df

def _ensure_label_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Backfill dual-label columns on cached parquet frames (T005).

    Older caches predate `ola_breached_synth` / `kpi_violado_obs` /
    `p1_n1_flag`; recompute them idempotently so every consumer sees the
    honest schema regardless of cache vintage.
    """
    df = df.copy()
    if 'kpi_violado_bool' not in df.columns and 'kpi_violado' in df.columns:
        df['kpi_violado_bool'] = (df['kpi_violado'] == 'SIM')
    if 'sla_limit_sec' not in df.columns and 'prio_clean' in df.columns:
        sla_limits = {'P1': 14400, 'P2': 14400, 'P3': 43200, 'P4': 86400}
        df['sla_limit_sec'] = df['prio_clean'].map(sla_limits).fillna(43200)
    if 'ola_breached_synth' not in df.columns:
        if {'kpi_violado_bool', 'duracao_sec', 'sla_limit_sec', 'is_fp'} <= set(df.columns):
            df['ola_breached_synth'] = df['kpi_violado_bool'] | (
                (df['duracao_sec'] > df['sla_limit_sec']) & (~df['is_fp']))
        elif 'ola_breached' in df.columns:
            df['ola_breached_synth'] = df['ola_breached']
    if 'kpi_violado_obs' not in df.columns:
        if 'kpi_violado_bool' in df.columns:
            df['kpi_violado_obs'] = df['kpi_violado_bool']
        else:
            df['kpi_violado_obs'] = False
    if 'ola_breached' not in df.columns and 'ola_breached_synth' in df.columns:
        df['ola_breached'] = df['ola_breached_synth']
    if 'p1_n1_flag' not in df.columns and 'prio_clean' in df.columns:
        df['p1_n1_flag'] = (df['prio_clean'] == 'P1')
    return df


def get_cluster_distribution(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Measured per-cluster volumes and false-positive rates (T005).

    All values are computed from the loader frame itself, so API counts that
    echo this distribution reconcile by construction (tolerance 1%).
    """
    dist: Dict[str, Dict[str, Any]] = {}
    for cid, sub in df.groupby('cluster_id'):
        dist[str(cid)] = {
            'incident_count': int(len(sub)),
            'false_positive_rate': round(float(sub['is_fp'].mean()) * 100, 1),
            'cluster_name': str(sub['cluster_name'].iloc[0]),
        }
    return dist


def reconcile_cluster_counts(api_counts: Dict[str, int], df: pd.DataFrame,
                             tol: float = 0.01) -> Tuple[bool, Dict[str, Any]]:
    """Check API cluster counts against loader distribution within `tol` (T005)."""
    dist = get_cluster_distribution(df)
    details: Dict[str, Any] = {}
    ok = True
    for cid, info in dist.items():
        expected = info['incident_count']
        got = int(api_counts.get(cid, -1))
        denom = max(1, expected)
        rel_err = abs(got - expected) / denom
        details[cid] = {'expected': expected, 'got': got,
                        'rel_err': round(rel_err, 4)}
        if rel_err > tol:
            ok = False
    return ok, details


_OBSERVED_GROUPS: Optional[List[str]] = None


def get_observed_groups(df: Optional[pd.DataFrame] = None) -> List[str]:
    """Squad vocabulary measured from the dataset (filter-bug fix).

    The legacy GROUPS constant mixed real and phantom squads and omitted real
    ones, so filter options did not match pool data. Filter dropdowns,
    synthetic generation and feature encoding all use this observed list;
    unseen groups map to a dedicated unknown bucket (never to index 0).
    """
    global _OBSERVED_GROUPS
    if _OBSERVED_GROUPS is None:
        frame = df if df is not None else get_or_create_processed_dataset()
        _OBSERVED_GROUPS = sorted(frame['grupo_clean'].astype(str).unique().tolist())
    return _OBSERVED_GROUPS


def group_index(group: str, df: Optional[pd.DataFrame] = None) -> float:
    """Ordinal encoding over the observed vocabulary + unknown bucket."""
    groups = get_observed_groups(df)
    if group in groups:
        return float(groups.index(group))
    return float(len(groups))  # unknown bucket (was: collision with index 0)


# ======================================================================
# Fase 2 — sanitização textual com máscaras canônicas (2.1)
# ======================================================================
_MASK_PATTERNS: List[Tuple[str, str]] = [
    (r"\b\d{1,3}(\.\d{1,3}){3}\b", "__IP__"),                       # IPv4
    (r"\b(?:[0-9a-fA-F]{0,4}:){2,}[0-9a-fA-F:]{2,}\b", "__IP__"),   # IPv6
    (r"0x[0-9a-fA-F]+|\b[A-Z]{3,}-\d{3,}\b", "__ERR_CODE__"),       # hex / códigos
    (r"https?://\S+|www\.\S+", "__URL__"),                         # URLs / FQDNs
    (r"\b(srv|db|app|node|web)\d{1,4}\b", "__SERVER_NAME__"),       # hostnames
    (r"\b[0-9a-fA-F-]{36}\b", "__UUID__"),                         # UUIDs / sessões
]
_MASK_RES = [(re.compile(p, re.IGNORECASE), tok) for p, tok in _MASK_PATTERNS]


def sanitize_technical_text(text: str) -> str:
    """Collapse high-cardinality technical tokens to canonical masks (2.1).

    Preserves semantics (an IP was present) while removing identifiers that
    fragment TF-IDF statistics. Idempotent and deterministic.
    """
    s = str(text or "")
    for rx, tok in _MASK_RES:
        s = rx.sub(tok, s)
    return re.sub(r"\s+", " ", s).strip()


# ======================================================================
# Fase 2 — representação textual: ST denso (opcional) ou TF-IDF+LSA (2.2)
# ======================================================================
N_TEXT_DIMS = 50


def _try_sentence_transformer():
    """ST compacto PT/EN se instalado E habilitado (opcional, 2.2).

    Default: None. torch (~GBs de RAM/imagem) viola a regra de portabilidade
    da Constituição para o deploy free; o caminho TF-IDF+LSA é o ativo.
    """
    if os.getenv("LOCAPREDICT_USE_ST", "0") != "1":
        return None
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    except Exception as e:
        logger.warning(f"SentenceTransformer indisponível; usando TF-IDF+LSA: {e}")
        return None


class HybridTextPipeline:
    """TF-IDF bi/tri-gramas (min_df=5, max_df=0.8) + SVD truncada k=50 (2.2).

    Fit exclusivo no treino da dobra; transform puro na inferência/teste.
    """

    def __init__(self, k: int = N_TEXT_DIMS):
        self.k = k
        self.st_model = _try_sentence_transformer()
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.svd: Optional[TruncatedSVD] = None
        self.mode = "st" if self.st_model is not None else "tfidf-lsa"

    def fit(self, texts: List[str]):
        clean = [sanitize_technical_text(t) for t in texts]
        if self.mode == "st":
            return self
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 3), min_df=5, max_df=0.8)
        X = self.vectorizer.fit_transform(clean)
        k = min(self.k, max(1, X.shape[1] - 1), max(1, X.shape[0] - 1))
        self.svd = TruncatedSVD(n_components=k, random_state=42)
        self.svd.fit(X)
        return self

    def transform(self, texts: List[str]) -> np.ndarray:
        clean = [sanitize_technical_text(t) for t in texts]
        if self.mode == "st":
            vecs = self.st_model.encode(clean, show_progress_bar=False)
            return np.asarray(vecs, dtype=float)
        assert self.vectorizer is not None and self.svd is not None, "pipeline not fitted"
        return np.asarray(self.svd.transform(self.vectorizer.transform(clean)), dtype=float)

    @property
    def dim(self) -> int:
        if self.mode == "st":
            return 384
        return int(self.svd.n_components) if self.svd is not None else self.k


# ======================================================================
# Fase 2 — codificação bayesiana de categóricas (2.3)
# ======================================================================
class BayesianTargetEncoder:
    """x_cat = (n*y_cat + m*y_global) / (n + m). Fit só no treino da dobra."""

    def __init__(self, m: float = 10.0):
        self.m = float(m)
        self.maps: Dict[str, Dict[Any, float]] = {}
        self.global_mean = 0.0

    def fit(self, df: pd.DataFrame, cols: List[str], y: pd.Series):
        self.global_mean = float(np.mean(y))
        for c in cols:
            stats = y.groupby(df[c].astype(str)).agg(["mean", "count"])
            self.maps[c] = {
                k: float((row["count"] * row["mean"] + self.m * self.global_mean)
                         / (row["count"] + self.m))
                for k, row in stats.iterrows()
            }
        return self

    def transform(self, df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
        out = pd.DataFrame(index=df.index)
        for c in cols:
            mapping = self.maps.get(c, {})
            out[c + "__te"] = df[c].astype(str).map(mapping).fillna(self.global_mean).astype(float)
        return out


# ======================================================================
# Fase 1 — variáveis temporais causais, só passado (1.2) + VIF (2.4)
# ======================================================================
def add_causal_temporal_features(df: pd.DataFrame,
                                 train_groups_weekday: Optional[pd.DataFrame] = None
                                 ) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Volume concorrente, velocidade de chegada e carga — estritamente passado.

    NOTA DE HONESTIDADE: "chamados ainda não resolvidos em t_i" exigiria saber
    o futuro (quando cada um resolve). Implementação causal correta: janelas
    de trailing apenas com aberturas (t_open ≤ t_i), sem nenhum end_time.
    Retorna (df com features, baseline grupo×weekday para inferência).
    """
    d = df.copy()
    d["t_open"] = pd.to_datetime(d["aberto"], errors="coerce")
    d = d.sort_values("t_open").reset_index(drop=True)
    opens = d["t_open"].values.astype("datetime64[s]").astype("int64")

    # Volume concorrente: aberturas nas últimas 24h (trailing, sem futuro).
    d["queue_volume_24h"] = np.searchsorted(opens, opens) - np.searchsorted(opens, opens - 24 * 3600)

    # Velocidade de chegada por produto: 15/60/240 min trailing.
    for wmin, col in ((15, "arrive_15m"), (60, "arrive_60m"), (240, "arrive_240m")):
        vals = np.zeros(len(d), dtype=float)
        for _, idx in d.groupby("produto_clean").groups.items():
            ii = np.asarray(sorted(idx))
            to = opens[ii]
            vals[ii] = np.searchsorted(to, to) - np.searchsorted(to, to - wmin * 60)
        d[col] = vals

    # Carga por grupo: pendentes (trailing 24h) / baseline grupo×weekday.
    d["wd"] = pd.to_datetime(d["t_open"]).dt.weekday.fillna(2).astype(int)
    grp_pending = np.zeros(len(d), dtype=float)
    for _, idx in d.groupby("grupo_clean").groups.items():
        ii = np.asarray(sorted(idx))
        to = opens[ii]
        grp_pending[ii] = np.searchsorted(to, to) - np.searchsorted(to, to - 24 * 3600)
    d["group_pending_24h"] = grp_pending
    if train_groups_weekday is None:
        base = d.groupby(["grupo_clean", "wd"])["group_pending_24h"].mean().rename("base").reset_index()
    else:
        base = train_groups_weekday
    d = d.merge(base, on=["grupo_clean", "wd"], how="left")
    d["base"] = d["base"].fillna(d["group_pending_24h"].mean() if len(d) else 1.0).clip(lower=1.0)
    d["load_ratio"] = d["group_pending_24h"] / d["base"]
    return d, base[["grupo_clean", "wd", "base"]]


def vif_filter(X: pd.DataFrame, thresh: float = 5.0, corr: float = 0.85) -> Tuple[List[str], Dict[str, Any]]:
    """Spearman |r|>corr ou VIF>thresh → descarta redundante (2.4, sem statsmodels)."""
    kept = list(X.columns)
    dropped: Dict[str, Any] = {}
    # 1) correlação bivariada: mantém a de maior variância do par.
    if len(kept) > 1:
        C = X[kept].corr(method="spearman").abs()
        from itertools import combinations
        for a, b in combinations(list(kept), 2):
            if a not in kept or b not in kept:
                continue
            if C.loc[a, b] > corr:
                drop = a if X[a].var() < X[b].var() else b
                kept.remove(drop)
                dropped[drop] = {"reason": f"spearman|r|={C.loc[a, b]:.3f}>{corr}", "kept_other": b if drop == a else a}
    # 2) VIF manual via OLS (numpy lstsq): VIF_j = 1/(1-R²_j).
    changed = True
    while changed and len(kept) > 1:
        changed = False
        vifs = {}
        A = X[kept].values.astype(float)
        for j in range(len(kept)):
            y = A[:, j]
            Xo = np.delete(A, j, axis=1)
            Xo1 = np.column_stack([np.ones(len(Xo)), Xo])
            coef, *_ = np.linalg.lstsq(Xo1, y, rcond=None)
            ss_res = float(((y - Xo1 @ coef) ** 2).sum())
            ss_tot = float(((y - y.mean()) ** 2).sum())
            r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
            vifs[kept[j]] = 1.0 / max(1e-9, 1.0 - min(r2, 0.999999999))
        worst = max(vifs, key=vifs.get)
        if vifs[worst] > thresh:
            kept.remove(worst)
            dropped[worst] = {"reason": f"VIF={vifs[worst]:.1f}>{thresh}"}
            changed = True
    return kept, {"dropped": dropped}


if __name__ == "__main__":
    df = get_or_create_processed_dataset()
    print(f"Parquet generated with {len(df)} rows.")
