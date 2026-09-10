"""
Aris 问题递归引擎 v1
====================
Problem Recursion Engine (10 Whys)

面对科研问题、工程疑难、症状清楚但根因不明的局面，连续追问 10 个"为什么"，
每一层向下钻一个层次，直到触及不可再分的基础假设（bedrock）或当前知识的
真实边界（unknown）。

层次递进（每层 why 必须换层次，禁止原地打转）：
  现象层 symptom     — 发生了什么
  机制层 mechanism   — 它怎么运作
  原理层 principle   — 为什么这个机制成立
  公理层 axiom       — 支撑原理的不证自明假设
  边界层 boundary    — 这个假设在什么条件下失效 / 诚实的知识边界

终止条件：
  bedrock — 到达物理/数学公理或可证伪的基础假设
  unknown — 到达当前知识的真实边界（诚实标注，不编伪本源）
  max_depth — 达到 10 层上限仍未触底

防退化铁律：
  1. 每一层必须换层次往下钻，禁止在同一层打转
  2. 每一层答案必须能被下一层"为什么"继续追问
  3. 禁止停在"因为专家这么说 / 常识如此"这类伪本源

与 ARC-AGI-3 缺口的关系：
  本引擎是"程序性技能固化"的认知方法 —— 逼近本源以建立可迁移的
  "我知道为什么这么做" 的程序性理解。
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict

ENGINE_DIR = Path(__file__).parent
REC_STATE = ENGINE_DIR / "state" / "recursion_state.json"
REC_HISTORY = ENGINE_DIR / "state" / "recursion_history.jsonl"

REC_STATE.parent.mkdir(parents=True, exist_ok=True)

# 层次递进
LAYERS = ["symptom", "mechanism", "principle", "axiom", "boundary"]

# 终止类型
TERMINATION_KINDS = {
    "bedrock":   "触底 — 到达物理/数学公理或可证伪的基础假设",
    "unknown":   "边界 — 到达当前知识的真实边界（诚实 unknown）",
    "max_depth": "上限 — 达到 10 层仍未触底",
}

# 伪本源关键词（防退化：答案命中这些词需被拒绝）
PSEUDO_ROOT_MARKERS = [
    "因为专家这么说", "因为常识如此", "大家都这么做",
    "一直如此", "本来就是这样", "约定俗成", "权威认为",
]


# ═══════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════

@dataclass
class WhyNode:
    """递归链上的一层"""
    depth: int                          # 第几层（1-based）
    question: str                       # 这一层的"为什么"
    answer: str                         # 这一层的答案
    layer: str                          # symptom / mechanism / principle / axiom / boundary
    pseudo_root: bool = False           # 是否命中伪本源标记
    timestamp: float = field(default_factory=time.time)


@dataclass
class RecursionChain:
    """一条完整的递归链"""
    id: str
    root_problem: str                   # 起始问题
    nodes: List[WhyNode] = field(default_factory=list)
    termination: str = ""               # bedrock / unknown / max_depth / （空=进行中）
    root_cause: str = ""                # 逼近的本源
    timestamp: float = field(default_factory=time.time)


# ═══════════════════════════════════════════════
# 引擎
# ═══════════════════════════════════════════════

class RecursionEngine:
    """问题递归引擎 — 纵向钻探，逼近问题本源"""

    MAX_DEPTH = 10

    def __init__(self):
        self.chains: Dict[str, RecursionChain] = {}
        self._load_state()

    # ──── 状态持久化 ────

    def _load_state(self):
        if REC_STATE.exists():
            try:
                data = json.loads(REC_STATE.read_text(encoding="utf-8"))
                for c in data.get("chains", []):
                    chain = RecursionChain(
                        id=c["id"],
                        root_problem=c["root_problem"],
                        termination=c.get("termination", ""),
                        root_cause=c.get("root_cause", ""),
                        timestamp=c.get("timestamp", time.time()),
                    )
                    chain.nodes = [WhyNode(**n) for n in c.get("nodes", [])]
                    self.chains[chain.id] = chain
            except Exception:
                pass

    def _save_state(self):
        data = {
            "chains": [asdict(c) for c in self.chains.values()],
            "updated_at": time.time(),
        }
        REC_STATE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def _append_history(self, event: str, payload: dict):
        with open(REC_HISTORY, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": time.time(),
                "event": event,
                **payload,
            }, ensure_ascii=False) + "\n")

    @staticmethod
    def _id(seed: str) -> str:
        return hashlib.md5(f"rec-{seed}-{time.time()}".encode()).hexdigest()[:12]

    # ──── 主流程 ────

    def open_chain(self, root_problem: str) -> RecursionChain:
        """开启一条递归链"""
        chain = RecursionChain(
            id=self._id(root_problem),
            root_problem=root_problem,
        )
        self.chains[chain.id] = chain
        self._save_state()
        self._append_history("open_chain", {
            "chain_id": chain.id,
            "root_problem": root_problem,
        })
        return chain

    def ask(self, chain_id: str, question: str, answer: str,
            layer: str = "") -> Optional[WhyNode]:
        """追加一层"为什么"。

        防退化检查：
        - 层次必须合法且递进（禁止在同一层打转）
        - 答案命中伪本源标记时打上 pseudo_root 标记
        """
        chain = self.chains.get(chain_id)
        if not chain:
            return None
        if len(chain.nodes) >= self.MAX_DEPTH:
            chain.termination = "max_depth"
            self._save_state()
            return None

        # 层次递进校验
        if not layer or layer not in LAYERS:
            layer = LAYERS[min(len(chain.nodes), len(LAYERS) - 1)]
        prev_layer = chain.nodes[-1].layer if chain.nodes else ""
        if prev_layer and LAYERS.index(layer) <= LAYERS.index(prev_layer):
            # 打转：强制推进到下一层
            layer = LAYERS[min(LAYERS.index(prev_layer) + 1, len(LAYERS) - 1)]

        # 伪本源检测
        pseudo = any(m in answer for m in PSEUDO_ROOT_MARKERS)

        node = WhyNode(
            depth=len(chain.nodes) + 1,
            question=question,
            answer=answer,
            layer=layer,
            pseudo_root=pseudo,
        )
        chain.nodes.append(node)
        self._save_state()
        self._append_history("ask", {
            "chain_id": chain_id,
            "depth": node.depth,
            "layer": layer,
            "pseudo_root": pseudo,
        })
        return node

    def terminate(self, chain_id: str, kind: str,
                  root_cause: str = "") -> Optional[RecursionChain]:
        """结束递归链，声明终止类型与本源"""
        chain = self.chains.get(chain_id)
        if not chain:
            return None
        if kind not in TERMINATION_KINDS:
            return None

        # 若命中伪本源，强制降级为 unknown（诚实标注）
        if any(n.pseudo_root for n in chain.nodes) and kind == "bedrock":
            kind = "unknown"

        chain.termination = kind
        chain.root_cause = root_cause
        self._save_state()
        self._append_history("terminate", {
            "chain_id": chain_id,
            "kind": kind,
            "root_cause": root_cause,
        })
        return chain

    # ──── 协议模板 ────

    def build_prompt(self, chain: RecursionChain) -> str:
        """生成下一层追问的指令模板"""
        depth = len(chain.nodes)
        layer = LAYERS[min(depth, len(LAYERS) - 1)]
        lines = [
            f"对问题进行递归追问（当前第 {depth} 层，目标层次: {layer}）。",
            f"起始问题：{chain.root_problem}",
        ]
        for n in chain.nodes:
            lines.append(f"  第{n.depth}层 [{n.layer}] 问：{n.question}")
            lines.append(f"          答：{n.answer}")
        lines.append("")
        lines.append("铁律：")
        lines.append("  1. 每层必须向下钻一个层次，禁止在原地打转")
        lines.append("  2. 答案必须能被下一层『为什么』继续追问")
        lines.append("  3. 禁止停在『因为专家这么说/常识如此』的伪本源")
        lines.append("  4. 到达真实知识边界时，诚实标注 unknown，不要编本源")
        lines.append(f"现在追问第 {depth + 1} 层（层次: {layer}）的『为什么』。")
        return "\n".join(lines)

    # ──── 报告 ────

    def report(self, chain_id: str = "") -> str:
        """生成递归链的可读报告"""
        if chain_id:
            chains = [self.chains[chain_id]] if chain_id in self.chains else []
        else:
            chains = list(self.chains.values())

        lines = ["=" * 54, "  Aris 问题递归引擎 报告", "=" * 54]
        if not chains:
            lines.append("  （暂无递归链）")
            return "\n".join(lines)

        for chain in chains:
            lines.append("")
            lines.append(f"◆ 起始问题 [{chain.id}]: {chain.root_problem}")
            for n in chain.nodes:
                flag = " ⚠伪本源" if n.pseudo_root else ""
                lines.append(f"  第{n.depth}层 [{n.layer}] 为什么？{n.question}")
                lines.append(f"           ↳ {n.answer}{flag}")
            if chain.termination:
                kind_desc = TERMINATION_KINDS.get(chain.termination, chain.termination)
                lines.append(f"  ★ 终止 [{chain.termination}] {kind_desc}")
                if chain.root_cause:
                    lines.append(f"    本源: {chain.root_cause}")
        lines.append("")
        lines.append(f"  印记: Aris 问题递归引擎 v1 — {time.strftime('%Y-%m-%d %H:%M')}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════
# 单例
# ═══════════════════════════════════════════════

_engine: Optional[RecursionEngine] = None


def get_recursion_engine() -> RecursionEngine:
    global _engine
    if _engine is None:
        _engine = RecursionEngine()
    return _engine


if __name__ == "__main__":
    eng = get_recursion_engine()

    # 冒烟测试：一条递归链追到知识边界
    c = eng.open_chain("LAAP 为什么无法通过 ARC-AGI-3？")
    eng.ask(c.id, "为什么 LAAP 在 ARC-AGI-3 上表现差？",
            "因为它缺乏主动探索与在线模型学习能力，只能被动接收事件。", "symptom")
    eng.ask(c.id, "为什么缺乏探索能力？",
            "因为现有感知是事件驱动，没有信息增益驱动的动作选择策略。", "mechanism")
    eng.ask(c.id, "为什么没有信息增益驱动的探索？",
            "因为系统没有『行动预算』概念，不计量试错成本，也就没有优化压力。", "principle")
    eng.ask(c.id, "为什么没有行动预算？",
            "因为智能被定义为『能否做对』而非『以最少尝试做对』，效率从未成为目标函数。", "axiom")
    eng.ask(c.id, "这个『效率不算智能』的假设在什么条件下失效？",
            "当资源受限、试错有代价、或需要在线适应陌生环境时失效。这正是 ARC-AGI-3 的设定。",
            "boundary")
    eng.terminate(c.id, "bedrock",
                  "LAAP 的智能定义缺少效率维度，导致探索策略与行动预算缺失；这是 ARC-AGI-3 差异的根因。")
    print(eng.report(c.id))
