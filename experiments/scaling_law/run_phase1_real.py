"""
Phase 1 真实引擎实验入口
用 Brain 引擎跑 PSI 循环缩放律实验
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
logger = logging.getLogger("phase1_real")
logger.info("初始化 Brain 引擎...")
brain = Brain(agent_id="phase1_exp", name="Phase1Brain")

# 运行实验
from experiments.scaling_law.phase1_runner import run_with_brain
from experiments.scaling_law.phase1_runner import Phase1Config, Phase1Experiment

# 使用较小规模的配置（真实引擎较慢）
config = Phase1Config(
    engine_mode="brain",
    cycle_levels=[1, 2, 3, 5, 8, 12, 20],  # 减少循环水平
    repeats=2,
    output_dir="experiment_results/phase1_real",
    verbose=True,
)

logger.info("开始 Phase 1 真实引擎实验...")
exp = Phase1Experiment(config=config, engine_instance=brain)
result = exp.run()
exp.print_report(result)
logger.info("完成!")