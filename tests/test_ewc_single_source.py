"""
单元测试: EWC 单一权威来源 (Single Source of Truth) 收敛验证

验证:
  1. 权威实现 `laap.cognition.ewc.ElasticWeightConsolidation` 可导入
  2. `laap.cognition.evolution` 仅 re-export 同一类对象 (E1 is E2)
  3. `laap.cognition` 包级导出亦指向同一类
  4. 权威实现可实例化且核心 EWC 功能正常工作
     (before_learning / compute_fisher / ewc_penalty / after_learning / status)
"""
import sys
import os

# 确保项目根目录在 sys.path（与 conftest/test_fitness 一致）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


# ═══════════════════════════════════════════════════════════════
# 单一来源收敛 — 导入与对象同一性
# ═══════════════════════════════════════════════════════════════

class TestEWCSingleSource:
    def test_import_from_ewc_module(self):
        """权威模块 laap.cognition.ewc 可成功导入 ElasticWeightConsolidation"""
        from laap.cognition.ewc import ElasticWeightConsolidation
        assert ElasticWeightConsolidation is not None
        assert callable(ElasticWeightConsolidation)

    def test_evolution_reexport_is_same_class(self):
        """evolution.py 必须 re-export 同一类对象（不是子类/副本）"""
        from laap.cognition.ewc import ElasticWeightConsolidation as E1
        from laap.cognition.evolution import ElasticWeightConsolidation as E2
        assert E1 is E2, "evolution.py 必须 re-export ewc.ElasticWeightConsolidation（同一对象）"

    def test_cognition_package_reexport_is_same_class(self):
        """laap.cognition 包级导出亦指向同一权威类"""
        from laap.cognition.ewc import ElasticWeightConsolidation as E1
        from laap.cognition import ElasticWeightConsolidation as E2
        assert E1 is E2

    def test_class_name_preserved(self):
        """类名保持为 ElasticWeightConsolidation（向后兼容）"""
        from laap.cognition.ewc import ElasticWeightConsolidation
        assert ElasticWeightConsolidation.__name__ == "ElasticWeightConsolidation"
        assert "ElasticWeightConsolidation" in ElasticWeightConsolidation.__qualname__


# ═══════════════════════════════════════════════════════════════
# 测试用桩对象 — 模拟 brain / unity / cortex / skill
# ═══════════════════════════════════════════════════════════════

class _StrProf(str):
    """str 子类，附带 .value 属性以模拟 SkillProficiency 枚举。

    作为 str 子类，在 compute_fisher 的字典查找中可与普通字符串键匹配；
    同时 .value 满足 before_learning 中 skill.proficiency.value 的访问。
    """

    @property
    def value(self) -> str:
        return str(self)


class _StubSkill:
    """模拟 EmbodiedSkill 的最小桩对象。"""

    def __init__(self, name: str, use_count: int = 5,
                 success_count: int = 4, avg_quality: float = 0.8,
                 proficiency: str = "expert"):
        self.name = name
        self.use_count = use_count
        self.success_count = success_count
        self.avg_quality = avg_quality
        self.proficiency = _StrProf(proficiency)

    @property
    def success_rate(self) -> float:
        return self.success_count / max(1, self.use_count)


class _StubUnity:
    """模拟 UnityEngine：仅需要 .skills 字典。"""

    def __init__(self, skills=None):
        self.skills = skills if skills is not None else {}


class _StubBrain:
    pass


class _StubCortex:
    pass


# ═══════════════════════════════════════════════════════════════
# 权威实现功能验证
# ═══════════════════════════════════════════════════════════════

class TestEWCFunctionality:
    @pytest.fixture
    def ewc(self):
        """构造一个带 2 个技能的 EWC 实例。"""
        from laap.cognition.ewc import ElasticWeightConsolidation
        skills = {
            "搜索": _StubSkill("搜索", use_count=10, success_count=9,
                              avg_quality=0.9, proficiency="expert"),
            "调试": _StubSkill("调试", use_count=2, success_count=1,
                              avg_quality=0.3, proficiency="novice"),
        }
        unity = _StubUnity(skills=skills)
        return ElasticWeightConsolidation(
            brain=_StubBrain(), unity=unity, cortex=_StubCortex(),
            lambda_ewc=0.5,
        )

    def test_instantiation(self, ewc):
        """权威实现可实例化，初始字段正确"""
        assert ewc.lambda_ewc == 0.5
        assert ewc.fisher_matrix == {}
        assert ewc.old_params == {}
        assert ewc.task_count == 0
        assert ewc.brain is not None
        assert ewc.unity is not None
        assert ewc.cortex is not None

    def test_before_learning_snapshots_params(self, ewc):
        """before_learning 保存参数快照并递增 task_count"""
        ewc.before_learning()
        assert ewc.task_count == 1
        assert set(ewc.old_params.keys()) == {"搜索", "调试"}
        snap = ewc.old_params["搜索"]
        assert snap["proficiency"] == "expert"
        assert snap["avg_quality"] == 0.9
        assert snap["success_rate"] == pytest.approx(0.9)

    def test_compute_fisher_populates_matrix(self, ewc):
        """compute_fisher 为每个技能计算重要性并填入 fisher_matrix"""
        ewc.task_count = 10  # 避免除零
        ewc.compute_fisher()
        assert set(ewc.fisher_matrix.keys()) == {"搜索", "调试"}
        # expert → proficiency_weight=0.8；success_rate=0.9；freq=10/10=1.0
        # importance = 1.0*0.3 + 0.9*0.3 + 0.8*0.4 = 0.3+0.27+0.32 = 0.89
        assert ewc.fisher_matrix["搜索"] == pytest.approx(0.89, abs=1e-6)
        # novice → 0.3；success_rate=0.5；freq=2/10=0.2
        # importance = 0.2*0.3 + 0.5*0.3 + 0.3*0.4 = 0.06+0.15+0.12 = 0.33
        assert ewc.fisher_matrix["调试"] == pytest.approx(0.33, abs=1e-6)
        # _importances 同步更新
        assert ewc._importances["搜索"] == ewc.fisher_matrix["搜索"]

    def test_compute_fisher_no_skills_is_noop(self):
        """unity 无 skills 属性时 compute_fisher 安全返回"""
        from laap.cognition.ewc import ElasticWeightConsolidation

        class _NoSkillsUnity:
            pass

        ewc = ElasticWeightConsolidation(
            brain=_StubBrain(), unity=_NoSkillsUnity(), cortex=_StubCortex(),
        )
        ewc.compute_fisher()  # 不应抛异常
        assert ewc.fisher_matrix == {}

    def test_ewc_penalty_empty_old_params_returns_zero(self, ewc):
        """无历史快照时 penalty 为 0"""
        assert ewc.old_params == {}
        assert ewc.ewc_penalty({"搜索": {"avg_quality": 0.5}}) == 0.0

    def test_ewc_penalty_nonzero_after_snapshot(self, ewc):
        """before_learning + compute_fisher 后，参数偏移产生正惩罚"""
        ewc.task_count = 10
        ewc.before_learning()
        ewc.compute_fisher()
        # 新参数与快照不同 → penalty > 0
        new_params = {
            "搜索": {"avg_quality": 0.5, "proficiency": "expert", "success_rate": 0.9},
            "调试": {"avg_quality": 0.1, "proficiency": "novice", "success_rate": 0.5},
        }
        penalty = ewc.ewc_penalty(new_params)
        assert penalty > 0.0
        # penalty = λ * Σ F_i * Σ (Δ)²；λ=0.5
        assert penalty == pytest.approx(0.5 * ewc.fisher_matrix["搜索"] * (
            (0.5 - 0.9) ** 2 + (0.9 - 0.9) ** 2 + (0.9 - 0.9) ** 2
        ) + 0.5 * ewc.fisher_matrix["调试"] * (
            (0.1 - 0.3) ** 2 + (0.5 - 0.5) ** 2 + (0.5 - 0.5) ** 2
        ), abs=1e-6)

    def test_after_learning_returns_constrained_and_penalty(self, ewc):
        """after_learning 完整流程：返回 constrained_params 与 penalty"""
        new_params = {
            "搜索": {"avg_quality": 0.95, "proficiency": "expert", "success_rate": 0.9},
            "调试": {"avg_quality": 0.4, "proficiency": "novice", "success_rate": 0.5},
        }
        result = ewc.after_learning(new_params)
        assert isinstance(result, dict)
        assert "constrained_params" in result
        assert "penalty" in result
        assert set(result["constrained_params"].keys()) == {"搜索", "调试"}
        assert result["penalty"] >= 0.0
        # task_count 经 before_learning 递增
        assert ewc.task_count >= 1

    def test_after_learning_constrains_important_params(self):
        """重要参数 (fisher>0.7) 被强约束：新值≈90%旧 + 10%新"""
        from laap.cognition.ewc import ElasticWeightConsolidation
        # 构造一个 fisher 必然 > 0.7 的技能：master + 高频 + 高成功率
        skills = {
            "核心": _StubSkill("核心", use_count=100, success_count=100,
                              avg_quality=0.9, proficiency="master"),
        }
        ewc = ElasticWeightConsolidation(
            brain=_StubBrain(), unity=_StubUnity(skills=skills),
            cortex=_StubCortex(), lambda_ewc=0.5,
        )
        ewc.task_count = 100
        ewc.before_learning()
        ewc.compute_fisher()
        assert ewc.fisher_matrix["核心"] > 0.7  # 确实是重要参数
        new_params = {"核心": {"avg_quality": 0.2, "proficiency": "master",
                              "success_rate": 1.0}}
        result = ewc.after_learning(new_params)
        # 重要参数：old*0.9 + new*0.1 = 0.9*0.9 + 0.2*0.1 = 0.81+0.02 = 0.83
        assert result["constrained_params"]["核心"] == pytest.approx(0.83, abs=1e-6)

    def test_status_shape(self, ewc):
        """status 返回包含约定键的字典"""
        s = ewc.status()
        assert "task_count" in s
        assert "lambda" in s
        assert "fisher_params" in s
        assert "important_params" in s
        assert s["lambda"] == 0.5
        assert s["fisher_params"] == 0  # 尚未 compute_fisher

    def test_to_float_handles_types(self, ewc):
        """_to_float 正确处理 int/float/str/其它"""
        assert ewc._to_float(3) == 3.0
        assert ewc._to_float(2.5) == 2.5
        assert ewc._to_float("hello") == 0.5  # len=5 / 10.0
        assert ewc._to_float(None) == 0.0
        assert ewc._to_float([1, 2, 3]) == 0.0


# ═══════════════════════════════════════════════════════════════
# laap_brain 简化版与权威类的关系（不破坏现有功能）
# ═══════════════════════════════════════════════════════════════

class TestLaapBrainEWCCoexistence:
    def test_laap_brain_still_imports(self):
        """laap_brain 仍可导入（自包含降级或引用权威类）"""
        import laap_brain  # noqa: F401
        assert hasattr(laap_brain, "LaapBrain")

    def test_laap_brain_ewc_methods_intact(self):
        """LaapBrain 内联简化 EWC 方法仍存在且可调用"""
        from laap_brain import LaapBrain
        for meth in ("_ewc_before_learning", "_ewc_compute_fisher"):
            assert hasattr(LaapBrain, meth), f"LaapBrain 缺少 {meth}"

    def test_laap_brain_native_ewc_ref_when_available(self):
        """当原生 LAAP 可用时，LaapBrain 持有权威类引用"""
        import laap_brain
        # _NativeEWC 要么是权威类，要么为 None（降级模式）
        assert laap_brain._NativeEWC is None or callable(laap_brain._NativeEWC)
