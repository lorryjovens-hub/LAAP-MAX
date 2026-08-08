# -*- coding: utf-8 -*-
"""RT-004 生命体间社交协议 / Hive 测试

覆盖：
- LifeformRole 枚举与角色权力顺序（RT-004.1）
- Hive 组建/解散与成员管理（RT-004.2）
- 信任机制：成功/失败更新、边界 clamp、每日衰减（RT-004.3）
- 权力关系：角色 base_power、业绩加成、leader、决策采纳（RT-004.4）
- cooperation 关系：可协作判定、协作执行、历史记录（RT-004.5）
- LAAP-COOP 集成：assign_task / share_fact / negotiate / query（RT-004.6）
- PSI 兼容性调度：高 arousal 退避、兼容伙伴推荐（RT-004.7）
- mock-friendly：使用 MagicMock 替代真实容器
"""
import time
from unittest.mock import MagicMock

import pytest

from laap.protocol.laap_coop import FactScope, NegotiationOutcome, SharedFact
from laap_runtime.social_protocol import (
    DEFAULT_TRUST,
    HIGH_AROUSAL_THRESHOLD,
    Hive,
    LifeformRole,
    SocialProtocol,
    _CooperationRecord,
)


def _make_mock_member(arousal: float = 0.0):
    """构造一个带 emotion 指标的 mock 成员"""
    member = MagicMock()
    member.get_metrics.return_value = {"emotion": {"arousal": arousal}}
    return member


def _make_hive_with_five_members() -> Hive:
    """构造包含 5 个标准角色的蜂巢"""
    hive = Hive(hive_id="test-hive")
    roles = [
        ("arch-1", LifeformRole.ARCHITECT),
        ("ops-1", LifeformRole.OPS),
        ("backend-1", LifeformRole.BACKEND),
        ("frontend-1", LifeformRole.FRONTEND),
        ("tester-1", LifeformRole.TESTER),
    ]
    for mid, role in roles:
        hive.join(mid, _make_mock_member(arousal=0.0), role, name=mid)
    return hive


# ═══════════════════════════════════════════════════════════════
# RT-004.1 LifeformRole 枚举
# ═══════════════════════════════════════════════════════════════

class TestLifeformRoleEnum:
    """角色枚举测试"""

    def test_role_values_are_strings(self):
        """角色枚举应继承 str，便于 JSON 序列化"""
        assert isinstance(LifeformRole.BACKEND, str)
        assert LifeformRole.BACKEND.value == "backend"

    def test_five_roles_defined(self):
        """应定义 5 种角色"""
        roles = list(LifeformRole)
        assert len(roles) == 5
        assert LifeformRole.FRONTEND in roles
        assert LifeformRole.BACKEND in roles
        assert LifeformRole.ARCHITECT in roles
        assert LifeformRole.TESTER in roles
        assert LifeformRole.OPS in roles

    def test_role_power_order(self):
        """角色默认权力满足 ARCHITECT > OPS > BACKEND > FRONTEND > TESTER"""
        assert LifeformRole.ARCHITECT.base_power > LifeformRole.OPS.base_power
        assert LifeformRole.OPS.base_power > LifeformRole.BACKEND.base_power
        assert LifeformRole.BACKEND.base_power > LifeformRole.FRONTEND.base_power
        assert LifeformRole.FRONTEND.base_power > LifeformRole.TESTER.base_power


# ═══════════════════════════════════════════════════════════════
# RT-004.2 Hive 组建/解散
# ═══════════════════════════════════════════════════════════════

class TestHiveLifecycle:
    """蜂巢生命周期测试"""

    def test_hive_initially_empty(self):
        """新建蜂巢为空"""
        hive = Hive()
        assert hive.member_count == 0
        assert hive.list_members() == []

    def test_join_increases_member_count(self):
        """加入成员后数量增加"""
        hive = Hive()
        hive.join("m1", MagicMock(), LifeformRole.BACKEND)
        assert hive.member_count == 1
        assert hive.get_member("m1").role == LifeformRole.BACKEND

    def test_list_members_returns_summary(self):
        """list_members 返回包含角色与权力的摘要"""
        hive = Hive()
        hive.join("m1", MagicMock(), LifeformRole.ARCHITECT)
        members = hive.list_members()
        assert len(members) == 1
        assert members[0]["member_id"] == "m1"
        assert members[0]["role"] == "architect"
        assert members[0]["power"] == LifeformRole.ARCHITECT.base_power

    def test_leave_removes_member(self):
        """成员离开后被移除"""
        hive = Hive()
        hive.join("m1", MagicMock(), LifeformRole.BACKEND)
        assert hive.leave("m1") is True
        assert hive.member_count == 0
        assert hive.leave("m1") is False

    def test_dissolve_clears_all_members(self):
        """解散蜂巢后成员清空"""
        hive = _make_hive_with_five_members()
        assert hive.member_count == 5
        hive.dissolve()
        assert hive.member_count == 0


# ═══════════════════════════════════════════════════════════════
# RT-004.3 信任机制
# ═══════════════════════════════════════════════════════════════

class TestTrustMechanism:
    """信任机制测试"""

    def test_default_trust_between_strangers(self):
        """未交互成员间默认信任值为 DEFAULT_TRUST"""
        hive = _make_hive_with_five_members()
        assert hive.get_trust("backend-1", "frontend-1") == DEFAULT_TRUST

    def test_successful_interaction_increases_trust(self):
        """成功协作使信任值 +0.1"""
        hive = _make_hive_with_five_members()
        initial = hive.get_trust("backend-1", "frontend-1")
        new_value = hive.record_interaction("backend-1", "frontend-1", success=True)
        assert new_value == pytest.approx(initial + 0.1)

    def test_failed_interaction_decreases_trust(self):
        """失败协作使信任值 -0.2"""
        hive = _make_hive_with_five_members()
        initial = hive.get_trust("backend-1", "frontend-1")
        new_value = hive.record_interaction("backend-1", "frontend-1", success=False)
        assert new_value == pytest.approx(initial - 0.2)

    def test_trust_clamped_to_zero_and_one(self):
        """信任值被限制在 [0, 1]"""
        hive = _make_hive_with_five_members()
        # 连续失败使信任降到 0
        for _ in range(10):
            hive.record_interaction("backend-1", "frontend-1", success=False)
        assert hive.get_trust("backend-1", "frontend-1") == 0.0
        # 连续成功使信任升到 1
        for _ in range(20):
            hive.record_interaction("backend-1", "frontend-1", success=True)
        assert hive.get_trust("backend-1", "frontend-1") == 1.0

    def test_trust_decay_per_day(self):
        """每完整一天无交互信任衰减 0.01"""
        hive = _make_hive_with_five_members()
        # 先建立信任记录
        hive.record_interaction("backend-1", "frontend-1", success=True)
        initial = hive.get_trust("backend-1", "frontend-1")
        # 模拟 3 天后衰减
        now = time.time() + 3 * 86400 + 1
        changed = hive.decay_trust(now=now)
        assert "backend-1->frontend-1" in changed
        assert hive.get_trust("backend-1", "frontend-1") == pytest.approx(
            initial - 3 * 0.01
        )

    def test_self_trust_is_one(self):
        """自身信任值为 1"""
        hive = _make_hive_with_five_members()
        assert hive.get_trust("backend-1", "backend-1") == 1.0


# ═══════════════════════════════════════════════════════════════
# RT-004.4 权力关系
# ═══════════════════════════════════════════════════════════════

class TestPowerHierarchy:
    """权力层次测试"""

    def test_role_base_power(self):
        """各角色权力等于 base_power"""
        hive = _make_hive_with_five_members()
        assert hive.get_power("arch-1") == LifeformRole.ARCHITECT.base_power
        assert hive.get_power("ops-1") == LifeformRole.OPS.base_power
        assert hive.get_power("tester-1") == LifeformRole.TESTER.base_power

    def test_performance_contribution_increases_power(self):
        """业绩贡献提升权力值"""
        hive = _make_hive_with_five_members()
        base = hive.get_power("backend-1")
        hive.record_performance("backend-1", 0.15)
        assert hive.get_power("backend-1") == pytest.approx(base + 0.15)

    def test_power_is_capped_at_one(self):
        """权力值上限为 1"""
        hive = _make_hive_with_five_members()
        hive.record_performance("arch-1", 0.5)
        assert hive.get_power("arch-1") == 1.0

    def test_leader_is_highest_power(self):
        """leader 为权力最高的成员"""
        hive = _make_hive_with_five_members()
        leader = hive.get_leader()
        assert leader.member_id == "arch-1"

    def test_leader_considers_performance(self):
        """业绩贡献可改变 leader"""
        hive = _make_hive_with_five_members()
        # 给 ops 大量业绩，使其权力超过 architect
        hive.record_performance("ops-1", 0.3)
        assert hive.get_leader().member_id == "ops-1"

    def test_high_power_decision_adopted_by_lower(self):
        """高权力者决策被低权力者采纳"""
        hive = _make_hive_with_five_members()
        assert hive.adopt_decision("arch-1", "backend-1") is True
        assert hive.adopt_decision("backend-1", "arch-1") is False


# ═══════════════════════════════════════════════════════════════
# RT-004.5 cooperation 关系
# ═══════════════════════════════════════════════════════════════

class TestCooperationRelation:
    """协作关系测试"""

    def test_can_cooperate_with_default_trust(self):
        """默认信任下低 arousal 成员可协作"""
        hive = _make_hive_with_five_members()
        assert hive.can_cooperate("backend-1", "frontend-1") is True

    def test_cannot_cooperate_when_trust_too_low(self):
        """信任低于阈值时不可协作"""
        hive = _make_hive_with_five_members()
        # 将双向信任降到阈值以下
        for _ in range(5):
            hive.record_interaction("backend-1", "frontend-1", success=False)
            hive.record_interaction("frontend-1", "backend-1", success=False)
        assert hive.can_cooperate("backend-1", "frontend-1") is False

    def test_cooperate_success_records_history(self):
        """协作成功会记录历史并提升信任"""
        hive = _make_hive_with_five_members()
        task = {"task_id": "t1", "description": "feat"}
        success, record = hive.cooperate("backend-1", "frontend-1", task=task)
        assert success is True
        assert isinstance(record, _CooperationRecord)
        assert record.task_id == "t1"
        history = hive.social_protocol.get_cooperation_history("backend-1")
        assert len(history) == 1

    def test_cooperate_failure_when_not_compatible(self):
        """不可协作时返回失败记录"""
        hive = _make_hive_with_five_members()
        # 让一方高 arousal 导致 PSI 不兼容
        hive._members["frontend-1"].member.get_metrics.return_value = {
            "emotion": {"arousal": 0.9}
        }
        success, record = hive.cooperate("backend-1", "frontend-1")
        assert success is False
        assert record.success is False


# ═══════════════════════════════════════════════════════════════
# RT-004.6 LAAP-COOP 集成
# ═══════════════════════════════════════════════════════════════

class TestLAAPCOOPIntegration:
    """LAAP-COOP 协议集成测试"""

    def test_assign_task_creates_assignment(self):
        """assign_task 返回 TaskAssignment 并记录"""
        hive = _make_hive_with_five_members()
        task = {
            "task_id": "task-1",
            "description": "实现 API",
            "required_capabilities": ["python"],
            "priority": "high",
        }
        assignment = hive.assign_task(task, assignee_id="backend-1")
        assert assignment.assignee_id == "backend-1"
        assert assignment.task_id == "task-1"
        assert assignment.assigner_id == "arch-1"  # 默认 leader 分配
        assert assignment.status.value == "assigned"

    def test_assign_task_with_custom_assigner(self):
        """可指定分配者"""
        hive = _make_hive_with_five_members()
        task = {"task_id": "task-2", "description": "测试"}
        assignment = hive.assign_task(
            task, assignee_id="tester-1", assigner_id="ops-1"
        )
        assert assignment.assigner_id == "ops-1"

    def test_share_fact_string_and_query(self):
        """share_fact 支持字符串事实并可通过 query 查询"""
        hive = _make_hive_with_five_members()
        fact = hive.share_fact(
            "数据库连接池大小为 20", scope=FactScope.TEAM, source_id="ops-1"
        )
        assert isinstance(fact, SharedFact)
        assert fact.content == "数据库连接池大小为 20"
        assert fact.scope == FactScope.TEAM
        assert fact.source_id == "ops-1"
        results = hive.query_shared_facts(source_id="ops-1")
        assert len(results) == 1

    def test_query_shared_facts_by_tags(self):
        """可通过标签过滤共享事实"""
        hive = _make_hive_with_five_members()
        fact = SharedFact(
            fact_id="f-1",
            content="缓存策略",
            scope=FactScope.TEAM,
            source_id="arch-1",
            tags=["performance"],
        )
        hive.share_fact(fact)
        hive.share_fact("无关事实", scope=FactScope.PRIVATE)
        results = hive.query_shared_facts(tags=["performance"])
        assert len(results) == 1
        assert results[0].fact_id == "f-1"

    def test_get_assignments_filter_by_assignee(self):
        """可按被分配者查询任务"""
        hive = _make_hive_with_five_members()
        hive.assign_task({"task_id": "t1"}, assignee_id="backend-1")
        hive.assign_task({"task_id": "t2"}, assignee_id="frontend-1")
        assert len(hive.get_assignments()) == 2
        assert len(hive.get_assignments(assignee_id="backend-1")) == 1

    def test_negotiate_accepted_by_higher_power(self):
        """高权力者向低权力者提议且信任足够时被接受"""
        hive = _make_hive_with_five_members()
        result = hive.negotiate(
            {"action": "重构接口"},
            proposer_id="arch-1",
            responder_id="backend-1",
        )
        assert result.outcome == NegotiationOutcome.ACCEPTED
        assert result.agreed_terms == {"action": "重构接口"}

    def test_negotiate_rejected_when_trust_too_low(self):
        """信任过低时协商被拒绝"""
        hive = _make_hive_with_five_members()
        # 让信任降到 0 以下
        for _ in range(5):
            hive.record_interaction("backend-1", "arch-1", success=False)
            hive.record_interaction("arch-1", "backend-1", success=False)
        result = hive.negotiate(
            {"action": "发布"},
            proposer_id="backend-1",
            responder_id="arch-1",
        )
        assert result.outcome == NegotiationOutcome.REJECTED

    def test_negotiate_countered_when_lower_power(self):
        """低权力者向高权力者提议通常被反报价"""
        hive = _make_hive_with_five_members()
        result = hive.negotiate(
            {"action": "跳过代码审查"},
            proposer_id="frontend-1",
            responder_id="arch-1",
        )
        assert result.outcome == NegotiationOutcome.COUNTERED
        assert result.counter_proposal is not None


# ═══════════════════════════════════════════════════════════════
# RT-004.7 PSI 兼容性调度
# ═══════════════════════════════════════════════════════════════

class TestPSICompatibility:
    """PSI 兼容性测试"""

    def test_psi_compatible_when_low_arousal(self):
        """低 arousal 成员 PSI 兼容"""
        hive = _make_hive_with_five_members()
        assert hive.psi_compatibility("backend-1", "frontend-1") is True

    def test_high_arousal_triggers_backoff(self):
        """任一成员 arousal > 0.7 时不兼容"""
        hive = _make_hive_with_five_members()
        hive._members["backend-1"].member.get_metrics.return_value = {
            "emotion": {"arousal": HIGH_AROUSAL_THRESHOLD + 0.1}
        }
        assert hive.psi_compatibility("backend-1", "frontend-1") is False

    def test_high_arousal_blocks_cooperation(self):
        """高 arousal 阻止直接协作"""
        hive = _make_hive_with_five_members()
        hive._members["backend-1"].member.get_metrics.return_value = {
            "emotion": {"arousal": 0.85}
        }
        assert hive.can_cooperate("backend-1", "frontend-1") is False

    def test_find_compatible_partners_excludes_high_arousal(self):
        """find_compatible_partners 排除高 arousal 成员"""
        hive = _make_hive_with_five_members()
        hive._members["frontend-1"].member.get_metrics.return_value = {
            "emotion": {"arousal": 0.85}
        }
        partners = hive.social_protocol.find_compatible_partners("backend-1")
        partner_ids = [p[0] for p in partners]
        assert "frontend-1" not in partner_ids
        assert "arch-1" in partner_ids

    def test_negotiate_deferred_when_high_arousal(self):
        """高 arousal 成员间协商被延后"""
        hive = _make_hive_with_five_members()
        hive._members["backend-1"].member.get_metrics.return_value = {
            "emotion": {"arousal": 0.85}
        }
        result = hive.negotiate(
            {"action": "联调"},
            proposer_id="backend-1",
            responder_id="frontend-1",
        )
        assert result.outcome == NegotiationOutcome.DEFERRED


# ═══════════════════════════════════════════════════════════════
# mock-friendly 与真实 MindLayer 集成
# ═══════════════════════════════════════════════════════════════

class TestMockFriendly:
    """mock 友好性测试"""

    def test_hive_works_with_magic_mock_members(self):
        """Hive 可直接使用 MagicMock 成员"""
        hive = Hive()
        for mid, role in [
            ("a", LifeformRole.ARCHITECT),
            ("b", LifeformRole.BACKEND),
        ]:
            hive.join(mid, MagicMock(), role)
        assert hive.member_count == 2
        assert hive.can_cooperate("a", "b") is True

    def test_extract_arousal_from_mind_layer(self):
        """可从真实 MindLayer 提取 arousal"""
        from laap_runtime.mind_layer import MindLayer

        mind = MindLayer("aris", role="architect")
        mind.update_emotion(arousal=0.75)
        hive = Hive()
        hive.join("aris", mind, LifeformRole.ARCHITECT)
        assert hive.social_protocol.get_arousal("aris") == pytest.approx(0.75)
        assert hive.psi_compatibility("aris", "aris") is False
