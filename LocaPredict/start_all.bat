@echo off
echo ==========================================================
echo  LocaPredict SLA Guard v3 - Iniciando Solucao Completa
echo ==========================================================
cd /d %~dp0
start "LocaPredict Backend API (Porta 8000)" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul
start "LocaPredict Frontend (Porta 5173)" cmd /k "cd frontend && npm run dev"
echo.
echo ==========================================================
echo  Ambiente operacional iniciado!
echo  Backend Docs:  http://localhost:8000/docs
echo  Frontend AIOps: http://localhost:5173
echo ==========================================================
