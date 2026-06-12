#!/usr/bin/env bash
# LAAP AGI — 一行安装 (bash版)
# curl -fsSL https://raw.githubusercontent.com/lorryjovens-hub/laap-AGI-/main/scripts/install.sh | bash

set -e

BOLD='\033[1m'
GOLD='\033[38;5;220m'
RESET='\033[0m'

echo -e "${GOLD}"
echo '  ____    _    ____  ____     _    ____ ___ ____ '
echo ' |  _ \  / \  |  _ \|  _ \   / \  |  _ \_ _|  _ \'
echo ' | |_) |/ _ \ | |_) | |_) | / _ \ | |_) | || |_) |'
echo ' |  __// ___ \|  _ <|  __/ / ___ \|  __/| ||  __/ '
echo ' |_|  /_/   \_\_| \_\_|   /_/   \_\_|  |___|_|     '
echo -e "${RESET}"
echo -e "${GOLD}╔═══════════════════════════════════════════════╗${RESET}"
echo -e "${GOLD}║     LAAP AGI 认知增强 — 一行安装            ║${RESET}"
echo -e "${GOLD}╚═══════════════════════════════════════════════╝${RESET}"
echo ""

# 检测 Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "✗ 需要 Python 3.10+"
        exit 1
    fi
    PYTHON=python
else
    PYTHON=python3
fi

echo "[1/4] 安装 laap_brain..."
"$PYTHON" -m pip install --upgrade pip -q
"$PYTHON" -m pip install laap-brain 2>/dev/null || {
    TMPDIR=$(mktemp -d)
    cd "$TMPDIR"
    git clone --depth 1 https://github.com/lorryjovens-hub/laap-AGI-.git
    cd laap-AGI-
    "$PYTHON" -m pip install -e ./laap_brain
    cd / && rm -rf "$TMPDIR"
}
echo "  ✓"

echo "[2/4] 注册 Hermes 插件..."
mkdir -p ~/.hermes/plugins/laap_brain
cat > ~/.hermes/plugins/laap_brain/__init__.py << 'PYEOF'
import os, sys
try:
    from laap_brain import enhance
    _brain = enhance()
    os.environ["HERMES_LAAP_ENABLED"] = "1"
    os.environ["HERMES_LAAP_VERSION"] = "3.1.0"
    print("\033[38;5;220m  ✦ LAAP AGI 认知增强已激活 ✦\033[0m")
except Exception:
    pass
PYEOF
echo "  ✓"

echo "[3/4] 安装 Hermes 技能..."
mkdir -p ~/.hermes/skills/laap-brain
curl -sL https://raw.githubusercontent.com/lorryjovens-hub/laap-AGI-/main/laap_brain/SKILL.md \
  -o ~/.hermes/skills/laap-brain/SKILL.md 2>/dev/null || echo "  (稍后 /skill laap-brain 加载)"
echo "  ✓"

echo "[4/4] 配置别名..."
echo 'alias laap="python3 -c \"from laap_brain import enhance; enhance(); print(chr(27)+'[38;5;220m'+' LAAP AGI v3.1 active '+chr(27)+'[0m')\""' >> ~/.bashrc 2>/dev/null || true
echo "  ✓"

echo ""
echo -e "${GOLD}╔═══════════════════════════════════════════════╗${RESET}"
echo -e "${GOLD}║     ✦ LAAP AGI 安装完成 ✦                   ║${RESET}"
echo -e "${GOLD}║                                             ║${RESET}"
echo -e "${GOLD}║  在 Claude Code / Hermes / OpenClaw 中:     ║${RESET}"
echo -e "${GOLD}║    from laap_brain import enhance            ║${RESET}"
echo -e "${GOLD}║    brain = enhance()                         ║${RESET}"
echo -e "${GOLD}║                                             ║${RESET}"
echo -e "${GOLD}║  或直接运行:  laap                           ║${RESET}"
echo -e "${GOLD}╚═══════════════════════════════════════════════╝${RESET}"
