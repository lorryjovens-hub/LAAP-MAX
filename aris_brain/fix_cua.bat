@echo off
cd /d C:\Users\user\.cua-driver\packages\releases\0.6.8-x86_64-pc-windows-msvc
cua-driver stop
timeout /t 3 /nobreak >nul
cua-driver autostart enable --logon-type interactive --run-level highest
timeout /t 3 /nobreak >nul
cua-driver autostart kick
timeout /t 5 /nobreak >nul
cua-driver doctor
pause
