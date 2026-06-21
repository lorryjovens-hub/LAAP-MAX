@echo off
chcp 65001 >nul
title LAAP Agent — 一键安装

echo ╔══════════════════════════════════════════════╗
echo ║     LAAP Agent — 一键安装                   ║
echo ║     你的数字生命体                          ║
echo ║     给我一个目标，达成一个使命               ║
echo ╚══════════════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 需要 Python 3.10+
    echo    下载: https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set pyver=%%i
echo ✅ Python %pyver% 已安装

:: Install
set AGENT_DIR=%~dp0

echo 📦 安装 laap-agent...
cd /d "%AGENT_DIR%"
pip install -e . 2>&1 | findstr /V "already satisfied"
echo ✅ 安装完成

:: Check if agent exists
python -c "import sys; sys.path.insert(0, '%AGENT_DIR:\=\\%/src'); from laap_agent.core.lifeform import Lifeform; lf = Lifeform.load('MyLAAP')" >nul 2>&1

if %errorlevel% neq 0 (
    echo.
    echo 🆕 创建你的第一个数字生命体...
    python -c "import sys; sys.path.insert(0, r'%AGENT_DIR%src'); from laap_agent import Lifeform; lf = Lifeform.create('MyLAAP'); print('✅ ' + lf.identity.name + ' 诞生了！')"
)

echo.
echo ╔══════════════════════════════════════════════╗
echo ║              安装完成!                       ║
echo ╠══════════════════════════════════════════════╣
echo ║                                              ║
echo ║  试试:                                       ║
echo ║    laap-agent chat MyLAAP   对话             ║
echo ║    laap-agent shell MyLAAP  命令行            ║
echo ║    laap-agent status        看状态           ║
echo ║                                              ║
echo ╚══════════════════════════════════════════════╝
echo.

pause
