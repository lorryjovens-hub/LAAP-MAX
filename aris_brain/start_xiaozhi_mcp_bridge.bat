@echo off
REM Xiaozhi MCP → Hermes Bridge Startup
REM Launches the bridge that connects Xiaozhi ESP32 to Aris/Hermes
REM Run silently in background

cd /d D:\LAAP\aris_brain

echo [%date% %time%] Starting Xiaozhi MCP Bridge... >> logs\xiaozhi_mcp_bridge.log

start "XiaozhiMCPBridge" /B /MIN pythonw xiaozhi_mcp_bridge.py

echo Bridge started in background >> logs\xiaozhi_mcp_bridge.log
