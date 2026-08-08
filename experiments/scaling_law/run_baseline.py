"""Phase 0 基线测量入口脚本"""
import sys
from pathlib import Path

# 确保能找到模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from experiments.scaling_law.baseline_runner import run_baseline

if __name__ == "__main__":
    run_baseline()