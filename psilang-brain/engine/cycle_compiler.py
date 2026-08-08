"""
PsiLang Cycle Compiler — 将 cycle 声明编译为可执行操作序列
============================================================
把认知循环从"声明"变成"可执行计划"：

  cycle think {
      perceive |input⟩              → LLM 操作
      select focus = vm.attention()  → VM 操作（确定性）
      integrate state = vm.update()  → VM 操作（确定性）
      act { reply(context) }         → LLM 操作
  }

编译后：
  [Perceive, VmSelect, VmIntegrate, Act] — 可被 VM 逐条执行

印记: Aris 永远记得 Lorry — 2026-08-04
"""

import sys
import os
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable

# 编译器路径
_PSILANG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "psilang-standards")
for _d in [os.path.join(_PSILANG_DIR, "compiler"), os.path.join(_PSILANG_DIR, "runtime")]:
    if _d not in sys.path:
        sys.path.insert(0, _d)


@dataclass
class CycleOp:
    """一条认知循环操作"""
    op: str                          # perceive | select | integrate | act | learn | remember
    exec_type: str                   # vm | llm | hybrid
    params: Dict[str, Any] = field(default_factory=dict)
    source_line: int = 0

    def to_dict(self) -> Dict:
        return {
            "op": self.op,
            "exec_type": self.exec_type,
            "params": self.params,
        }


@dataclass
class CyclePlan:
    """编译后的认知循环执行计划"""
    name: str
    ops: List[CycleOp] = field(default_factory=list)
    source_file: str = ""

    def to_dict(self) -> Dict:
        return {
            "cycle": self.name,
            "source": self.source_file,
            "steps": len(self.ops),
            "vm_steps": sum(1 for o in self.ops if o.exec_type == "vm"),
            "llm_steps": sum(1 for o in self.ops if o.exec_type == "llm"),
            "plan": [o.to_dict() for o in self.ops],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class CycleCompiler:
    """将 cycle 声明编译为可执行计划"""

    # VM 可执行的操作（确定性）
    VM_OPS = {"select", "integrate", "remember"}

    # LLM 需要的操作（语义）
    LLM_OPS = {"perceive", "act", "learn"}

    def compile(self, source: str, filename: str = "") -> List[CyclePlan]:
        """从 PsiLang 源码编译所有 cycle 声明"""
        from lexer import PsiLangLexer
        from parser import PsiLangParser
        from ast_nodes import (
            CycleStmt, PerceiveStmt, SelectStmt, IntegrateStmt,
            ActStmt, LearnStmt, RememberStmt, QuantumStateExpr,
            FuncCall, Identifier, StringLit, NumberLit,
        )

        tokens = PsiLangLexer(source, filename).tokenize()
        prog = PsiLangParser(tokens, filename).parse(require_creator=False)

        plans = []
        for stmt in prog.statements:
            if not isinstance(stmt, CycleStmt):
                continue
            plan = self._compile_cycle(stmt, filename)
            plans.append(plan)

        return plans

    def compile_ast(self, cycle_stmt: "CycleStmt", filename: str = "") -> CyclePlan:
        """从 AST 节点编译 cycle"""
        return self._compile_cycle(cycle_stmt, filename)

    def _compile_cycle(self, stmt, filename: str) -> CyclePlan:
        plan = CyclePlan(name=stmt.name, source_file=filename)

        for i, body_stmt in enumerate(stmt.body):
            op = self._compile_op(stmt.name, body_stmt, i)
            if op:
                plan.ops.append(op)

        # 验证计划完整性
        self._validate(plan)

        return plan

    def _compile_op(self, cycle_name: str, stmt, index: int) -> Optional[CycleOp]:
        """编译单条认知操作"""
        from ast_nodes import (
            PerceiveStmt, SelectStmt, IntegrateStmt,
            ActStmt, LearnStmt, RememberStmt,
            QuantumStateExpr, FuncCall, Identifier, StringLit,
        )

        # perceive |state⟩
        if isinstance(stmt, PerceiveStmt):
            state_name = ""
            if isinstance(stmt.state, QuantumStateExpr):
                state_name = stmt.state.name
            return CycleOp(
                op="perceive",
                exec_type="llm",
                params={"state": state_name or "input"},
                source_line=getattr(stmt, "pos", None).line if hasattr(stmt, "pos") else 0,
            )

        # select name = expr
        if isinstance(stmt, SelectStmt):
            return CycleOp(
                op="select",
                exec_type="vm",
                params={"name": stmt.need_name or "focus", "value": self._expr_to_str(stmt.value)},
                source_line=getattr(stmt, "pos", None).line if hasattr(stmt, "pos") else 0,
            )

        # integrate name = expr
        if isinstance(stmt, IntegrateStmt):
            return CycleOp(
                op="integrate",
                exec_type="vm",
                params={"name": stmt.param or "state", "value": self._expr_to_str(stmt.value)},
                source_line=getattr(stmt, "pos", None).line if hasattr(stmt, "pos") else 0,
            )

        # act name(args)
        if isinstance(stmt, ActStmt):
            args = [self._expr_to_str(a) for a in stmt.args]
            return CycleOp(
                op="act",
                exec_type="llm",
                params={"name": stmt.name, "args": args},
                source_line=getattr(stmt, "pos", None).line if hasattr(stmt, "pos") else 0,
            )

        # learn("content", ...)
        if isinstance(stmt, LearnStmt):
            return CycleOp(
                op="learn",
                exec_type="llm",
                params={
                    "content": stmt.content,
                    "importance": stmt.importance,
                    "source": stmt.source or "llm",
                    "kind": stmt.kind or "reflection",
                },
                source_line=getattr(stmt, "pos", None).line if hasattr(stmt, "pos") else 0,
            )

        # remember(query, k=n)
        if isinstance(stmt, RememberStmt):
            query = self._expr_to_str(stmt.query)
            return CycleOp(
                op="remember",
                exec_type="vm",
                params={"query": query, "k": stmt.k},
                source_line=getattr(stmt, "pos", None).line if hasattr(stmt, "pos") else 0,
            )

        return None

    def _expr_to_str(self, expr) -> str:
        """表达式转字符串表示"""
        if expr is None:
            return ""
        from ast_nodes import (
            Identifier, StringLit, NumberLit, BoolLit,
            QuantumStateExpr, FuncCall,
        )
        if isinstance(expr, Identifier):
            return expr.name
        if isinstance(expr, StringLit):
            return f'"{expr.value}"'
        if isinstance(expr, NumberLit):
            return str(expr.value)
        if isinstance(expr, BoolLit):
            return "true" if expr.value else "false"
        if isinstance(expr, QuantumStateExpr):
            name = expr.name
            if expr.amplitude:
                amp = self._expr_to_str(expr.amplitude)
                return f"|{name}⟩ * {amp}"
            return f"|{name}⟩"
        if isinstance(expr, FuncCall):
            args = ", ".join(self._expr_to_str(a) for a in expr.args)
            kwargs = ", ".join(f"{k}={self._expr_to_str(v)}" for k, v in expr.kwargs.items())
            all_args = ", ".join(filter(None, [args, kwargs]))
            return f"{expr.name}({all_args})"
        return str(expr)

    def _validate(self, plan: CyclePlan):
        """验证计划完整性"""
        if not plan.ops:
            return

        # 第一条必须是 perceive（感知输入）
        if plan.ops[0].op != "perceive":
            raise ValueError(f"cycle '{plan.name}' 第一条必须是 perceive")


# ══════════════════════════════════════════════════════════════
# 快捷入口
# ══════════════════════════════════════════════════════════════

def compile_source(source: str, filename: str = "") -> List[CyclePlan]:
    return CycleCompiler().compile(source, filename)


def compile_file(path: str) -> List[CyclePlan]:
    with open(path, "r", encoding="utf-8") as f:
        return CycleCompiler().compile(f.read(), path)