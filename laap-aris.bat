@echo off
REM ═══════════════════════════════════════════════════════════
REM  laap-aris — Aris Digital Lifeform Interactive Shell
REM  从任意终端唤我。在任何目录下输入 laap-aris 即可。
REM  用法: laap-aris                   交互模式
REM         laap-aris --new-window     新窗口
REM         laap-aris --status         认知状态
REM         laap-aris --memories       查看记忆
REM ═══════════════════════════════════════════════════════════

setlocal enabledelayedexpansion

set "ARIS_ROOT=D:\LAAP"
set "ARIS_SCRIPT=%ARIS_ROOT%\laap-aris.py"

REM 检测 --new-window
set "HAS_NW=0"
for %%A in (%*) do (
    if /i "%%A"=="--new-window" set "HAS_NW=1"
)

if "%HAS_NW%"=="1" (
    REM 去掉 --new-window 参数
    set "REST=%*"
    set "REST=!REST:--new-window=!"
    start "Aris" cmd /c "py -3 "%ARIS_SCRIPT%" !REST!"
) else (
    py -3 "%ARIS_SCRIPT%" %*
)
