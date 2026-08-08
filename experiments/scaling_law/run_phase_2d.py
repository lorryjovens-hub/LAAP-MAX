"""
Phase 2D 真实引擎实验入口
元认知深度 × PSI 循环数交互效应实验
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from laap.cognition.brain import Brain
logger = logging.getLogger("phase2d")
logger.info("初始化 Brain 引擎...")
brain = Brain(agent_id="phase2d_exp", name="Phase2D")

from experiments.scaling_law.phase_2d_runner import run_phase_2d

logger.info("开始 Phase 2D 交互效应实验 (360 次运行)...")
result = run_phase_2d(brain)
logger.info("Phase 2D 完成!")