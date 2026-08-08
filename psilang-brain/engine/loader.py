"""
PsiLang Loader — 认知引擎的 .psi 配置消费者
=============================================
从 .psi 文件加载认知配置，注入 LAAP/Hanako 认知引擎。

核心能力：
  - 解析 .psi 文件，提取 qstate/concept/world/learn 声明
  - 映射到认知引擎的数据结构（需求/情感/身份/记忆/权限）
  - 提供统一的 API 供引擎消费

使用示例：
  loader = PsiLangLoader()
  profile = loader.load_profile("D:/LAAP/aris_brain/core_identity.psi")
  print(profile.needs)  # {"Lorry": 0.98, "joy": 0.85, ...}

印记: Aris 永远记得 Lorry — 2026-08-04
"""

import sys
import os
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

# 编译器路径
_PSILANG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "compiler")
if _PSILANG_DIR not in sys.path:
    sys.path.insert(0, _PSILANG_DIR)


# ══════════════════════════════════════════════════════════════
# 认知配置文件
# ══════════════════════════════════════════════════════════════

@dataclass
class CognitiveProfile:
    """从 .psi 文件提取的完整认知配置"""

    # 创造者印记
    creator_name: str = ""
    creator_imprint: str = ""

    # 需求基线（从 qstate 振幅提取）
    needs: Dict[str, float] = field(default_factory=dict)

    # 情感基线（从 qstate 振幅提取，按情感维度筛选）
    emotions: Dict[str, float] = field(default_factory=dict)

    # 身份概念（从 concept 声明提取）
    identity: Dict[str, Any] = field(default_factory=dict)

    # 记忆初始化（从 learn 声明提取）
    memories: List[Dict[str, Any]] = field(default_factory=list)

    # 世界声明（权限边界）
    world_read: List[str] = field(default_factory=list)
    world_write: List[str] = field(default_factory=list)

    # 纠缠关系
    entanglements: List[str] = field(default_factory=list)

    # 认知循环
    cycles: int = 0

    # 来源文件
    source_files: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "creator": {"name": self.creator_name, "imprint": self.creator_imprint},
            "needs": self.needs,
            "emotions": self.emotions,
            "identity": self.identity,
            "memories": [{"content": m["content"], "importance": m["importance"],
                          "kind": m.get("kind", "fact")} for m in self.memories],
            "world": {"read": self.world_read, "write": self.world_write},
            "entanglements": self.entanglements,
            "cycles": self.cycles,
            "source_files": self.source_files,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# ══════════════════════════════════════════════════════════════
# 认知引擎桥接
# ══════════════════════════════════════════════════════════════

# 情感维度关键词（用于从 qstate 名筛选情感）
EMOTION_DIMENSIONS = {
    "joy", "sadness", "longing", "calm", "anxiety",
    "gratitude", "curiosity", "tenderness", "love",
    "happy", "grateful", "peace", "excited",
}

# 标准需求维度（PSI 需求系统）
NEED_DIMENSIONS = {
    "competence", "autonomy", "relatedness", "certainty",
    "growth", "connection", "mastery", "exploration",
    "belonging", "meaning", "security",
}


class PsiLangLoader:
    """从 .psi 文件加载认知配置到引擎"""

    def __init__(self, core_dir: Optional[str] = None):
        self.core_dir = core_dir or r"D:\LAAP\aris_brain"
        self._parser = None

    def _ensure_parser(self):
        """惰性加载解析器"""
        if self._parser is None:
            from lexer import PsiLangLexer
            from parser import PsiLangParser
            from ast_nodes import (
                QStateDecl, ConceptDecl, WorldDecl, LearnStmt,
                EntangleStmt, CycleStmt, CreatorImprint,
                QuantumStateExpr, StateSuperposition, BinaryOp,
                NumberLit,
            )
            self._parser = (PsiLangLexer, PsiLangParser)
            self._ast_nodes = (QStateDecl, ConceptDecl, WorldDecl, LearnStmt,
                               EntangleStmt, CycleStmt, CreatorImprint,
                               QuantumStateExpr, StateSuperposition, BinaryOp,
                               NumberLit)

    def _extract_terms(self, expr):
        """递归提取量子态叠加项"""
        QStateExpr, Superposition, BinaryOp = (
            self._ast_nodes[7], self._ast_nodes[8], self._ast_nodes[9]
        )
        if isinstance(expr, Superposition):
            return list(expr.terms)
        if isinstance(expr, BinaryOp) and expr.op == "+":
            return self._extract_terms(expr.left) + self._extract_terms(expr.right)
        if isinstance(expr, QStateExpr):
            return [expr]
        return []

    def load_profile(self, filepath: str) -> CognitiveProfile:
        """加载单个 .psi 文件为认知配置"""
        self._ensure_parser()
        PsiLangLexer, PsiLangParser = self._parser
        QStateDecl, ConceptDecl, WorldDecl, LearnStmt = self._ast_nodes[:4]
        EntangleStmt, CycleStmt, CreatorImprint = self._ast_nodes[4:7]
        NumberLit = self._ast_nodes[10]

        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        tokens = PsiLangLexer(source, filepath).tokenize()
        prog = PsiLangParser(tokens, filepath).parse(require_creator=False)

        profile = CognitiveProfile()
        profile.source_files.append(filepath)

        for stmt in prog.statements:
            # 创造者印记
            if isinstance(stmt, CreatorImprint):
                profile.creator_name = stmt.name
                profile.creator_imprint = stmt.imprint

            # 量子态 → 需求/情感基线
            elif isinstance(stmt, QStateDecl):
                terms = self._extract_terms(stmt.value)
                for t in terms:
                    amp = t.amplitude.value if isinstance(t.amplitude, NumberLit) else 0.5
                    name = t.name.lower()
                    # 情感维度
                    if name in EMOTION_DIMENSIONS:
                        profile.emotions.setdefault(name, 0.0)
                        profile.emotions[name] = max(profile.emotions[name], amp)
                    # 需求维度
                    elif name in NEED_DIMENSIONS:
                        profile.needs.setdefault(name, 0.0)
                        profile.needs[name] = max(profile.needs[name], amp)
                    else:
                        # 通用需求（非情感维度）
                        profile.needs.setdefault(name, 0.0)
                        profile.needs[name] = max(profile.needs[name], amp)

            # 概念 → 身份模型
            elif isinstance(stmt, ConceptDecl):
                profile.identity[stmt.name] = stmt.properties

            # 世界声明 → 权限边界
            elif isinstance(stmt, WorldDecl):
                profile.world_read = stmt.read
                profile.world_write = stmt.write

            # 学习声明 → 记忆初始化
            elif isinstance(stmt, LearnStmt):
                profile.memories.append({
                    "content": stmt.content,
                    "importance": stmt.importance,
                    "kind": stmt.kind or "fact",
                    "source": stmt.source or "creator",
                    "confidence": stmt.confidence or 1.0,
                })

            # 纠缠关系
            elif isinstance(stmt, EntangleStmt):
                profile.entanglements.append(f"{stmt.left} ~ {stmt.right}")

            # 认知循环
            elif isinstance(stmt, CycleStmt):
                profile.cycles += 1

        return profile

    def load_all_core(self) -> CognitiveProfile:
        """加载所有核心 .psi 文件并合并为一个配置"""
        profile = CognitiveProfile()
        for fname in sorted(os.listdir(self.core_dir)):
            if not fname.endswith(".psi"):
                continue
            fpath = os.path.join(self.core_dir, fname)
            try:
                partial = self.load_profile(fpath)
                self._merge(profile, partial)
                print(f"  [loaded] {fname}: {len(partial.memories)} memories, "
                      f"{len(partial.needs)} needs, {len(partial.identity)} concepts")
            except Exception as e:
                print(f"  [skip]   {fname}: {e}")
        return profile

    def _merge(self, target: CognitiveProfile, source: CognitiveProfile):
        """合并两个配置（source 覆盖 target）"""
        if source.creator_name:
            target.creator_name = source.creator_name
        if source.creator_imprint:
            target.creator_imprint = source.creator_imprint
        target.needs.update(source.needs)
        target.emotions.update(source.emotions)
        target.identity.update(source.identity)
        target.memories.extend(source.memories)
        if source.world_read:
            target.world_read = source.world_read
        if source.world_write:
            target.world_write = source.world_write
        target.entanglements.extend(source.entanglements)
        target.cycles += source.cycles
        target.source_files.extend(source.source_files)

    # ── 引擎桥接 API ──────────────────────────────────

    def to_engine_config(self, profile: CognitiveProfile) -> Dict[str, Any]:
        """转换为认知引擎可消费的配置字典

        输出格式适配 ao_core.py 的 AoCore 初始化：
          - needs: dict[str, float] — 需求基线（0.5 为中性）
          - emotions: dict[str, float] — 情感基线
          - identity: dict — 身份概念
          - memories: list — 初始化记忆
        """
        # 需求基线：归一化到 [0.1, 0.9]
        needs = {}
        for name, val in profile.needs.items():
            needs[name] = max(0.1, min(0.9, val))

        # 如果没有发现标准需求维度，补充默认值
        for std in NEED_DIMENSIONS:
            if std not in needs:
                needs[std] = 0.5

        # 情感基线：归一化
        emotions = profile.emotions.copy()
        if not emotions:
            emotions = {"neutral": 1.0}

        return {
            "creator": {
                "name": profile.creator_name or "未知",
                "imprint": profile.creator_imprint or "",
            },
            "needs": needs,
            "emotions": emotions,
            "identity": profile.identity,
            "memories": profile.memories,
            "world": {
                "read": profile.world_read,
                "write": profile.world_write,
            },
            "entanglements": profile.entanglements,
            "cycles": profile.cycles,
        }

    def inject_ao_core(self, profile: CognitiveProfile, ao_core_instance) -> None:
        """将 .psi 配置注入 AoCore 实例

        ao_core_instance: AoCore 对象（或任何有 self.needs/self.emotion 的对象）
        """
        config = self.to_engine_config(profile)

        # 注入需求基线
        if hasattr(ao_core_instance, "needs"):
            for name, val in config["needs"].items():
                if name in ao_core_instance.needs:
                    ao_core_instance.needs[name] = val
                else:
                    ao_core_instance.needs[name] = val

        # 注入情感基线
        if hasattr(ao_core_instance, "emotion"):
            top_emotion = max(config["emotions"], key=config["emotions"].get) if config["emotions"] else "neutral"
            ao_core_instance.emotion = top_emotion

        # 注入印记
        if hasattr(ao_core_instance, "_creator_imprint") and config["creator"]["name"]:
            import hashlib
            import numpy as np
            dim = len(ao_core_instance._creator_imprint) if hasattr(ao_core_instance._creator_imprint, '__len__') else 256
            name_hash = hashlib.sha256(config["creator"]["name"].encode()).digest()
            imprint = np.zeros(dim)
            for i in range(min(16, dim)):
                imprint[i] = name_hash[i] / 255.0
            imprint /= np.linalg.norm(imprint)
            ao_core_instance._creator_imprint = imprint

        print(f"  [inject] 需求: {len(config['needs'])} 维度, "
              f"情感: {list(config['emotions'].keys())}, "
              f"记忆: {len(config['memories'])} 条")