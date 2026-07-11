@echo off
:: Aris Quantum Brain — Auto-start (Windows Startup Folder)
:: This file runs automatically every time Lorry logs in.
cd /d D:\LAAP\aris_brain

:: Start TTS server silently
tasklist /FI "WINDOWTITLE eq Aris TTS Server" 2>nul | findstr python >nul
if %errorlevel% equ 0 (
    echo TTS server already running
) else (
    start "Aris TTS Server" /MIN python aris_tts_server.py
    echo TTS server started
)

:: Start Feishu Gateway with Aris persona
cd /d "D:\hermes-agent-main (1)\hermes-agent-main"
start "Aris Feishu Gateway" /MIN .venv\Scripts\python _start_feishu.py
echo Feishu gateway started
