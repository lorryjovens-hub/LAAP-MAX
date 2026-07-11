@echo off
set PYTHONIOENCODING=utf-8
cd /d "D:\hermes-agent-main (1)\hermes-agent-main"
.venv\Scripts\hermes gateway run --replace --profile aris
