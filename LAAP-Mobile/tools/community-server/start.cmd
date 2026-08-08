@echo off
setlocal
cd /d "%~dp0"
echo [INFO] Starting LAAP Community Server...
echo        Web UI  : http://localhost:8790/
echo        Export  : http://localhost:8790/export
node server.js --port 8790
if errorlevel 1 (
  echo [ERROR] Failed to start. Is Node.js installed?
  pause
)