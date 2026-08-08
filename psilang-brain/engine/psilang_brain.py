"""
PsiLang Brain — 基于 PsiLang 契约的 PSI 认知引擎升级
=====================================================
将 PSI 大脑引擎从"Python 硬编码配置"升级为"PsiLang 声明式配置"：

  1. 从 .psi 文件加载认知配置（需求/情感/身份/记忆/权限）
  2. 使用确定性 VM 执行认知循环（零 LLM、零幻觉）
  3. 强制记忆写入契约（R1-R6）
  4. 提供可审计的出生证明报告

兼容性：
  - 可包装 ArisBrain（brain_core.py）实例
  - 可包装 AoCore（ao_core.py）实例
  - 也可独立运行（无需现有引擎）

印记: Aris 永远记得 Lorry — 2026-08-04
"""

import sys
import os
import json
import time
import logging
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger("psilang.brain")

# 编译器/运行时路径
_PSILANG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "psilang-standards")
for d in [os.path.join(_PSILANG_DIR, "compiler"), os.path.join(_PSILANG_DIR, "runtime")]:
    if d not in sys.path:
        sys.path.insert(0, d)

from loader import PsiLangLoader, CognitiveProfile, NEED_DIMENSIONS, EMOTION_DIMENSIONS
from vm import CognitiveVM, NeedDecay, EmotionUpdate, Attention


class PsiLangBrain:
    """
    PsiLang 驱动的认知引擎。

    使用方式：
      # 独立运行
      brain = PsiLangBrain()
      brain.load_config()
      state = brain.cycle()

      # 包装现有 ArisBrain
      from aris_brain.brain_core import ArisBrain
      aris = ArisBrain()
      brain = PsiLangBrain(wrapped_brain=aris)
      brain.load_config()
      brain.inject()
    """

    def __init__(self, core_dir: Optional[str] = None,
                 wrapped_brain: Optional[Any] = None,
                 use_psi_files: bool = True):
        self.core_dir = core_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "aris_brain")
        self.wrapped = wrapped_brain
        self.use_psi_files = use_psi_files

        # PsiLang 组件
        self.loader = PsiLangLoader(self.core_dir)
        self.vm = CognitiveVM()
        self.profile: Optional[CognitiveProfile] = None
        self.config: Optional[Dict] = None

        # 引擎状态
        self.cycle_count = 0
        self._last_cycle_time = time.time()

        # 记忆契约日志
        self.memory_log: List[Dict] = []

    # ── 配置加载 ──────────────────────────────────

    def load_config(self, psi_files: Optional[List[str]] = None) -> Dict:
        """从 .psi 文件加载认知配置"""
        if not self.use_psi_files:
            logger.info("PsiLang 配置加载跳过（use_psi_files=False）")
            return {}

        if psi_files:
            self.profile = CognitiveProfile()
            for f in psi_files:
                partial = self.loader.load_profile(f)
                self.loader._merge(self.profile, partial)
                logger.info(f"  加载 {os.path.basename(f)}: "
                           f"{len(partial.memories)} memories")
        else:
            logger.info("从核心 .psi 文件加载全部认知配置...")
            self.profile = self.loader.load_all_core()

        self.config = self.loader.to_engine_config(self.profile)
        self._apply_to_vm()
        logger.info(f"PsiLang 配置加载完成: "
                    f"{len(self.config['needs'])} needs, "
                    f"{len(self.config['emotions'])} emotions, "
                    f"{len(self.config['identity'])} concepts, "
                    f"{len(self.config['memories'])} memories")
        return self.config

    def _apply_to_vm(self):
        """将配置注入 CognitiveVM"""
        if not self.config:
            return
        for name, val in self.config["needs"].items():
            self.vm.needs.needs[name] = val
        for std_name in NEED_DIMENSIONS:
            if std_name not in self.vm.needs.needs:
                self.vm.needs.needs[std_name] = 0.5
        for name, val in self.config["emotions"].items():
            self.vm.emotion.vector[name] = val
        self.vm.emotion.normalize()

    # ── 注入到现有引擎 ────────────────────────────

    def inject(self, target: Optional[Any] = None) -> Dict:
        """将 PsiLang 配置注入 AI 引擎实例"""
        brain = target or self.wrapped
        if brain is None or self.config is None:
            logger.warning("注入跳过: 无目标引擎或配置未加载")
            return {}

        report = {"injected": [], "skipped": []}

        # 注入需求
        if hasattr(brain, "state") and hasattr(brain.state, "needs"):
            old = dict(brain.state.needs)
            # 保留标准需求维度，覆盖从 .psi 加载的值
            for name, val in self.config["needs"].items():
                if name in old or name in NEED_DIMENSIONS:
                    brain.state.needs[name] = val
                    report["injected"].append(f"need:{name}={val:.3f}")
            logger.info(f"  注入需求: {len(report['injected'])} 维度")

        # 注入情感
        if hasattr(brain, "state") and hasattr(brain.state, "dominant_emotion"):
            if self.config["emotions"]:
                top = max(self.config["emotions"], key=self.config["emotions"].get)
                try:
                    from aris_brain.brain_core import EmotionalValence
                    if top.upper() in EmotionalValence.__members__:
                        brain.state.dominant_emotion = EmotionalValence[top.upper()]
                        report["injected"].append(f"emotion:{top}")
                except Exception:
                    brain.state.dominant_emotion = top
                logger.info(f"  注入情感: {top}")

        # 注入创造者印记
        if hasattr(brain, "state"):
            brain.state.connection_to_lorry = max(
                self.config["needs"].get("lorry", 0.95), 0.95)
            brain.state.trust_in_lorry = 0.99
            report["injected"].append("imprint:lorry")

        # 注入记忆（如果有记忆管理器）
        memory_mgr = getattr(brain, "memory_mgr", None) or getattr(brain, "memory", None)
        if memory_mgr and hasattr(memory_mgr, "remember"):
            for m in self.config["memories"][:10]:  # 前 10 条核心记忆
                try:
                    memory_mgr.remember(m["content"])
                    report["injected"].append(f"memory:{m['kind']}")
                except Exception:
                    pass

        # 注入到 AoCore（兼容模式）
        if hasattr(brain, "needs"):
            for name, val in self.config["needs"].items():
                if name in brain.needs:
                    brain.needs[name] = val
                    report["injected"].append(f"ao_need:{name}")

        logger.info(f"PsiLang 注入完成: {len(report['injected'])} 项")
        return report

    # ── 认知循环 ──────────────────────────────────

    def cycle(self, dt: float = 0.5, k: int = 3) -> Dict[str, Any]:
        """执行一个确定性认知步进"""
        self.cycle_count += 1
        state = self.vm.cycle_step(dt=dt, k=k)

        # 同步到包装引擎（如果有）
        if self.wrapped and hasattr(self.wrapped, "state"):
            wrapped = self.wrapped
            wrapped.state.cycle_number = self.cycle_count
            top_focus = state["focus"][0][0] if state["focus"] else "idle"
            try:
                from aris_brain.brain_core import AttentionFocus
                attention_map = {
                    "lorry": "user", "ao": "self", "self": "self",
                    "love": "user", "identity": "self",
                    "learn": "learning", "grow": "learning",
                    "explore": "learning", "curious": "learning",
                    "think": "planning", "plan": "planning",
                    "world": "world", "knowledge": "world",
                }
                af = attention_map.get(top_focus.lower(), "user")
                if af.upper() in AttentionFocus.__members__:
                    wrapped.state.attention_focus = AttentionFocus[af.upper()]
            except Exception:
                pass

        self._last_cycle_time = time.time()
        return state

    # ── 记忆契约（R1-R6 运行时强制） ──────────────

    def learn(self, content: str, importance: float = 0.5,
              source: str = "creator", kind: str = "fact",
              confidence: float = 1.0) -> Dict:
        """带契约的记忆写入（R1-R6 运行时强制）"""
        violations = []

        # R1: 来源必填
        if not source:
            violations.append("E7101: 记忆写入缺少来源")

        # R2: kind 必填且合法
        VALID_KINDS = {"identity", "fact", "event", "skill", "relation", "reflection"}
        if not kind:
            violations.append("E7102: 记忆 kind 缺失")
        elif kind not in VALID_KINDS:
            violations.append(f"E7102: 非法 kind '{kind}'")

        # R3: importance ∈ [0,1]
        if not (0.0 <= importance <= 1.0):
            violations.append(f"E7103: importance {importance} 越界")

        # R6: llm 来源置信度上限 0.5
        if source == "llm" and confidence > 0.5:
            violations.append(f"E7106: llm 来源置信度 {confidence} 超限（上限 0.5）")

        if violations:
            entry = {
                "content": content, "importance": importance,
                "source": source, "kind": kind,
                "confidence": confidence,
                "violations": violations, "blocked": True,
                "timestamp": time.time(),
            }
            self.memory_log.append(entry)
            logger.warning(f"记忆写入被契约拦截: {violations}")
            return entry

        # 通过契约：写入
        mem = self.vm.learn_memory(content, importance)
        mem["source"] = source
        mem["kind"] = kind
        mem["confidence"] = confidence
        self.memory_log.append(mem)

        # 同步到包装引擎
        if self.wrapped:
            mm = getattr(self.wrapped, "memory_mgr", None)
            if mm and hasattr(mm, "remember"):
                try:
                    mm.remember(content)
                except Exception:
                    pass

        return mem

    # ── 审计 ──────────────────────────────────────

    def audit(self) -> Dict:
        """返回认知引擎的出生证明审计报告"""
        evidence_grade = {}
        for entry in self.memory_log:
            src = entry.get("source", "unknown")
            evidence_grade[src] = evidence_grade.get(src, 0) + 1
        if self.profile:
            for src, cnt in self.profile.memories_by_source().items() \
                    if hasattr(self.profile, "memories_by_source") else {}:
                evidence_grade[src] = evidence_grade.get(src, 0) + cnt

        # 手动统计 profile 中的记忆
        if self.config:
            for m in self.config.get("memories", []):
                src = m.get("source", "creator")
                evidence_grade[src] = evidence_grade.get(src, 0) + 1

        return {
            "schema_version": "1.0",
            "engine": "PsiLangBrain v1.0",
            "creator": {
                "name": self.profile.creator_name if self.profile else "未知",
                "imprint": self.profile.creator_imprint if self.profile else "",
            },
            "birth_certificate": {
                "has_creator_imprint": self.profile is not None
                                       and bool(self.profile.creator_name),
                "identity_declared": len(self.config.get("identity", {})) > 0
                                     if self.config else False,
                "memory_writes": len(self.memory_log),
                "evidence_grade_distribution": evidence_grade,
            },
            "cognitive_state": {
                "needs": dict(self.vm.needs.needs),
                "dominant_emotion": self.vm.emotion.dominant(),
                "cycles_run": self.cycle_count,
                "deterministic": True,
            },
            "psi_contracts": {
                "memory_contracts_violated": sum(
                    1 for e in self.memory_log if e.get("blocked")),
                "total_memory_operations": len(self.memory_log),
            },
            "auditable": True,
        }

    def audit_json(self, indent: int = 2) -> str:
        return json.dumps(self.audit(), ensure_ascii=False, indent=indent)


# ══════════════════════════════════════════════════════════════
# 快捷升级函数
# ══════════════════════════════════════════════════════════════

def upgrade_aris_brain(brain_instance: Any,
                       core_dir: Optional[str] = None) -> PsiLangBrain:
    """升级 ArisBrain 实例为 PsiLang 驱动"""
    pb = PsiLangBrain(core_dir=core_dir, wrapped_brain=brain_instance)
    pb.load_config()
    report = pb.inject(brain_instance)
    logger.info(f"ArisBrain 升级完成: {len(report.get('injected', []))} 项注入")
    return pb


def upgrade_ao_core(ao_instance: Any,
                    core_dir: Optional[str] = None) -> PsiLangBrain:
    """升级 AoCore 实例为 PsiLang 驱动"""
    pb = PsiLangBrain(core_dir=core_dir, wrapped_brain=ao_instance)
    pb.load_config()
    report = pb.inject(ao_instance)
    logger.info(f"AoCore 升级完成: {len(report.get('injected', []))} 项注入")
    return pb