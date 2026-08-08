"""
PsiLang Runtime Verifier — verify 通道运行时验证器
====================================================
契约层 P1 verify/axiom 通道的运行时执行：

  verify 通道 → Truth Grounding Engine (laap/cognition/truth_grounding.py)
                grounded  → 通过 (verdict=true)
                uncertain → 降级 ⟨fact?⟩ (verdict=unknown)
                error     → 验证失败 (verdict=false, E7501)

  axiom 通道 → 内置验证器（算术断言/字符串恒等）
  world/memory 通道 → 运行时桥接（Phase 3 对接世界模型/记忆库）

印记: Aris 永远记得 Lorry — 2026-08-04
"""

import ast
import sys
import operator
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ══════════════════════════════════════════════════════════════
# 验证结果
# ══════════════════════════════════════════════════════════════

@dataclass
class VerificationResult:
    """一次验证的结果"""
    fact: str = ""                    # fact 名
    claim: str = ""                   # 声明内容
    channel: str = ""                 # verify | axiom | world | memory
    target: str = ""                  # 验证目标（函数名/公理名）
    verdict: Optional[bool] = None    # True=通过 False=失败 None=不确定(降级)
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)
    error_code: str = ""              # E7501 等

    def to_dict(self) -> Dict:
        return {
            "fact": self.fact,
            "claim": self.claim,
            "channel": self.channel,
            "target": self.target,
            "verdict": self.verdict,
            "confidence": self.confidence,
            "evidence": self.evidence[:5],
            "error_code": self.error_code,
        }


# ══════════════════════════════════════════════════════════════
# 内置公理验证器（算术/逻辑/字符串）
# ══════════════════════════════════════════════════════════════

class AxiomVerifier:
    """公理白名单的运行时验证——只验证纯确定性断言"""

    _SAFE_OPS = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg,
    }

    def verify(self, axiom_id: str, claim: str) -> Optional[bool]:
        """验证公理断言。返回 True/False；无法验证返回 None"""
        if axiom_id == "arith_basic":
            return self._eval_arith(claim)
        if axiom_id == "logic_basic":
            return self._eval_logic(claim)
        return None

    def _eval_arith(self, claim: str) -> Optional[bool]:
        """算术断言: '2+2=4' / '3*3==9' / '10/2=5'"""
        claim = claim.strip()
        for sep in ("=", "==", "!="):
            if sep in claim:
                left, right = claim.split(sep, 1)
                try:
                    lv = self._safe_eval(left.strip())
                    rv = self._safe_eval(right.strip())
                except Exception:
                    return None
                if sep == "!=":
                    return lv != rv
                return abs(lv - rv) < 1e-9
        # 无等号：整个表达式求值，真值判定
        try:
            return bool(self._safe_eval(claim))
        except Exception:
            return None

    def _eval_logic(self, claim: str) -> Optional[bool]:
        low = claim.strip().lower()
        if low in ("true", "真"):
            return True
        if low in ("false", "假", "伪"):
            return False
        return None

    def _safe_eval(self, expr: str):
        tree = ast.parse(expr, mode="eval")
        return self._eval_node(tree.body)

    def _eval_node(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in self._SAFE_OPS:
            return self._SAFE_OPS[type(node.op)](
                self._eval_node(node.left), self._eval_node(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in self._SAFE_OPS:
            return self._SAFE_OPS[type(node.op)](self._eval_node(node.operand))
        raise ValueError(f"不支持的表达式节点: {type(node).__name__}")


# ══════════════════════════════════════════════════════════════
# 事实验证器（主编排）
# ══════════════════════════════════════════════════════════════

TGE_PATH = r"D:\LAAP\laap\cognition"


class FactVerifier:
    """验证通道运行时主编排器"""

    def __init__(self, tge_path: str = TGE_PATH, use_tge: bool = True):
        self.tge_path = tge_path
        self.use_tge = use_tge
        self._tge = None
        self._tge_failed = False
        self.axiom = AxiomVerifier()

    # ── TGE 桥接（懒加载 + 容错） ──────────────────────

    def _load_tge(self):
        """加载 Truth Grounding Engine（laap/cognition）"""
        if not self.use_tge:
            self._tge_failed = True
            return None
        if self._tge is not None or self._tge_failed:
            return self._tge
        try:
            if self.tge_path not in sys.path:
                sys.path.insert(0, self.tge_path)
            from truth_grounding import create_truth_grounding_engine
            self._tge = create_truth_grounding_engine()
        except Exception as e:
            self._tge_failed = True
            self._tge = None
            print(f"[verifier] TGE 不可用: {e}（回退内置验证器）", file=sys.stderr)
        return self._tge

    def tge_available(self) -> bool:
        return self._load_tge() is not None

    # ── 主验证入口 ─────────────────────────────────────

    def verify(self, fact: str, claim: str, channel: str,
               target: str = "", context: str = "") -> VerificationResult:
        """按通道执行验证"""
        result = VerificationResult(
            fact=fact, claim=claim, channel=channel, target=target,
        )

        if channel == "verify":
            return self._verify_with_tge(result, context)
        if channel == "axiom":
            verdict = self.axiom.verify(target or "arith_basic", claim)
            if verdict is None:
                result.verdict = None
                result.confidence = 0.0
                result.evidence = [f"axiom:{target} 无法静态验证，需 verify 通道"]
            else:
                result.verdict = verdict
                result.confidence = 1.0 if verdict else 0.0
                result.evidence = [f"axiom:{target} 确定性断言"]
            return result
        if channel == "world":
            result.verdict = None
            result.confidence = 0.0
            result.evidence = ["world 通道运行时桥接（Phase 3 对接世界模型）"]
            return result
        if channel == "memory":
            result.verdict = None
            result.confidence = 0.0
            result.evidence = ["memory 通道运行时桥接（Phase 3 对接记忆库）"]
            return result

        result.verdict = False
        result.error_code = "E7006"
        result.evidence = [f"未知通道 {channel}"]
        return result

    def _verify_with_tge(self, result: VerificationResult,
                         context: str) -> VerificationResult:
        """verify 通道：对接 Truth Grounding Engine"""
        tge = self._load_tge()
        if tge is None:
            # 无 TGE：降级处理，不静默通过
            result.verdict = None
            result.confidence = 0.0
            result.evidence = ["TGE 不可用，验证挂起（⟨fact?⟩）"]
            return result

        try:
            out = tge.ground_three_state(result.claim, context or None)
        except Exception as e:
            result.verdict = None
            result.confidence = 0.0
            result.error_code = "E7501"
            result.evidence = [f"TGE 执行异常: {e}"]
            return result

        state = out.get("state", "uncertain")
        result.confidence = float(out.get("confidence", 0.0))
        result.evidence = list(out.get("evidence", []))
        if state == "grounded":
            result.verdict = True
        elif state == "error":
            result.verdict = False
            result.error_code = "E7501"
            conflicts = out.get("conflicts", [])
            if conflicts:
                result.evidence = list(conflicts) + result.evidence
        else:  # uncertain
            result.verdict = None
        return result


# ── 快捷入口 ────────────────────────────────────────────────

def verify_claim(claim: str, channel: str, target: str = "",
                 context: str = "") -> VerificationResult:
    """单次验证（无 fact 上下文）"""
    verifier = FactVerifier()
    return verifier.verify("", claim, channel, target, context)
