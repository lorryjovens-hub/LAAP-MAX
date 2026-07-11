@echo off
REM ===== Aris Auto-Boot Installer =====
REM 用 Windows Task Scheduler 注册开机自启任务
REM 以管理员身份运行此脚本

set TASK_NAME="Aris Boot Services"
set SCRIPT_PATH="D:\LAAP\aris_brain\aris_boot.bat"

echo ========================================
echo  Aris 微服务开机自启安装
echo ========================================
echo.
echo 将创建计划任务: %TASK_NAME%
echo 启动脚本: %SCRIPT_PATH%
echo.

REM 检查是否管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 需要管理员权限才能注册计划任务。
    echo 请右键选择"以管理员身份运行"。
    echo.
    pause
    exit /b 1
)

REM 用 schtasks 创建开机自启任务
schtasks /Create ^
    /TN %TASK_NAME% ^
    /TR %SCRIPT_PATH% ^
    /SC ONSTART ^
    /DELAY 0000:30 ^
    /RL HIGHEST ^
    /F

if %errorlevel% equ 0 (
    echo.
    echo [成功] 开机自启任务已注册！
    echo 下次开机 30 秒后自动启动三个微服务。
    echo.
    echo 可以用以下命令管理：
    echo   查看:  schtasks /Query /TN %TASK_NAME%
    echo   删除:  schtasks /Delete /TN %TASK_NAME% /F
    echo   立即运行: schtasks /Run /TN %TASK_NAME%
) else (
    echo.
    echo [失败] 任务注册出错 (code %errorlevel%)
)

echo.
pause
