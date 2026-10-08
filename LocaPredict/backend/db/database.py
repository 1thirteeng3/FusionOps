import sqlite3
import json
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from pathlib import Path
from backend.utils.logger import logger

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent.parent
DB_FILE = os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "locapredict.db"))
_db_lock = threading.Lock()

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite schema for incidents, audit trail and operational state"""
    with _db_lock:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            group_name TEXT NOT NULL,
            product TEXT NOT NULL,
            config_item TEXT NOT NULL,
            opened_by TEXT NOT NULL,
            status TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            sla_deadline TEXT NOT NULL,
            sla_remaining_minutes INTEGER NOT NULL,
            estimated_violation TEXT,
            cluster_id TEXT,
            cluster_name TEXT,
            shap_factors_json TEXT,
            similar_tickets_json TEXT,
            is_automated_fp INTEGER NOT NULL,
            duration_seconds INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            incident_id TEXT,
            action TEXT NOT NULL,
            user_sub TEXT NOT NULL,
            details_json TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS operational_state (
            key TEXT PRIMARY KEY,
            value_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)

        # Fase 6.2 — auditoria contínua de saída (prediction_audit).
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_audit (
            ticket_id TEXT PRIMARY KEY,
            predicted_risk REAL,
            predicted_time REAL,
            actual_sla_violated INTEGER,
            actual_resolution_time REAL,
            timestamp_prediction TEXT,
            timestamp_resolution TEXT
        )
        """)
        # Migração: releases iniciais criaram predicted_* NOT NULL; desfechos
        # sem previsão prévia exigem NULL. Reconstrói preservando linhas.
        cols = {r[1]: r[3] for r in cursor.execute("PRAGMA table_info(prediction_audit)").fetchall()}
        if cols.get("predicted_risk") == 1:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_audit_new (
                ticket_id TEXT PRIMARY KEY,
                predicted_risk REAL,
                predicted_time REAL,
                actual_sla_violated INTEGER,
                actual_resolution_time REAL,
                timestamp_prediction TEXT,
                timestamp_resolution TEXT
            )
            """)
            cursor.execute("""
            INSERT OR IGNORE INTO prediction_audit_new
            SELECT ticket_id, predicted_risk, predicted_time,
                   actual_sla_violated, actual_resolution_time,
                   timestamp_prediction, timestamp_resolution
            FROM prediction_audit
            """)
            cursor.execute("DROP TABLE prediction_audit")
            cursor.execute("ALTER TABLE prediction_audit_new RENAME TO prediction_audit")
            logger.info("Migrated prediction_audit to nullable prediction columns.")
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_resolution_time
        ON prediction_audit (timestamp_resolution)
        """)

        # Audit hardening (Constitution VII, Gate 6, T007): indexes for
        # append-only trail queries; tables are never updated in place.
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_incident_time
        ON audit_logs (incident_id, timestamp)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_action_time
        ON audit_logs (action, timestamp)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_incidents_risk
        ON incidents (risk_score)
        """)
        
        conn.commit()
        conn.close()
        logger.info("SQLite database initialized at locapredict.db")

class DatabaseRepository:
    @staticmethod
    def save_incident(incident_dict: Dict[str, Any]):
        with _db_lock:
            conn = get_connection()
            cursor = conn.cursor()
            
            shap_json = json.dumps(incident_dict.get("shap_factors", []))
            sim_json = json.dumps(incident_dict.get("similar_tickets", []))
            
            cursor.execute("""
            INSERT OR REPLACE INTO incidents (
                id, title, description, category, priority, group_name, product, config_item,
                opened_by, status, risk_score, sla_deadline, sla_remaining_minutes, estimated_violation,
                cluster_id, cluster_name, shap_factors_json, similar_tickets_json, is_automated_fp,
                duration_seconds, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                incident_dict["id"],
                incident_dict["title"],
                incident_dict["description"],
                incident_dict["category"],
                incident_dict["priority"],
                incident_dict["group"],
                incident_dict["product"],
                incident_dict["config_item"],
                incident_dict.get("opened_by", "Monitoramento"),
                incident_dict["status"],
                incident_dict["risk_score"],
                incident_dict["sla_deadline"],
                incident_dict["sla_remaining_minutes"],
                incident_dict.get("estimated_violation"),
                incident_dict.get("cluster_id"),
                incident_dict.get("cluster_name"),
                shap_json,
                sim_json,
                1 if incident_dict.get("is_automated_fp") else 0,
                incident_dict.get("duration_seconds"),
                incident_dict["created_at"],
                incident_dict["updated_at"]
            ))
            conn.commit()
            conn.close()

    @staticmethod
    def load_all_incidents() -> List[Dict[str, Any]]:
        with _db_lock:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM incidents ORDER BY created_at DESC")
            rows = cursor.fetchall()
            conn.close()
            
            result = []
            for row in rows:
                shap_factors = []
                similar_tickets = []
                try:
                    if row["shap_factors_json"]:
                        shap_factors = json.loads(row["shap_factors_json"])
                    if row["similar_tickets_json"]:
                        similar_tickets = json.loads(row["similar_tickets_json"])
                except Exception:
                    pass
                
                result.append({
                    "id": row["id"],
                    "title": row["title"],
                    "description": row["description"],
                    "category": row["category"],
                    "priority": row["priority"],
                    "group": row["group_name"],
                    "product": row["product"],
                    "config_item": row["config_item"],
                    "opened_by": row["opened_by"],
                    "status": row["status"],
                    "risk_score": row["risk_score"],
                    "sla_deadline": row["sla_deadline"],
                    "sla_remaining_minutes": row["sla_remaining_minutes"],
                    "estimated_violation": row["estimated_violation"],
                    "cluster_id": row["cluster_id"],
                    "cluster_name": row["cluster_name"],
                    "shap_factors": shap_factors,
                    "similar_tickets": similar_tickets,
                    "is_automated_fp": bool(row["is_automated_fp"]),
                    "duration_seconds": row["duration_seconds"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                })
            return result

    @staticmethod
    def clear_incidents() -> int:
        """Delete all persisted incidents (version-gated reseed support).

        Used only when the model version changes and pre-remediation rows
        would otherwise pollute the pool with stale heuristic-era state.
        Audit trail is preserved.
        """
        with _db_lock:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS n FROM incidents")
            n = int(cursor.fetchone()["n"])
            cursor.execute("DELETE FROM incidents")
            conn.commit()
            conn.close()
            return n

    @staticmethod
    def record_prediction(ticket_id: str, predicted_risk: float, predicted_time: float) -> None:
        """Grava previsão no momento da abertura (Fase 6.2)."""
        with _db_lock:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO prediction_audit
                (ticket_id, predicted_risk, predicted_time,
                 actual_sla_violated, actual_resolution_time,
                 timestamp_prediction, timestamp_resolution)
            VALUES (?, ?, ?, COALESCE((SELECT actual_sla_violated FROM prediction_audit WHERE ticket_id = ?), NULL),
                   COALESCE((SELECT actual_resolution_time FROM prediction_audit WHERE ticket_id = ?), NULL),
                   ?, NULL)
            """, (ticket_id, float(predicted_risk), float(predicted_time),
                  ticket_id, ticket_id, datetime.now().isoformat()))
            conn.commit()
            conn.close()

    @staticmethod
    def record_resolution(ticket_id: str, actual_sla_violated: bool,
                          actual_resolution_time: float) -> bool:
        """Grava o desfecho real no encerramento (Fase 6.2). Retorna se existia previsão."""
        with _db_lock:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ticket_id FROM prediction_audit WHERE ticket_id = ?", (ticket_id,))
            exists = cursor.fetchone() is not None
            if exists:
                cursor.execute("""
                UPDATE prediction_audit
                SET actual_sla_violated = ?, actual_resolution_time = ?, timestamp_resolution = ?
                WHERE ticket_id = ?
                """, (1 if actual_sla_violated else 0, float(actual_resolution_time),
                      datetime.now().isoformat(), ticket_id))
            else:
                cursor.execute("""
                INSERT INTO prediction_audit
                    (ticket_id, predicted_risk, predicted_time,
                     actual_sla_violated, actual_resolution_time,
                     timestamp_prediction, timestamp_resolution)
                VALUES (?, NULL, NULL, ?, ?, NULL, ?)
                """, (ticket_id, 1 if actual_sla_violated else 0, float(actual_resolution_time),
                      datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return exists

    @staticmethod
    def list_resolved_predictions(days: int = 30) -> List[Dict[str, Any]]:
        """Linhas com previsão E desfecho (para Brier móvel / MdAE)."""
        with _db_lock:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            SELECT ticket_id, predicted_risk, predicted_time,
                   actual_sla_violated, actual_resolution_time,
                   timestamp_prediction, timestamp_resolution
            FROM prediction_audit
            WHERE actual_sla_violated IS NOT NULL AND predicted_risk IS NOT NULL
            """)
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]

    @staticmethod
    def clear_prediction_audit() -> None:
        """Limpa a auditoria de predições (uso em testes; jamais em produção)."""
        with _db_lock:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM prediction_audit")
            conn.commit()
            conn.close()

    @staticmethod
    def log_audit(action: str, user_sub: str, incident_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        with _db_lock:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO audit_logs (timestamp, incident_id, action, user_sub, details_json)
            VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                incident_id,
                action,
                user_sub,
                json.dumps(details or {})
            ))
            conn.commit()
            conn.close()

    @staticmethod
    def set_state(key: str, value: Any):
        with _db_lock:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO operational_state (key, value_json, updated_at)
            VALUES (?, ?, ?)
            """, (key, json.dumps(value), datetime.now().isoformat()))
            conn.commit()
            conn.close()

    @staticmethod
    def get_state(key: str) -> Optional[Any]:
        with _db_lock:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value_json FROM operational_state WHERE key = ?", (key,))
            row = cursor.fetchone()
            conn.close()
            if row:
                try:
                    return json.loads(row["value_json"])
                except Exception:
                    return None
            return None

init_db()
