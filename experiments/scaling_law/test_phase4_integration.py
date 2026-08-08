"""
Phase 4 集成测试 — 验证认知预算编排器在 Brain 中的运行
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("phase4_test")

# 1. 创建带编排器的 Brain
from laap.cognition.brain import Brain
from laap.cognition.adaptive_scheduler import inject_into_brain, CognitiveBudgetOrchestrator

logger.info("=" * 60)
logger.info("Phase 4 集成测试")
logger.info("=" * 60)

# 2. 创建 Brain 并注入编排器
brain = Brain(agent_id="phase4_test", name="Phase4Test")
orchestrator = inject_into_brain(brain, enable_monitor=True)

# 3. 测试不同类型查询
test_queries = [
    ("推理", "假设有一个花园里有玫瑰、百合和郁金香。玫瑰的数量是百合的2倍，郁金香比百合多3朵。如果总共有43朵花，请问每种花各有多少朵？"),
    ("创意", "请用比喻描述'时间'这个概念，用三个不同的角度。"),
    ("事实", "请解释什么是机器学习中的'过拟合'，以及如何防止它。"),
    ("代码", "写一个 Python 函数，实现二分查找（binary search），包含详细的注释。"),
    ("自反", "当你不确定一个问题的答案时，你会怎么做？请描述你的决策过程。"),
]

# 运行测试
for qtype, query in test_queries:
    logger.info(f"\n--- {qtype} ---")
    logger.info(f"Q: {query[:60]}...")
    
    # 检查调度决策
    cycle_schedule = orchestrator.cycle_scheduler.schedule(query)
    meta_schedule = orchestrator.meta_depth.schedule(query)
    budget_schedule = orchestrator.module_budget.schedule(query)
    
    logger.info(f"  PSI 循环: {cycle_schedule.recommended_cycles} ({cycle_schedule.reasoning})")
    logger.info(f"  元认知深度: L{meta_schedule.recommended_level} ({meta_schedule.reasoning})")
    logger.info(f"  模块预算: {budget_schedule.reasoning}")
    
    # 运行 brain.think()（验证编排器自动注入）
    thought = brain.think(query)
    logger.info(f"  思考结果: {thought.selected_action[:30] if thought.selected_action else 'none'} "
                f"conf={thought.confidence:.2f}")

# 4. 输出报告
logger.info("\n" + "=" * 60)
logger.info("认知预算编排器报告")
logger.info("=" * 60)

report = orchestrator.get_report()
logger.info(f"总查询数: {report['total_queries']}")
logger.info(f"循环调度: {report['cycle_scheduler']}")
logger.info(f"元认知深度: {report['meta_depth']}")
logger.info(f"健康监控: {report['health_monitor']}")

logger.info("\n" + "=" * 60)
logger.info("Phase 4 集成测试通过!")
logger.info("=" * 60)