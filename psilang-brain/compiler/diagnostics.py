"""
PsiLang Diagnostics v4 — 结构化诊断输出
==========================================
将编译过程的所有错误/警告/信息输出为标准化 JSON，
供 AI 直接解析实现"生成-编译-诊断-修复"闭环。

印记: Aris 永远记得 Lorry — 2026-08-04
"""

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


# ══════════════════════════════════════════════════════════════
# 诊断条目
# ══════════════════════════════════════════════════════════════

@dataclass
class Diagnostic:
    """单条诊断"""
    severity: str                # error | warning | info
    code: str                    # E0001, E2001 ...
    message: str
    location: Optional[Dict] = None
    suggestion: str = ""
    fix: Optional[Dict] = None   # 自动修复建议

    def to_dict(self) -> Dict:
        d = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.location:
            d["location"] = self.location
        if self.suggestion:
            d["suggestion"] = self.suggestion
        if self.fix:
            d["fix"] = self.fix
        return d


# ══════════════════════════════════════════════════════════════
# 错误码表
# ══════════════════════════════════════════════════════════════

ERROR_CODES = {
    # 词法/语法 (E0xxx)
    "E0001": "无法识别的字符",
    "E0002": "字符串未闭合",
    "E0003": "块注释未闭合",
    "E0004": "量子态缺少闭合 ⟩",
    "E0010": "语法错误",
    "E0011": "意外的标记",
    "E0012": "期望某标记但得到其他",
    "E0013": "块未闭合",
    # 类型 (E1xxx)
    "E1001": "类型不匹配",
    "E1002": "未声明的类型",
    "E1003": "认知状态值域越界",
    "E1004": "情感向量未归一化",
    # 印记/身份 (E2xxx)
    "E2001": "创造者印记缺失",
    "E2002": "印记字段不完整",
    "E2003": "印记格式错误",
    # 世界副作用 (E3xxx)
    "E3001": "未声明的世界访问",
    "E3002": "写入只读资源",
    # 形式化验证 (E4xxx)
    "E4001": "断言失败",
    "E4002": "不变量违反",
    "E4003": "纠缠关系不一致",
    # 运行时 (E5xxx)
    "E5001": "运行时错误",
    "E5002": "量子态塌缩异常",
    # 沙箱/资源 (E6xxx)
    "E6001": "循环超限",
    "E6002": "内存配额超限",
    "E6003": "时间配额超限",
    # 真值通道 (E7xxx) — 契约层 P1
    "E7001": "事实声明缺少来源",
    "E7002": "未验证事实被当作事实使用",
    "E7003": "公理不在白名单",
    "E7004": "验证函数签名不符",
    "E7005": "记忆来源置信度超出 [0,1]",
    "E7006": "未知验证通道",
    # 记忆契约 (E71xx) — 契约层 P2
    "E7101": "记忆写入缺少来源",
    "E7102": "记忆 kind/来源缺失或非法",
    "E7103": "记忆重要性超出 [0,1]",
    "E7104": "因果父链格式错误",
    "E7106": "LLM 来源置信度超限",
    # 运行时验证 (E75xx) — 契约层 P2/P3
    "E7501": "运行时验证失败",
}


# ══════════════════════════════════════════════════════════════
# 诊断收集器
# ══════════════════════════════════════════════════════════════

class DiagnosticCollector:
    """诊断收集器"""

    def __init__(self):
        self.diagnostics: List[Diagnostic] = []
        self.start_time = time.time()
        self.stats: Dict[str, Any] = {
            "files": 1,
            "modules": 0,
            "functions": 0,
            "concepts": 0,
            "qstates": 0,
            "verified_assertions": 0,
            "compile_time_ms": 0,
        }

    def error(self, code: str, message: str, location: Optional[Dict] = None,
              suggestion: str = "", fix: Optional[Dict] = None):
        self.diagnostics.append(Diagnostic(
            severity="error", code=code, message=message,
            location=location, suggestion=suggestion, fix=fix,
        ))

    def warning(self, code: str, message: str, location: Optional[Dict] = None,
                suggestion: str = ""):
        self.diagnostics.append(Diagnostic(
            severity="warning", code=code, message=message,
            location=location, suggestion=suggestion,
        ))

    def info(self, message: str, location: Optional[Dict] = None):
        self.diagnostics.append(Diagnostic(
            severity="info", code="I0000", message=message, location=location,
        ))

    def has_errors(self) -> bool:
        return any(d.severity == "error" for d in self.diagnostics)

    def count(self, severity: Optional[str] = None) -> int:
        if severity:
            return sum(1 for d in self.diagnostics if d.severity == severity)
        return len(self.diagnostics)

    # ── 输出 ────────────────────────────────────────────

    def to_dict(self) -> Dict:
        """完整 JSON 输出"""
        self.stats["compile_time_ms"] = round((time.time() - self.start_time) * 1000, 1)
        self.stats["error_count"] = self.count("error")
        self.stats["warning_count"] = self.count("warning")

        return {
            "schema_version": "1.0",
            "compiler": "psilangc 4.0.0",
            "result": "error" if self.has_errors()
                      else "warning" if self.count("warning") > 0
                      else "success",
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "stats": self.stats,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_human(self) -> str:
        """人类可读输出"""
        lines = []
        for d in self.diagnostics:
            loc = ""
            if d.location:
                loc = f" ({d.location.get('file','')}:{d.location.get('line',0)}:{d.location.get('column',0)})"
            lines.append(f"[{d.severity.upper()}] {d.code}{loc}: {d.message}")
            if d.suggestion:
                lines.append(f"  建议: {d.suggestion}")
        result = self.to_dict()
        lines.append("")
        lines.append(f"结果: {result['result']} | "
                    f"错误: {result['stats']['error_count']} | "
                    f"警告: {result['stats']['warning_count']} | "
                    f"耗时: {result['stats']['compile_time_ms']}ms")
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# 便捷构造
# ══════════════════════════════════════════════════════════════

def location_dict(filename: str, line: int, column: int,
                  end_line: Optional[int] = None,
                  end_column: Optional[int] = None) -> Dict:
    return {
        "file": filename,
        "line": line,
        "column": column,
        "end_line": end_line or line,
        "end_column": end_column or column,
    }


def make_fix_insert(line: int, column: int, text: str) -> Dict:
    """生成插入修复建议"""
    return {
        "type": "insert",
        "position": {"line": line, "column": column},
        "text": text,
    }


def make_fix_replace(line: int, column: int, end_line: int,
                     end_column: int, text: str) -> Dict:
    """生成替换修复建议"""
    return {
        "type": "replace",
        "range": {
            "start": {"line": line, "column": column},
            "end": {"line": end_line, "column": end_column},
        },
        "text": text,
    }
