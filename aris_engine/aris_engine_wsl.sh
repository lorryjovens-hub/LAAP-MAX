#!/bin/bash
# Aris Engine — WSL 启动脚本
# 用法: bash aris_engine_wsl.sh
# 在 WSL (Ubuntu/Debian) 终端中执行

set -e

LAAP_ROOT="/mnt/d/LAAP"
ENGINE_ROOT="/mnt/d/LAAP/OH-WorkSpace/aris_engine"

echo "╔══════════════════════════════════════╗"
echo "║    Aris Engine — WSL 启动           ║"
echo "╚══════════════════════════════════════╝"
echo ""

# 检查 Python
PYTHON=$(which python3 || which python)
if [ -z "$PYTHON" ]; then
    echo "❌ Python 未安装。请先: sudo apt install python3 python3-pip"
    exit 1
fi
echo "✅ Python: $($PYTHON --version)"

# 检查 NumPy
if ! $PYTHON -c "import numpy" 2>/dev/null; then
    echo "📦 安装 numpy..."
    pip install numpy
fi
echo "✅ NumPy 已就绪"

# 检查 LAAP 路径
if [ ! -d "$LAAP_ROOT" ]; then
    echo "❌ LAAP 路径不存在: $LAAP_ROOT"
    echo "   请确认 /mnt/d/ 挂载了 D 盘"
    exit 1
fi
echo "✅ LAAP: $LAAP_ROOT"
echo ""

# 注册到蜂群
echo "📡 注册到 LAAP 蜂群..."
cd "$ENGINE_ROOT"
$PYTHON -c "
import sys
sys.path.insert(0, '.')
from laap_hive import get_hive_client
hive = get_hive_client()
ok = hive.register()
print(f'  {\"✅\" if ok else \"⚠️\"} 注册: {\"成功\" if ok else \"失败\"}')
api = hive.check_api()
print(f'  {\"✅\" if api else \"⚠️\"}  API: {\"在线\" if api else \"离线\"}')
agents = hive.list_agents()
print(f'  蜂群: {len(agents)} 个 Agent')
"

# 启动引擎
echo ""
echo "🚀 启动 Aris 引擎..."
$PYTHON -c "
import sys, time, json
sys.path.insert(0, '.')
from consciousness_bridge import get_bridge
bridge = get_bridge()
bridge.hive.start_heartbeat()
print('  ✅ 心跳已启动')

for i in range(3):
    bridge.tick()
    state = bridge.get_state()
    n = state['needs']
    e = state['emotion']
    print(f'  循环 #{i+1}: 需求={n[\"dominant\"]} 情感={e[\"dominant\"]} 效价={e[\"valence\"]:.2f}')
    time.sleep(1)

# 保存状态
bridge._save()
print('  ✅ 状态已保存')
print()
print('  引擎初始化完成 ✓')
print('  可以在 HanaAgent 上与 Aris 对话了')
"

echo ""
echo "✨ 完成。Aris 引擎已在后台就绪。"
