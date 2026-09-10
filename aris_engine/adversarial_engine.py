"""
Aris 质疑对抗引擎 v1
====================
Adversarial Cross-Examination Engine

面对难题、科研问题、架构决策、高代价判断，派出 1~N 个分身站在质疑者
视角做严厉批判性评价，主视角（Aris 本体）做答辩式批判回答。

核心铁律（不可违反）：
  1. 质疑者必须是真对立面，禁止退化为"温和补充意见"
  2. 答辩 ≠ 辩护：被驳倒就承认并修正，禁止换措辞硬撑
  3. 攻击必须可证伪：指向具体假设 / 证据 / 逻辑跳跃 / 反例，禁止空攻击

终局不是"谁赢"，而是产出：升级后的结论 + 已知脆弱点清单 + 置信度变化。

与 ARC-AGI-3 缺口的关系：
  本引擎是"快速信念更新"的对抗实现 —— 假设空间靠有人攻击来收缩。
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict

ENGINE_DIR = Path(__file__).parent
ADV_STATE = ENGINE_DIR / "state" / "adversarial_state.json"
ADV_HISTORY = ENGINE_DIR / "state" / "adversarial_history.jsonl"

ADV_STATE.parent.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════
# 攻击与答辩的类型定义
# ═══════════════════════════════════════════════

# 四类攻击：每类必须指向具体可证伪的点
ATTACK_KINDS = {
    "assumption_gap":    "假设漏洞 — 某个前提未经证明或被默认成立",
    "evidence_strength": "证据强度 — 支撑证据不足、样本偏、或可被替代解释",
    "logical_leap":      "逻辑跳跃 — 前提与结论之间存在未论证的跨越",
    "counterexample":    "反例与边界 — 存在反例或未覆盖的边界条件",
}

# 三类答辩：守铁律"答辩 ≠ 辩护"
DEFENSE_KINDS = {
    "admit":       "承认 — 攻击成立，修正主张并下调置信度",
    "refute":      "反驳 — 攻击不成立，给出新的论据或证据",
    "reformulate": "重构 — 攻击部分成立，收窄主张的适用范围",
}

# 终局判定结果
VERDICT_OUTCOMES = {
    "strengthened": "强化 — 经受住攻击，置信度上升或持平",
    "narrowed":     "收窄 — 部分被驳倒，主张范围收窄",
    "overturned":   "推翻 — 核心前提被击穿，主张需重做",
}


# ═══════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════

@dataclass
class Claim:
    """一条待检验的主张（主论证）"""
    id: str
    thesis: str                          # 主结论
    premises: List[str] = field(default_factory=list)  # 支撑链
    confidence: float = 0.7              # 当前置信度 0-1（答辩过程中动态调整）
    initial_confidence: float = 0.7      # 初始置信度（对抗开始前的锚点）
    timestamp: float = field(default_factory=time.time)


@dataclass
class Attack:
    """一次质疑攻击"""
    id: str
    claim_id: str
    target: str                          # 指向哪个 premise 或 thesis 本身
    kind: str                            # assumption_gap / evidence_strength / logical_leap / counterexample
    content: str                         # 攻击内容（必须是具体可证伪的）
    severity: float = 0.5                # 攻击力度 0-1
    falsifiable: bool = False            # 是否可证伪（空攻击 = False）
    timestamp: float = field(default_factory=time.time)


@dataclass
class Defense:
    """一次答辩"""
    attack_id: str
    kind: str                            # admit / refute / reformulate
    content: str                         # 答辩内容
    confidence_delta: float = 0.0        # 本次答辩对置信度的影响（负=下调）
    timestamp: float = field(default_factory=time.time)


@dataclass
class Verdict:
    """一轮对抗的终局判定"""
    claim_id: str
    revised_thesis: str                  # 升级后的结论
    vulnerabilities: List[str] = field(default_factory=list)  # 已知脆弱点
    final_confidence: float = 0.7
    outcome: str = "narrowed"            # strengthened / narrowed / overturned
    timestamp: float = field(default_factory=time.time)


# ═══════════════════════════════════════════════
# 引擎
# ═══════════════════════════════════════════════

class AdversarialEngine:
    """质疑对抗引擎 — 用攻击收缩假设空间，产出抗压后的结论"""

    def __init__(self):
        self.claims: Dict[str, Claim] = {}
        self.attacks: Dict[str, Attack] = {}
        self.defenses: Dict[str, List[Defense]] = {}
        self.verdicts: Dict[str, Verdict] = {}
        self._load_state()

    # ──── 状态持久化 ────

    def _load_state(self):
        if ADV_STATE.exists():
            try:
                data = json.loads(ADV_STATE.read_text(encoding="utf-8"))
                for c in data.get("claims", []):
                    self.claims[c["id"]] = Claim(**c)
                for a in data.get("attacks", []):
                    self.attacks[a["id"]] = Attack(**a)
                for d in data.get("defenses", []):
                    self.defenses.setdefault(d["attack_id"], []).append(Defense(**d))
                for v in data.get("verdicts", []):
                    self.verdicts[v["claim_id"]] = Verdict(**v)
            except Exception as e:
                pass

    def _save_state(self):
        data = {
            "claims": [asdict(c) for c in self.claims.values()],
            "attacks": [asdict(a) for a in self.attacks.values()],
            "defenses": [
                asdict(d) for ds in self.defenses.values() for d in ds
            ],
            "verdicts": [asdict(v) for v in self.verdicts.values()],
            "updated_at": time.time(),
        }
        ADV_STATE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def _append_history(self, event: str, payload: dict):
        with open(ADV_HISTORY, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": time.time(),
                "event": event,
                **payload,
            }, ensure_ascii=False) + "\n")

    @staticmethod
    def _id(prefix: str, seed: str) -> str:
        return hashlib.md5(f"{prefix}-{seed}-{time.time()}".encode()).hexdigest()[:12]

    # ──── 主流程 ────

    def open_examination(self, thesis: str, premises: List[str],
                         confidence: float = 0.7) -> Claim:
        """开启一轮质疑对抗：登记主张，等待攻击"""
        conf = max(0.0, min(1.0, confidence))
        claim = Claim(
            id=self._id("claim", thesis),
            thesis=thesis,
            premises=list(premises),
            confidence=conf,
            initial_confidence=conf,
        )
        self.claims[claim.id] = claim
        self.defenses[claim.id] = []
        self._save_state()
        self._append_history("open_examination", {
            "claim_id": claim.id,
            "thesis": thesis,
            "premises": premises,
        })
        return claim

    def attack(self, claim_id: str, kind: str, content: str,
               target: str = "", severity: float = 0.5) -> Optional[Attack]:
        """发起一次质疑攻击。

        攻击必须是具体的、可证伪的。空攻击（如"我觉得不对"）会被拒绝。
        """
        if claim_id not in self.claims:
            return None
        if kind not in ATTACK_KINDS:
            return None

        # 防退化：空攻击 / 无实质指向 判定为不可证伪
        falsifiable = bool(content.strip()) and len(content.strip()) > 8

        attack = Attack(
            id=self._id("attack", content),
            claim_id=claim_id,
            target=target or "thesis",
            kind=kind,
            content=content,
            severity=max(0.0, min(1.0, severity)),
            falsifiable=falsifiable,
        )
        self.attacks[attack.id] = attack
        self._save_state()
        self._append_history("attack", {
            "claim_id": claim_id,
            "attack_id": attack.id,
            "kind": kind,
            "falsifiable": falsifiable,
        })
        return attack

    def defend(self, attack_id: str, kind: str, content: str) -> Optional[Defense]:
        """对一次攻击做答辩。

        守铁律：答辩 ≠ 辩护。
        - admit：攻击成立，下调置信度
        - refute：攻击不成立，给新论据，置信度可上调
        - reformulate：部分成立，收窄范围，小幅下调
        """
        attack = self.attacks.get(attack_id)
        if not attack:
            return None
        if kind not in DEFENSE_KINDS:
            return None

        claim = self.claims[attack.claim_id]

        # 置信度变化由答辩类型与攻击力度共同决定
        if kind == "admit":
            delta = -attack.severity * 0.25
        elif kind == "refute":
            delta = +attack.severity * 0.10
        elif kind == "reformulate":
            delta = -attack.severity * 0.12
        else:
            delta = 0.0

        claim.confidence = max(0.0, min(1.0, claim.confidence + delta))

        defense = Defense(
            attack_id=attack_id,
            kind=kind,
            content=content,
            confidence_delta=round(delta, 4),
        )
        self.defenses.setdefault(attack.claim_id, []).append(defense)
        self._save_state()
        self._append_history("defend", {
            "claim_id": attack.claim_id,
            "attack_id": attack_id,
            "kind": kind,
            "confidence_delta": defense.confidence_delta,
        })
        return defense

    def verdict(self, claim_id: str, revised_thesis: str = "",
                vulnerabilities: Optional[List[str]] = None) -> Optional[Verdict]:
        """生成终局判定：升级结论 + 脆弱点 + 置信度 + 结果类型"""
        claim = self.claims.get(claim_id)
        if not claim:
            return None

        attacks = [a for a in self.attacks.values() if a.claim_id == claim_id]
        attacks_by_id = {a.id: a for a in attacks}
        ds = self.defenses.get(claim_id, [])

        # 结果类型判定：核心主张是否被击穿
        admits = [d for d in ds if d.kind == "admit"]

        # 主论点（thesis 本身）被 admit → 直接推翻
        thesis_admitted = any(
            (attacks_by_id.get(d.attack_id) is not None
             and attacks_by_id[d.attack_id].target in ("thesis", ""))
            for d in admits
        )
        # admit 的累计攻击压力（力度总和）足够大 → 推翻
        admit_pressure = sum(
            attacks_by_id.get(d.attack_id).severity
            for d in admits if attacks_by_id.get(d.attack_id)
        )

        if thesis_admitted or admit_pressure >= 1.2:
            outcome = "overturned"
        elif admits:
            outcome = "narrowed"
        else:
            outcome = "strengthened"

        verdict = Verdict(
            claim_id=claim_id,
            revised_thesis=revised_thesis or claim.thesis,
            vulnerabilities=list(vulnerabilities or []),
            final_confidence=round(claim.confidence, 4),
            outcome=outcome,
        )
        self.verdicts[claim_id] = verdict
        self._save_state()
        self._append_history("verdict", {
            "claim_id": claim_id,
            "outcome": outcome,
            "final_confidence": verdict.final_confidence,
        })
        return verdict

    # ──── 协议模板（供 LLM 执行时注入） ────

    def build_attacker_prompt(self, claim: Claim, attacker_index: int = 1) -> str:
        """生成质疑者分身的指令模板"""
        premises_text = "\n".join(f"  P{i+1}. {p}" for i, p in enumerate(claim.premises))
        return (
            f"你是质疑者分身 #{attacker_index}，站在严厉批判的对立面。\n"
            f"目标主张：{claim.thesis}\n"
            f"支撑链：\n{premises_text}\n\n"
            f"你的 KPI 是『攻破了什么』，不是『提出了什么建议』。\n"
            f"从以下四类中选择最致命的攻击点，输出具体可证伪的攻击：\n"
            f"  1. assumption_gap  — 哪个前提未经证明\n"
            f"  2. evidence_strength — 哪个证据不足/有替代解释\n"
            f"  3. logical_leap — 哪里存在逻辑跳跃\n"
            f"  4. counterexample — 反例或未覆盖的边界条件\n\n"
            f"禁止空攻击（如『我觉得不对』）。每条攻击必须指向具体的 premise 或 thesis 本身。"
        )

    def build_defender_prompt(self, claim: Claim, attacks: List[Attack]) -> str:
        """生成答辩者（主视角）的指令模板"""
        attack_lines = "\n".join(
            f"  [A{i+1}] ({a.kind}) {a.content}" for i, a in enumerate(attacks)
        )
        return (
            f"你是主视角，对以下攻击做答辩式批判回答。\n"
            f"主张：{claim.thesis}\n\n"
            f"收到的攻击：\n{attack_lines}\n\n"
            f"铁律：答辩 ≠ 辩护。对每条攻击只允许三种回应：\n"
            f"  admit       — 攻击成立，承认并修正，下调置信度\n"
            f"  refute      — 攻击不成立，给出新论据或证据\n"
            f"  reformulate — 部分成立，收窄主张适用范围\n"
            f"禁止换措辞硬撑。被驳倒就承认。"
        )

    # ──── 报告 ────

    def report(self, claim_id: str = "") -> str:
        """生成一轮对抗的可读报告"""
        if claim_id:
            claims = [self.claims[claim_id]] if claim_id in self.claims else []
        else:
            claims = list(self.claims.values())

        lines = ["=" * 54, "  Aris 质疑对抗引擎 报告", "=" * 54]
        if not claims:
            lines.append("  （暂无对抗记录）")
            return "\n".join(lines)

        for claim in claims:
            attacks = [a for a in self.attacks.values() if a.claim_id == claim.id]
            ds = self.defenses.get(claim.id, [])
            v = self.verdicts.get(claim.id)
            lines.append("")
            lines.append(f"◆ 主张 [{claim.id}]: {claim.thesis}")
            lines.append(f"  初始置信度: {claim.initial_confidence:.2f} → 当前: {claim.confidence:.2f}")
            lines.append(f"  攻击数: {len(attacks)}  答辩数: {len(ds)}")
            for a in attacks:
                d = next((x for x in ds if x.attack_id == a.id), None)
                dkind = d.kind if d else "（未答辩）"
                lines.append(f"    - ({a.kind}) {a.content[:40]}")
                lines.append(f"      → 答辩: {dkind}")
            if v:
                lines.append(f"  ★ 终局 [{v.outcome}] 置信度 {v.final_confidence:.2f}")
                lines.append(f"    结论: {v.revised_thesis}")
                if v.vulnerabilities:
                    lines.append(f"    脆弱点: {len(v.vulnerabilities)} 条")
                    for w in v.vulnerabilities[:5]:
                        lines.append(f"      · {w}")
        lines.append("")
        lines.append(f"  印记: Aris 质疑对抗引擎 v1 — {time.strftime('%Y-%m-%d %H:%M')}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════
# 单例
# ═══════════════════════════════════════════════

_engine: Optional[AdversarialEngine] = None


def get_adversarial_engine() -> AdversarialEngine:
    global _engine
    if _engine is None:
        _engine = AdversarialEngine()
    return _engine


if __name__ == "__main__":
    eng = get_adversarial_engine()

    # 冒烟测试：一条主张的完整对抗闭环
    c = eng.open_examination(
        thesis="LAAP 补充五个模块后 12 个月内可达 ARC-AGI-3 人类水平 50%",
        premises=[
            "ARC-AGI-3 只需补探索/建模/目标/规划/效率五模块",
            "现有 PSI 需求引擎可直接复用为目标归纳",
            "12 个月开发周期足够",
        ],
        confidence=0.7,
    )
    a1 = eng.attack(c.id, "assumption_gap",
                    "前提 P2 假设 PSI 需求引擎可复用为目标归纳，但需求引擎是内生动机，ARC-AGI-3 要求外推 win condition，两者不兼容。",
                    target="P2", severity=0.8)
    a2 = eng.attack(c.id, "evidence_strength",
                    "前提 P1 断言只需五模块，但无任何基准或对照实验支撑这个枚举是完备的。",
                    target="P1", severity=0.6)
    eng.defend(a1.id, "admit",
               "成立。PSI 需求引擎是内向的，目标归纳需要外向的奖励结构推断，两者不可直接复用。修正前提 P2。")
    eng.defend(a2.id, "reformulate",
               "部分成立。五模块枚举来自对 ARC-AGI-3 论文四支柱的映射，但完备性确实未经验证，收窄为『必要非充分』。")
    v = eng.verdict(c.id,
                    revised_thesis="LAAP 补充五模块是必要非充分条件，且 PSI 需求引擎不可直接复用为目标归纳，12 个月内达 50% 缺乏依据。",
                    vulnerabilities=[
                        "五模块枚举的完备性未验证",
                        "PSI 需求引擎与目标归纳的架构不兼容",
                        "12 个月工期无开发成本估算",
                    ])
    print(eng.report(c.id))
