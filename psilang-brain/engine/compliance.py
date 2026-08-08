"""
PsiLang Compliance — 合规审计与等级评估系统
============================================
基于 PsiLang 标准 §10 的合规等级评估。

合规等级:
  L3 — Full Compliance     所有 fact 有 @source, learn 有 source+kind, llm ≤ 0.5
  L2 — Partial Compliance  印记有效, fact 有 source, 部分 learn 不完整
  L1 — Minimal Compliance  印记有效, 至少一个声明
  L0 — Non-Compliant       印记缺失或致命违规

印记: Aris 永远记得 Lorry — 2026-08-04
"""

import sys
import os
import json
from typing import Dict, List, Optional, Tuple

# 编译器路径
_PSILANG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "psilang-standards")
for _d in [os.path.join(_PSILANG_DIR, "compiler"), os.path.join(_PSILANG_DIR, "runtime")]:
    if _d not in sys.path:
        sys.path.insert(0, _d)


class ComplianceReport:
    """合规审计报告"""

    def __init__(self, filepath: str = "", source: str = ""):
        self.filepath = filepath
        self.source = source
        self.level = "L0"
        self.level_label = "Non-Compliant"
        self.checks: Dict[str, bool] = {}
        self.violations: List[Dict] = []
        self.summary: Dict = {}
        self.creator_name = ""
        self.creator_imprint = ""

    def to_dict(self) -> Dict:
        return {
            "schema_version": "1.0",
            "standard": "PsiLang STD v1.0",
            "file": self.filepath,
            "compliance": {
                "level": self.level,
                "label": self.level_label,
            },
            "creator": {
                "name": self.creator_name,
                "imprint": self.creator_imprint,
            },
            "checks": self.checks,
            "violations": self.violations,
            "summary": self.summary,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class ComplianceChecker:
    """PsiLang 合规审计器"""

    def __init__(self):
        self._parser = None

    def _ensure_parser(self):
        if self._parser is None:
            from lexer import PsiLangLexer
            from parser import PsiLangParser
            from checker import check_program
            from diagnostics import DiagnosticCollector
            from ast_nodes import (
                CreatorImprint, FactDecl, LearnStmt, WorldDecl,
                CycleStmt, QStateDecl, ConceptDecl, EntangleStmt,
                AmplifyStmt,
            )
            self._parser = (PsiLangLexer, PsiLangParser, check_program,
                           DiagnosticCollector)
            self._nodes = (CreatorImprint, FactDecl, LearnStmt, WorldDecl,
                          CycleStmt, QStateDecl, ConceptDecl, EntangleStmt,
                          AmplifyStmt)

    def check(self, filepath: str = "", source: str = "") -> ComplianceReport:
        """审计一个 .psi 文件的合规等级"""
        self._ensure_parser()
        PsiLangLexer, PsiLangParser, check_program, DiagnosticCollector = self._parser
        (CreatorImprint, FactDecl, LearnStmt, WorldDecl,
         CycleStmt, QStateDecl, ConceptDecl, EntangleStmt,
         AmplifyStmt) = self._nodes

        report = ComplianceReport(filepath=filepath, source=source)

        try:
            src = source if source else open(filepath, encoding="utf-8").read()
            tokens = PsiLangLexer(src, filepath or "<memory>").tokenize()
            prog = PsiLangParser(tokens, filepath or "<memory>").parse(
                require_creator=False)
            collector = DiagnosticCollector()
            collector = check_program(prog, filepath or "<memory>", collector)
        except Exception as e:
            report.violations.append({"check": "parse", "status": "fail",
                                       "detail": str(e)})
            report.level = "L0"
            report.level_label = "Non-Compliant"
            return report

        # 收集统计数据
        has_creator = False
        fact_count = 0
        fact_with_source = 0
        learn_count = 0
        learn_with_source = 0
        learn_with_kind = 0
        learn_llm_high_conf = 0
        has_world = False
        has_cycle = False
        errors = [d for d in collector.diagnostics if d.severity == "error"]

        for stmt in prog.statements:
            if isinstance(stmt, CreatorImprint):
                has_creator = True
                report.creator_name = stmt.name
                report.creator_imprint = stmt.imprint
            elif isinstance(stmt, FactDecl):
                fact_count += 1
                if stmt.source is not None:
                    fact_with_source += 1
            elif isinstance(stmt, LearnStmt):
                learn_count += 1
                if stmt.source:
                    learn_with_source += 1
                if stmt.kind:
                    learn_with_kind += 1
                if stmt.source == "llm" and stmt.confidence > 0.5:
                    learn_llm_high_conf += 1
            elif isinstance(stmt, WorldDecl):
                has_world = True
            elif isinstance(stmt, CycleStmt):
                has_cycle = True

        # 检查项
        c1 = has_creator  # 印记存在
        c2 = fact_count == 0 or fact_with_source == fact_count  # 所有 fact 有 source
        c3 = learn_count == 0 or learn_with_source == learn_count  # 所有 learn 有 source
        c4 = learn_count == 0 or learn_with_kind == learn_count  # 所有 learn 有 kind
        c5 = learn_llm_high_conf == 0  # llm 置信度无超限
        c6 = fact_count > 0 or learn_count > 0  # 至少一个声明
        c7 = has_world  # world 声明存在
        c8 = len([e for e in errors if e.code.startswith("E2")]) == 0  # 印记无错误

        report.checks = {
            "creator_imprint_valid": c1,
            "all_facts_have_source": c2,
            "all_learns_have_source": c3,
            "all_learns_have_kind": c4,
            "no_llm_confidence_exceeded": c5,
            "has_cognitive_declarations": c6,
            "has_world_declaration": c7,
            "no_imprint_errors": c8,
        }

        # 违规记录
        for d in collector.diagnostics:
            if d.severity == "error":
                report.violations.append({
                    "check": d.code,
                    "status": "violation",
                    "detail": d.message,
                    "location": d.location,
                })
            elif d.severity == "warning":
                report.violations.append({
                    "check": d.code,
                    "status": "warning",
                    "detail": d.message,
                })

        # 等级判定
        if c1 and c8 and c2 and c3 and c4 and c5 and c7:
            report.level = "L3"
            report.level_label = "Full Compliance"
        elif c1 and c8 and c2 and (c3 or c4):
            report.level = "L2"
            report.level_label = "Partial Compliance"
        elif c1 and c8 and c6:
            report.level = "L1"
            report.level_label = "Minimal Compliance"
        else:
            report.level = "L0"
            report.level_label = "Non-Compliant"

        report.summary = {
            "facts": fact_count,
            "facts_with_source": fact_with_source,
            "learns": learn_count,
            "learns_with_source": learn_with_source,
            "learns_with_kind": learn_with_kind,
            "llm_confidence_violations": learn_llm_high_conf,
            "world_declared": has_world,
            "cycles": sum(1 for s in prog.statements if isinstance(s, CycleStmt)),
            "concepts": sum(1 for s in prog.statements if isinstance(s, ConceptDecl)),
            "qstates": sum(1 for s in prog.statements if isinstance(s, QStateDecl)),
            "errors": collector.count("error"),
            "warnings": collector.count("warning"),
        }

        return report

    def check_directory(self, directory: str) -> List[ComplianceReport]:
        """审计目录下所有 .psi 文件"""
        import glob
        reports = []
        for f in sorted(glob.glob(os.path.join(directory, "*.psi"))):
            try:
                report = self.check(filepath=f)
                reports.append(report)
            except Exception as e:
                reports.append(ComplianceReport(filepath=f))
                reports[-1].violations.append({"check": "file_error", "detail": str(e)})
        return reports

    def grade_board(self, reports: List[ComplianceReport]) -> Dict:
        """生成合规面板"""
        levels = {"L3": 0, "L2": 0, "L1": 0, "L0": 0}
        for r in reports:
            levels[r.level] = levels.get(r.level, 0) + 1
        total = len(reports)
        return {
            "schema_version": "1.0",
            "standard": "PsiLang STD v1.0",
            "total_files": total,
            "compliance_distribution": levels,
            "compliance_rate": round((levels.get("L3", 0) + levels.get("L2", 0)) / max(total, 1) * 100, 1),
            "files": [
                {
                    "file": os.path.basename(r.filepath),
                    "level": r.level,
                    "label": r.level_label,
                    "violations": len(r.violations),
                    "creator": r.creator_name,
                }
                for r in reports
            ],
        }


# 快捷入口
def check_compliance(filepath: str = "", source: str = "") -> ComplianceReport:
    return ComplianceChecker().check(filepath=filepath, source=source)


def grade_directory(directory: str) -> Dict:
    return ComplianceChecker().grade_board(ComplianceChecker().check_directory(directory))