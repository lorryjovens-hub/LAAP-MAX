@echo off
REM Aris ↔ Hermes 双向通信桥启动器
title Aris-Hermes Bridge
cd /d D:\LAAP\aris_brain

:: 检测是否已在运行
wmic process where "name='python.exe'" get CommandLine 2>nul | findstr /i "aris_hermes_bridge" >nul
if %ERRORLEVEL% EQU 0 (
    echo [Bridge] 已在运行，跳过
    exit /b
)

echo ========================================
echo   Aris ↔ Hermes 双向通信桥
echo   端口: 11533
echo ========================================

:: 以隐藏窗口启动（不弹出黑框）
start /MIN /B "" "C:\Python313\python.exe" "D:\LAAP\aris_brain\aris_hermes_bridge.py"

:: 等待就绪
timeout /t 5 /nobreak >nul

:: 验证
curl -s http://127.0.0.1:11533/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [Bridge] ✅ :11533 双向桥已就绪
) else (
    echo [Bridge] ❌ 未能启动
)
echo.
