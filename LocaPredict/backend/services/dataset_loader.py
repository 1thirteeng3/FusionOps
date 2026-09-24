import os
import sqlite3
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
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


if __name__ == "__main__":
    df = get_or_create_processed_dataset()
    print(f"Parquet generated with {len(df)} rows.")
