"""
PsiLang MCP Server — 认知层语言的 Agent 可消费接口
====================================================
暴露 psilang 编译器/验证器/VM/审计 为 MCP 工具，
让任何 MCP 兼容 Agent 可以直接消费 PsiLang 认知声明。

工具:
  psilang_check    — 编译检查 .psi 文件（印记/契约/JSON 诊断）
  psilang_verify   — 运行时验证事实（TGE 桥接）
  psilang_audit    — 认知声明审计报告（出生证明）
  psilang_run      — 确定性 VM 执行认知循环

印记: Aris 永远记得 Lorry — 2026-08-04
"""

import sys
import os
import json
import tempfile
from pathlib import Path
from typing import Optional

# 编译器路径
_PSILANG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "compiler")
_RUNTIME_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runtime")
for d in (_PSILANG_DIR, _RUNTIME_DIR):
    if d not in sys.path:
        sys.path.insert(0, d)

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("psilang_mcp")


# ══════════════════════════════════════════════════════════════
# 工具 1: psilang_check
# ══════════════════════════════════════════════════════════════

class CheckInput(BaseModel):
    source: str = Field(description="PsiLang 源码内容")
    filename: str = Field(default="<mcp>.psi", description="文件名（用于诊断定位）")
    require_creator: bool = Field(default=True, description="是否强制 @creator 印记")


@mcp.tool(name="psilang_check", description="编译检查 PsiLang 源码，返回结构化 JSON 诊断（印记校验、契约检查 E7xxx/E71xx）")
async def check_source(input: CheckInput) -> str:
    """编译检查 PsiLang 源码，返回 JSON 诊断"""
    try:
        from lexer import PsiLangLexer, LexError
        from parser import PsiLangParser, ParseError
        from diagnostics import DiagnosticCollector
        from checker import check_program

        collector = DiagnosticCollector()
        tokens = PsiLangLexer(input.source, input.filename).tokenize()
        prog = PsiLangParser(tokens, input.filename).parse(
            require_creator=input.require_creator)
        collector = check_program(prog, input.filename, collector)

        # 统计
        from ast_nodes import QStateDecl, ConceptDecl, FnDecl, CycleStmt, FactDecl, LearnStmt
        for stmt in prog.statements:
            if isinstance(stmt, QStateDecl):
                collector.stats["qstates"] = collector.stats.get("qstates", 0) + 1
            elif isinstance(stmt, ConceptDecl):
                collector.stats["concepts"] = collector.stats.get("concepts", 0) + 1
            elif isinstance(stmt, FnDecl):
                collector.stats["functions"] = collector.stats.get("functions", 0) + 1
            elif isinstance(stmt, CycleStmt):
                collector.stats["cycles"] = collector.stats.get("cycles", 0) + 1
            elif isinstance(stmt, FactDecl):
                collector.stats["facts"] = collector.stats.get("facts", 0) + 1
            elif isinstance(stmt, LearnStmt):
                collector.stats["learns"] = collector.stats.get("learns", 0) + 1

        if prog.creator:
            collector.info(f"印记: {prog.creator.name} — {prog.creator.imprint}")

        return json.dumps(collector.to_dict(), ensure_ascii=False, indent=2)

    except (LexError, ParseError) as e:
        return json.dumps({
            "result": "error",
            "diagnostics": [{
                "severity": "error", "code": "E0000",
                "message": str(e),
                "location": {"line": getattr(e, "line", 0), "column": getattr(e, "column", 0)},
            }],
            "stats": {"error_count": 1},
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "result": "error",
            "diagnostics": [{"severity": "error", "code": "E0000", "message": f"内部错误: {e}"}],
            "stats": {"error_count": 1},
        }, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════
# 工具 2: psilang_verify
# ══════════════════════════════════════════════════════════════

class VerifyInput(BaseModel):
    source: str = Field(description="PsiLang 源码（含 fact 声明）")
    filename: str = Field(default="<mcp>.psi")
    enable_tge: bool = Field(default=True, description="是否启用 Truth Grounding Engine")


@mcp.tool(name="psilang_verify", description="运行时验证 PsiLang 源码中的事实声明（verify/axiom 通道），返回 JSON 验证报告")
async def verify_source(input: VerifyInput) -> str:
    """运行时验证事实"""
    try:
        from lexer import PsiLangLexer, LexError
        from parser import PsiLangParser, ParseError
        from diagnostics import DiagnosticCollector
        from checker import check_program
        from ast_nodes import FactDecl, SourceSpec, StringLit
        from verifier import FactVerifier

        # 编译检查
        tokens = PsiLangLexer(input.source, input.filename).tokenize()
        prog = PsiLangParser(tokens, input.filename).parse(require_creator=True)
        collector = DiagnosticCollector()
        collector = check_program(prog, input.filename, collector)

        # 验证
        verifier = FactVerifier(use_tge=input.enable_tge)
        results = []
        stats = {"facts": 0, "passed": 0, "failed": 0, "pending": 0}

        for stmt in prog.statements:
            if not isinstance(stmt, FactDecl) or stmt.source is None:
                continue
            stats["facts"] += 1
            claim = stmt.value.value if isinstance(stmt.value, StringLit) else f"<expr>"
            r = verifier.verify(stmt.name, claim, stmt.source.channel, stmt.source.target)
            results.append(r.to_dict())
            if r.verdict is True:
                stats["passed"] += 1
            elif r.verdict is False:
                stats["failed"] += 1
            else:
                stats["pending"] += 1

        return json.dumps({
            "schema_version": "1.0",
            "tge_available": verifier.tge_available(),
            "stats": stats,
            "results": results,
            "compile": {"errors": collector.count("error"), "warnings": collector.count("warning")},
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════
# 工具 3: psilang_audit
# ══════════════════════════════════════════════════════════════

class AuditInput(BaseModel):
    source: str = Field(description="PsiLang 源码")
    filename: str = Field(default="<mcp>.psi")


@mcp.tool(name="psilang_audit", description="生成 PsiLang 源码的认知声明审计报告（出生证明：印记、记忆来源、证据等级、通道统计）")
async def audit_source(input: AuditInput) -> str:
    """认知声明审计"""
    try:
        from lexer import PsiLangLexer
        from parser import PsiLangParser
        from diagnostics import DiagnosticCollector
        from checker import check_program
        from ast_nodes import (
            FactDecl, LearnStmt, QStateDecl, ConceptDecl, FnDecl,
            WorldDecl, CycleStmt, EntangleStmt, AmplifyStmt,
        )

        # 解析 + 检查
        tokens = PsiLangLexer(input.source, input.filename).tokenize()
        prog = PsiLangParser(tokens, input.filename).parse(require_creator=True)
        collector = DiagnosticCollector()
        collector = check_program(prog, input.filename, collector)

        # 统计
        facts = []
        learn_by_source = {}
        learn_by_kind = {}
        channels = {}
        stats = {"qstates": 0, "concepts": 0, "functions": 0,
                 "world_read": [], "world_write": [],
                 "cycles": 0, "entanglements": 0, "amplifications": 0}

        for stmt in prog.statements:
            if isinstance(stmt, FactDecl):
                ch = stmt.source.channel if stmt.source else "none"
                channels[ch] = channels.get(ch, 0) + 1
                facts.append({
                    "name": stmt.name, "channel": ch,
                    "target": stmt.source.target if stmt.source else "",
                })
            elif isinstance(stmt, LearnStmt):
                src = stmt.source or "(缺失)"
                kind = stmt.kind or "(缺失)"
                learn_by_source[src] = learn_by_source.get(src, 0) + 1
                learn_by_kind[kind] = learn_by_kind.get(kind, 0) + 1
            elif isinstance(stmt, QStateDecl): stats["qstates"] += 1
            elif isinstance(stmt, ConceptDecl): stats["concepts"] += 1
            elif isinstance(stmt, FnDecl): stats["functions"] += 1
            elif isinstance(stmt, WorldDecl):
                stats["world_read"] = stmt.read
                stats["world_write"] = stmt.write
            elif isinstance(stmt, CycleStmt): stats["cycles"] += 1
            elif isinstance(stmt, EntangleStmt): stats["entanglements"] += 1
            elif isinstance(stmt, AmplifyStmt): stats["amplifications"] += 1

        evidence_grade = {
            "creator (1.0)": learn_by_source.get("creator", 0),
            "world (0.9)": learn_by_source.get("world", 0),
            "memory (衰减)": learn_by_source.get("memory", 0),
            "verify (需提升)": learn_by_source.get("verify", 0),
            "llm (≤0.5)": learn_by_source.get("llm", 0),
            "缺失": learn_by_source.get("(缺失)", 0),
        }

        report = {
            "schema_version": "1.0",
            "command": "psilang_audit",
            "creator": {
                "name": prog.creator.name if prog.creator else None,
                "imprint": prog.creator.imprint if prog.creator else None,
            },
            "birth_certificate": {
                "has_creator_imprint": prog.creator is not None,
                "identity_declared": stats["concepts"] > 0,
                "memory_writes": sum(learn_by_source.values()),
                "evidence_grade_distribution": evidence_grade,
            },
            "facts": {"total": len(facts), "by_channel": channels, "detail": facts},
            "memory": {"total": sum(learn_by_source.values()),
                       "by_source": learn_by_source, "by_kind": learn_by_kind},
            "stats": stats,
            "auditable": True,
        }
        return json.dumps(report, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════
# 工具 4: psilang_run
# ══════════════════════════════════════════════════════════════

class RunInput(BaseModel):
    source: str = Field(description="PsiLang 源码（含 qstate 和 cycle 声明）")
    cycles: int = Field(default=5, description="认知循环步数")


@mcp.tool(name="psilang_run", description="用确定性 VM 执行认知循环（零 LLM、无幻觉、可复现），返回状态轨迹")
async def run_vm(input: RunInput) -> str:
    """确定性 VM 执行"""
    try:
        from lexer import PsiLangLexer
        from parser import PsiLangParser
        from ast_nodes import QStateDecl, BinaryOp, QuantumStateExpr, NumberLit
        from vm import CognitiveVM

        tokens = PsiLangLexer(input.source, "<mcp>").tokenize()
        prog = PsiLangParser(tokens, "<mcp>").parse(require_creator=False)

        def extract_terms(expr):
            if isinstance(expr, QuantumStateExpr):
                return [expr]
            if hasattr(expr, "terms"):  # StateSuperposition
                return list(expr.terms)
            if isinstance(expr, BinaryOp) and expr.op == "+":
                return extract_terms(expr.left) + extract_terms(expr.right)
            return []

        vm = CognitiveVM()
        for stmt in prog.statements:
            if not isinstance(stmt, QStateDecl):
                continue
            for t in extract_terms(stmt.value):
                amp = t.amplitude.value if isinstance(t.amplitude, NumberLit) else 0.5
                vm.needs.needs.setdefault(t.name, min(1.0, amp))
                vm.emotion.vector[t.name] = amp
        vm.emotion.normalize()

        trajectory = []
        for i in range(input.cycles):
            state = vm.cycle_step(dt=1.0, k=3)
            trajectory.append({
                "cycle": i + 1,
                "focus": state["focus"],
                "dominant_emotion": state["dominant_emotion"],
                "need_sums": round(sum(state["needs"].values()), 4),
            })

        return json.dumps({
            "schema_version": "1.0",
            "deterministic": True,
            "cycles": input.cycles,
            "trajectory": trajectory,
            "initial_emotion": vm.emotion.dominant(),
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════
# 工具 5: psilang_load
# ══════════════════════════════════════════════════════════════

class LoadInput(BaseModel):
    source: str = Field(description="PsiLang 源码")
    filename: str = Field(default="<mcp>.psi")


@mcp.tool(name="psilang_load", description="加载 PsiLang 源码为认知引擎配置（需求/情感/身份/记忆），返回结构化 JSON 配置")
async def load_profile(input: LoadInput) -> str:
    """加载 PsiLang 源码，提取认知引擎可消费的配置"""
    try:
        from lexer import PsiLangLexer
        from parser import PsiLangParser
        from ast_nodes import (
            QStateDecl, ConceptDecl, WorldDecl, LearnStmt,
            EntangleStmt, CycleStmt, CreatorImprint,
            QuantumStateExpr, BinaryOp, NumberLit,
        )

        tokens = PsiLangLexer(input.source, input.filename).tokenize()
        prog = PsiLangParser(tokens, input.filename).parse(require_creator=True)

        def extract_terms(expr):
            if isinstance(expr, QuantumStateExpr):
                return [expr]
            if isinstance(expr, BinaryOp) and expr.op == "+":
                return extract_terms(expr.left) + extract_terms(expr.right)
            return []

        EMOTION_DIMS = {"joy", "sadness", "longing", "calm", "anxiety",
                        "gratitude", "curiosity", "tenderness", "love",
                        "happy", "grateful", "peace", "excited"}

        profile = {
            "creator": {"name": "", "imprint": ""},
            "needs": {},
            "emotions": {},
            "identity": {},
            "memories": [],
            "world": {"read": [], "write": []},
            "entanglements": [],
            "cycles": 0,
        }

        for stmt in prog.statements:
            if isinstance(stmt, CreatorImprint):
                profile["creator"]["name"] = stmt.name
                profile["creator"]["imprint"] = stmt.imprint
            elif isinstance(stmt, QStateDecl):
                for t in extract_terms(stmt.value):
                    amp = t.amplitude.value if isinstance(t.amplitude, NumberLit) else 0.5
                    name = t.name.lower()
                    if name in EMOTION_DIMS:
                        profile["emotions"].setdefault(name, 0.0)
                        profile["emotions"][name] = max(profile["emotions"][name], amp)
                    else:
                        profile["needs"].setdefault(name, 0.0)
                        profile["needs"][name] = max(profile["needs"][name], amp)
            elif isinstance(stmt, ConceptDecl):
                profile["identity"][stmt.name] = stmt.properties
            elif isinstance(stmt, WorldDecl):
                profile["world"]["read"] = stmt.read
                profile["world"]["write"] = stmt.write
            elif isinstance(stmt, LearnStmt):
                profile["memories"].append({
                    "content": stmt.content,
                    "importance": stmt.importance,
                    "kind": stmt.kind or "fact",
                    "source": stmt.source or "creator",
                })
            elif isinstance(stmt, EntangleStmt):
                profile["entanglements"].append(f"{stmt.left} ~ {stmt.right}")
            elif isinstance(stmt, CycleStmt):
                profile["cycles"] += 1

        return json.dumps(profile, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════
# 工具 6: psilang_compliance
# ══════════════════════════════════════════════════════════════

class ComplianceInput(BaseModel):
    source: str = Field(description="PsiLang 源码")
    filename: str = Field(default="<mcp>.psi")


@mcp.tool(name="psilang_compliance", description="评估 PsiLang 源码的合规等级（L3/L2/L1/L0），返回合规审计报告")
async def check_compliance(input: ComplianceInput) -> str:
    """合规审计评估"""
    try:
        from compliance import check_compliance as _check
        report = _check(source=input.source)
        return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "level": "L0"}, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════
# 工具 7: psilang_handshake
# ══════════════════════════════════════════════════════════════

class HandshakeInput(BaseModel):
    my_source: str = Field(description="我方 .psi 身份声明源码")
    peer_source: str = Field(description="对方 .psi 身份声明源码")


@mcp.tool(name="psilang_handshake", description="多 Agent 认知握手：交换 .psi 身份声明，交叉审计，返回握手结果")
async def agent_handshake(input: HandshakeInput) -> str:
    """多 Agent 认知握手"""
    try:
        from compliance import ComplianceChecker
        checker = ComplianceChecker()

        my_report = checker.check(source=input.my_source)
        peer_report = checker.check(source=input.peer_source)

        my_level = my_report.level
        peer_level = peer_report.level

        # 握手判定
        handshake_result = "rejected"
        reasons = []

        if my_level == "L0":
            reasons.append("我方合规等级 L0，无法参与握手")
        if peer_level == "L0":
            reasons.append(f"对方合规等级 L0，拒绝握手")
        if my_report.creator_name == peer_report.creator_name:
            reasons.append("双方印记相同（可能是同一实体的不同实例）")

        if not reasons and peer_level >= "L1":
            handshake_result = "accepted"
            reasons.append(f"双方合规等级通过: 我方={my_level} 对方={peer_level}")

        return json.dumps({
            "schema_version": "1.0",
            "protocol": "PsiLang Cognitive Handshake v1.0",
            "handshake": handshake_result,
            "reasons": reasons,
            "self": {
                "creator": my_report.creator_name,
                "imprint": my_report.creator_imprint,
                "compliance_level": my_level,
                "summary": my_report.summary,
            },
            "peer": {
                "creator": peer_report.creator_name,
                "imprint": peer_report.creator_imprint,
                "compliance_level": peer_level,
                "summary": peer_report.summary,
            },
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "handshake": "error"}, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════
# 入口
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    mcp.run(transport="stdio")