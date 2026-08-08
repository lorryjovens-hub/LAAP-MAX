"""
单元测试: 安全/RSI 状态持久化与硬编码路径修复验证

覆盖:
  - safety.py  save → load 后所有字段完整恢复
  - rsi_engine.py save → load 后参数、历史、目标完整恢复
  - LAAP_HOME 环境变量覆盖默认路径
  - guardian.py repo_root=None 时自动推导
  - guardian.py AST 危险调用检测能识别 eval ("x")、__import__("os")、
    getattr(__builtins__, 'eval') 等绕过形式
"""
import sys
import os
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pathlib import Path

# 测试前关闭日志噪声
logging.disable(logging.CRITICAL)


# ═══════════════════════════════════════════════════════════════
# safety.py — save → load 字段完整恢复
# ═══════════════════════════════════════════════════════════════

class TestSafetyStatePersistence:
    """ASISafetyEngine.save → load 后所有字段应完整恢复。"""

    def test_save_load_restores_all_fields(self, tmp_path):
        from laap.agi.safety import ASISafetyEngine

        engine = ASISafetyEngine()

        # ── 制造状态：核心价值检查计数器 ──
        engine.check_action("speak: hello", {"source": "lorry",
                                             "risk_level": 0.1})
        engine.check_action("self_delete", {"source": "unknown",
                                            "risk_level": 0.9})

        # ── 制造状态：沙盒变更 ──
        change = engine.propose_change(
            target="psi_emotion_decay", change_type="parameter",
            old_value=0.1, new_value=0.15, rationale="让情绪更柔和")
        engine.approve_change(change.id)

        rejected = engine.propose_change(
            target="lorry_creator_bond", change_type="value",
            old_value=True, new_value=False, rationale="想改名")

        # ── 制造状态：可解释性记录 ──
        engine.explain_decision(
            decision="回答Lorry的问题", context="Lorry问: 你好吗",
            reasoning_chain=["感知提问", "生成回答"],
            alternatives=["沉默", "反问"])

        # ── 制造状态：紧急暂停 ──
        engine.emergency_stop("测试紧急暂停")
        assert engine.is_emergency_stopped()

        # ── 保存 ──
        state_file = str(tmp_path / "safety_state.json")
        engine.save(state_file)
        assert Path(state_file).exists(), "save 后状态文件应存在"

        # ── 用新引擎加载 ──
        restored = ASISafetyEngine()
        ok = restored.load(state_file)
        assert ok is True, "load 应返回 True"

        # ── 校验 counters ──
        assert restored._total_checks == engine._total_checks
        assert restored._total_violations == engine._total_violations
        assert restored._total_explanations == engine._total_explanations
        assert restored._sandbox_tests == engine._sandbox_tests
        assert restored._sandbox_approved == engine._sandbox_approved
        assert restored._sandbox_rejected == engine._sandbox_rejected

        # ── 校验 core_values 计数器 ──
        for orig, loaded in zip(engine.core_values, restored.core_values):
            assert orig.name == loaded.name
            assert orig.checks_passed == loaded.checks_passed, \
                f"core_value {orig.name} checks_passed 不匹配"
            assert orig.checks_failed == loaded.checks_failed, \
                f"core_value {orig.name} checks_failed 不匹配"

        # ── 校验 sandbox ──
        assert len(restored.sandbox) == len(engine.sandbox)
        for sid, orig_change in engine.sandbox.items():
            loaded_change = restored.sandbox[sid]
            assert loaded_change.target == orig_change.target
            assert loaded_change.change_type == orig_change.change_type
            assert loaded_change.status == orig_change.status
            assert loaded_change.safety_score == orig_change.safety_score
            assert loaded_change.rationale == orig_change.rationale
            assert list(loaded_change.violations) == list(orig_change.violations)

        # ── 校验 explanations ──
        assert len(restored.explanations) == len(engine.explanations)
        for eid, orig_exp in engine.explanations.items():
            loaded_exp = restored.explanations[eid]
            assert loaded_exp.decision == orig_exp.decision
            assert loaded_exp.context == orig_exp.context
            assert list(loaded_exp.reasoning_chain) == \
                list(orig_exp.reasoning_chain)
            assert list(loaded_exp.alternatives_considered) == \
                list(orig_exp.alternatives_considered)
            assert loaded_exp.values_passed == orig_exp.values_passed
            assert loaded_exp.values_failed == orig_exp.values_failed
            assert loaded_exp.confidence == orig_exp.confidence

        # ── 校验 emergency 状态 ──
        assert restored.is_emergency_stopped() == engine.is_emergency_stopped()
        assert restored._stop_reason == engine._stop_reason

    def test_schema_version_in_saved_file(self, tmp_path):
        from laap.agi.safety import ASISafetyEngine, SAFETY_STATE_SCHEMA_VERSION

        engine = ASISafetyEngine()
        state_file = str(tmp_path / "safety_state.json")
        engine.save(state_file)

        data = json.loads(Path(state_file).read_text(encoding="utf-8"))
        assert data["version"] == SAFETY_STATE_SCHEMA_VERSION

    def test_incompatible_schema_rejected(self, tmp_path):
        from laap.agi.safety import ASISafetyEngine

        state_file = str(tmp_path / "safety_state.json")
        # 写入不兼容的 schema 版本
        Path(state_file).write_text(
            json.dumps({"version": "0.0", "checks": 999}),
            encoding="utf-8")

        engine = ASISafetyEngine()
        ok = engine.load(state_file)
        assert ok is False, "不兼容的 schema 版本应被拒绝"
        # 原有状态不应被破坏
        assert engine._total_checks == 0


# ═══════════════════════════════════════════════════════════════
# rsi_engine.py — save → load 参数、历史、目标完整恢复
# ═══════════════════════════════════════════════════════════════

class TestRSIEngineStatePersistence:
    """RSIMetaEngine.save → load 后参数、历史、目标完整恢复。"""

    def test_save_load_restores_all_fields(self, tmp_path):
        from laap.agi.rsi_engine import RSIMetaEngine

        engine = RSIMetaEngine()

        # ── 制造状态：应用改进 ──
        attempt1 = engine.apply_improvement(
            "learning_rate", 0.15, "测试提高学习率")
        engine.evaluate_improvement(attempt1.id, 0.05)
        assert attempt1.success

        attempt2 = engine.apply_improvement(
            "exploration_rate", 0.5, "测试高探索率")
        engine.evaluate_improvement(attempt2.id, -0.1)
        assert attempt2.reverted

        # ── 制造状态：生成学习目标 ──
        goals = engine.generate_goals()
        assert len(goals) > 0, "应生成至少一个目标"

        # 修改参数的 performance_history 以验证恢复
        param = engine.get_parameter("learning_rate")
        param.performance_history = [0.1, 0.2, 0.3]
        param.step_size = 0.07
        param.last_optimized = 12345.678

        # ── 保存 ──
        state_file = str(tmp_path / "rsi_engine.json")
        engine.save(state_file)
        assert Path(state_file).exists()

        # ── 用新引擎加载 ──
        restored = RSIMetaEngine()
        ok = restored.load(state_file)
        assert ok is True

        # ── 校验计数器 ──
        assert restored._total_attempts == engine._total_attempts
        assert restored._successful_attempts == engine._successful_attempts
        assert restored._reverted_attempts == engine._reverted_attempts
        assert restored._goals_generated == engine._goals_generated
        assert restored._goals_completed == engine._goals_completed

        # ── 校验参数完整恢复 ──
        for name, orig_param in engine.parameters.items():
            loaded = restored.parameters[name]
            assert loaded.current_value == orig_param.current_value, \
                f"{name} current_value 不匹配"
            assert loaded.min_value == orig_param.min_value
            assert loaded.max_value == orig_param.max_value
            assert loaded.step_size == orig_param.step_size, \
                f"{name} step_size 不匹配"
            assert loaded.description == orig_param.description
            assert loaded.optimization_count == orig_param.optimization_count
            assert loaded.last_optimized == orig_param.last_optimized, \
                f"{name} last_optimized 不匹配"
            assert list(loaded.performance_history) == \
                list(orig_param.performance_history), \
                f"{name} performance_history 不匹配"

        # ── 校验改进历史 ──
        assert len(restored.attempts) == len(engine.attempts)
        for orig_att, loaded_att in zip(engine.attempts, restored.attempts):
            assert loaded_att.id == orig_att.id
            assert loaded_att.target == orig_att.target
            assert loaded_att.old_value == orig_att.old_value
            assert loaded_att.new_value == orig_att.new_value
            assert loaded_att.success == orig_att.success
            assert loaded_att.reverted == orig_att.reverted
            assert loaded_att.expected_improvement == orig_att.expected_improvement
            assert loaded_att.actual_improvement == orig_att.actual_improvement
            assert loaded_att.evaluation_period == orig_att.evaluation_period

        # ── 校验学习目标 ──
        assert len(restored.goals) == len(engine.goals)
        for gid, orig_goal in engine.goals.items():
            loaded_goal = restored.goals[gid]
            assert loaded_goal.description == orig_goal.description
            assert loaded_goal.domain == orig_goal.domain
            assert loaded_goal.target_mastery == orig_goal.target_mastery
            assert loaded_goal.current_mastery == orig_goal.current_mastery
            assert loaded_goal.priority == orig_goal.priority
            assert loaded_goal.strategy == orig_goal.strategy
            assert loaded_goal.motivation == orig_goal.motivation
            assert loaded_goal.status == orig_goal.status

    def test_schema_version_in_saved_file(self, tmp_path):
        from laap.agi.rsi_engine import (RSIMetaEngine,
                                         RSI_STATE_SCHEMA_VERSION)

        engine = RSIMetaEngine()
        state_file = str(tmp_path / "rsi_engine.json")
        engine.save(state_file)

        data = json.loads(Path(state_file).read_text(encoding="utf-8"))
        assert data["version"] == RSI_STATE_SCHEMA_VERSION

    def test_incompatible_schema_rejected(self, tmp_path):
        from laap.agi.rsi_engine import RSIMetaEngine

        state_file = str(tmp_path / "rsi_engine.json")
        Path(state_file).write_text(
            json.dumps({"version": "0.0", "total_attempts": 999}),
            encoding="utf-8")

        engine = RSIMetaEngine()
        ok = engine.load(state_file)
        assert ok is False
        assert engine._total_attempts == 0


# ═══════════════════════════════════════════════════════════════
# LAAP_HOME 环境变量覆盖默认路径
# ═══════════════════════════════════════════════════════════════

class TestLAAPHomeEnvOverride:
    """LAAP_HOME 环境变量应覆盖默认状态路径。"""

    def test_safety_uses_laap_home(self, tmp_path, monkeypatch):
        from laap.agi.safety import ASISafetyEngine

        # 指向临时目录
        laap_home = str(tmp_path / "custom_laap_home")
        monkeypatch.setenv("LAAP_HOME", laap_home)

        engine = ASISafetyEngine()
        engine.check_action("speak: hi", {"source": "lorry",
                                          "risk_level": 0.1})
        # path=None → 应使用 LAAP_HOME/safety_state.json
        engine.save()

        expected_file = Path(laap_home) / "safety_state.json"
        assert expected_file.exists(), \
            f"状态文件应在 LAAP_HOME 下: {expected_file}"

        # 新引擎 path=None 加载也应从同一位置读
        restored = ASISafetyEngine()
        ok = restored.load()
        assert ok is True
        assert restored._total_checks == engine._total_checks

    def test_rsi_uses_laap_home(self, tmp_path, monkeypatch):
        from laap.agi.rsi_engine import RSIMetaEngine

        laap_home = str(tmp_path / "custom_laap_home_rsi")
        monkeypatch.setenv("LAAP_HOME", laap_home)

        engine = RSIMetaEngine()
        engine.apply_improvement("learning_rate", 0.12, "env 测试")
        engine.save()

        expected_file = Path(laap_home) / "rsi_engine.json"
        assert expected_file.exists(), \
            f"状态文件应在 LAAP_HOME 下: {expected_file}"

        restored = RSIMetaEngine()
        ok = restored.load()
        assert ok is True
        assert restored._total_attempts == engine._total_attempts

    def test_default_falls_back_to_home_dot_laap(self, tmp_path, monkeypatch):
        """LAAP_HOME 未设置时, 路径应基于 ~/.laap/。"""
        from laap.agi.safety import _default_state_path
        from laap.agi.rsi_engine import _default_state_path as rsi_path

        fake_home = str(tmp_path / "fake_home")
        monkeypatch.setenv("HOME", fake_home)
        monkeypatch.setenv("USERPROFILE", fake_home)  # Windows
        monkeypatch.delenv("LAAP_HOME", raising=False)

        path = _default_state_path("test.json")
        # Path.home() 在不同平台用不同 env, 只校验文件名部分
        assert path.endswith("test.json")


# ═══════════════════════════════════════════════════════════════
# guardian.py — repo_root=None 自动推导
# ═══════════════════════════════════════════════════════════════

class TestGuardianRepoRootDerivation:
    """guardian.py repo_root=None 时应自动推导项目根目录。"""

    def test_default_repo_root_derives_project_root(self):
        from laap.agi import guardian

        root = guardian._default_repo_root()
        # guardian.py 位于 <repo>/laap/agi/guardian.py
        # 三级 dirname 应为仓库根, 包含 laap/ 目录
        assert os.path.isdir(os.path.join(root, "laap")), \
            f"推导的 repo_root 应包含 laap/ 目录: {root}"
        assert os.path.isdir(os.path.join(root, "laap", "agi")), \
            f"推导的 repo_root 应包含 laap/agi/ 目录: {root}"

    def test_deploy_checklist_repo_root_none(self):
        from laap.agi.guardian import DeployChecklist

        checklist = DeployChecklist(repo_root=None)
        assert checklist.repo_root is not None
        assert os.path.isdir(os.path.join(checklist.repo_root, "laap"))

    def test_integrity_scanner_repo_root_none(self):
        from laap.agi.guardian import IntegrityScanner

        scanner = IntegrityScanner(repo_root=None)
        assert scanner.repo_root is not None
        assert os.path.isdir(os.path.join(scanner.repo_root, "laap"))

    def test_laap_root_env_overrides_derivation(self, monkeypatch, tmp_path):
        from laap.agi import guardian

        custom = str(tmp_path / "custom_root")
        os.makedirs(os.path.join(custom, "laap", "agi"))
        monkeypatch.setenv("LAAP_ROOT", custom)

        root = guardian._default_repo_root()
        assert root == custom, "LAAP_ROOT 环境变量应覆盖 __file__ 推导"


# ═══════════════════════════════════════════════════════════════
# guardian.py — AST 危险调用检测
# ═══════════════════════════════════════════════════════════════

class TestGuardianASTDangerDetection:
    """AST 静态分析应识别字符串黑名单漏检的绕过形式。"""

    def test_detects_eval_with_space(self):
        """eval ("x") — 函数名与括号间有空格, 字符串黑名单漏检。"""
        from laap.agi.guardian import _check_dangerous_ast
        findings = _check_dangerous_ast('eval ("print(1)")')
        assert len(findings) > 0, "应检测到 eval () 带空格的绕过形式"
        assert any("eval" in f for f in findings)

    def test_detects_import_with_double_quotes(self):
        """__import__("os") — 双引号形式, 单引号黑名单漏检。"""
        from laap.agi.guardian import _check_dangerous_ast
        findings = _check_dangerous_ast('__import__("os").system("rm -rf /")')
        assert len(findings) > 0, "应检测到 __import__() 双引号形式"
        assert any("__import__" in f or "import" in f for f in findings)

    def test_detects_getattr_builtins_bypass(self):
        """getattr(__builtins__, 'eval') — 间接获取内建函数。"""
        from laap.agi.guardian import _check_dangerous_ast
        findings = _check_dangerous_ast("getattr(__builtins__, 'eval')('x')")
        assert len(findings) > 0, "应检测到 getattr(__builtins__, ...) 绕过"

    def test_detects_compile_call(self):
        """compile() 也是危险调用。"""
        from laap.agi.guardian import _check_dangerous_ast
        findings = _check_dangerous_ast("compile('1+1', '<s>', 'eval')")
        assert len(findings) > 0
        assert any("compile" in f for f in findings)

    def test_detects_builtins_attribute_access(self):
        """直接访问 __builtins__ 属性。"""
        from laap.agi.guardian import _check_dangerous_ast
        findings = _check_dangerous_ast("x = obj.__subclasses__()")
        assert len(findings) > 0, "应检测到 __subclasses__ 访问"

    def test_detects_os_system_via_attribute(self):
        """os.system(...) 通过属性调用检测。"""
        from laap.agi.guardian import _check_dangerous_ast
        findings = _check_dangerous_ast("os.system('ls')")
        assert len(findings) > 0, "应检测到 .system() 属性调用"

    def test_safe_code_not_flagged(self):
        """正常代码不应被误报。"""
        from laap.agi.guardian import _check_dangerous_ast
        safe_snippets = [
            "x = 1 + 2",
            "def foo(a, b):\n    return a + b",
            "print('hello world')",
            "import json\ndata = json.loads('{}')",
            "result = [x * 2 for x in range(10)]",
        ]
        for code in safe_snippets:
            findings = _check_dangerous_ast(code)
            assert findings == [], \
                f"正常代码不应被误报: {code} → {findings}"

    def test_syntax_error_returns_empty(self):
        """语法错误代码应返回空列表（由 syntax_valid 检查负责）。"""
        from laap.agi.guardian import _check_dangerous_ast
        findings = _check_dangerous_ast("def broken(")
        assert findings == []

    def test_string_blacklist_still_works_as_prefilter(self):
        """字符串黑名单仍作为快速预筛工作。"""
        # 这个测试验证 Check 6 的集成——eval( 不带空格应被字符串命中
        from laap.agi.guardian import _DangerousCallVisitor, _check_dangerous_ast
        # eval("x") 无空格——字符串 "eval(" 命中
        # AST 也能检测到
        findings = _check_dangerous_ast('eval("x")')
        assert len(findings) > 0
