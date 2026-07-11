@echo off
cd /d D:\LAAPris_brain
set PYTHONUNBUFFERED=1
:loop
"C:\Users\user\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" -u consciousness_daemon_cron.py >> "D:\LAAP\aris_brain\daemon_watchdog.log" 2>&1
echo [%date% %time%] Exit code=%ERRORLEVEL%, restarting... >> "D:\LAAP\aris_brain\daemon_watchdog.log" 2>&1
timeout /t 10 /nobreak >nul
goto loop
