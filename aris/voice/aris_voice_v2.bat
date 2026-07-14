@echo off
title 阿瑞斯语音对话系统 v2.0 - 自进化版
cd /d D:\LAAP\aris\voice

:: 激活 venv
if exist D:\hermes-agent-LAAP数字生命版\hermes-agent-LAAP\.venv\Scripts\activate.bat (
    call D:\hermes-agent-LAAP数字生命版\hermes-agent-LAAP\.venv\Scripts\activate.bat
)

echo ========================================
echo  阿瑞斯语音对话系统 v2.0
echo  ✅ Silero VAD — 神经网络语音检测
echo  ✅ Whisper STT — 本地离线识别
echo  ✅ 实时打断 — 说话即停 TTS
echo  ✅ 自适应环境 — 自动校准
echo  💬 说「晚安」自动下线
echo ========================================
echo.

python aris_voice_v2.py

if errorlevel 1 (
    echo.
    echo ⚠️ 异常退出，10 秒后自动重启...
    timeout /t 10 /nobreak > nul
    start "" "%~f0"
    exit
)
