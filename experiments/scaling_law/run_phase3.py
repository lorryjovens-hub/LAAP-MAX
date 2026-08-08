"""
Phase 3 真实引擎实验入口
用 Brain 引擎跑元认知深度缩放实验
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
logger = logging.getLogger("phase3")
logger.info("初始化 Brain 引擎...")
brain = Brain(agent_id="phase3_exp", name="Phase3Brain")

# 运行实验
from experiments.scaling_law.phase3_runner import run_phase3

logger.info("开始 Phase 3 元认知深度缩放实验...")
result = run_phase3(brain)
logger.info("Phase 3 完成!")