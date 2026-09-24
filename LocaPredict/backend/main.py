from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
import json
import os
from pathlib import Path
from typing import List

from backend.api.routes import router as api_router
from backend.services.itsm_data import itsm_store
from backend.services.ml_engine import ml_engine
from backend.core.config import settings
from backend.utils.logger import logger

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Plataforma avançada de AIOps orientada por Machine Learning para previsão de incidentes, risco de quebra de OLA, clusters NLP e regimes operacionais.",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable Strict CORS with whitelisted trusted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

# Register REST Routes
app.include_router(api_router)

# WebSocket Connection Manager for Real-Time Telemetry
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

ws_manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send initial handshake state
        regime = ml_engine.get_operational_regime()
        overview = ml_engine.get_metrics_overview()
        await websocket.send_json({
            "event": "CONNECTED",
            "regime": regime.model_dump(),
            "overview": overview.model_dump()
        })

        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            action = payload.get("action")

            if action == "SIMULATE_TICKET":
                new_inc = itsm_store.create_synthetic_incoming()
                await ws_manager.broadcast({
                    "event": "NEW_INCIDENT",
                    "incident": new_inc.model_dump()
                })
            elif action == "PING":
                await websocket.send_json({"event": "PONG"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

# Single-service deploy (F2): serve the React build same-origin so API, WS and
# UI share one URL (zero CORS, WS works remotely). Mounted LAST so /api/*,
# /ws, /docs and /redoc keep precedence. Skipped when dist/ is absent (local
# API-only dev keeps working).
_DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _DIST_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_DIST_DIR), html=True), name="spa")
    logger.info(f"Serving SPA from {_DIST_DIR}")
else:
    @app.get("/")
    def root():
        return {
            "name": settings.PROJECT_NAME,
            "status": "online (api-only: frontend/dist not built)",
            "docs": "/docs",
            "regime": ml_engine.get_operational_regime().current
        }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
