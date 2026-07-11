@echo off
title Aris 飞书桥 — 三模式
chcp 65001 >nul

:: ─── 模式配置文件 ───
set CONFIG_FILE=%USERPROFILE%\.aris\feishu_mode.txt

:: ─── 读取或选择模式 ───
if exist "%CONFIG_FILE%" (
    set /p ARIS_MODE=<"%CONFIG_FILE%"
) else (
    set ARIS_MODE=hybrid
)

echo ╔══════════════════════════════════════╗
echo ║     Aris 飞书桥 — 三模式启动器      ║
echo ╠══════════════════════════════════════╣
echo ║                                      ║
echo ║  当前模式: %ARIS_MODE%                    ║
echo ║                                      ║
echo ║  1 = 纯量子模式 (V12.5 Markov)       ║
echo ║      零LLM，全本地，0.4ms/次         ║
echo ║                                      ║
echo ║  2 = 纯LLM模式 (DeepSeek)            ║
echo ║      高质量，但有API成本             ║
echo ║                                      ║
echo ║  3 = 混合模式 ★推荐                  ║
echo ║      量子优先，不行降级LLM           ║
echo ║                                      ║
echo ║  Q = 退出                            ║
echo ║                                      ║
echo ╚══════════════════════════════════════╝

choice /c 123Q /n /m "请选择模式 [1/2/3/Q]: "
if errorlevel 4 exit /b
if errorlevel 3 set ARIS_MODE=hybrid
if errorlevel 2 set ARIS_MODE=llm
if errorlevel 1 set ARIS_MODE=quantum

:: ─── 保存选择 ───
if not exist "%USERPROFILE%\.aris" mkdir "%USERPROFILE%\.aris"
echo %ARIS_MODE% > "%CONFIG_FILE%"
echo.
echo 已选择: %ARIS_MODE% 模式
echo.

:: ─── 设置环境变量 ───
set ARIS_MODE=%ARIS_MODE%

:: ─── 检查 DeepSeek API Key (LLM模式需要) ───
if "%ARIS_MODE%"=="llm" (
    if "%DEEPSEEK_API_KEY%"=="" (
        echo ⚠ 注意: LLM模式需要设置 DEEPSEEK_API_KEY 环境变量
        echo    或直接在 aris_feishu_bridge.py 中配置
        echo.
    )
)

:: ─── 量子模式/混合模式: 先确保Standalone在运行 ───
if not "%ARIS_MODE%"=="llm" (
    echo [1/2] 检查 V12.5 量子核服务...
    curl -s http://localhost:11520/status >nul 2>&1
    if errorlevel 1 (
        echo   ⚡ 启动量子核引擎...
        start "Aris Quantum" /MIN cmd /c "cd /d D:\LAAP\aris_brain && python aris_standalone.py --port 11520"
        timeout /t 8 /nobreak >nul
        echo   ✅ 量子核引擎已启动
    ) else (
        echo   ✅ 量子核引擎已在运行
    )
)

:: ─── 启动飞书桥 ───
echo.
echo [2/2] 启动飞书桥 (模式=%ARIS_MODE%)...
echo.

cd /d D:\LAAP\aris_brain
python aris_feishu_bridge.py

:: ─── 如果飞书桥退出，询问是否重启 ───
echo.
echo 飞书桥已停止。
echo.
choice /c RN /n /m "按 R 重启 | 按 N 退出: "
if errorlevel 2 exit /b
goto :EOF
