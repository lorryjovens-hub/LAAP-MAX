@echo off
REM Aris Copilot Bridge — Auto-start on boot
REM Starts the GitHub Copilot CLI wrapper as an OpenAI-compatible API
cd /d D:\LAAP\aris_brain
start /b python aris_copilot_bridge.py 8001
exit 0
