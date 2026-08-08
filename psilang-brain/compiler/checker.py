"""
PsiLang Checker v4.1 — 语义检查器（契约层 Step 1）
====================================================
在 Parser 之上执行认知契约检查：

  P1 验证通道（E7xxx）
    E7001 事实声明缺少来源        — fact 无 @source
    E7002 未验证事实被当作事实使用  — ⟨fact?⟩ 类型用于 fact 值
    E7003 公理不在白名单           — axiom 通道引用未知公理
    E7004 验证函数签名不符         — verify 通道引用的函数签名错误
    E7005 记忆置信度超出 [0,1]     — memory 通道 min_confidence 越界
    E7006 未知验证通道             — channel 非 world/axiom/verify/memory
    E3001 未声明的世界访问         — world 通道引用未在 world 声明中的资源

  P2 记忆契约（E71xx）
    E7101 记忆写入缺少来源         — learn 无 source
    E7102 记忆 kind 缺失/非法      — learn kind 非六种枚举
    E7103 记忆重要性超出 [0,1]     — importance 越界
    E7104 因果父链格式错误         — causal_parents 引用非法
    E7106 LLM 来源置信度超限       — source=llm 且 confidence > 0.5

印记: Aris 永远记得 Lorry — 2026-08-04
"""

from typing import Any, Dict, List, Optional, Set

from ast_nodes import (
    ASTNode, Expr,
    FactDecl, SourceSpec, WorldDecl, FnDecl, LetDecl, Identifier,
    QStateDecl, LearnStmt, PsiLangProgram,
)
from diagnostics import DiagnosticCollector, location_dict


# ══════════════════════════════════════════════════════════════
# 内置公理白名单（Step 1 内置；后续支持项目级 manifest 扩展）
# ══════════════════════════════════════════════════════════════

DEFAULT_AXIOMS: Set[str] = {
    "arith_basic",      # 基本算术公理
    "logic_basic",      # 基本逻辑公理
    "set_basic",        # 基本集合公理
    "order_basic",      # 序关系公理
}

VALID_CHANNELS: Set[str] = {"world", "axiom", "verify", "memory"}

# 记忆 kind 枚举（契约 R2）
VALID_KINDS: Set[str] = {"identity", "fact", "event", "skill", "relation", "reflection"}

# 记忆来源枚举（契约 R1）
VALID_SOURCES: Set[str] = {"creator", "world", "memory", "verify", "llm"}


# ══════════════════════════════════════════════════════════════
# 语义检查器
# ══════════════════════════════════════════════════════════════

class PsiLangChecker:
    """PsiLang 认知契约检查器"""

    def __init__(self, prog: PsiLangProgram, filename: str,
                 collector: Optional[DiagnosticCollector] = None,
                 axiom_whitelist: Optional[Set[str]] = None):
        self.prog = prog
        self.filename = filename
        self.collector = collector or DiagnosticCollector()
        self.axiom_whitelist = axiom_whitelist or DEFAULT_AXIOMS

        # 符号信息
        self.functions: Dict[str, FnDecl] = {}
        self.world: Optional[WorldDecl] = None
        self.facts: Dict[str, FactDecl] = {}
        # 类型环境：name -> 类型标注（含 ⟨fact?⟩ 等未验证类型）
        self.type_env: Dict[str, str] = {}

    # ── 主入口 ──────────────────────────────────────────

    def check(self) -> DiagnosticCollector:
        """执行全部语义检查"""
        self._collect_symbols()
        self._check_facts()
        self._check_learns()
        return self.collector

    # ── 符号收集 ────────────────────────────────────────

    def _collect_symbols(self):
        """第一遍扫描：收集函数/世界声明/类型标注"""
        for stmt in self._walk(self.prog.statements):
            if isinstance(stmt, FnDecl):
                self.functions[stmt.name] = stmt
                # 参数类型标注（含 ⟨fact?⟩）
                for pname, ptype in stmt.params:
                    if ptype:
                        self.type_env[pname] = ptype
            elif isinstance(stmt, WorldDecl):
                self.world = stmt
            elif isinstance(stmt, LetDecl):
                if stmt.type_anno:
                    self.type_env[stmt.name] = stmt.type_anno

    def _walk(self, statements: List[ASTNode]):
        """遍历语句（含嵌套块）"""
        for stmt in statements:
            yield stmt
            for child in getattr(stmt, "body", []) or []:
                yield from self._walk([child])
            for child in getattr(stmt, "then_body", []) or []:
                yield from self._walk([child])
            for child in getattr(stmt, "else_body", []) or []:
                yield from self._walk([child])
            fn = getattr(stmt, "tests", None)
            if fn:
                yield from self._walk(fn)

    # ── fact 检查 ───────────────────────────────────────

    def _check_facts(self):
        """检查所有 fact 声明（E7xxx 系列）"""
        for stmt in self._walk(self.prog.statements):
            if not isinstance(stmt, FactDecl):
                continue
            self.facts[stmt.name] = stmt
            loc = self._loc(stmt)

            # E7001: 事实声明缺少来源
            if stmt.source is None:
                self.collector.error(
                    "E7001", "事实声明缺少来源: 必须携带 @source(...)",
                    loc,
                    suggestion="示例: fact x = ... @source(world: entity.prop) 或 @source(axiom: arith_basic)",
                    fix={"type": "insert",
                         "position": {"line": loc["line"], "column": loc["column"]},
                         "text": "@source(world: ) "},
                )
                continue

            self._check_source(stmt, stmt.source)

    def _check_source(self, fact: FactDecl, src: SourceSpec):
        """检查单个验证通道"""
        loc = self._loc(fact)

        # E7006: 未知通道
        if src.channel not in VALID_CHANNELS:
            self.collector.error(
                "E7006", f"未知验证通道 '{src.channel}'（可选: world/axiom/verify/memory）",
                loc, suggestion="使用 world | axiom | verify | memory 之一",
            )
            return

        # world 通道 → E3001 联动: 必须已声明 world 且资源 ∈ read
        if src.channel == "world":
            root = src.target.split(".")[0]
            if self.world is None:
                self.collector.error(
                    "E3001", "world 通道引用了未声明的世界: 缺少 world { read: [...] } 声明",
                    loc, suggestion="添加 world { read: [%s] } 声明" % root,
                )
            elif root not in self.world.read:
                self.collector.error(
                    "E3001", f"world 通道访问了未声明的资源 '{root}'",
                    loc,
                    suggestion=f"在 world 声明的 read 列表中加入 {root}",
                    fix={"type": "replace",
                         "range": {"start": {"line": loc["line"], "column": loc["column"]},
                                   "end": {"line": loc["line"], "column": loc["column"]}},
                         "text": ""},
                )

        # axiom 通道 → E7003: 白名单
        elif src.channel == "axiom":
            if src.target not in self.axiom_whitelist:
                self.collector.error(
                    "E7003", f"公理 '{src.target}' 不在白名单中",
                    loc,
                    suggestion=f"可用公理: {', '.join(sorted(self.axiom_whitelist))}",
                )

        # verify 通道 → E7004: 函数存在 + 签名 (⟨claim⟩) → ⟨verdict⟩
        elif src.channel == "verify":
            fn = self.functions.get(src.target)
            if fn is None:
                self.collector.error(
                    "E7004", f"验证函数 '{src.target}' 未声明",
                    loc,
                    suggestion="声明一个 fn %s(claim: ⟨claim⟩) -> ⟨verdict⟩ { ... }" % src.target,
                )
            else:
                ret = fn.return_type
                if ret not in ("⟨verdict⟩", "verdict", "⟨fact⟩", "fact"):
                    self.collector.error(
                        "E7004",
                        f"验证函数 '{src.target}' 返回类型 '{ret or '(未标注)'}' 不是 ⟨verdict⟩",
                        loc,
                        suggestion="验证函数必须返回 ⟨verdict⟩",
                    )
                if len(fn.params) < 1:
                    self.collector.error(
                        "E7004", f"验证函数 '{src.target}' 缺少 claim 参数",
                        loc, suggestion="签名应为 (claim: ⟨claim⟩) -> ⟨verdict⟩",
                    )

        # memory 通道 → E7005: min_confidence ∈ [0,1]
        elif src.channel == "memory":
            if not (0.0 <= src.min_confidence <= 1.0):
                self.collector.error(
                    "E7005", f"记忆来源置信度阈值 {src.min_confidence} 超出 [0,1]",
                    loc, suggestion="min_confidence 必须在 0.0 到 1.0 之间",
                )

        # E7002: 未验证事实（⟨fact?⟩）被当作事实使用
        self._check_fact_value(fact, fact.value, loc)

    def _check_fact_value(self, fact: FactDecl, value: Expr, loc: dict):
        """检查 fact 的值表达式：⟨fact?⟩ 类型变量不能作为事实来源"""
        if isinstance(value, Identifier):
            declared_type = self.type_env.get(value.name, "")
            if "fact?" in declared_type:
                self.collector.error(
                    "E7002",
                    f"未验证事实 '{value.name}'（类型 {declared_type}）被当作事实使用",
                    loc,
                    suggestion="先用 verify 通道验证: fact x = v @source(verify: check)",
                )

    def _check_learns(self):
        """记忆写入契约 R1-R6（E71xx 系列）"""
        for stmt in self._walk(self.prog.statements):
            if not isinstance(stmt, LearnStmt):
                continue
            loc = self._loc(stmt)

            # R1: 无来源 = 拒绝写入
            if not stmt.source:
                self.collector.error(
                    "E7101", "记忆写入缺少来源: learn 必须携带 source",
                    loc,
                    suggestion='示例: learn("内容", importance=0.9, source=creator, kind=fact, confidence=1.0)',
                )
            elif stmt.source not in VALID_SOURCES:
                self.collector.error(
                    "E7102", f"非法来源 '{stmt.source}'（可选: {', '.join(sorted(VALID_SOURCES))}）",
                    loc,
                )

            # R2: kind 必填且合法
            if not stmt.kind:
                self.collector.error(
                    "E7102", "记忆 kind 缺失（可选: identity/fact/event/skill/relation/reflection）",
                    loc, suggestion="kind=identity 用于身份类记忆，kind=fact 用于事实类记忆",
                )
            elif stmt.kind not in VALID_KINDS:
                self.collector.error(
                    "E7102", f"非法 kind '{stmt.kind}'（可选: {', '.join(sorted(VALID_KINDS))}）",
                    loc,
                )

            # R3: importance ∈ [0,1]
            if not (0.0 <= stmt.importance <= 1.0):
                self.collector.error(
                    "E7103", f"记忆重要性 {stmt.importance} 超出 [0,1]",
                    loc, suggestion="importance 必须在 0.0 到 1.0 之间",
                )

            # R4: causal_parents 提供时检查格式（缺失默认 [root]，合法）
            for p in stmt.causal_parents:
                if not p or p in ("[", "]"):
                    self.collector.error(
                        "E7104", f"因果父链引用格式错误: {p!r}",
                        loc, suggestion="causal_parents=[root] 或引用已存在记忆 id",
                    )

            # R5: 写入遵守 world 声明（无 world 声明时警告，不阻断）
            if self.world is None:
                self.collector.warning(
                    "E3001", "文件无 world 声明: learn 写入未受边界约束（建议声明 write: [memory]）",
                    loc,
                )
            elif "memory" not in self.world.write and stmt.source in ("world", "llm", "memory"):
                self.collector.warning(
                    "E3001", f"world 声明未包含 write: [memory]，learn 写入越界",
                    loc,
                )

            # R6: llm 来源 confidence ≤ 0.5
            if stmt.source == "llm" and stmt.confidence > 0.5:
                self.collector.error(
                    "E7106",
                    f"LLM 来源记忆置信度 {stmt.confidence} 超限（上限 0.5）",
                    loc,
                    suggestion="llm 来源记忆必须经过 verify 通道提升置信度",
                )

    # ── 工具 ────────────────────────────────────────────

    def _loc(self, node: ASTNode) -> dict:
        pos = getattr(node, "pos", None)
        if pos is None:
            return location_dict(self.filename, 0, 0)
        return location_dict(self.filename, pos.line, pos.column,
                             pos.end_line, pos.end_column)


# ── 快捷入口 ────────────────────────────────────────────────

def check_program(prog: PsiLangProgram, filename: str,
                  collector: Optional[DiagnosticCollector] = None) -> DiagnosticCollector:
    """对已解析的程序执行契约检查"""
    checker = PsiLangChecker(prog, filename, collector)
    return checker.check()
