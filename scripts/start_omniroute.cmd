@echo off
REM ============================================================
REM LAAP — OmniRoute Launcher (永久免费 LLM 路由网关)
REM ============================================================
REM 启动 OmniRoute 服务 (http://localhost:20128, OpenAI 兼容端点)
REM 聚合 290+ provider / 90+ 免费 tier, RTK+Caveman 压缩节省 15-95% tokens
REM
REM 用法:
REM   scripts\start_omniroute.cmd            REM 前台启动
REM   scripts\start_omniroute.cmd --check    REM 仅探测健康状态
REM   scripts\start_omniroute.cmd --help     REM 显示帮助
REM ============================================================

setlocal EnableDelayedExpansion

set "OMNIROUTE_DIR=%~dp0..\OmniRoute-release-v3.8.50"
set "OMNIROUTE_PORT=20128"
set "OMNIROUTE_BASE_URL=http://localhost:%OMNIROUTE_PORT%"
set "HEALTH_URL=http://localhost:%OMNIROUTE_PORT%/api/health"

REM ── 处理参数 ──
if /i "%~1"=="--help" goto :show_help
if /i "%~1"=="-h" goto :show_help
if /i "%~1"=="--check" goto :check_health

REM ── 检查 OmniRoute 目录 ──
if not exist "%OMNIROUTE_DIR%\package.json" (
    echo [ERROR] OmniRoute 未找到: %OMNI_DIR%
    echo [INFO]  请先拉取 OmniRoute 项目到该目录, 或修改本脚本中的 OMNIROUTE_DIR
    exit /b 1
)

REM ── 检查 Node.js 版本 (要求 ^22.22.2 || ^24 || ^25 || ^26) ──
where node >nul 2>nul
if errorlevel 1 (
    echo [ERROR] 未检测到 Node.js。OmniRoute 要求 Node ^22.22.2 || ^24 || ^25 || ^26
    echo [INFO]  安装: https://nodejs.org/
    exit /b 1
)
for /f "tokens=*" %%v in ('node -v') do set "NODE_VER=%%v"
echo [INFO] Node 版本: %NODE_VER% (OmniRoute 要求 ^22.22.2 || ^24 || ^25 || ^26)

REM ── 健康检查: 是否已经在运行 ──
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri '%HEALTH_URL%' -TimeoutSec 2 -UseBasicParsing; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>nul
if not errorlevel 1 (
    echo [OK] OmniRoute 已在运行: %OMNIROUTE_BASE_URL%
    echo [INFO] 端点: %OMNIROUTE_BASE_URL%/v1  (OpenAI 兼容)
    echo [INFO] 健康: %HEALTH_URL%
    exit /b 0
)

REM ── 首次运行: 安装依赖 ──
if not exist "%OMNIROUTE_DIR%\node_modules" (
    echo [INFO] 首次启动, 正在安装依赖 (npm install)...
    pushd "%OMNIROUTE_DIR%"
    call npm install
    set "INSTALL_EXIT=!errorlevel!"
    popd
    if not "!INSTALL_EXIT!"=="0" (
        echo [ERROR] npm install 失败 (exit !INSTALL_EXIT!)
        exit /b !INSTALL_EXIT!
    )
    echo [OK] 依赖安装完成
)

REM ── 启动 OmniRoute ──
echo [INFO] 启动 OmniRoute...
echo [INFO] 目录: %OMNIROUTE_DIR%
echo [INFO] 端点: %OMNIROUTE_BASE_URL%/v1
echo [INFO] 健康: %HEALTH_URL%
echo [INFO] 按 Ctrl+C 停止服务
echo.

pushd "%OMNIROUTE_DIR%"
call npm start
set "START_EXIT=!errorlevel!"
popd

if not "!START_EXIT!"=="0" (
    echo [ERROR] OmniRoute 退出 (exit !START_EXIT!)
    exit /b !START_EXIT!
)

endlocal
exit /b 0

:check_health
echo [INFO] 探测 OmniRoute 健康: %HEALTH_URL%
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri '%HEALTH_URL%' -TimeoutSec 3 -UseBasicParsing; Write-Host '[OK] OmniRoute 在线 (HTTP' $r.StatusCode ')'; exit 0 } catch { Write-Host '[WARN] OmniRoute 离线'; exit 1 }"
exit /b %errorlevel%

:show_help
echo 用法: %~nx0 [选项]
echo.
echo 选项:
echo   (无)        前台启动 OmniRoute 服务
echo   --check     仅探测健康状态
echo   --help, -h  显示此帮助
echo.
echo 环境变量:
echo   OMNIROUTE_BASE_URL  覆盖默认端点 (默认 http://localhost:20128)
echo   OMNIROUTE_API_KEY   远程部署时的 API key (本地默认无需)
echo.
echo 启动后, LAAP 会自动探测到 OmniRoute 并优先使用免费路由。
echo   - provider.py:  OmniRouteProvider
echo   - router.py:    prefer_free (auto_detect=True)
echo   - registry.py:  omniroute/* 模型 (cost=0)
exit /b 0
