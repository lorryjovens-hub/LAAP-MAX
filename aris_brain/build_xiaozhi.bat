@echo off
call D:\user\Documents\ESPclaw-lorry\esp\esp-idf\export.bat
cd /d D:\xiaozhi-esp32-main (2)\xiaozhi-esp32-main
echo === Setting target ===
idf.py set-target esp32c3
echo exit code: %errorlevel%
echo === Building ===
idf.py build
echo exit code: %errorlevel%
