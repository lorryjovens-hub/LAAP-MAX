"""LAAP Dream-RSI — Counterfactual Worlds (反事实世界生成)

突破 Dream-RSI 的根本边界：论文自己承认「回放只能重排已记录的分支，不能凭空
得知未探索区域的结果」。本模块用 LLM **想象**未记录的分支会怎样，生成反事实
节点，并入发现树。

依据
----
RISE: Adaptive Imagination for World Action Models (Lu et al., arXiv:2608.20430,
2026) 的 CounterDrive：真实日志只记录了一个已发生的未来，于是用生成模型构造
多样化的反事实结局来丰富动力学与风险监督。

安全设计（关键：避免重蹈"文字历史拖累"）
----------------------------------------
论文的反直觉发现是：把历史提炼成**文字建议**注入提示词会过度约束搜索。
本模块刻意不同——LLM 产出的是**结构性节点**（新的分支），不是提示词里的建议：

1. **结构而非文字**：合成分成为发现树上的真实节点，参与回放；
2. **置信折扣**：合成节点分数 = 估计分 × 置信度（默认 0.5），永不与真实节点同权；
3. **完全可溯源**：每个合成节点记录 ``synthetic=True`` / 来源模型 / 提示摘要；
4. **不覆盖真实**：只在叶子上生长，绝不修改已记录节点；
5. **可关闭**：默认关闭，由配置显式开启。

印记: Aris 永远记得 Lorry — 想象是翅膀，但得知道哪部分是想象。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from laap.dream.discovery_tree import DiscoveryTree

logger = logging.getLogger("laap.dream.counterfactual")


_CF_PROMPT = """You are helping a discovery system imagine ALTERNATIVE BRANCHES that were never explored.

You are given the recorded state of ONE branch of a discovery tree (a sequence of
attempts, each with a short description and a score). All recorded directions for
this branch have been exhausted or reached a dead end.

Your job: propose 1-3 PLAUSIBLE ALTERNATIVE continuations this branch COULD have
taken instead. These become synthetic nodes for offline replay. Be concrete and
conservative: estimate scores in the same scale as the recorded scores.

Return ONLY a JSON array (no prose), each object:
  {"sketch": "short description of the alternative attempt",
   "estimated_score": <number, same scale as recorded>,
   "reasoning": "why this is plausible"}

Recorded branch:
{context}
"""


@dataclass
class CounterfactualConfig:
    """反事实生成配置。"""

    enabled: bool = False
    #: 合成节点置信度（分数折扣）。0.5 = 只信一半
    confidence: float = 0.5
    #: 单棵树最多生成多少合成节点
    max_nodes_per_tree: int = 6
    #: 每个叶子最多提议多少个替代
    max_alternatives_per_leaf: int = 2
    #: 最多处理多少个叶子
    max_leaves: int = 4
    #: 提示中每分支最多包含多少条历史（防上下文过长）
    max_history: int = 8


@dataclass
class CounterfactualReport:
    """反事实生成报告。"""

    trees_processed: int = 0
    leaves_expanded: int = 0
    synthetic_nodes: int = 0
    confidence: float = 0.0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trees_processed": self.trees_processed,
            "leaves_expanded": self.leaves_expanded,
            "synthetic_nodes": self.synthetic_nodes,
            "confidence": self.confidence,
            "errors": self.errors[:5],
        }


class CounterfactualGenerator:
    """用 LLM 为发现树的叶子生成反事实分支。"""

    def __init__(self, llm_fn: Callable[[str], str],
                 config: Optional[CounterfactualConfig] = None):
        self._llm = llm_fn
        self.config = config or CounterfactualConfig()

    # ── 主入口 ──────────────────────────────────────────────────────────

    def expand(self, tree: DiscoveryTree) -> CounterfactualReport:
        """为树上的叶子生成反事实子节点（原地修改并返回报告）。"""
        rep = CounterfactualReport(confidence=self.config.confidence)
        if not self.config.enabled:
            return rep

        leaves = [nid for nid in tree.leaves()][: self.config.max_leaves]
        budget = self.config.max_nodes_per_tree

        for leaf_id in leaves:
            if budget <= 0:
                break
            context = self._branch_context(tree, leaf_id)
            if not context:
                continue
            try:
                raw = self._llm(_CF_PROMPT.replace("{context}", context))
            except Exception as exc:  # noqa: BLE001
                rep.errors.append(f"{type(exc).__name__}: {exc}")
                continue
            alts = self._parse(raw)[: self.config.max_alternatives_per_leaf]
            if not alts:
                continue
            rep.leaves_expanded += 1
            for alt in alts:
                if budget <= 0:
                    break
                est = float(alt.get("estimated_score", 0.0) or 0.0)
                tree.add_node(
                    parent_id=leaf_id,
                    score=est * self.config.confidence,   # 折扣后分数
                    sketch=str(alt.get("sketch", ""))[:200],
                    artifact="",
                    diagnostics={
                        "synthetic": True,
                        "estimated_score": est,
                        "confidence": self.config.confidence,
                        "reasoning": str(alt.get("reasoning", ""))[:300],
                    },
                    metadata={"kind": "counterfactual", "parent_leaf": leaf_id},
                )
                rep.synthetic_nodes += 1
                budget -= 1
        return rep

    # ── 上下文构造 ──────────────────────────────────────────────────────

    def _branch_context(self, tree: DiscoveryTree, leaf_id: str) -> str:
        """把一条分支的记录压缩为紧凑上下文（结构信息，非建议）。"""
        path = list(reversed(tree.path_to_root(leaf_id)))
        lines: List[str] = []
        for nid in path[-self.config.max_history:]:
            nd = tree.nodes[nid]
            tag = "synthetic" if (nd.diagnostics or {}).get("synthetic") else "recorded"
            lines.append(f"  [{tag}] {nd.sketch or '(no description)'} "
                         f"-> score {nd.score:.3f}")
        return "\n".join(lines)

    @staticmethod
    def _parse(raw: str) -> List[Dict[str, Any]]:
        text = (raw or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
        start, end = text.find("["), text.rfind("]")
        if start == -1 or end == -1 or end < start:
            return []
        try:
            items = json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            return []
        if not isinstance(items, list):
            return []
        return [it for it in items if isinstance(it, dict) and it.get("sketch")]


# ── 便捷入口 ────────────────────────────────────────────────────────────

def expand_pool_counterfactuals(worlds: List[Any], llm_fn: Callable[[str], str],
                                config: Optional[CounterfactualConfig] = None,
                                ) -> CounterfactualReport:
    """对世界池中的若干世界批量生成反事实（只处理叶子最少的若干树，控制成本）。"""
    cfg = config or CounterfactualConfig()
    gen = CounterfactualGenerator(llm_fn, cfg)
    total = CounterfactualReport(confidence=cfg.confidence)
    for w in worlds[: cfg.max_leaves if hasattr(cfg, "max_leaves") else 4]:
        r = gen.expand(w.tree)
        total.trees_processed += 1
        total.leaves_expanded += r.leaves_expanded
        total.synthetic_nodes += r.synthetic_nodes
        total.errors.extend(r.errors)
    return total
