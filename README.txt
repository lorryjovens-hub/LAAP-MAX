LAAP Digital Lifeform - Quick Start
========================================

Web: http://localhost:8081
API: ws://localhost:8766 (WebSocket for chat)

START:
  Double-click D:\LAAP\start.bat
  OR:  python D:\LAAP\laap_web.py
  OR:  powershell D:\LAAP\laap_start.ps1

TTS (Voice output):
  - Built-in EdgeTTS works without any setup
  - For FishSpeech: start_docker.bat then restart LAAP
  - Auto-fallback: if Docker TTS not available, uses EdgeTTS

Characters:
  - Ctrl+C opens character panel
  - Search: Furina, Klee, Ganyu, HuTao, etc.
  - 13 game characters with full personality

Voice Input:
  - Hold Space to record, release to send
  - Chrome/Edge browser required
  - First use: allow microphone permission

Tips:
  - F12 opens DevTools console for debugging
  - http://localhost:8081/debug_bones.html tests VRM skeleton
  - Characters/memories persist in laap/character_engine/
