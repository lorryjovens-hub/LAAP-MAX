@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
echo [Aether] 启动 Hermes 网关管理脚本...
powershell -ExecutionPolicy Bypass -File "D:\LAAP\aris_brain\_gw_manager.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo [Aether] 启动完成（查看日志: state\gateway_manager.log）
) else (
    echo [Aether] 启动完成
)
pause
