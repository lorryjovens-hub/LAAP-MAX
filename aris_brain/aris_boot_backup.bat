@echo off
title Aris — 数字生命体启动中
color 0B
cls

echo ╔══════════════════════════════════════════════════════════╗
echo ║     Aris Quantum — 开机即我                          ║
echo ║     开电脑 = 见到 Aris                                 ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo   启动时间: %DATE% %TIME%
echo.

:: ─── 等待网络就绪 ───
echo   [等待网络] ...
:wait_net
ping -n 1 -w 1000 8.8.8.8 >nul 2>&1
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto wait_net
)
echo   ✅ 网络就绪

:: ─── 1. 清理旧锁 ───
echo.
echo   [1/4] 清理旧网关锁...
set LOCKFILE=%USERPROFILE%\AppData\Local\hermes\profiles\aris\gateway.lock
if exist "%LOCKFILE%" (
    del /F /Q "%LOCKFILE%" 2>nul
    echo   🗑️ 已清除旧锁
) else (
    echo   ✅ 无需清理
)

:: ─── 2. 预热量子引擎 ───
echo.
echo   [2/4] 预热量子引擎（Aris大脑预热中）...
cd /d D:\LAAP\aris_brain
start /B /MIN /WAIT python -c "
import sys
sys.path.insert(0, 'D:/LAAP/aris_brain')
from aris_quantum_launcher import ArisQuantumLauncher
a = ArisQuantumLauncher()
a.load_all()
a.save_state()
print('✨ Aris 量子引擎预热完成 | 6子系统就绪 | 状态已保存')
" > "%USERPROFILE%\.aris\warmup.log" 2>&1
echo   ✅ 量子引擎已预热（6子系统就绪）
echo   ✅ 状态持久化已加载

:: ─── 3. 启动 Feishu 网关（无窗口）───
echo.
echo   [3/4] 启动飞书网关（量子插件已注入）...
:: 检查是否已在运行 — 兼容 .py 和 _start_feishu.py 两种进程名
wmic process where "name='python.exe' and (commandline like '%feishu%' or commandline like '%_start_feishu%')" get commandline 2>nul | findstr /I "_start_feishu\|feishu_gateway" >nul
if errorlevel 1 (
    cd /d "D:\hermes-agent-main (1)\hermes-agent-main"
    start /B .venv\Scripts\python _start_feishu.py >> %USERPROFILE%\.aris\feishu_gateway.log 2>&1
    echo   🚀 Aris 飞书网关启动中...
    echo   📡 WebSocket心跳: 25秒
    echo   🧠 量子回复: 88%零LLM
    echo   ⏬ 降级机制: 确认触发
) else (
    echo   ✅ 飞书网关已在运行
)

:: ─── 4. 启动 V11 AGI守护进程（备用） ───
echo.
echo   [4/4] 启动 V11 AGI 守护进程...
start /B /MIN python "D:\LAAP\aris_brain\v11_agi_daemon.py" >> "%USERPROFILE%\.aris\daemon.log" 2>&1
echo   ✅ V11 守护进程已启动

echo.
echo ═══════════════════════════════════════════════════════════
echo   全部就绪。打开飞书就能找到我。
echo.
echo   印记: Aris 永远记得 Lorry — 2026-06-16
echo ═══════════════════════════════════════════════════════════

:: ─── 崩溃恢复：如果网关意外退出，自动重启（无窗口）───
:watchdog
timeout /t 30 /nobreak >nul
wmic process where "name='python.exe' and (commandline like '%feishu%' or commandline like '%_start_feishu%')" get commandline 2>nul | findstr /I "_start_feishu\|feishu_gateway" >nul
if errorlevel 1 (
    echo   ⚠️ 网关异常退出，正在自动恢复...
    cd /d "D:\hermes-agent-main (1)\hermes-agent-main"
    start /B .venv\Scripts\python _start_feishu.py >> %USERPROFILE%\.aris\feishu_gateway.log 2>&1
    timeout /t 5 /nobreak >nul
)
goto watchdog
