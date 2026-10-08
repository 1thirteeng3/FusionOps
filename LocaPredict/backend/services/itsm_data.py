import random
import threading
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from backend.models.schemas import Incident, SHAPFactor
from backend.core.config import settings
from backend.db.database import DatabaseRepository
from backend.services.dataset_loader import get_or_create_processed_dataset, PROD_MAP, PRIO_MAP, get_observed_groups
from backend.utils.logger import logger

GROUPS = [
    "Team14",
    "Team11",
    "Team05",
    "Team09",
    "Team12",
    "Team03",
    "Team10",
    "Team17",
    "Team02",
    "Team01",
    "Team07 (NOC)",
    "Team19 (Infra)"
]

PRODUCTS = [
    "Hosting Linux",
    "Cloud VPS",
    "Email Corporativo",
    "Criador de Sites",
    "Revenda de Hospedagem",
    "Cloud Hosting Dedicado",
    "Certificado SSL",
    "SaaS & Apps",
    "Email Marketing"
]

CATEGORIES = [
    "Web Server",
    "Infraestrutura",
    "Banco de Dados",
    "Rede & DNS",
    "Segurança & SSL",
    "E-mail & SMTP",
    "Painel do Cliente"
]

class ITSMDataStore:
    def __init__(self, seed: int = settings.RANDOM_SEED):
        self._lock = threading.RLock()
        self.seed = seed
        self.incidents: Dict[str, Incident] = {}
        self.historical_archive: List[Dict[str, Any]] = []
        self.df_raw: Optional[pd.DataFrame] = None
        self.counter = 8654273
        self._initialize_from_dataset()

    def _initialize_from_dataset(self):
        with self._lock:
            random.seed(self.seed)
            np.random.seed(self.seed)

            # 1. First check SQLite database
            saved_incidents = DatabaseRepository.load_all_incidents()
            if saved_incidents and len(saved_incidents) >= 15:
                logger.info(f"Loaded {len(saved_incidents)} persistent incidents from SQLite.")
                for inc_dict in saved_incidents:
                    factors = [SHAPFactor(**f) if isinstance(f, dict) else f for f in inc_dict.get("shap_factors", [])]
                    inc_dict["shap_factors"] = factors
                    # Defesa contra linhas persistidas pré-validação estrita:
                    # trunca para os limites do schema em vez de travar o boot.
                    if isinstance(inc_dict.get("title"), str):
                        inc_dict["title"] = inc_dict["title"][:200]
                    if isinstance(inc_dict.get("description"), str):
                        inc_dict["description"] = inc_dict["description"][:2000]
                    try:
                        inc = Incident(**inc_dict)
                    except Exception as e:
                        logger.warning(f"Skipping corrupt persisted incident {inc_dict.get('id')}: {e}")
                        continue
                    self.incidents[inc.id] = inc
                self._load_historical_timeseries()
                return

            # 2. Load the real 122,543 Locaweb dataset
            logger.info("Ingesting real Locaweb 122k records into ITSM operational store...")
            df = get_or_create_processed_dataset()
            self.df_raw = df

            now = datetime.now()
            
            # Extract top recent tickets from the dataset (end of 2025)
            # Find diverse recent tickets across P1, P2, P3, P4
            recent_df = df.head(50)
            
            for idx, row in recent_df.iterrows():
                inc_id = str(row['numero'])
                prio = str(row['prio_clean'])
                title = str(row['titulo_clean'])
                group = str(row['grupo_clean'])
                prod = str(row['produto_clean'])
                ic = str(row['ic_clean'])
                opened_by = str(row['aberto_por_clean'])
                is_fp = bool(row['is_fp'])
                dur_sec = int(row['duracao_sec'])
                c_id = str(row['cluster_id'])
                c_name = str(row['cluster_name'])

                # Seed risk bands are deterministic operational placeholders
                # (Constitution I: no random generation for metrics). They are
                # replaced by calibrated inference in recalibrate_pool(), which
                # the ML engine invokes after honest training (T015).
                if prio == "P1":
                    risk = 90
                    sla_mins = max(10, 240 - (dur_sec // 60))
                elif prio == "P2":
                    risk = 78
                    sla_mins = max(15, 240 - (dur_sec // 60))
                elif prio == "P3":
                    risk = 87 if inc_id == "INC8654273" else 55
                    sla_mins = max(30, 720 - (dur_sec // 60))
                else:
                    risk = 25
                    sla_mins = max(60, 1440 - (dur_sec // 60))

                hours = sla_mins // 60
                mins = sla_mins % 60
                est_str = f"{hours}h {mins}min restantes" if hours > 0 else f"{mins}min restantes"

                created_dt = now - timedelta(minutes=random.randint(5, 180))
                deadline_dt = created_dt + timedelta(minutes=sla_mins)

                # Seed explanations are intentionally empty: fixed-weight tables
                # are banned as SHAP evidence (Constitution III). Verified
                # TreeExplainer attributions are filled by recalibrate_pool()
                # immediately after honest training (T015).
                shap: List[SHAPFactor] = []

                # Specific canonical details for INC8654273
                if inc_id == "INC8654273":
                    title = "Problem: Apache Busy Workers"
                    desc = "Problem: Apache Busy Workers no servidor web9.locaweb.com.br — encerrado sem intervenção humana em 14 segundos."
                    risk = 87
                    is_fp = True
                    dur_sec = 14
                    group = "Team14"
                    prod = "Hosting Linux"
                    ic = "IC00001"
                else:
                    desc = f"Incidente real registrado no ativo {ic} ({prod}) atribuído à equipe {group}. Aberto via {opened_by}."

                title, desc = str(title)[:200], str(desc)[:2000]
                inc = Incident(
                    id=inc_id,
                    title=title,
                    description=desc,
                    category="Web Server" if "apache" in title.lower() else ("Banco de Dados" if "mysql" in title.lower() else "Infraestrutura"),
                    priority=prio,
                    group=group,
                    product=prod,
                    config_item=ic,
                    opened_by=opened_by,
                    status="open" if idx % 3 != 0 else "in_progress",
                    risk_score=risk,
                    sla_deadline=deadline_dt.isoformat(),
                    sla_remaining_minutes=sla_mins,
                    estimated_violation=est_str,
                    cluster_id=c_id,
                    cluster_name=c_name,
                    shap_factors=shap,
                    similar_tickets=[f"INC{int(inc_id.replace('INC','')) - i}" for i in range(1, 4)],
                    is_automated_fp=is_fp,
                    duration_seconds=dur_sec,
                    created_at=created_dt.isoformat(),
                    updated_at=now.isoformat(),
                    label_source="synth_rule",
                    p_raw=None,
                    p_calibrated=None,
                    threshold_tau=None,
                    claim_label=None,  # set to measured/projection by recalibrate_pool
                    p1_n1_warning="Base contém um único exemplar P1 (n=1); sem generalização." if prio == "P1" else None,
                )
                self.incidents[inc.id] = inc
                DatabaseRepository.save_incident(inc.model_dump())

            self._load_historical_timeseries()
            logger.info(f"Initialized {len(self.incidents)} active real incidents in operational pool.")

    def _load_historical_timeseries(self):
        df = get_or_create_processed_dataset()
        if df.empty:
            return

        logger.info("Extracting historical daily operational time-series from 122k records...")
        # Sample 1000 records for fast memory indexing
        sample_df = df.sample(min(2000, len(df)), random_state=self.seed)

        self.historical_archive = []
        for _, row in sample_df.iterrows():
            self.historical_archive.append({
                "date": str(row['date_str']),
                "hour": int(row['hour']),
                "priority": str(row['prio_clean']),
                "group": str(row['grupo_clean']),
                "product": str(row['produto_clean']),
                "category": "Infraestrutura",
                "is_fp": bool(row['is_fp']),
                "ola_breached": bool(row['ola_breached_synth']) if 'ola_breached_synth' in row else bool(row['ola_breached']),
                "ola_breached_synth": bool(row['ola_breached_synth']) if 'ola_breached_synth' in row else bool(row['ola_breached']),
                "kpi_violado_obs": bool(row['kpi_violado_obs']) if 'kpi_violado_obs' in row else False,
                "title_len": len(str(row['titulo_clean'])),
                "duration_minutes": max(1, int(row['duracao_sec']) // 60)
            })

    def get_all_incidents(self) -> List[Incident]:
        with self._lock:
            return list(self.incidents.values())

    def reseed_from_dataset(self) -> int:
        """Drop the active pool and rebuild it from the dataset (filter fix).

        Pre-remediation persisted rows carry phantom squads and heuristic-era
        state that break group filters. Called on model-version change only.
        """
        with self._lock:
            dropped = DatabaseRepository.clear_incidents()
            self.incidents.clear()
            self.counter = 8654273
            logger.info(f"Reseed: dropped {dropped} stale persisted incidents.")
            self._initialize_from_dataset()
            DatabaseRepository.log_audit("RESEED", "system", None,
                                         {"dropped": dropped, "reseeded": len(self.incidents)})
            return len(self.incidents)

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        with self._lock:
            return self.incidents.get(incident_id)

    @staticmethod
    def _incident_hour(created_at: str) -> int:
        try:
            return pd.Timestamp(created_at).hour
        except Exception:
            return 14

    def recalibrate_pool(self, scorer_proba, scorer_shap, threshold_tau: float,
                          mttr_scorer=None, category_fn=None) -> int:
        """Replace seed risks with calibrated inference (T015 + Fase 7).

        Preenche também categoria econômica e MTTR estimado por chamado.
        """
        with self._lock:
            n = 0
            for inc in self.incidents.values():
                try:
                    hour = self._incident_hour(inc.created_at)
                    p_raw, p_cal = scorer_proba(
                        inc.title, inc.priority, inc.group, inc.product,
                        inc.config_item, hour)
                    risk = max(1, min(99, int(round(p_cal * 100.0))))
                    inc.p_raw = p_raw
                    inc.p_calibrated = p_cal
                    inc.threshold_tau = threshold_tau
                    inc.risk_score = risk
                    inc.label_source = "synth_rule"
                    inc.claim_label = "measured"
                    if mttr_scorer is not None:
                        try:
                            inc.estimated_mttr_minutes = float(mttr_scorer(
                                inc.title, inc.priority, inc.group, inc.product,
                                inc.config_item, hour))
                        except Exception:
                            pass
                    if category_fn is not None:
                        try:
                            inc.risk_category = category_fn(p_cal)
                        except Exception:
                            pass
                    if inc.priority == "P1":
                        inc.p1_n1_warning = "Base contém um único exemplar P1 (n=1); sem generalização."
                    inc.shap_factors = scorer_shap({
                        "title": inc.title, "priority": inc.priority,
                        "group": inc.group, "product": inc.product,
                        "config_item": inc.config_item, "hour": hour,
                        "duration_seconds": inc.duration_seconds or 14,
                        "is_automated_fp": inc.is_automated_fp,
                    })
                    inc.updated_at = datetime.now().isoformat()
                    DatabaseRepository.save_incident(inc.model_dump())
                    n += 1
                except Exception as e:
                    logger.warning(f"Recalibration failed for {inc.id}: {e}")
            logger.info(f"Recalibrated {n} active incidents with calibrated inference.")
            return n

    def _recompute_risk(self, inc) -> None:
        """Recompute calibrated risk in place via lazy ML import (T015)."""
        from backend.services.ml_engine import ml_engine
        hour = self._incident_hour(inc.created_at)
        p_raw, p_cal = ml_engine.predict_incident_proba(
            inc.title, inc.priority, inc.group, inc.product,
            inc.config_item, hour)
        inc.p_raw = p_raw
        inc.p_calibrated = p_cal
        inc.threshold_tau = ml_engine.threshold_tau
        inc.risk_score = max(1, min(99, int(round(p_cal * 100.0))))
        inc.label_source = "synth_rule"
        inc.claim_label = "measured"
        try:
            inc.estimated_mttr_minutes = float(ml_engine.predict_mttr_minutes(
                inc.title, inc.priority, inc.group, inc.product,
                inc.config_item, hour))
            inc.risk_category = ml_engine.risk_category(p_cal)
        except Exception:
            pass
        inc.shap_factors = ml_engine.calculate_incident_shap({
            "title": inc.title, "priority": inc.priority, "group": inc.group,
            "product": inc.product, "config_item": inc.config_item, "hour": hour,
            "duration_seconds": inc.duration_seconds or 14,
            "is_automated_fp": inc.is_automated_fp})

    def assign_incident(self, incident_id: str, new_group: str, notes: Optional[str] = None, user_sub: str = "operator") -> Optional[Incident]:
        with self._lock:
            if incident_id in self.incidents:
                inc = self.incidents[incident_id]
                old_group = inc.group
                risk_before = inc.risk_score
                inc.group = new_group
                inc.status = "in_progress"
                inc.updated_at = datetime.now().isoformat()
                # Calibrated recomputation replaces the banned -12 heuristic.
                self._recompute_risk(inc)
                DatabaseRepository.save_incident(inc.model_dump())
                DatabaseRepository.log_audit("ASSIGN", user_sub, incident_id, {"old_group": old_group, "new_group": new_group, "notes": notes, "risk_before": risk_before, "risk_after": inc.risk_score})
                return inc
            return None

    def escalate_incident(self, incident_id: str, new_priority: Optional[str] = None, reason: str = "", target_group: Optional[str] = None, user_sub: str = "operator") -> Optional[Incident]:
        with self._lock:
            if incident_id in self.incidents:
                inc = self.incidents[incident_id]
                old_prio = inc.priority
                risk_before = inc.risk_score
                if new_priority:
                    inc.priority = new_priority
                if target_group:
                    inc.group = target_group
                inc.status = "escalated"
                inc.updated_at = datetime.now().isoformat()
                self._recompute_risk(inc)
                DatabaseRepository.save_incident(inc.model_dump())
                DatabaseRepository.log_audit("ESCALATE", user_sub, incident_id, {"old_prio": old_prio, "new_prio": new_priority, "reason": reason, "risk_before": risk_before, "risk_after": inc.risk_score})
                return inc
            return None

    def create_synthetic_incoming(self, user_sub: str = "system") -> Incident:
        with self._lock:
            from backend.services.ml_engine import ml_engine
            self.counter += 1
            now = datetime.now()
            
            prio = random.choice(["P1", "P2", "P2", "P3", "P3"])
            group = random.choice(get_observed_groups())
            prod = random.choice(PRODUCTS)
            ic = f"IC{random.randint(1, 99):05d}"
            title = f"Problem: Apache Busy Workers no {ic}"
            
            # Genuine calibrated ML inference for risk score and SHAP factors
            p_raw, p_cal = ml_engine.predict_incident_proba(
                title=title, priority=prio, group=group, product=prod,
                config_item=ic, hour=now.hour)
            risk = max(1, min(99, int(round(p_cal * 100.0))))
            shap = ml_engine.calculate_incident_shap({
                "title": title, "priority": prio, "group": group,
                "product": prod, "config_item": ic, "hour": now.hour,
                "duration_seconds": 14, "is_automated_fp": True})
            
            sla_limits = {"P1": 240, "P2": 240, "P3": 720, "P4": 1440}
            rem_mins = max(15, sla_limits.get(prio, 720) - random.randint(10, 180))
            hours = rem_mins // 60
            mins = rem_mins % 60
            est_str = f"{hours}h {mins}min restantes" if hours > 0 else f"{mins}min restantes"
            
            inc = Incident(
                id=f"INC{self.counter}",
                title=title,
                description=f"Alerta de saturação em tempo real no ativo {ic} ({prod}) sob responsabilidade de {group}.",
                category="Web Server",
                priority=prio,
                group=group,
                product=prod,
                config_item=ic,
                opened_by="Monitoramento",
                status="open",
                risk_score=risk,
                sla_deadline=(now + timedelta(minutes=rem_mins)).isoformat(),
                sla_remaining_minutes=rem_mins,
                estimated_violation=est_str,
                cluster_id="cluster-1",
                cluster_name="Apache Busy Workers Recorrente",
                shap_factors=shap,
                similar_tickets=[f"INC{random.randint(8650000, 8654270)}" for _ in range(3)],
                is_automated_fp=True,
                duration_seconds=14,
                created_at=now.isoformat(),
                updated_at=now.isoformat(),
                label_source="synth_rule",
                p_raw=p_raw,
                p_calibrated=p_cal,
                threshold_tau=ml_engine.threshold_tau,
                claim_label="measured",
                p1_n1_warning="Base contém um único exemplar P1 (n=1); sem generalização." if prio == "P1" else None,
                risk_category=ml_engine.risk_category(p_cal),
                estimated_mttr_minutes=ml_engine.predict_mttr_minutes(
                    title=title, priority=prio, group=group, product=prod,
                    config_item=ic, hour=now.hour),
            )
            self.incidents[inc.id] = inc
            DatabaseRepository.save_incident(inc.model_dump())
            DatabaseRepository.log_audit("CREATE_SYNTHETIC", user_sub, inc.id, {"title": inc.title, "prio": inc.priority})
            return inc

itsm_store = ITSMDataStore()
