@echo off
REM =====================================================================
REM  LAAP Desktop Tools Launcher
REM  Starts the community server (port 8790) and the remote control
REM  bridge (port 8791) so phones on the LAN can control the desktop LAAP.
REM =====================================================================
setlocal
cd /d "%~dp0"

echo [LAAP] Starting Community Server (http://localhost:8790) ...
start "LAAP Community Server" cmd /k "node community-server\server.cjs"

echo [LAAP] Starting Remote Bridge (phone control: http://localhost:8791) ...
start "LAAP Remote Bridge" cmd /k "node community-server\remote-bridge.cjs"

echo.
echo [LAAP] Both services started in separate windows.
echo   Community Server : http://localhost:8790  (browse/publish/export APK)
echo   Remote Bridge    : http://localhost:8791  (phone controls desktop LAAP)
echo   Phone control UI : http://<your-desktop-ip>:8791/  (same WiFi)
echo.
endlocal