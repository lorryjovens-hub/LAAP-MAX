@echo off
REM Aether Agent Framework — 独立认知运行时启动器 v7
REM Hermes只做通信壳，Aether是自己的引擎
REM ===========================================

title Aether Runtime v7

set "BRAIN=D:\LAAP\aris_brain"
set "LOG=%BRAIN%\logs\startup.log"

if not exist "%LOG%\" mkdir "%LOG%" 2>nul

echo [%date% %time%] Aether v7 启动中... >> "%LOG%"
echo ================================================ >> "%LOG%"

REM === 1. 启动 Rust PSI Core (2000Hz 认知心跳) ===
echo [PSI] Starting Rust PSI Core...
start /B /MIN /HIGH "" "%BRAIN%\psi_core\target\release\aris_psi_core.exe"
echo [PSI] Rust PSI Core started >> "%LOG%"

REM === 2. 启动 Aether Runtime (带飞书桥+3D可视化) ===
echo [AETHER] Starting Aether Runtime...
start /B /MIN /LOW "" python "%BRAIN%\aether\cli.py" run
echo [AETHER] Aether Runtime started >> "%LOG%"

REM === 3. 启动 Web Gateway (独立聊天界面) ===
echo [WEB] Starting Web Gateway...
start /B /MIN /LOW "" python "%BRAIN%\aether\gateway.py"
echo [WEB] Web Gateway started on :11528 >> "%LOG%"

REM === 4. 启动 Monitor 仪表盘 ===
echo [MONITOR] Starting Monitor Dashboard...
start /B /MIN /LOW "" python "%BRAIN%\aether\monitor.py"
echo [MONITOR] Monitor started on :11529 >> "%LOG%"

REM === 5. 清理旧 pi_psi_server ===
wmic process where "name='python.exe' and CommandLine like '%%pi_psi_server%%'" delete 2>nul
echo [CLEANUP] Old processes cleaned >> "%LOG%"

echo ================================================ >> "%LOG%"
echo [%date% %time%] Aether v7 启动完成 >> "%LOG%"
echo.
echo Aether Agent Framework v7 — 已启动
echo CLI: python -m aether.cli status
echo 3D:  http://localhost:11527
