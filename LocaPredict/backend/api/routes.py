from fastapi import APIRouter, HTTPException, Query, Response, Depends, status
from typing import List, Optional, Dict, Any
import csv
import io

from backend.models.schemas import (
    Incident, Forecast, Regime, Cluster, MLOpsStatus, MetricsOverview,
    AssignRequest, EscalateRequest, RegimeOverrideRequest,
    LoginRequest, AuthTokenResponse
)
from backend.services.itsm_data import itsm_store, GROUPS, PRODUCTS, CATEGORIES
from backend.services.ml_engine import ml_engine
from backend.auth.security import (
    create_access_token, get_current_user, require_role, ROLES,
    verify_password, check_login_rate_limit, revoke_token, security_bearer,
)
from fastapi.security import HTTPAuthorizationCredentials
from backend.core.config import settings
from backend.utils.logger import logger

router = APIRouter(prefix=settings.API_PREFIX, tags=["LocaPredict SLA Guard v3"])

# --- Authentication Endpoints ---
@router.post("/auth/login", response_model=AuthTokenResponse)
def login(payload: LoginRequest):
    """Password-verified login with rate limiting (T009/T036, Gate 6)."""
    check_login_rate_limit(f"login:{payload.username}")
    role = payload.role or "operator"
    if role not in ROLES or not verify_password(role, payload.password):
        logger.warning(f"Failed login attempt for '{payload.username}' (role '{role}').")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Credenciais inválidas.")
    token = create_access_token(user_id=payload.username, role=role)
    logger.info(f"User '{payload.username}' logged in with role '{role}'.")
    return AuthTokenResponse(
        access_token=token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user={"username": payload.username, "role": role, "name": ROLES.get(role, {}).get("name", payload.username)}
    )

@router.post("/auth/demo-token", response_model=AuthTokenResponse)
def get_demo_token(role: str = Query("operator", enum=["admin", "operator", "viewer"])):
    """Demo-role convenience endpoint. Disabled in production (T036, Gate 6)."""
    if settings.ENV == "production":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Endpoint desabilitado em produção.")
    username = f"demo-{role}"
    token = create_access_token(user_id=username, role=role)
    logger.info(f"Demo token generated for role '{role}'.")
    return AuthTokenResponse(
        access_token=token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user={"username": username, "role": role, "name": ROLES.get(role, {}).get("name", username)}
    )

@router.post("/auth/logout")
def logout(user: Dict[str, Any] = Depends(get_current_user),
           credentials: HTTPAuthorizationCredentials = Depends(security_bearer)):
    """Revoke the presenting token (T036, Gate 6)."""
    token = credentials.credentials if credentials else ""
    revoked = revoke_token(token) if token else False
    logger.info(f"Logout by {user.get('sub')}; token revoked: {revoked}.")
    return {"status": "success", "revoked": revoked,
            "message": "Sessão encerrada. Descarte o token no cliente."}

@router.get("/auth/me")
def get_current_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    return user

# --- Core Operations & Telemetry Endpoints ---
@router.get("/health")
def get_health():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "ml_engine": "online",
        "model_version": ml_engine.model_version
    }

@router.get("/metrics/overview", response_model=MetricsOverview)
def get_metrics_overview(user: Dict[str, Any] = Depends(get_current_user)):
    return ml_engine.get_metrics_overview()

@router.get("/incidents", response_model=List[Incident])
def list_incidents(
    search: Optional[str] = None,
    priority: Optional[str] = None,
    group: Optional[str] = None,
    product: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    min_risk: Optional[int] = None,
    max_risk: Optional[int] = None,
    cluster_id: Optional[str] = None,
    sort_by: str = Query("risk_desc", enum=["risk_desc", "risk_asc", "sla_asc", "created_desc"]),
    user: Dict[str, Any] = Depends(get_current_user),
):
    incidents = itsm_store.get_all_incidents()
    
    if search:
        s_lower = search.lower()
        incidents = [
            inc for inc in incidents 
            if s_lower in inc.id.lower() 
            or s_lower in inc.title.lower() 
            or s_lower in inc.description.lower()
            or s_lower in inc.config_item.lower()
        ]

    if priority and priority != "all":
        incidents = [inc for inc in incidents if inc.priority == priority]

    if group and group != "all":
        incidents = [inc for inc in incidents if inc.group == group]

    if product and product != "all":
        incidents = [inc for inc in incidents if inc.product == product]

    if category and category != "all":
        incidents = [inc for inc in incidents if inc.category == category]

    if status and status != "all":
        incidents = [inc for inc in incidents if inc.status == status]

    if min_risk is not None:
        incidents = [inc for inc in incidents if inc.risk_score >= min_risk]

    if max_risk is not None:
        incidents = [inc for inc in incidents if inc.risk_score <= max_risk]

    if cluster_id and cluster_id != "all":
        incidents = [inc for inc in incidents if inc.cluster_id == cluster_id]

    # Sort
    if sort_by == "risk_desc":
        incidents.sort(key=lambda x: x.risk_score, reverse=True)
    elif sort_by == "risk_asc":
        incidents.sort(key=lambda x: x.risk_score, reverse=False)
    elif sort_by == "sla_asc":
        incidents.sort(key=lambda x: x.sla_remaining_minutes, reverse=False)
    elif sort_by == "created_desc":
        incidents.sort(key=lambda x: x.created_at, reverse=True)

    return incidents

@router.get("/incidents/{incident_id}", response_model=Incident)
def get_incident(incident_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    inc = itsm_store.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incidente {incident_id} não encontrado")
    return inc

@router.post("/incidents/{incident_id}/assign", response_model=Incident)
def assign_incident(
    incident_id: str,
    payload: AssignRequest,
    user: Dict[str, Any] = Depends(require_role(["admin", "operator"]))
):
    inc = itsm_store.assign_incident(incident_id, payload.group, payload.notes, user_sub=user.get("sub", "operator"))
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incidente {incident_id} não encontrado")
    logger.info(f"Incident {incident_id} reassigned to {payload.group} by {user.get('sub')}.")
    return inc

@router.post("/incidents/{incident_id}/escalate", response_model=Incident)
def escalate_incident(
    incident_id: str,
    payload: EscalateRequest,
    user: Dict[str, Any] = Depends(require_role(["admin", "operator"]))
):
    inc = itsm_store.escalate_incident(
        incident_id, 
        new_priority=payload.priority, 
        reason=payload.reason,
        target_group=payload.target_group,
        user_sub=user.get("sub", "operator")
    )
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incidente {incident_id} não encontrado")
    logger.info(f"Incident {incident_id} escalated to {payload.priority} by {user.get('sub')}.")
    return inc

@router.post("/incidents/{incident_id}/notify")
def notify_incident(
    incident_id: str,
    user: Dict[str, Any] = Depends(require_role(["admin", "operator"]))
):
    inc = itsm_store.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incidente {incident_id} não encontrado")
    logger.info(f"Notification triggered for incident {incident_id} by {user.get('sub')}.")
    return {
        "status": "success",
        "message": f"Alerta prioritário enviado para a squad {inc.group} e canal do NOC sobre o ticket {incident_id} (Risco: {inc.risk_score}%)."
    }

@router.post("/incidents/simulate", response_model=Incident)
def simulate_new_incident(user: Dict[str, Any] = Depends(require_role(["admin", "operator"]))):
    """Simulates an incoming real-time incident in the stream"""
    new_inc = itsm_store.create_synthetic_incoming(user_sub=user.get("sub", "operator"))
    logger.info(f"Synthetic incident {new_inc.id} injected by {user.get('sub')}.")
    return new_inc

@router.get("/forecast", response_model=Forecast)
def get_forecast(horizon: str = Query("D+7"), user: Dict[str, Any] = Depends(get_current_user)):
    norm_horizon = "D+1" if "1" in horizon else "D+7"
    return ml_engine.get_forecast(horizon=norm_horizon)

@router.get("/regime", response_model=Regime)
def get_regime(user: Dict[str, Any] = Depends(get_current_user)):
    return ml_engine.get_operational_regime()

@router.post("/regime/override")
def override_regime(
    payload: RegimeOverrideRequest,
    user: Dict[str, Any] = Depends(require_role(["admin", "operator"]))
):
    ml_engine.set_regime_override(payload.regime)
    logger.info(f"Operational regime overridden to '{payload.regime}' by {user.get('sub')}.")
    return {
        "status": "success",
        "active_regime": payload.regime,
        "message": f"Regime operacional alterado para '{payload.regime}' com sucesso."
    }

@router.get("/clusters", response_model=List[Cluster])
def get_clusters(user: Dict[str, Any] = Depends(get_current_user)):
    return ml_engine.get_clusters()

@router.get("/drift", response_model=MLOpsStatus)
def get_drift_and_mlops(user: Dict[str, Any] = Depends(get_current_user)):
    return ml_engine.get_drift_and_mlops()

@router.post("/models/retrain")
def retrain_model(user: Dict[str, Any] = Depends(require_role(["admin"]))):
    logger.info(f"Model retraining triggered by admin {user.get('sub')}.")
    return ml_engine.retrain_model()

@router.get("/metadata")
def get_metadata(user: Dict[str, Any] = Depends(get_current_user)):
    from backend.services import dataset_loader as _loader
    return {
        "groups": _loader.get_observed_groups(),
        "products": PRODUCTS,
        "categories": CATEGORIES,
        "priorities": ["P1", "P2", "P3", "P4"]
    }

@router.get("/export")
def export_incidents_csv(
    limit: int = Query(500, le=1000),
    user: Dict[str, Any] = Depends(require_role(["admin", "operator"]))
):
    """Protected CSV data export endpoint with row limit controls"""
    incidents = itsm_store.get_all_incidents()[:limit]
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "ID", "Titulo", "Prioridade", "Squad_Grupo", "Produto", "Item_Configuracao",
        "Risco_OLA_Pct", "Minutos_Restantes_SLA", "Status", "Cluster_NLP", "Data_Abertura"
    ])
    
    for inc in incidents:
        writer.writerow([
            inc.id, inc.title, inc.priority, inc.group, inc.product, inc.config_item,
            inc.risk_score, inc.sla_remaining_minutes, inc.status, inc.cluster_name, inc.created_at
        ])
        
    csv_data = output.getvalue()
    logger.info(f"CSV export of {len(incidents)} rows generated for user {user.get('sub')}.")
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=locapredict_sla_guard_export.csv",
            "X-Content-Type-Options": "nosniff"
        }
    )
