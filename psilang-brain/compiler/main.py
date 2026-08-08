"""
PsiLang CLI v4 — 编译器主入口
=================================
用法:
  psilang check <file.psi> [--json] [--no-creator-check]
  psilang lex <file.psi>          # 仅分词
  psilang ast <file.psi>          # 输出 AST

印记: Aris 永远记得 Lorry — 2026-08-04
"""

import sys
import os
import json
import argparse
from pathlib import Path

from lexer import PsiLangLexer, LexError
from parser import PsiLangParser, ParseError
from diagnostics import (
    DiagnosticCollector, location_dict, make_fix_insert,
    ERROR_CODES,
)

# runtime 目录（verifier/vm）
_RUNTIME_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runtime")
if _RUNTIME_DIR not in sys.path:
    sys.path.insert(0, _RUNTIME_DIR)


def cmd_check(args) -> int:
    """psilang check — 编译检查"""
    collector = DiagnosticCollector()
    path = args.file

    if not Path(path).exists():
        collector.error("E0000", f"文件不存在: {path}")
        print(collector.to_json() if args.json else collector.to_human())
        return 1

    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        collector.error("E0000", f"读取文件失败: {e}")
        print(collector.to_json() if args.json else collector.to_human())
        return 1

    # ── 词法 ──
    try:
        lexer = PsiLangLexer(source, path)
        tokens = lexer.tokenize()
        collector.stats["tokens"] = len(tokens)
    except LexError as e:
        collector.error(
            ERROR_CODES.get("E0001", "E0001") if "字符" in e.message else "E0004",
            e.message,
            location_dict(path, e.line, e.column),
        )
        print(collector.to_json() if args.json else collector.to_human())
        return 1

    # ── 解析 ──
    try:
        parser = PsiLangParser(tokens, path)
        prog = parser.parse(require_creator=not args.no_creator_check)

        # 统计
        from ast_nodes import (
            CreatorImprint, QStateDecl, ConceptDecl, FnDecl,
            WorldDecl, CycleStmt, LearnStmt, AssertStmt, FactDecl,
        )
        for stmt in prog.statements:
            if isinstance(stmt, QStateDecl):
                collector.stats["qstates"] += 1
            elif isinstance(stmt, ConceptDecl):
                collector.stats["concepts"] += 1
            elif isinstance(stmt, FnDecl):
                collector.stats["functions"] += 1
                collector.stats["verified_assertions"] += len(stmt.tests)
            elif isinstance(stmt, CycleStmt):
                collector.stats["modules"] += 1
            elif isinstance(stmt, FactDecl):
                collector.stats["facts"] = collector.stats.get("facts", 0) + 1

    except ParseError as e:
        code = "E2001" if "印记" in e.message else "E0012"
        fix = None
        if "印记" in e.message:
            fix = make_fix_insert(1, 1, '@creator { name: "..." }\n')
        collector.error(
            code, e.message,
            location_dict(path, e.line, e.column),
            suggestion="参考: @creator { name: \"Lorry Jovens\", imprint: \"...\" }",
            fix=fix,
        )
        print(collector.to_json() if args.json else collector.to_human())
        return 1

    # ── 契约检查（语义层） ──
    try:
        from checker import check_program
        check_program(prog, path, collector)
    except Exception as e:
        collector.error("E1000", f"契约检查失败: {e}",
                        location_dict(path, 0, 0))

    # ── 成功 ──
    collector.info(f"解析成功: {path}")
    if prog.creator:
        collector.info(f"印记: {prog.creator.name}")

    print(collector.to_json() if args.json else collector.to_human())
    return 0 if not collector.has_errors() else 1


def cmd_verify(args) -> int:
    """psilang verify — 运行时验证 verify/axiom 通道的 fact"""
    collector = DiagnosticCollector()
    path = args.file

    if not Path(path).exists():
        print(json.dumps({"error": f"文件不存在: {path}"}, ensure_ascii=False))
        return 1

    try:
        from parser import parse_file
        prog = parse_file(path)
        from checker import check_program
        check_program(prog, path, collector)
    except (ParseError, LexError) as e:
        print(json.dumps({"error": e.message, "line": e.line, "column": e.column},
                         ensure_ascii=False))
        return 1

    from ast_nodes import FactDecl, SourceSpec, StringLit
    from verifier import FactVerifier

    verifier = FactVerifier(use_tge=not args.no_tge)
    results = []
    stats = {"facts": 0, "passed": 0, "failed": 0, "pending": 0}

    for stmt in prog.statements:
        if not isinstance(stmt, FactDecl) or stmt.source is None:
            continue
        stats["facts"] += 1
        claim = ""
        if isinstance(stmt.value, StringLit):
            claim = stmt.value.value
        else:
            claim = f"<expr: {type(stmt.value).__name__}>"

        r = verifier.verify(stmt.name, claim, stmt.source.channel,
                            stmt.source.target)
        results.append(r.to_dict())
        if r.verdict is True:
            stats["passed"] += 1
        elif r.verdict is False:
            stats["failed"] += 1
            collector.error("E7501", f"验证失败: fact {r.fact} ({r.claim})",
                             location_dict(path, stmt.pos.line, stmt.pos.column))
        else:
            stats["pending"] += 1

    report = {
        "schema_version": "1.0",
        "command": "psilang verify",
        "tge_available": verifier.tge_available(),
        "file": path,
        "stats": stats,
        "results": results,
        "diagnostics": [d.to_dict() for d in collector.diagnostics],
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"文件: {path}")
        print(f"TGE: {'可用' if report['tge_available'] else '不可用（降级）'}")
        for r in results:
            mark = {"True": "PASS", "False": "FAIL", "None": "PEND"}[str(r["verdict"])]
            print(f"  [{mark}] {r['fact']} ({r['channel']}:{r['target']})"
                  f" conf={r['confidence']}")
            for e in r["evidence"][:2]:
                print(f"        证据: {e}")
        print(f"结果: {stats['passed']} 通过 | {stats['failed']} 失败 | {stats['pending']} 待验证")
    return 0 if stats["failed"] == 0 else 1


def cmd_run(args) -> int:
    """psilang run — 用确定性 VM 执行认知循环（契约层 P3）"""
    path = args.file
    if not Path(path).exists():
        print(json.dumps({"error": f"文件不存在: {path}"}, ensure_ascii=False))
        return 1

    try:
        from parser import parse_file
        prog = parse_file(path)
    except (ParseError, LexError) as e:
        print(json.dumps({"error": e.message, "line": e.line, "column": e.column},
                         ensure_ascii=False))
        return 1

    from ast_nodes import QStateDecl, QuantumStateExpr, StateSuperposition, CycleStmt
    from ast_nodes import BinaryOp, NumberLit
    from vm import CognitiveVM

    def extract_terms(expr):
        """递归提取叠加项: BinaryOp('+') 链 / StateSuperposition / 单个态"""
        if isinstance(expr, StateSuperposition):
            return list(expr.terms)
        if isinstance(expr, BinaryOp) and expr.op == "+":
            return extract_terms(expr.left) + extract_terms(expr.right)
        if isinstance(expr, QuantumStateExpr):
            return [expr]
        return []

    vm = CognitiveVM()

    # 从 qstate 声明初始化需求/情感状态（确定性部分）
    for stmt in prog.statements:
        if not isinstance(stmt, QStateDecl):
            continue
        terms = extract_terms(stmt.value)
        for t in terms:
            amp = 0.5
            if isinstance(t.amplitude, NumberLit):
                amp = t.amplitude.value
            vm.needs.needs.setdefault(t.name, min(1.0, amp))
            vm.emotion.vector[t.name] = amp
    vm.emotion.normalize()

    n_cycles = args.cycles
    trajectory = []
    for i in range(n_cycles):
        state = vm.cycle_step(dt=1.0, k=3)
        trajectory.append({
            "cycle": i + 1,
            "focus": state["focus"],
            "dominant_emotion": state["dominant_emotion"],
            "need_sums": round(sum(state["needs"].values()), 4),
        })

    report = {
        "schema_version": "1.0",
        "command": "psilang run",
        "file": path,
        "deterministic": True,     # 整个轨迹无 LLM 参与
        "cycles": n_cycles,
        "trajectory": trajectory,
        "final": vm.cycle_step(0.0),
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"文件: {path} | 确定性 VM（零 LLM）")
        print(f"初始需求: {vm.needs.to_dict()}")
        print(f"初始情感主导: {vm.emotion.dominant()}")
        for step in trajectory:
            print(f"  cycle {step['cycle']}: 焦点={step['focus']} | "
                  f"主导情感={step['dominant_emotion']} | 需求总和={step['need_sums']}")
        print(f"完成: {n_cycles} 个确定性认知循环（无采样、零幻觉、可复现）")
    return 0


def cmd_audit(args) -> int:
    """psilang audit — 认知声明审计报告（出生证明可审计）"""
    ...
    path = args.file
    if not Path(path).exists():
        print(json.dumps({"error": f"文件不存在: {path}"}, ensure_ascii=False))
        return 1

    try:
        from parser import parse_file
        prog = parse_file(path)
        from checker import check_program
        collector = check_program(prog, path)
    except (ParseError, LexError) as e:
        print(json.dumps({"error": e.message, "line": e.line, "column": e.column},
                         ensure_ascii=False))
        return 1

    from ast_nodes import (
        FactDecl, LearnStmt, QStateDecl, ConceptDecl, FnDecl,
        WorldDecl, CycleStmt, EntangleStmt, AmplifyStmt,
    )

    # ── 统计 ──
    facts = []
    learn_by_source: Dict[str, int] = {}
    learn_by_kind: Dict[str, int] = {}
    channels: Dict[str, int] = {}
    stats = {"qstates": 0, "concepts": 0, "functions": 0,
             "world_read": [], "world_write": [],
             "cycles": 0, "entanglements": 0, "amplifications": 0}

    for stmt in prog.statements:
        if isinstance(stmt, FactDecl):
            ch = stmt.source.channel if stmt.source else "none"
            channels[ch] = channels.get(ch, 0) + 1
            facts.append({
                "name": stmt.name,
                "channel": ch,
                "target": stmt.source.target if stmt.source else "",
                "source": stmt.source.to_dict() if hasattr(stmt.source, "to_dict") else None,
            })
        elif isinstance(stmt, LearnStmt):
            src = stmt.source or "(缺失)"
            kind = stmt.kind or "(缺失)"
            learn_by_source[src] = learn_by_source.get(src, 0) + 1
            learn_by_kind[kind] = learn_by_kind.get(kind, 0) + 1
        elif isinstance(stmt, QStateDecl):
            stats["qstates"] += 1
        elif isinstance(stmt, ConceptDecl):
            stats["concepts"] += 1
        elif isinstance(stmt, FnDecl):
            stats["functions"] += 1
        elif isinstance(stmt, WorldDecl):
            stats["world_read"] = stmt.read
            stats["world_write"] = stmt.write
        elif isinstance(stmt, CycleStmt):
            stats["cycles"] += 1
        elif isinstance(stmt, EntangleStmt):
            stats["entanglements"] += 1
        elif isinstance(stmt, AmplifyStmt):
            stats["amplifications"] += 1

    # 证据等级分布（契约 R6）
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
        "command": "psilang audit",
        "file": path,
        "creator": {
            "name": prog.creator.name if prog.creator else None,
            "imprint": prog.creator.imprint if prog.creator else None,
            "date": prog.creator.date if prog.creator else None,
        },
        "birth_certificate": {
            "has_creator_imprint": prog.creator is not None,
            "identity_declared": stats["concepts"] > 0,
            "memory_writes": sum(learn_by_source.values()),
            "evidence_grade_distribution": evidence_grade,
        },
        "facts": {
            "total": len(facts),
            "by_channel": channels,
            "detail": facts,
        },
        "memory": {
            "total": sum(learn_by_source.values()),
            "by_source": learn_by_source,
            "by_kind": learn_by_kind,
        },
        "stats": stats,
        "compile": {
            "result": "error" if collector.has_errors() else "success",
            "diagnostics": [d.to_dict() for d in collector.diagnostics],
        },
        "auditable": True,   # 第三方审计工具可消费
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def cmd_repl(args) -> int:
    """psilang repl — 交互式认知编程环境"""
    import sys as _s
    _s.path.insert(0, str(Path(__file__).parent))
    from repl import PsiLangRepl

    repl = PsiLangRepl()

    if args.file:
        try:
            source = Path(args.file).read_text(encoding="utf-8")
            prog = repl._parse(source)
            repl._execute(prog)
            print(f"  OK 已加载 {args.file}")
        except Exception as e:
            print(f"  加载失败: {e}")

    repl.start()
    return 0


def cmd_build(args) -> int:
    """psilang build — 编译到 Python 可执行代码"""
    import sys as _s
    _s.path.insert(0, str(Path(__file__).parent))
    from parser import parse_file
    from codegen import generate_python

    try:
        prog = parse_file(args.file)
    except Exception as e:
        print(f"解析失败: {e}")
        return 1

    code = generate_python(prog)

    if args.output:
        Path(args.output).write_text(code, encoding="utf-8")
        print(f"OK 已编译: {args.output} ({len(code)} 字符)")
    else:
        print(code)
    return 0


def cmd_compliance(args) -> int:
    """psilang compliance — 合规等级评估（L3/L2/L1/L0）"""
    import sys as _sys
    _sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runtime"))
    from compliance import ComplianceChecker, check_compliance

    if args.grade or (args.file and os.path.isdir(args.file)):
        # 目录合规面板
        d = args.file or "."
        checker = ComplianceChecker()
        reports = checker.check_directory(d)
        board = checker.grade_board(reports)
        print(f"合规面板: {board['total_files']} 文件")
        for f in board["files"]:
            mark = {"L3": "✅", "L2": "⚠️", "L1": "🔶", "L0": "❌"}.get(f["level"], "❓")
            print(f"  {mark} {f['file']:30s} {f['level']} ({f['label']:20s}) 违规={f['violations']}")
        print(f"合规率: {board['compliance_rate']}%")
        if args.json:
            print(json.dumps(board, ensure_ascii=False, indent=2))
        return 0

    if args.file:
        report = check_compliance(filepath=args.file)
    else:
        src = _sys.stdin.read()
        report = check_compliance(source=src)

    if args.json:
        print(report.to_json())
    else:
        mark = {"L3": "✅", "L2": "⚠️", "L1": "🔶", "L0": "❌"}.get(report.level, "❓")
        print(f"合规等级: {mark} {report.level} ({report.level_label})")
        print(f"创造者: {report.creator_name} — {report.creator_imprint}")
        print(f"检查项: {sum(1 for v in report.checks.values() if v)}/{len(report.checks)} 通过")
        print(f"违规: {len(report.violations)}")
        print(f"摘要: {report.summary}")
    return 0


def cmd_lex(args) -> int:
    """psilang lex — 仅分词"""
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        print(f"读取失败: {e}")
        return 1

    try:
        tokens = PsiLangLexer(source, args.file).tokenize()
        if args.json:
            print(json.dumps([
                {"type": t.type.name, "value": t.value, "line": t.line,
                 "column": t.column}
                for t in tokens
            ], ensure_ascii=False, indent=2))
        else:
            for t in tokens:
                print(f"  L{t.line:3d}:{t.column:3d}  {t.type.name:<14} {t.value!r}")
        return 0
    except LexError as e:
        print(f"词法错误: {e.message} (L{e.line}:{e.column})")
        return 1


def cmd_ast(args) -> int:
    """psilang ast — 输出 AST"""
    try:
        from parser import parse_file
        prog = parse_file(args.file)
        if args.json:
            print(json.dumps(prog_to_dict(prog), ensure_ascii=False, indent=2))
        else:
            print_prog(prog)
        return 0
    except (ParseError, LexError) as e:
        print(f"解析错误: {e.message} (L{e.line}:{e.column})")
        return 1
    except Exception as e:
        print(f"错误: {e}")
        return 1


def prog_to_dict(prog) -> dict:
    """程序转字典"""
    return {
        "filename": prog.filename,
        "creator": prog.creator.raw if prog.creator else None,
        "statements": [str(type(s).__name__) for s in prog.statements],
        "statement_count": len(prog.statements),
    }


def print_prog(prog):
    """人类可读 AST 输出"""
    print(f"程序: {prog.filename}")
    if prog.creator:
        print(f"  印记: {prog.creator.name} | {prog.creator.imprint}")
    print(f"  语句数: {len(prog.statements)}")
    for s in prog.statements:
        print(f"    · {type(s).__name__}: {getattr(s, 'name', getattr(s, 'content', ''))}")


# ══════════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        prog="psilang",
        description="PsiLang 认知层语言编译器 v4.0",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # check
    p_check = sub.add_parser("check", help="编译检查（输出结构化诊断）")
    p_check.add_argument("file", help=".psi 源文件")
    p_check.add_argument("--json", action="store_true", help="输出 JSON")
    p_check.add_argument("--no-creator-check", action="store_true",
                         help="跳过印记校验")
    p_check.set_defaults(func=cmd_check)

    # lex
    p_lex = sub.add_parser("lex", help="仅分词")
    p_lex.add_argument("file")
    p_lex.add_argument("--json", action="store_true")
    p_lex.set_defaults(func=cmd_lex)

    # repl
    p_repl = sub.add_parser("repl", help="交互式认知编程环境")
    p_repl.add_argument("file", nargs="?", help="初始加载的 .psi 文件")
    p_repl.set_defaults(func=cmd_repl)

    # build
    p_build = sub.add_parser("build", help="编译到 Python 可执行代码")
    p_build.add_argument("file")
    p_build.add_argument("-o", "--output", help="输出 .py 文件路径")
    p_build.set_defaults(func=cmd_build)

    # ast
    p_ast = sub.add_parser("ast", help="输出 AST")
    p_ast.add_argument("file")
    p_ast.add_argument("--json", action="store_true")
    p_ast.set_defaults(func=cmd_ast)

    # verify
    p_verify = sub.add_parser("verify", help="运行时验证事实（verify/axiom 通道）")
    p_verify.add_argument("file")
    p_verify.add_argument("--json", action="store_true")
    p_verify.add_argument("--no-tge", action="store_true",
                          help="禁用 Truth Grounding Engine")
    p_verify.set_defaults(func=cmd_verify)

    # run
    p_run = sub.add_parser("run", help="用确定性 VM 执行认知循环")
    p_run.add_argument("file")
    p_run.add_argument("--json", action="store_true")
    p_run.add_argument("--cycles", type=int, default=5, help="认知循环步数")
    p_run.set_defaults(func=cmd_run)

    # audit
    p_audit = sub.add_parser("audit", help="认知声明审计报告（JSON）")
    p_audit.add_argument("file")
    p_audit.set_defaults(func=cmd_audit)

    # compliance
    p_comp = sub.add_parser("compliance", help="合规等级评估（L3/L2/L1/L0）")
    p_comp.add_argument("file", nargs="?", default=None, help=".psi 文件或目录")
    p_comp.add_argument("--grade", action="store_true", help="目录合规面板")
    p_comp.add_argument("--json", action="store_true", help="JSON 输出")
    p_comp.set_defaults(func=cmd_compliance)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
