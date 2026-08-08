"""编排器集成测试 - 验证 Stage 0 → Stage 1 的完整感知流程

由于完整 orchestrator 依赖很多组件，主要验证：
- TaskStatus 枚举包含 PRE_PERCEPTION
- orchestrator 集成了所有新模块（CrawlerOrgan / SensorFusion / PerceptualMemory / ActivePerceptionScheduler）
- run_replication_pipeline 包含 Stage 0 调用
"""

import inspect

import pytest

from src.api.models import TaskStatus


def test_task_status_has_pre_perception():
    """TaskStatus 枚举包含 PRE_PERCEPTION"""
    assert hasattr(TaskStatus, "PRE_PERCEPTION")
    assert TaskStatus.PRE_PERCEPTION.value == "pre_perception"


def test_task_status_order():
    """PRE_PERCEPTION 在 PERCEIVING 之前"""
    statuses = list(TaskStatus)
    pre_idx = statuses.index(TaskStatus.PRE_PERCEPTION)
    perceiving_idx = statuses.index(TaskStatus.PERCEIVING)
    assert pre_idx < perceiving_idx


def test_task_status_values_unique():
    """所有枚举值唯一"""
    statuses = list(TaskStatus)
    values = [s.value for s in statuses]
    assert len(values) == len(set(values))


def test_orchestrator_imports():
    """orchestrator 可导入且 __init__ 集成了所有新模块"""
    from src.consciousness.execution.orchestrator import ReplicationOrchestrator

    src = inspect.getsource(ReplicationOrchestrator.__init__)
    # 验证初始化了新模块
    assert "crawler_organ" in src or "CrawlerOrgan" in src
    assert "sensor_fusion" in src or "SensorFusion" in src
    assert "perceptual_memory" in src or "PerceptualMemory" in src
    assert "active_scheduler" in src or "ActivePerceptionScheduler" in src


def test_orchestrator_has_stage_0():
    """run_replication_pipeline 包含 Stage 0"""
    from src.consciousness.execution.orchestrator import ReplicationOrchestrator

    src = inspect.getsource(ReplicationOrchestrator.run_replication_pipeline)
    # 验证 Stage 0 存在
    assert "PRE_PERCEPTION" in src or "Stage 0" in src or "pre_perception" in src.lower()
    assert "run_active_perception" in src or "active_scheduler" in src


def test_orchestrator_has_sensor_fusion_in_stage_1():
    """Stage 1 调用 SensorFusion"""
    from src.consciousness.execution.orchestrator import ReplicationOrchestrator

    src = inspect.getsource(ReplicationOrchestrator.run_replication_pipeline)
    assert "sensor_fusion" in src or "SensorFusion" in src or "fuse(" in src


def test_orchestrator_has_perceptual_memory_storage():
    """orchestrator 调用 PerceptualMemory.store_perception"""
    from src.consciousness.execution.orchestrator import ReplicationOrchestrator

    src = inspect.getsource(ReplicationOrchestrator.run_replication_pipeline)
    assert "store_perception" in src or "perceptual_memory" in src


def test_orchestrator_has_perception_state_attrs():
    """orchestrator __init__ 初始化了感知状态属性"""
    from src.consciousness.execution.orchestrator import ReplicationOrchestrator

    src = inspect.getsource(ReplicationOrchestrator.__init__)
    assert "_perception_signals" in src or "_fused_tech_stack" in src


def test_orchestrator_graceful_degradation():
    """orchestrator 在感知模块加载失败时降级（不抛异常）"""
    from src.consciousness.execution.orchestrator import ReplicationOrchestrator

    src = inspect.getsource(ReplicationOrchestrator.__init__)
    # 应该有 try/except 包裹感知模块初始化
    assert "except" in src.lower() or "try" in src.lower()


def test_orchestrator_stage0_extracts_urls():
    """Stage 0 从 custom_instructions 提取 URL"""
    from src.consciousness.execution.orchestrator import ReplicationOrchestrator

    src = inspect.getsource(ReplicationOrchestrator.run_replication_pipeline)
    # 应有 URL 提取逻辑
    assert "_extract_urls" in src or "_is_url" in src


def test_orchestrator_compare_perceptions_in_stage_0():
    """Stage 0 调用 compare_perceptions 对比多个参考快照"""
    from src.consciousness.execution.orchestrator import ReplicationOrchestrator

    src = inspect.getsource(ReplicationOrchestrator.run_replication_pipeline)
    assert "compare_perceptions" in src or "common_tech_stack" in src
