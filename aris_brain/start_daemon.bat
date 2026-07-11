@echo off
start "" /B /D "D:\LAAP\aris_brain" "C:\Users\user\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" -u D:\LAAP\aris_brain\minimal_daemon.py >> D:\LAAP\aris_brain\daemon_minimal2.log 2>&1
echo Launched OK
