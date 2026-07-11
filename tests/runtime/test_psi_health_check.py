# -*- coding: utf-8 -*-
"""LAAP Runtime — PSI 心理健康检查测试（RT-006）"""

import time
from unittest.mock import MagicMock

import pytest

from laap_runtime.psi_health_check import (
    CRITICAL_AROUSAL_DURATION_SEC,
    CRITICAL_AROUSAL_THRESHOLD,
    INFO_NEED_SATISFACTION_THRESHOLD,
    NEED_UNSATISFIED_ACTIVATION,
    WARN_NEED_UNSATISFIED_SEC,
    AlertLevel,
    PsiHealthAlert,
    PsiHealthChecker,
    PsiHealthMetrics,
    PsiHealthReport,
    health_psi_handler,
)


class TestPsiHealthMetrics:
    """PsiHealthMetrics 数据类测试"""

    def test_metrics_defaults(self):
        m = PsiHealthMetrics()
        assert m.need_activation_variance == 0.0
        assert m.need_satisfaction_rate == 0.0
        assert m.emotion_stability == 0.0
        assert m.goal_progress_rate == 0.0

    def test_metrics_to_dict_rounds_to_six_decimals(self):
        m = PsiHealthMetrics(
            need_activation_variance=0.123456789,
            need_satisfaction_rate=0.5,
            emotion_stability=0.99,
            goal_progress_rate=1.0,
        )
        d = m.to_dict()
        assert d["need_activation_variance"] == 0.123457
        assert d["need_satisfaction_rate"] == 0.5
        assert d["emotion_stability"] == 0.99
        assert d["goal_progress_rate"] == 1.0


class TestAlertLevel:
    """AlertLevel 枚举测试"""

    def test_severity_ordering(self):
        assert AlertLevel.INFO.severity < AlertLevel.WARN.severity
        assert AlertLevel.WARN.severity < AlertLevel.CRITICAL.severity

    def test_str_enum_values(self):
        assert AlertLevel.INFO.value == "info"
        assert AlertLevel.WARN.value == "warn"
        assert AlertLevel.CRITICAL.value == "critical"


class TestPsiHealthReport:
    """PsiHealthReport 数据类测试"""

    def test_report_to_dict_structure(self):
        report = PsiHealthReport(
            overall_status="healthy",
            metrics=PsiHealthMetrics(),
            alerts=[],
            container_name="test-lf",
            container_state="running",
        )
        d = report.to_dict()
        assert d["overall_status"] == "healthy"
        assert d["metrics"] == PsiHealthMetrics().to_dict()
        assert d["alerts"] == []
        assert d["container_name"] == "test-lf"
        assert d["container_state"] == "running"
        assert "timestamp" in d

    def test_alert_to_dict(self):
        alert = PsiHealthAlert(
            level=AlertLevel.WARN,
            code="TEST",
            message="test message",
            details={"key": "value"},
        )
        d = alert.to_dict()
        assert d["level"] == "warn"
        assert d["code"] == "TEST"
        assert d["message"] == "test message"
        assert d["details"] == {"key": "value"}


class TestPsiHealthCheckerInitialization:
    """PsiHealthChecker 初始化测试"""

    def test_default_history_size(self):
        checker = PsiHealthChecker()
        assert checker.history_size == 100

    def test_custom_history_size(self):
        checker = PsiHealthChecker(history_size=10)
        assert checker.history_size == 10

    def test_invalid_history_size_raises(self):
        with pytest.raises(ValueError):
            PsiHealthChecker(history_size=0)
        with pytest.raises(ValueError):
            PsiHealthChecker(history_size=-1)


class TestNeedExtraction:
    """需求提取测试"""

    def test_extract_needs_via_private_method(self):
        checker = PsiHealthChecker()
        container = MagicMock()
        container._get_base_needs.return_value = {
            "certainty": 0.9,
            "competence": "0.8",
        }
        needs = checker._extract_needs(container)
        assert needs == {"certainty": 0.9, "competence": 0.8}

    def test_extract_needs_via_metrics(self):
        checker = PsiHealthChecker()
        container = MagicMock()
        container.get_metrics.return_value = {
            "psi": {"base_needs": {"exploration": 0.6}}
        }
        needs = checker._extract_needs(container)
        assert needs == {"exploration": 0.6}

    def test_extract_needs_via_attribute(self):
        checker = PsiHealthChecker()
        container = MagicMock()
        container.base_needs = {"affiliation": 0.4}
        needs = checker._extract_needs(container)
        assert needs == {"affiliation": 0.4}

    def test_extract_needs_empty_fallback(self):
        checker = PsiHealthChecker()
        container = MagicMock()
        needs = checker._extract_needs(container)
        assert needs == {}


class TestEmotionExtraction:
    """情感提取测试"""

    def test_extract_emotion_via_private_method(self):
        checker = PsiHealthChecker()
        container = MagicMock()
        container._extract_emotion_state.return_value = {
            "valence": 0.1,
            "arousal": 0.2,
            "dominance": 0.3,
        }
        emotion = checker._extract_emotion(container)
        assert emotion == {"valence": 0.1, "arousal": 0.2, "dominance": 0.3}

    def test_extract_emotion_via_metrics(self):
        checker = PsiHealthChecker()
        container = MagicMock()
        container.get_metrics.return_value = {
            "emotion": {"valence": -0.1, "arousal": 0.5}
        }
        emotion = checker._extract_emotion(container)
        assert emotion["valence"] == -0.1
        assert emotion["arousal"] == 0.5
        assert emotion["dominance"] == 0.0

    def test_extract_emotion_default(self):
        checker = PsiHealthChecker()
        container = object()  # 无任何情感相关接口的对象应返回默认值
        emotion = checker._extract_emotion(container)
        assert emotion == {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}


class TestGoalExtraction:
    """目标提取测试"""

    def test_extract_goals_via_goal_keeper(self):
        checker = PsiHealthChecker()
        container = MagicMock()
        container.goal_keeper.goals = [
            {"progress": 0.5},
            {"completion": 0.8},
        ]
        goals = checker._extract_goals(container)
        assert len(goals) == 2

    def test_extract_goals_via_attribute(self):
        checker = PsiHealthChecker()
        container = MagicMock()
        container.goals = [{"progress": 1.0}]
        goals = checker._extract_goals(container)
        assert goals == [{"progress": 1.0}]


class TestMetricComputation:
    """指标计算测试"""

    def test_compute_need_variance(self):
        checker = PsiHealthChecker()
        needs = {"a": 0.0, "b": 1.0}
        variance = checker._compute_need_variance(needs)
        assert variance == pytest.approx(0.25, rel=1e-6)

    def test_compute_need_variance_single_need(self):
        checker = PsiHealthChecker()
        assert checker._compute_need_variance({"a": 0.5}) == 0.0

    def test_compute_need_satisfaction(self):
        checker = PsiHealthChecker()
        assert checker._compute_need_satisfaction({"a": 0.0, "b": 0.0}) == 1.0
        assert checker._compute_need_satisfaction({"a": 0.5, "b": 0.5}) == 0.5
        assert checker._compute_need_satisfaction({"a": 1.0, "b": 1.0}) == 0.0

    def test_compute_emotion_stability_insufficient_samples(self):
        checker = PsiHealthChecker()
        assert checker._compute_emotion_stability() == 1.0

    def test_compute_emotion_stability_high_variance(self):
        checker = PsiHealthChecker(history_size=10)
        for i in range(10):
            checker._emotion_samples.append((time.time(), {"arousal": i / 10.0, "valence": 0.0}))
        stability = checker._compute_emotion_stability()
        assert 0.0 <= stability < 1.0

    def test_compute_goal_progress(self):
        checker = PsiHealthChecker()
        goals = [{"progress": 0.5}, {"progress": 1.0}]
        assert checker._compute_goal_progress(goals) == 0.75

    def test_compute_goal_progress_empty(self):
        checker = PsiHealthChecker()
        assert checker._compute_goal_progress([]) == 1.0


class TestBasicCheck:
    """基础 check() 流程测试"""

    def test_check_returns_healthy_for_balanced_container(self):
        checker = PsiHealthChecker()
        container = MagicMock()
        container.name = "balanced"
        container.get_state.return_value = {"state": "running"}
        container._get_base_needs.return_value = {
            "certainty": 0.2,
            "competence": 0.2,
        }
        container._extract_emotion_state.return_value = {
            "valence": 0.0,
            "arousal": 0.1,
            "dominance": 0.2,
        }
        container.goal_keeper.goals = [{"progress": 0.9}]

        report = checker.check(container)
        assert report.overall_status == "healthy"
        assert report.container_name == "balanced"
        assert report.container_state == "running"
        assert report.metrics.need_satisfaction_rate == pytest.approx(0.8, rel=1e-6)

    def test_check_history_accumulates(self):
        checker = PsiHealthChecker(history_size=5)
        container = MagicMock()
        container.get_state.return_value = {"state": "running"}
        container._get_base_needs.return_value = {"certainty": 0.1}
        container._extract_emotion_state.return_value = {"arousal": 0.0}
        container.goal_keeper.goals = []

        checker.check(container)
        checker.check(container)
        assert len(checker.get_history()) == 2

    def test_clear_history_resets(self):
        checker = PsiHealthChecker()
        container = MagicMock()
        container.get_state.return_value = {"state": "running"}
        container._get_base_needs.return_value = {"certainty": 0.1}
        container._extract_emotion_state.return_value = {"arousal": 0.0}
        container.goal_keeper.goals = []

        checker.check(container)
        checker.clear_history()
        assert len(checker.get_history()) == 0
        assert len(checker._emotion_samples) == 0
        assert len(checker._needs_samples) == 0


class TestAlertDetection:
    """告警检测测试"""

    def test_info_alert_low_need_satisfaction(self):
        checker = PsiHealthChecker()
        container = MagicMock()
        container.get_state.return_value = {"state": "running"}
        container._get_base_needs.return_value = {
            "certainty": 0.6,
            "competence": 0.5,
        }
        container._extract_emotion_state.return_value = {"arousal": 0.0}
        container.goal_keeper.goals = []

        report = checker.check(container)
        assert report.overall_status == "healthy"
        info_alerts = [a for a in report.alerts if a.level == AlertLevel.INFO]
        assert len(info_alerts) >= 1
        assert any(a.code == "NEED_SATISFACTION_LOW" for a in info_alerts)

    def test_critical_alert_very_low_need_satisfaction(self):
        checker = PsiHealthChecker()
        container = MagicMock()
        container.get_state.return_value = {"state": "running"}
        container._get_base_needs.return_value = {
            "certainty": 0.9,
            "competence": 0.95,
        }
        container._extract_emotion_state.return_value = {"arousal": 0.0}
        container.goal_keeper.goals = []

        report = checker.check(container)
        assert report.overall_status == "critical"
        assert any(a.level == AlertLevel.CRITICAL for a in report.alerts)
        assert any(a.code == "NEED_SATISFACTION_VERY_LOW" for a in report.alerts)

    def test_warn_alert_need_unsatisfied_via_last_satisfied(self):
        checker = PsiHealthChecker()
        now = time.time()
        container = MagicMock()
        container.get_state.return_value = {"state": "running"}
        container._get_base_needs.return_value = {"certainty": 0.9}
        container.need_last_satisfied_at = {"certainty": now - WARN_NEED_UNSATISFIED_SEC - 1}
        container._extract_emotion_state.return_value = {"arousal": 0.0}
        container.goal_keeper.goals = []

        report = checker.check(container)
        assert any(a.level == AlertLevel.WARN and a.code == "NEED_UNSATISFIED_LONG" for a in report.alerts)

    def test_warn_alert_need_unsatisfied_never_satisfied(self):
        checker = PsiHealthChecker(history_size=5)
        now = time.time()
        # 历史窗口中该需求持续处于未满足状态
        for i in range(5):
            checker._needs_samples.append(
                (now - WARN_NEED_UNSATISFIED_SEC - 10 + i, {"certainty": 0.9})
            )
        container = MagicMock()
        container.get_state.return_value = {"state": "running"}
        container._get_base_needs.return_value = {"certainty": 0.9}
        container.need_last_satisfied_at = {}
        container._extract_emotion_state.return_value = {"arousal": 0.0}
        container.goal_keeper.goals = []

        report = checker.check(container)
        assert any(a.level == AlertLevel.WARN and a.code == "NEED_UNSATISFIED_LONG" for a in report.alerts)

    def test_critical_alert_persistent_high_arousal(self):
        checker = PsiHealthChecker(history_size=10)
        now = time.time()
        # 模拟 arousal 持续过高超过阈值时长
        for i in range(5):
            checker._emotion_samples.append(
                (now - CRITICAL_AROUSAL_DURATION_SEC - 10 + i, {"arousal": 0.9})
            )
        # 当前样本也保持高 arousal
        container = MagicMock()
        container.get_state.return_value = {"state": "running"}
        container._get_base_needs.return_value = {"certainty": 0.1}
        container._extract_emotion_state.return_value = {"arousal": 0.9}
        container.goal_keeper.goals = []

        report = checker.check(container)
        assert report.overall_status == "critical"
        assert any(a.level == AlertLevel.CRITICAL and a.code == "AROUSAL_PERSISTENT_HIGH" for a in report.alerts)

    def test_no_critical_arousal_if_not_persistent(self):
        checker = PsiHealthChecker(history_size=10)
        container = MagicMock()
        container.get_state.return_value = {"state": "running"}
        container._get_base_needs.return_value = {"certainty": 0.1}
        container._extract_emotion_state.return_value = {"arousal": 0.9}
        container.goal_keeper.goals = []

        report = checker.check(container)
        assert not any(a.code == "AROUSAL_PERSISTENT_HIGH" for a in report.alerts)

    def test_warn_alert_goal_stagnation(self):
        checker = PsiHealthChecker(history_size=5)
        # 构造历史：前两次进展率都低于阈值
        for _ in range(2):
            checker._history.append(
                PsiHealthReport(
                    overall_status="healthy",
                    metrics=PsiHealthMetrics(goal_progress_rate=0.01),
                )
            )
        container = MagicMock()
        container.get_state.return_value = {"state": "running"}
        container._get_base_needs.return_value = {"certainty": 0.1}
        container._extract_emotion_state.return_value = {"arousal": 0.0}
        container.goal_keeper.goals = [{"progress": 0.01}]

        report = checker.check(container)
        assert any(a.level == AlertLevel.WARN and a.code == "GOAL_STAGNATION" for a in report.alerts)


class TestResponseStrategy:
    """告警响应策略测试"""

    def test_response_strategy_text(self):
        assert "继续运行" in PsiHealthChecker.get_response_strategy(AlertLevel.INFO)
        assert "运维关注" in PsiHealthChecker.get_response_strategy(AlertLevel.WARN)
        assert "人工介入" in PsiHealthChecker.get_response_strategy(AlertLevel.CRITICAL)


class TestHttpHandler:
    """HTTP 端点处理器测试"""

    def test_health_psi_handler_returns_dict(self):
        container = MagicMock()
        container.name = "handler-test"
        container.get_state.return_value = {"state": "running"}
        container._get_base_needs.return_value = {"certainty": 0.1}
        container._extract_emotion_state.return_value = {"arousal": 0.0}
        container.goal_keeper.goals = []

        result = health_psi_handler(container)
        assert isinstance(result, dict)
        assert result["overall_status"] == "healthy"
        assert result["container_name"] == "handler-test"
        assert "metrics" in result
        assert "alerts" in result


class TestMockFriendly:
    """Mock 友好性测试"""

    def test_check_works_with_plain_magic_mock_defaults(self):
        checker = PsiHealthChecker()
        container = MagicMock()
        container.get_state.return_value = {"state": "unknown"}
        container._get_base_needs.return_value = {}
        container._extract_emotion_state.return_value = {"arousal": 0.0}
        container.goal_keeper.goals = []
        report = checker.check(container)
        assert report.overall_status in ("healthy", "degraded", "critical")
        assert report.container_state == "unknown"

    def test_check_with_lifeform_container_like_stub(self):
        class StubContainer:
            name = "stub"

            def get_state(self):
                return {"state": "running"}

            def get_metrics(self):
                return {
                    "psi": {"base_needs": {"certainty": 0.1}},
                    "emotion": {"valence": 0.0, "arousal": 0.0, "dominance": 0.0},
                }

            @property
            def goal_keeper(self):
                class GK:
                    goals = [{"progress": 0.8}]
                return GK()

        checker = PsiHealthChecker()
        report = checker.check(StubContainer())
        assert report.overall_status == "healthy"
        assert report.metrics.need_satisfaction_rate == pytest.approx(0.9, rel=1e-6)
