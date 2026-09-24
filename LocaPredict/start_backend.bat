@echo off
echo ==========================================================
echo  LocaPredict SLA Guard v3 - Iniciando Backend FastAPI
echo ==========================================================
cd /d %~dp0
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause
