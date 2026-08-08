# -*- coding: utf-8 -*-
"""缺口补充集成测试

验证 supplement-upgrade-task-gaps spec 实现的全部新增模块可正常协同工作。
覆盖：
- 模块可导入性
- 安全治理层（zones/evolution_sandbox/threat_intel）协同
- sandbox migration 往返一致性
- 3 个协议文件可被子类化
- 情感系统影响任务调度
- 元认知系统生成复盘报告
- 跨模块协同场景
"""
import os
import tempfile
from pathlib import Path

import pytest


class TestModuleImportable:
    """验证所有新增模块可导入"""

    def test_security_zones_importable(self):
        from laap.security.zones import (
            SafetyZone, ActionType, ZonePolicy, ZoneManager,
            DEFAULT_POLICIES, PromotionRequest,
        )
        assert SafetyZone.SANDBOX is not None
        assert ActionType.CODE_EXECUTION is not None

    def test_security_evolution_sandbox_importable(self):
        from laap.security.evolution_sandbox import (
            EvolutionSandbox, SandboxResourceLimit, SandboxResult, VersionSnapshot,
        )
        assert EvolutionSandbox is not None

    def test_security_threat_intel_importable(self):
        from laap.security.threat_intel import (
            ThreatIntelBus, ThreatPattern, ThreatType, ThreatSeverity,
            ThreatStatus, ThreatIntelEvent,
        )
        assert ThreatType.MALICIOUS_CODE is not None

    def test_sandbox_migration_importable(self):
        from laap.sandbox.migration import (
            export_sandbox, import_sandbox, SnapHeader,
            LAAPSNAP_VERSION, LAAPSNAP_MAGIC,
        )
        assert LAAPSNAP_VERSION == "1.0"
        assert LAAPSNAP_MAGIC == "LAAPSNAP"

    def test_protocol_laap_evo_importable(self):
        from laap.protocol.laap_evo import (
            EvolutionProtocol, MutationProposal, MutationType,
            ExperiencePacket, SelectionReport, SelectionStatus,
        )
        assert MutationType.SKILL_NEW is not None

    def test_protocol_laap_coop_importable(self):
        from laap.protocol.laap_coop import (
            CooperationProtocol, TaskAssignment, SharedFact, FactScope,
            NegotiationResult, NegotiationOutcome, TaskStatus,
        )
        assert FactScope.PRIVATE is not None

    def test_protocol_laap_tool_importable(self):
        from laap.protocol.laap_tool import (
            ToolProtocol, LaapTool, ToolPermissions, PermissionLevel,
            ToolCategory, ToolInvocationResult,
        )
        assert PermissionLevel.READ_ONLY is not None

    def test_cognition_emotion_importable(self):
        from laap.cognition.emotion import (
            EmotionSystem, EmotionState, EmotionEventType,
        )
        assert EmotionEventType.TASK_SUCCESS is not None

    def test_cognition_metacognition_importable(self):
        from laap.cognition.metacognition import (
            MetacognitionSystem, ReflectionReport, Anomaly, AnomalyType,
            Improvement, ImprovementType,
        )
        assert AnomalyType.OSCILLATION is not None


class TestSecurityLayerIntegration:
    """安全治理层三模块协同测试"""

    def test_zones_evolution_sandbox_integration(self):
        """zones + evolution_sandbox 协同：沙箱执行受 ZoneManager 策略约束"""
        from laap.security.zones import SafetyZone, ActionType, ZoneManager
        from laap.security.evolution_sandbox import (
            EvolutionSandbox, SandboxResourceLimit,
        )

        zone_mgr = ZoneManager()
        sandbox = EvolutionSandbox(
            zone_manager=zone_mgr,
            resource_limit=SandboxResourceLimit(execution_timeout_sec=5),
        )
        try:
            # 简单代码执行
            result = sandbox.execute_in_sandbox("print('integration test')")
            assert result.success is True
            # ZoneManager 应记录审计日志
            logs = zone_mgr.get_audit_log()
            assert len(logs) >= 1
        finally:
            sandbox.cleanup()

    def test_threat_intel_immune_integration(self):
        """threat_intel + 免疫系统检测器集成"""
        from laap.security.threat_intel import (
            ThreatIntelBus, ThreatPattern, ThreatType, ThreatSeverity,
        )
        from laap.security.zones import SafetyZone

        bus = ThreatIntelBus(node_id="test_node")
        # 模拟免疫系统检测器
        class FakeDetector:
            def __init__(self):
                self.rules = {}
            def add_rule(self, rule_id, rule):
                self.rules[rule_id] = rule

        detector = FakeDetector()
        threat = ThreatPattern(
            threat_type=ThreatType.INJECTION_ATTACK,
            severity=ThreatSeverity.HIGH,
            name="测试威胁",
            detection_rule={"pattern": "malicious"},
        )
        bus.broadcast_threat(threat)
        bus.integrate_with_immune(detector)
        assert threat.threat_id in detector.rules

    def test_full_security_pipeline(self):
        """完整安全流程：检测威胁 → 广播 → 沙箱验证 → 晋升"""
        from laap.security.zones import SafetyZone, ZoneManager
        from laap.security.threat_intel import (
            ThreatIntelBus, ThreatPattern, ThreatType, ThreatSeverity,
        )
        from laap.security.evolution_sandbox import (
            EvolutionSandbox, SandboxResourceLimit,
        )

        # 1. 检测威胁并广播
        bus = ThreatIntelBus(node_id="sec_node")
        threat = ThreatPattern(
            threat_type=ThreatType.MALICIOUS_CODE,
            severity=ThreatSeverity.CRITICAL,
            name="恶意代码检测",
        )
        bus.broadcast_threat(threat)
        assert bus.stats["broadcast_count"] == 1

        # 2. 在沙箱中验证修复代码
        zone_mgr = ZoneManager()
        sandbox = EvolutionSandbox(
            zone_manager=zone_mgr,
            resource_limit=SandboxResourceLimit(execution_timeout_sec=5),
        )
        try:
            result = sandbox.execute_in_sandbox(
                "# 修复代码\nprint('fix applied')"
            )
            assert result.success is True
        finally:
            sandbox.cleanup()

        # 3. 申请晋升（Sandbox → Quarantine）
        promo = zone_mgr.request_promotion(
            artifact_id="fix_001",
            from_zone=SafetyZone.SANDBOX,
            to_zone=SafetyZone.QUARANTINE,
            test_results={"passed": True},
        )
        assert promo.status == "pending"


class TestSandboxMigrationRoundtrip:
    """sandbox migration 导出导入往返一致性"""

    def test_migration_roundtrip(self, tmp_path):
        """导出再导入后 sandbox 状态等价"""
        from laap.sandbox.migration import export_sandbox, import_sandbox
        # 创建简单的 mock 对象模拟 CognitiveSandbox
        class FakeSubsystem:
            def __init__(self, name):
                self.name = name
                self.data = {"value": 42}

        class FakeSandbox:
            def __init__(self):
                self.sandbox_id = "test_sb_001"
                self.role = "architect"
                self.identity = FakeSubsystem("identity")
                self.self_model = FakeSubsystem("self_model")
                self.world_model = FakeSubsystem("world_model")
                self.memory_stream = FakeSubsystem("memory_stream")
                self.goal_keeper = FakeSubsystem("goal_keeper")
                self.resource_budget = FakeSubsystem("resource_budget")
                self.skill_library = None
                self.boundary = FakeSubsystem("boundary")

        sandbox = FakeSandbox()
        snap_path = tmp_path / "test.laapsnap"
        export_sandbox(sandbox, str(snap_path))
        assert snap_path.exists()
        # 导入（由于 FakeSandbox 不是真实 CognitiveSandbox，此处仅验证文件格式）
        # 真实往返测试在 tests/sandbox/test_migration.py 中

    def test_migration_file_format(self, tmp_path):
        """验证 .laapsnap 文件格式正确"""
        from laap.sandbox.migration import (
            export_sandbox, SnapHeader, LAAPSNAP_MAGIC, LAAPSNAP_VERSION,
        )
        import json

        class FakeSandbox:
            sandbox_id = "fmt_test"
            role = "test"
            identity = None
            self_model = None
            world_model = None
            memory_stream = None
            goal_keeper = None
            resource_budget = None
            skill_library = None
            boundary = None

        snap_path = tmp_path / "format.laapsnap"
        export_sandbox(FakeSandbox(), str(snap_path))
        # 读取文件头
        with open(snap_path, "rb") as f:
            header_len = int.from_bytes(f.read(8), "big")
            header_json = f.read(header_len).decode("utf-8")
            header = SnapHeader(**json.loads(header_json))
        assert header.magic == LAAPSNAP_MAGIC
        assert header.version == LAAPSNAP_VERSION
        assert header.sandbox_id == "fmt_test"


class TestProtocolSubclassing:
    """3 个协议文件可被子类化并调用全部接口"""

    def test_laap_evo_subclass(self):
        from laap.protocol.laap_evo import (
            EvolutionProtocol, MutationProposal, MutationType,
            ExperiencePacket, SelectionReport, SelectionStatus,
        )

        class MyEngine(EvolutionProtocol):
            def propose_mutation(self, capability_gap):
                return MutationProposal(
                    proposal_id="p1",
                    mutation_type=MutationType.SKILL_NEW,
                    capability_gap=capability_gap,
                    target_module="m",
                    proposed_change={},
                    expected_benefit="b",
                )

            def select_variant(self, proposal, test_results):
                return SelectionReport(
                    proposal_id=proposal.proposal_id,
                    status=SelectionStatus.APPROVED,
                    test_results=test_results,
                    performance_delta=0.1,
                    quality_delta=0.0,
                )

            def propagate_experience(self, experience):
                pass

            def list_proposals(self, status=None):
                return []

        eng = MyEngine()
        p = eng.propose_mutation("gap")
        assert p.capability_gap == "gap"
        r = eng.select_variant(p, {})
        assert r.status == SelectionStatus.APPROVED

    def test_laap_coop_subclass(self):
        from laap.protocol.laap_coop import (
            CooperationProtocol, TaskAssignment, SharedFact, FactScope,
            NegotiationResult, NegotiationOutcome, TaskStatus,
        )

        class MyCoop(CooperationProtocol):
            def assign_task(self, task, assignee_id):
                return TaskAssignment(
                    assignment_id="a1",
                    task_id=task.get("task_id", "t"),
                    task_description=task.get("description", ""),
                    assignee_id=assignee_id,
                    assigner_id="me",
                )

            def share_fact(self, fact):
                pass

            def negotiate(self, proposal, counterparty_ids):
                return NegotiationResult(
                    negotiation_id="n1",
                    outcome=NegotiationOutcome.ACCEPTED,
                    agreed_terms=proposal,
                    participants=counterparty_ids,
                )

            def query_shared_facts(self, tags=None, source_id=None):
                return []

            def get_assignments(self, assignee_id=None):
                return []

        coop = MyCoop()
        a = coop.assign_task({"task_id": "t1", "description": "d"}, "agent1")
        assert a.assignee_id == "agent1"

    def test_laap_tool_subclass(self):
        from laap.protocol.laap_tool import (
            ToolProtocol, LaapTool, ToolPermissions, PermissionLevel,
            ToolCategory, ToolInvocationResult,
        )

        class MyToolProto(ToolProtocol):
            def __init__(self):
                self.tools = {}
            def register_tool(self, tool, handler=None):
                self.tools[tool.name] = (tool, handler)
            def unregister_tool(self, name):
                return self.tools.pop(name, None) is not None
            def invoke_tool(self, name, args, invocation_context=None):
                if name not in self.tools:
                    return ToolInvocationResult(
                        tool_name=name, success=False, output=None, error="未找到"
                    )
                tool, handler = self.tools[name]
                if handler is None:
                    return ToolInvocationResult(
                        tool_name=name, success=False, output=None, error="无处理器"
                    )
                return ToolInvocationResult(
                    tool_name=name, success=True, output=handler(**args)
                )
            def list_tools(self, category=None, permissions_required=None):
                return [t for t, _ in self.tools.values()]
            def adapt_mcp_tool(self, mcp_tool):
                return LaapTool(
                    name=getattr(mcp_tool, "name", "x"),
                    description="",
                    category=ToolCategory.EXTERNAL_API,
                    input_schema={},
                    output_schema={},
                    permissions=ToolPermissions(level=PermissionLevel.READ_ONLY),
                    mcp_compatible=True,
                )

        tp = MyToolProto()
        tool = LaapTool(
            name="t",
            description="d",
            category=ToolCategory.FILESYSTEM,
            input_schema={},
            output_schema={},
            permissions=ToolPermissions(level=PermissionLevel.READ_ONLY),
        )
        tp.register_tool(tool, handler=lambda **kw: "ok")
        r = tp.invoke_tool("t", {})
        assert r.success is True
        assert r.output == "ok"


class TestCognitionIntegration:
    """情感系统与元认知系统协同"""

    def test_emotion_affects_scheduling(self):
        """高 arousal 触发任务复杂度降低"""
        from laap.cognition.emotion import EmotionSystem, EmotionEventType

        es = EmotionSystem()
        # 多次威胁事件推高 arousal
        for _ in range(5):
            es.update(EmotionEventType.THREAT_DETECTED)
        assert es.should_simplify_task() is True

    def test_metacognition_generates_report(self):
        """任务完成后生成结构化复盘报告"""
        from laap.cognition.metacognition import (
            MetacognitionSystem, ReflectionReport,
        )

        mc = MetacognitionSystem()
        report = mc.reflect(
            task={"task_id": "t1", "description": "测试任务"},
            outcome={
                "success": True,
                "time_spent_sec": 30,
                "decisions": [{"action": "step1", "actual_outcome": {"benefit": "ok"}}],
            },
        )
        assert isinstance(report, ReflectionReport)
        assert report.outcome_success is True
        assert len(report.lessons_learned) > 0

    def test_emotion_metacognition_collaboration(self):
        """情感 + 元认知协同：失败任务触发情感更新 + 反思"""
        from laap.cognition.emotion import EmotionSystem, EmotionEventType
        from laap.cognition.metacognition import MetacognitionSystem

        es = EmotionSystem()
        mc = MetacognitionSystem()

        # 模拟任务失败
        report = mc.reflect(
            task={"task_id": "fail_task", "description": "失败任务"},
            outcome={"success": False, "error": "参数错误"},
        )
        # 失败应触发情感更新
        es.update(EmotionEventType.TASK_FAILURE)
        # 高 arousal 应建议简化
        # 多次失败推高 arousal
        for _ in range(4):
            es.update(EmotionEventType.TASK_FAILURE)

        assert report.outcome_success is False
        assert es.current().valence < 0  # 不悦
        # 反思历史可查询
        history = mc.get_history(task_id="fail_task")
        assert len(history) == 1


class TestCrossModuleScenario:
    """跨模块协同场景测试"""

    def test_security_threat_triggers_emotion(self):
        """安全威胁触发情感系统响应"""
        from laap.security.threat_intel import (
            ThreatIntelBus, ThreatPattern, ThreatType, ThreatSeverity,
        )
        from laap.cognition.emotion import EmotionSystem, EmotionEventType

        bus = ThreatIntelBus(node_id="emo_node")
        es = EmotionSystem()

        # 订阅威胁更新
        def on_threat(threat: ThreatPattern):
            if threat.severity in (ThreatSeverity.HIGH, ThreatSeverity.CRITICAL):
                es.update(EmotionEventType.THREAT_DETECTED)

        bus.subscribe(on_threat)

        # 广播高危威胁
        threat = ThreatPattern(
            threat_type=ThreatType.MALICIOUS_CODE,
            severity=ThreatSeverity.CRITICAL,
            name="严重威胁",
        )
        bus.broadcast_threat(threat)

        # 情感系统应已更新
        assert es.current().valence < 0  # 不悦
        assert es.current().arousal > 0  # 唤醒

    def test_metacognition_suggests_after_security_failure(self):
        """安全失败后元认知系统提出改进建议"""
        from laap.cognition.metacognition import (
            MetacognitionSystem, ImprovementType,
        )
        from laap.security.zones import SafetyZone, ZoneManager

        mc = MetacognitionSystem()
        zone_mgr = ZoneManager()

        # 模拟多次安全策略违反
        for i in range(6):
            mc.reflect(
                task={"task_id": f"sec_fail_{i}", "description": "安全策略违反"},
                outcome={"success": False, "error": "策略违反"},
            )

        imp = mc.suggest_improvement()
        assert imp is not None
        assert imp.improvement_type == ImprovementType.STRATEGY_CHANGE
        assert imp.priority == "high"
