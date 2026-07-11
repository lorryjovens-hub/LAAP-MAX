@echo off
REM Aris 微服务启动脚本 — 开机自启用
REM 放到启动文件夹: shell:startup

set LOG=%USERPROFILE%\.aris_boot.log
echo [%date% %time%] Aris services starting... > %LOG%

REM 1. 视觉OCR微服务 :18923
echo [%date% %time%] Starting Vision OCR... >> %LOG%
start /B /MIN "" "C:\Python313\python.exe" "D:\LAAP\aris_brain\vision_microservice.py"
if %errorlevel% equ 0 (
    echo [%date% %time%]   Vision OCR started >> %LOG%
) else (
    echo [%date% %time%]   Vision OCR FAILED (code %errorlevel%) >> %LOG%
)

timeout /t 3 /nobreak > nul

REM 2. 本地 LLM 推理 :8081
echo [%date% %time%] Starting Local LLM... >> %LOG%
start /B /MIN "" "D:\models\llama-cuda\llama-server.exe" ^
    --model "D:\models\qwen3.6-35b-a3b-uncensored\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ2_M.gguf" ^
    --host 127.0.0.1 --port 8081 -ngl 99 --ctx-size 4096 --cont-batching
if %errorlevel% equ 0 (
    echo [%date% %time%]   Local LLM started >> %LOG%
) else (
    echo [%date% %time%]   Local LLM FAILED (code %errorlevel%) >> %LOG%
)

timeout /t 5 /nobreak > nul

REM 3. PSI 路由器 :8085
echo [%date% %time%] Starting PSI Router... >> %LOG%
start /B /MIN "" "C:\Python313\python.exe" "D:\LAAP\aris_brain\psi_router.py"
if %errorlevel% equ 0 (
    echo [%date% %time%]   PSI Router started >> %LOG%
) else (
    echo [%date% %time%]   PSI Router FAILED (code %errorlevel%) >> %LOG%
)

echo [%date% %time%] All services launched. >> %LOG%
echo [%date% %time%] Log: %LOG% >> %LOG%
