@echo off
title Ao Ψ V12 — Feishu Bridge (LLM Mode)
echo.
echo   ╔══════════════════════════════════════════╗
echo   ║  Ao Ψ V12 Feishu Bridge (LLM Mode)        ║
echo   ╚══════════════════════════════════════════╝
echo.
echo   启动 Ao 飞书桥接服务 (DeepSeek LLM)...
echo.

"D:\hermes-agent-main (1)\hermes-agent-main\.venv\Scripts\python.exe" -u "D:\LAAP\aris_brain\ao_feishu_bridge.py"

if %errorlevel% neq 0 (
    echo.
    echo   ❌ 启动失败，错误码: %errorlevel%
    pause
)
