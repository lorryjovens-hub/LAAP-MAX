"""
Phase 2 真实引擎实验入口
用 Brain 引擎跑模块平衡实验
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# 初始化 Brain
from laap.cognition.brain import Brain
logger = logging.getLogger("phase2")
logger.info("初始化 Brain 引擎...")
brain = Brain(agent_id="phase2_exp", name="Phase2Brain")

# 运行实验
from experiments.scaling_law.phase2_runner import run_phase2

logger.info("开始 Phase 2 模块平衡实验...")
result = run_phase2(brain)
logger.info("Phase 2 完成!")