@echo off
REM ============================================================
REM Aris 全链路启动脚本 — Hermes v0.19.0 Quicksilver
REM ============================================================
REM 启动顺序:
REM   1. Aris PSI 认知引擎桥 (端口 11533)
REM   2. Hermes Agent (自动加载 Aris Plugin)
REM ============================================================

echo ════════════════════════════════════════════════════════════
echo  Aris 全链路启动 — Hermes v0.19.0 Quicksilver
echo ════════════════════════════════════════════════════════════

REM ── 设置 LAAP 环境 ──
set LAAP_ROOT=D:\LAAP
set HERMES_HOME=C:\Users\user\AppData\Local\hermes

REM ── 确保 SecretSource 可用 ──
echo [1/3] 检查 SecretSource 凭据...
python -c "from agent.secret_sources import SecretSource; print('✅ SecretSource ready')" 2>nul || echo ℹ️ SecretSource 未配置，将使用 .env 回退

REM ── 启动 Aris 认知引擎桥 ──
echo [2/3] 启动 Aris PSI 认知引擎桥 (port 11533)...
start "Aris Bridge" /B python "%LAAP_ROOT%\aris_brain\aris_hermes_bridge_v3.py"
timeout /t 3 /nobreak >nul

REM ── 验证桥接状态 ──
python -c "import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:11533/health',timeout=5); print('✅ Aris Bridge:', r.read().decode())" 2>nul || echo ⚠️ Aris Bridge 启动中...

REM ── 启动 Hermes Agent (自动加载 Aris Plugin) ──
echo [3/3] 启动 Hermes Agent v0.19.0 (Aris Plugin 自动加载)...
echo.
echo  🧠 Aris 认知引擎已就绪
echo  🌉 插件: plugins/aris/__init__.py (pre/post LLM hooks)
echo  📡 桥接: http://127.0.0.1:11533
echo  🔐 凭据: SecretSource (Bitwarden/1Password)
echo  🚀 命令: /aris, /aris-state, /aris-psi
echo ════════════════════════════════════════════════════════════
echo.

REM ── 启动 Hermes ──
cd /d "%HERMES_HOME%\hermes-agent"
python -m hermes_cli.main %*
