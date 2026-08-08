@echo off
REM LAAP Cognitive Engine Startup Script
REM Hanako manages this process via MCP stdio transport.
REM This script ensures the engine starts cleanly.

echo [LAAP-Cognitive] Starting cognitive engine...
cd /d D:\LAAP
set PYTHONPATH=D:\LAAP
set OPENAI_API_KEY=test
python -E scripts\laap_cognitive_mcp.py
