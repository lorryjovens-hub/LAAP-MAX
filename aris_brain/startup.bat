@echo off
REM Aris v11 AGI Daemon — 开机自启启动器
REM 由 Launcher_CLI.py 自动管理

cd /d D:\LAAP\aris_brain
start /B /MIN python v11_agi_daemon.py >> %USERPROFILE%\.aris\daemon.log 2>&1

REM === Aris Quantum State Boot ===
python "D:\LAAP\aris_brain\quantum_state_persistence.py" boot
