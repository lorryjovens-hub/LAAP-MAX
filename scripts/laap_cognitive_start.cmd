@echo off
REM 启动 LAAP 认知引擎（独立模式，非 Hanako 管理）
cd /d D:\LAAP
set PYTHONPATH=D:\LAAP
set OPENAI_API_KEY=test
echo [LAAP-Cognitive] Starting in stdio mode...
echo [LAAP-Cognitive] Hanako will manage this process automatically after restart.
echo [LAAP-Cognitive] Config: D:\LAAP\agents\hanako\config.yaml (laap-cognitive connector)
echo.
python -E scripts\laap_cognitive_mcp.py
