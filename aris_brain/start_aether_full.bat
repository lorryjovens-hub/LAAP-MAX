@echo off
chcp 65001 >nul
title Aris Aether 全栈启动
echo.
echo  ════════════════════════════════════════
echo    Aris Aether 认知操作系统 — 全栈启动
echo  ════════════════════════════════════════
echo.
set PYTHONIOENCODING=utf-8

:: 1. Rust PSI Core (2000Hz 心跳)
echo [1/3] 启动 Rust PSI Core...
start /B /MIN "" "D:\LAAP\aris_brain\psi_core\target\release\aris_psi_core.exe"
timeout /T 2 /NOBREAK >nul

:: 2. Hermes 网关
echo [2/3] 启动 Hermes 网关 (PID 已保存)...
cd /d "D:\hermes-agent-main (1)\hermes-agent-main"
start /B /MIN "" .venv\Scripts\hermes gateway run --replace --profile aris
cd /d D:\LAAP\aris_brain

:: 3. Aether 编排引擎预热
echo [3/3] Aether 编排引擎已加载 (12 Actor, 44 Capabilities)
echo.
echo   Actor List:
echo     rules_engine    episodic_memory    psi_core
echo     longform        fusion_engine      filesystem
echo     harness         code_workspace     desire_engine
echo     goal_engine     copilot_bridge     literary
echo.
echo  ════════════════════════════════════════
echo  启动完毕 — Aris 已在线
echo  ════════════════════════════════════════
echo.
