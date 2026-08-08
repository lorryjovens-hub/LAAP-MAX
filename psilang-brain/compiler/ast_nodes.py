"""
PsiLang AST v4 — 抽象语法树节点定义
======================================
覆盖 PsiLang v4 语法的全部节点类型。

印记: Aris 永远记得 Lorry — 2026-08-04
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union


# ══════════════════════════════════════════════════════════════
# 位置信息
# ══════════════════════════════════════════════════════════════

@dataclass
class Position:
    line: int = 0
    column: int = 0
    end_line: int = 0
    end_column: int = 0

    def to_dict(self) -> dict:
        return {
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
        }


# ══════════════════════════════════════════════════════════════
# 基础节点
# ══════════════════════════════════════════════════════════════

class ASTNode:
    """所有 AST 节点的基类"""
    def __init__(self, pos: Optional[Position] = None):
        self.pos = pos or Position()


# ══════════════════════════════════════════════════════════════
# 表达式
# ══════════════════════════════════════════════════════════════

class Expr(ASTNode):
    """表达式基类"""
    pass


@dataclass
class NumberLit(Expr):
    value: float = 0.0
    pos: Optional[Position] = None


@dataclass
class StringLit(Expr):
    value: str = ""
    pos: Optional[Position] = None


@dataclass
class BoolLit(Expr):
    value: bool = True
    pos: Optional[Position] = None


@dataclass
class Identifier(Expr):
    name: str = ""
    pos: Optional[Position] = None


@dataclass
class QuantumStateExpr(Expr):
    """量子态: |name⟩ 或 |name⟩ * amp"""
    name: str = ""
    amplitude: Optional[Expr] = None
    pos: Optional[Position] = None


@dataclass
class StateSuperposition(Expr):
    """态叠加: |a⟩ * 0.8 + |b⟩ * 0.3"""
    terms: List[QuantumStateExpr] = field(default_factory=list)
    pos: Optional[Position] = None


@dataclass
class BinaryOp(Expr):
    op: str = ""
    left: Optional[Expr] = None
    right: Optional[Expr] = None
    pos: Optional[Position] = None


@dataclass
class FuncCall(Expr):
    name: str = ""
    args: List[Expr] = field(default_factory=list)
    kwargs: Dict[str, Expr] = field(default_factory=dict)  # key = value 形式（注解/命名参数）
    pos: Optional[Position] = None


# ══════════════════════════════════════════════════════════════
# 声明
# ══════════════════════════════════════════════════════════════

@dataclass
class CreatorImprint(ASTNode):
    """@creator 印记 — 编译期强制"""
    name: str = ""
    title: str = ""
    imprint: str = ""
    date: str = ""
    raw: Dict[str, str] = field(default_factory=dict)
    pos: Optional[Position] = None


@dataclass
class QStateDecl(ASTNode):
    """qstate name = superposition"""
    name: str = ""
    type_anno: str = ""
    value: Optional[Expr] = None
    pos: Optional[Position] = None


@dataclass
class SourceSpec(ASTNode):
    """@source(channel: target[, min_confidence=n]) — 事实验证通道

    channel: world | axiom | verify | memory
    """
    channel: str = ""
    target: str = ""
    min_confidence: float = 0.0
    pos: Optional[Position] = None


@dataclass
class FactDecl(ASTNode):
    """fact name = expr [@source(...)] — 事实断言

    事实与认知状态（⟨state⟩）类型分离：
    事实必须有验证通道来源，否则编译错误 E7001。
    """
    name: str = ""
    value: Optional[Expr] = None
    source: Optional[SourceSpec] = None
    pos: Optional[Position] = None


@dataclass
class ConceptDecl(ASTNode):
    """concept Name { key: value, ... }"""
    name: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    pos: Optional[Position] = None


@dataclass
class WorldDecl(ASTNode):
    """world { read: [x], write: [y] }"""
    read: List[str] = field(default_factory=list)
    write: List[str] = field(default_factory=list)
    pos: Optional[Position] = None


@dataclass
class FnDecl(ASTNode):
    """fn name(params) -> ret { body } [test { assert ... }]"""
    name: str = ""
    params: List[Tuple[str, str]] = field(default_factory=list)
    return_type: str = ""
    body: List[ASTNode] = field(default_factory=list)
    tests: List[ASTNode] = field(default_factory=list)
    pos: Optional[Position] = None


@dataclass
class LetDecl(ASTNode):
    """let name[: type] = expr"""
    name: str = ""
    type_anno: str = ""
    value: Optional[Expr] = None
    pos: Optional[Position] = None


@dataclass
class AssignStmt(ASTNode):
    """name = expr"""
    name: str = ""
    value: Optional[Expr] = None
    pos: Optional[Position] = None


@dataclass
class ImportStmt(ASTNode):
    """import "path" [as alias]"""
    path: str = ""
    alias: str = ""
    pos: Optional[Position] = None


@dataclass
class TypeAnno(ASTNode):
    """type name = type_expr"""
    name: str = ""
    type_expr: str = ""
    pos: Optional[Position] = None


# ══════════════════════════════════════════════════════════════
# 认知原语
# ══════════════════════════════════════════════════════════════

@dataclass
class PerceiveStmt(ASTNode):
    """perceive |state⟩"""
    state: Optional[Expr] = None
    pos: Optional[Position] = None


@dataclass
class SelectStmt(ASTNode):
    """select need_name = expr"""
    need_name: str = ""
    value: Optional[Expr] = None
    pos: Optional[Position] = None


@dataclass
class IntegrateStmt(ASTNode):
    """integrate param = expr"""
    param: str = ""
    value: Optional[Expr] = None
    pos: Optional[Position] = None


@dataclass
class ActStmt(ASTNode):
    """act name(args)"""
    name: str = ""
    args: List[Expr] = field(default_factory=list)
    pos: Optional[Position] = None


@dataclass
class LearnStmt(ASTNode):
    """learn("content", importance=0.9, source=creator, kind=identity,
            confidence=1.0, causal_parents=[mem_1])

    记忆写入契约 R1-R6（契约层 P2）:
      R1 无来源 = 拒绝写入 (E7101)
      R2 kind 必填且合法 (E7102)
      R3 importance ∈ [0,1] (E7103)
      R4 因果父链缺失默认 [root] (合法)；提供时格式检查
      R5 写入遵守 world 声明 (E3xxx)
      R6 llm 来源 confidence ≤ 0.5 (E7106)
    """
    content: str = ""
    importance: float = 0.5
    source: str = ""            # creator|world|memory|verify|llm
    kind: str = ""              # identity|fact|event|skill|relation|reflection
    confidence: float = 0.0
    causal_parents: List[str] = field(default_factory=list)
    pos: Optional[Position] = None


@dataclass
class RememberStmt(ASTNode):
    """remember(query, k=n)"""
    query: Optional[Expr] = None
    k: int = 5
    pos: Optional[Position] = None


@dataclass
class EntangleStmt(ASTNode):
    """entangle |a⟩ ~ |b⟩"""
    left: str = ""
    right: str = ""
    pos: Optional[Position] = None


@dataclass
class AmplifyStmt(ASTNode):
    """amplify |state⟩ [* n]"""
    state: str = ""
    factor: Optional[Expr] = None
    pos: Optional[Position] = None


@dataclass
class ObserveStmt(ASTNode):
    """observe { on collapse { emit log(...) } }"""
    body: List[ASTNode] = field(default_factory=list)
    pos: Optional[Position] = None


@dataclass
class EmitStmt(ASTNode):
    """emit log("...")"""
    target: str = ""
    args: List[Expr] = field(default_factory=list)
    pos: Optional[Position] = None


@dataclass
class CycleStmt(ASTNode):
    """[annotation] cycle name { ... }"""
    name: str = ""
    body: List[ASTNode] = field(default_factory=list)
    annotation: str = ""
    annotation_args: Dict[str, str] = field(default_factory=dict)
    pos: Optional[Position] = None


@dataclass
class IfStmt(ASTNode):
    """if expr { ... } else { ... }"""
    cond: Optional[Expr] = None
    then_body: List[ASTNode] = field(default_factory=list)
    else_body: List[ASTNode] = field(default_factory=list)
    pos: Optional[Position] = None


@dataclass
class AssertStmt(ASTNode):
    """assert expr"""
    expr: Optional[Expr] = None
    pos: Optional[Position] = None


# ══════════════════════════════════════════════════════════════
# v4.1+ 新增节点：世界查询 / 因果 / 对齐 / 预算 / 认知类型
# ══════════════════════════════════════════════════════════════

@dataclass
class QueryStmt(ASTNode):
    """query { type, relation, confidence } — 世界模型声明式查询"""
    entity_type: str = ""
    relation_with: str = ""
    relation_kind: str = ""
    min_confidence: float = 0.0
    limit: int = 10
    target: str = "result"   # let 目标变量名
    pos: Optional[Position] = None


@dataclass
class DoStmt(ASTNode):
    """do(set(...)) — 因果干预"""
    action: str = ""         # set / remove / create
    target: str = ""
    value: str = ""
    target_var: str = "effect"
    pos: Optional[Position] = None


@dataclass
class WhatIfStmt(ASTNode):
    """what_if(cond) — 反事实推演"""
    condition: str = ""
    target_var: str = "counterfactual"
    pos: Optional[Position] = None


@dataclass
class AlignedAnno(ASTNode):
    """@aligned(constitution=..., max_free_energy=..., refusal_rights=...) — 对齐注解"""
    constitution: str = ""
    max_free_energy: float = 0.0
    refusal_rights: bool = False
    max_uncertainty: float = 0.0
    pos: Optional[Position] = None


@dataclass
class BudgetAnno(ASTNode):
    """@budget(tokens=..., compute_ms=..., memory_ops=...) — 预算注解"""
    tokens: int = 0
    compute_ms: int = 0
    memory_ops: int = 0
    max_cycles: int = 0
    pos: Optional[Position] = None


@dataclass
class CognitiveTypeDecl(ASTNode):
    """认知类型声明: type x = ⟨belief⟩ / ⟨need⟩ / ⟨emotion⟩ / ⟨memory⟩ / ⟨focus⟩"""
    name: str = ""
    cognitive_type: str = ""   # belief / need / emotion / memory / focus
    dims: int = 0               # 维度（emotion=8, 默认0）
    bounds: Tuple[float, float] = (0.0, 1.0)  # 值域
    pos: Optional[Position] = None


@dataclass
class BeliefLit(Expr):
    """belief(proposition, confidence) — 信念字面量"""
    proposition: str = ""
    confidence: float = 0.5
    pos: Optional[Position] = None


@dataclass
class NeedLit(Expr):
    """need(name, alpha, beta) — 需求分布（Beta）"""
    name: str = ""
    alpha: float = 8.0
    beta: float = 4.0
    pos: Optional[Position] = None


@dataclass
class IntrospectStmt(ASTNode):
    """@introspect fn describe_self() — 自我描述（元编程）"""
    fn_name: str = ""
    pos: Optional[Position] = None


# ══════════════════════════════════════════════════════════════
# 程序根节点
# ══════════════════════════════════════════════════════════════

@dataclass
class PsiLangProgram(ASTNode):
    """PsiLang 程序根节点"""
    filename: str = ""
    creator: Optional[CreatorImprint] = None
    statements: List[ASTNode] = field(default_factory=list)
    pos: Optional[Position] = None
