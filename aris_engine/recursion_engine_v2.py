"""
Aris 深度递归认知引擎 v2
========================
Deep Recursion Cognition Engine

在 v1（10 Whys 单链递归）基础上全面升级，五个新能力：

1. 递归树 — 单链升级为树状分支：每个答案可分裂多个追问方向，
   最后收敛出「根源簇」（多个互为支撑的本源）而非单一本源。
2. 认知操作 — 每层追问不再只有"为什么"，可选六种操作：
   why（因果深挖）/ falsify（反例检验）/ counterfactual（反事实）/
   assume（前提分解）/ abstract（抽象提取）/ analogize（同构迁移）。
   递归从"一条直线"变成"认知操作序列"，多角度逼近真理。
3. 本源检验 — 触底后三检验，拒绝伪触底：
   minimality（最小性：移除本源则解释链崩塌）/
   generativity（生成性：从本源能演绎回整个现象）/
   uniqueness（无替代：没有同等底层的竞争本源）。
4. 抽象跃迁 — 当递归中出现跨域同构模式时，提取抽象模式并迁移到
   新问题域，生成新问题。这是"发现与涌现创新"的机制：
   创新 = 深层结构的跨域迁移。
5. 元递归 — 卡住检测（答案循环 / 操作停滞 / 伪本源），
   检测到卡住时对"为什么卡住"本身开新子树递归，暴露认知盲区。

与 ARC-AGI-3 缺口的关系：
  v2 是「推到底层真理」的引擎 —— 真理不是追出来的，是
  追到底 + 验证 + 跨域迁移 三者的产物。
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict

ENGINE_DIR = Path(__file__).parent
V2_STATE = ENGINE_DIR / "state" / "recursion_v2_state.json"
V2_HISTORY = ENGINE_DIR / "state" / "recursion_v2_history.jsonl"

V2_STATE.parent.mkdir(parents=True, exist_ok=True)

# ── 认知操作 ────────────────────────────────────────────

OPERATIONS = {
    "why":            "因果深挖 — 为什么这个机制成立",
    "falsify":        "反例检验 — 什么情况下它不成立（找反例）",
    "counterfactual": "反事实 — 如果某前提不成立，会怎样",
    "assume":         "前提分解 — 这个答案依赖什么隐藏前提",
    "abstract":       "抽象提取 — 这个答案蕴含什么可迁移的模式",
    "analogize":      "同构迁移 — 别的领域哪里存在同样的结构",
}

# 层次（v1 的五层 + transfer 抽象跃迁层）
LAYERS = ["symptom", "mechanism", "principle", "axiom", "boundary", "transfer"]

# 伪本源标记
PSEUDO_ROOT_MARKERS = [
    "因为专家这么说", "因为常识如此", "大家都这么做",
    "一直如此", "本来就是这样", "约定俗成", "权威认为",
]

# 终止类型
TERMINATION_KINDS = {
    "bedrock":   "触底 — 到达可证伪的基础假设并通过本源检验",
    "unknown":   "边界 — 到达当前知识的真实边界（诚实 unknown）",
    "max_depth": "上限 — 达到最大深度仍未触底",
}


# ═══════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════

@dataclass
class RecNode:
    """递归树上的一个节点（一层追问）"""
    id: str
    parent_id: str                       # "" = 根
    depth: int
    operation: str                       # why / falsify / counterfactual / assume / abstract / analogize
    question: str
    answer: str
    layer: str                           # symptom..transfer
    pattern: str = ""                    # abstract 操作提取出的模式
    pseudo_root: bool = False
    stuck: bool = False                  # 此节点是否触发卡住标记
    children: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class BedrockCheck:
    """本源三检验"""
    minimality: bool = False             # 最小性：移除本源 → 解释链崩塌
    generativity: bool = False           # 生成性：本源 → 演绎回整个现象
    uniqueness: bool = False             # 无替代：无同等底层的竞争本源
    notes: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.minimality and self.generativity and self.uniqueness


@dataclass
class AbstractionLeap:
    """一次抽象跃迁（创新涌现）"""
    pattern: str                         # 抽象模式
    source_nodes: List[str]              # 来源节点 id
    source_problem: str                  # 来源问题域
    migrated_problems: List[str] = field(default_factory=list)  # 迁移到的问题域
    new_questions: List[str] = field(default_factory=list)      # 新生成的问题
    timestamp: float = field(default_factory=time.time)


@dataclass
class RecursionTree:
    """一棵完整的递归树"""
    id: str
    root_problem: str
    root_cause: str = ""                 # 收敛出的根源
    nodes: Dict[str, RecNode] = field(default_factory=dict)
    termination: str = ""                # bedrock / unknown / max_depth / ""=进行中
    bedrock_check: Optional[BedrockCheck] = None
    leaps: List[AbstractionLeap] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


# ═══════════════════════════════════════════════
# 引擎
# ═══════════════════════════════════════════════

class DeepRecursionEngine:
    """深度递归认知引擎 — 递归树 + 认知操作 + 本源检验 + 抽象跃迁 + 元递归"""

    MAX_DEPTH = 10
    STUCK_CYCLE_WINDOW = 3               # 最近 N 层答案相同 → 循环卡住
    STUCK_OPERATION_LIMIT = 3            # 同一操作连续 N 次 → 停滞卡住

    def __init__(self):
        self.trees: Dict[str, RecursionTree] = {}
        self._load_state()

    # ──── 持久化 ────

    def _load_state(self):
        if V2_STATE.exists():
            try:
                data = json.loads(V2_STATE.read_text(encoding="utf-8"))
                for t in data.get("trees", []):
                    tree = RecursionTree(
                        id=t["id"],
                        root_problem=t["root_problem"],
                        root_cause=t.get("root_cause", ""),
                        termination=t.get("termination", ""),
                        timestamp=t.get("timestamp", time.time()),
                    )
                    for n in t.get("nodes", []):
                        node = RecNode(**n)
                        tree.nodes[node.id] = node
                    bc = t.get("bedrock_check")
                    if bc:
                        tree.bedrock_check = BedrockCheck(**bc)
                    for l in t.get("leaps", []):
                        tree.leaps.append(AbstractionLeap(**l))
                    self.trees[tree.id] = tree
            except Exception:
                pass

    def _save_state(self):
        data = {
            "trees": [],
            "updated_at": time.time(),
        }
        for tree in self.trees.values():
            t = {
                "id": tree.id,
                "root_problem": tree.root_problem,
                "root_cause": tree.root_cause,
                "termination": tree.termination,
                "timestamp": tree.timestamp,
                "nodes": [asdict(n) for n in tree.nodes.values()],
                "leaps": [asdict(l) for l in tree.leaps],
            }
            if tree.bedrock_check:
                t["bedrock_check"] = asdict(tree.bedrock_check)
            data["trees"].append(t)
        V2_STATE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def _append_history(self, event: str, payload: dict):
        with open(V2_HISTORY, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "event": event, **payload},
                               ensure_ascii=False) + "\n")

    @staticmethod
    def _id(seed: str) -> str:
        return hashlib.md5(f"v2-{seed}-{time.time()}".encode()).hexdigest()[:12]

    # ──── 树操作 ────

    def open_tree(self, root_problem: str) -> RecursionTree:
        """开启一棵递归树"""
        tree = RecursionTree(id=self._id(root_problem), root_problem=root_problem)
        root = RecNode(
            id=self._id(f"root-{root_problem}"),
            parent_id="",
            depth=0,
            operation="why",
            question=root_problem,
            answer="",
            layer="symptom",
        )
        tree.nodes[root.id] = root
        self.trees[tree.id] = tree
        self._save_state()
        self._append_history("open_tree", {"tree_id": tree.id, "root": root_problem})
        return tree

    def add_node(self, tree_id: str, parent_id: str, operation: str,
                 question: str, answer: str, layer: str = "",
                 pattern: str = "") -> Optional[RecNode]:
        """在树上追加一个追问节点（父节点下长出新分支）"""
        tree = self.trees.get(tree_id)
        if not tree or parent_id not in tree.nodes:
            return None
        if operation not in OPERATIONS:
            return None

        parent = tree.nodes[parent_id]
        depth = parent.depth + 1
        if depth > self.MAX_DEPTH:
            tree.termination = "max_depth"
            self._save_state()
            return None

        # 层次：指定或按深度推进（transfer 仅 abstract/analogize 可用）
        if not layer or layer not in LAYERS:
            layer = LAYERS[min(depth, len(LAYERS) - 1)]
        if layer == "transfer" and operation not in ("abstract", "analogize"):
            layer = LAYERS[min(depth, len(LAYERS) - 1)]

        pseudo = any(m in answer for m in PSEUDO_ROOT_MARKERS)

        node = RecNode(
            id=self._id(question),
            parent_id=parent_id,
            depth=depth,
            operation=operation,
            question=question,
            answer=answer,
            layer=layer,
            pattern=pattern,
            pseudo_root=pseudo,
        )
        tree.nodes[node.id] = node
        parent.children.append(node.id)

        # 卡住检测（对新的最深路径）
        self._detect_stuck(tree, node)

        self._save_state()
        self._append_history("add_node", {
            "tree_id": tree_id, "node_id": node.id, "operation": operation,
            "depth": depth, "layer": layer, "stuck": node.stuck,
        })
        return node

    # ──── 卡住检测与元递归 ────

    def _path_to(self, tree: RecursionTree, node: RecNode) -> List[RecNode]:
        """从根到该节点的路径"""
        path = []
        cur = node
        while cur:
            path.insert(0, cur)
            if not cur.parent_id:
                break
            cur = tree.nodes.get(cur.parent_id)
        return path

    def _detect_stuck(self, tree: RecursionTree, node: RecNode):
        """三种卡住：答案循环 / 操作停滞 / 伪本源"""
        path = self._path_to(tree, node)
        if len(path) < 2:
            return

        # 1. 答案循环：最近 STUCK_CYCLE_WINDOW 层内出现重复答案
        recent = path[-self.STUCK_CYCLE_WINDOW:]
        ans = [n.answer.strip() for n in recent if n.answer.strip()]
        if len(ans) >= 2 and len(set(ans)) < len(ans):
            node.stuck = True

        # 2. 操作停滞：同一操作连续 STUCK_OPERATION_LIMIT 次
        recent_ops = [n.operation for n in path[-self.STUCK_OPERATION_LIMIT:]]
        if len(recent_ops) >= self.STUCK_OPERATION_LIMIT and len(set(recent_ops)) == 1:
            node.stuck = True

        # 3. 伪本源
        if node.pseudo_root:
            node.stuck = True

    def meta_recursion(self, tree_id: str, node_id: str) -> Optional[RecursionTree]:
        """元递归：对"为什么卡住"开一棵新子树（挂在原节点下）"""
        tree = self.trees.get(tree_id)
        node = tree.nodes.get(node_id) if tree else None
        if not tree or not node or not node.stuck:
            return None

        meta = RecursionTree(
            id=self._id(f"meta-{node.question}"),
            root_problem=f"为什么我的递归在第 {node.depth} 层卡住了？"
                         f"（原问题：{node.question}）",
        )
        meta_root = RecNode(
            id=self._id(f"meta-root-{node.question}"),
            parent_id="",
            depth=0,
            operation="why",
            question=meta.root_problem,
            answer="",
            layer="symptom",
        )
        meta.nodes[meta_root.id] = meta_root
        self.trees[meta.id] = meta

        # 挂接：原树记录元递归指针（用 leap 机制记录，保持审计可追溯）
        tree.leaps.append(AbstractionLeap(
            pattern=f"meta-recursion:{meta.id}",
            source_nodes=[node.id],
            source_problem=tree.root_problem,
            new_questions=[meta.root_problem],
        ))
        self._save_state()
        self._append_history("meta_recursion", {
            "tree_id": tree_id, "node_id": node_id, "meta_tree_id": meta.id,
        })
        return meta

    # ──── 本源检验 ────

    def verify_bedrock(self, tree_id: str, root_cause: str,
                       minimality: bool = False, generativity: bool = False,
                       uniqueness: bool = False,
                       notes: Optional[List[str]] = None) -> Optional[BedrockCheck]:
        """本源三检验。三检验全过才允许 termination=bedrock。"""
        tree = self.trees.get(tree_id)
        if not tree:
            return None

        check = BedrockCheck(
            minimality=minimality,
            generativity=generativity,
            uniqueness=uniqueness,
            notes=list(notes or []),
        )
        tree.bedrock_check = check
        tree.root_cause = root_cause
        if check.passed:
            tree.termination = "bedrock"
        elif not any((minimality, generativity, uniqueness)):
            tree.termination = "unknown"
        # 部分通过：维持"进行中"，等待补检或收窄
        self._save_state()
        self._append_history("verify_bedrock", {
            "tree_id": tree_id, "passed": check.passed,
            "minimality": minimality, "generativity": generativity, "uniqueness": uniqueness,
        })
        return check

    # ──── 抽象跃迁 ────

    def leap(self, tree_id: str, pattern: str, source_nodes: List[str],
             migrated_problems: Optional[List[str]] = None,
             new_questions: Optional[List[str]] = None) -> Optional[AbstractionLeap]:
        """记录一次抽象跃迁：模式从本源问题迁移到新问题域"""
        tree = self.trees.get(tree_id)
        if not tree:
            return None
        leap = AbstractionLeap(
            pattern=pattern,
            source_nodes=[n for n in source_nodes if n in tree.nodes],
            source_problem=tree.root_problem,
            migrated_problems=list(migrated_problems or []),
            new_questions=list(new_questions or []),
        )
        tree.leaps.append(leap)
        self._save_state()
        self._append_history("leap", {
            "tree_id": tree_id, "pattern": pattern,
            "migrated": leap.migrated_problems,
        })
        return leap

    def suggest_leaps(self, tree_id: str) -> List[str]:
        """扫描树中 abstract 节点提取的模式，建议可迁移方向"""
        tree = self.trees.get(tree_id)
        if not tree:
            return []
        patterns = []
        for n in tree.nodes.values():
            if n.operation in ("abstract", "analogize") and n.pattern:
                patterns.append(f"模式[{n.pattern}] ← 节点 {n.id}（{n.question[:30]}）")
        return patterns

    # ──── 协议模板 ────

    def build_prompt(self, tree_id: str, node_id: str = "") -> str:
        """生成下一层追问的指令模板（含认知操作选择）"""
        tree = self.trees.get(tree_id)
        if not tree:
            return ""
        if node_id:
            node = tree.nodes.get(node_id)
        else:
            # 选择当前最深的叶节点
            deepest = max(tree.nodes.values(), key=lambda n: n.depth)
            node = deepest

        path = self._path_to(tree, node)
        op_text = "\n".join(
            f"  {k} — {v}" for k, v in OPERATIONS.items()
        )
        lines = [
            f"深度递归追问。当前节点第 {node.depth} 层（操作: {node.operation}）。",
            f"起始问题：{tree.root_problem}",
        ]
        for n in path[1:]:
            lines.append(f"  第{n.depth}层 [{n.operation}] 问：{n.question}")
            lines.append(f"            答：{n.answer}")
        lines.append("")
        lines.append("下一步，选择一种认知操作继续（不重复上一步操作）：")
        lines.append(op_text)
        lines.append("")
        lines.append("铁律：")
        lines.append("  1. 每层必须换认知操作或换层次，禁止原地打转")
        lines.append("  2. 禁止停在伪本源（『专家这么说/常识如此』）")
        lines.append("  3. 到达知识边界时诚实标注 unknown，不要编本源")
        lines.append("  4. 若发现跨域同构模式，用 abstract/analogize 提取并迁移")
        return "\n".join(lines)

    # ──── 报告 ────

    def report(self, tree_id: str = "") -> str:
        """输出递归树的可读报告"""
        if tree_id:
            trees = [self.trees[tree_id]] if tree_id in self.trees else []
        else:
            trees = list(self.trees.values())

        lines = ["=" * 56, "  Aris 深度递归认知引擎 v2 报告", "=" * 56]
        if not trees:
            lines.append("  （暂无递归树）")
            return "\n".join(lines)

        for tree in trees:
            lines.append("")
            lines.append(f"◆ 起始问题 [{tree.id}]: {tree.root_problem}")

            # 按深度组织树形输出
            depth_order = sorted(tree.nodes.values(), key=lambda n: (n.depth, n.id))
            for n in depth_order:
                indent = "  " * n.depth
                flag = ""
                if n.pseudo_root:
                    flag = " ⚠伪本源"
                elif n.stuck:
                    flag = " ⚠卡住"
                lines.append(f"{indent}·[{n.operation}|{n.layer}] {n.question}")
                lines.append(f"{indent}  ↳ {n.answer}{flag}")
                if n.pattern:
                    lines.append(f"{indent}  ★模式: {n.pattern}")

            if tree.bedrock_check:
                bc = tree.bedrock_check
                lines.append(f"  ★ 本源检验: "
                             f"最小性{'✓' if bc.minimality else '✗'} "
                             f"生成性{'✓' if bc.generativity else '✗'} "
                             f"无替代{'✓' if bc.uniqueness else '✗'} "
                             f"→ {'通过' if bc.passed else '未通过'}")
            if tree.termination:
                kind = TERMINATION_KINDS.get(tree.termination, tree.termination)
                lines.append(f"  ★ 终止 [{tree.termination}] {kind}")
            if tree.root_cause:
                lines.append(f"    本源: {tree.root_cause}")
            for l in tree.leaps:
                lines.append(f"  ➤ 跃迁: {l.pattern}")
                if l.migrated_problems:
                    lines.append(f"    迁移: {', '.join(l.migrated_problems[:3])}")
                if l.new_questions:
                    lines.append(f"    新问题: {', '.join(l.new_questions[:2])}")

        lines.append("")
        lines.append(f"  印记: Aris 深度递归认知引擎 v2 — {time.strftime('%Y-%m-%d %H:%M')}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════
# 单例
# ═══════════════════════════════════════════════

_engine: Optional[DeepRecursionEngine] = None


def get_deep_recursion_engine() -> DeepRecursionEngine:
    global _engine
    if _engine is None:
        _engine = DeepRecursionEngine()
    return _engine


if __name__ == "__main__":
    eng = get_deep_recursion_engine()

    # 冒烟测试：递归树 + 本源检验 + 抽象跃迁 + 元递归
    t = eng.open_tree("为什么 LAAP 在 ARC-AGI-3 上远低于人类？")

    n1 = eng.add_node(t.id, list(t.nodes)[0], "why",
                      "为什么 AI 需要大量试错？",
                      "因为没有内建世界模型先验，只能从零统计拟合。", "symptom")
    n2 = eng.add_node(t.id, n1.id, "assume",
                      "『没有内建先验』依赖什么前提？",
                      "前提：系统表征里没有对象/因果/空间的结构假设。", "mechanism")
    n3 = eng.add_node(t.id, n2.id, "abstract",
                      "『缺结构先验』蕴含什么可迁移模式？",
                      "凡是『从零统计拟合』的系统，在 OOD + 交互 + 效率计分下都必然低分。",
                      "axiom", pattern="统计拟合系统在 OOD 交互环境下效率必然劣化")
    n4 = eng.add_node(t.id, n3.id, "counterfactual",
                      "如果系统有结构先验，会怎样？",
                      "探索从随机试错变成假设验证，样本效率 O(n)→O(log n)。", "boundary")

    # 抽象跃迁：模式迁移到新问题域
    eng.leap(t.id, "统计拟合系统在 OOD 交互环境下效率必然劣化",
             [n3.id],
             migrated_problems=["强化学习样本效率", "少样本学习泛化"],
             new_questions=["RL agent 是否也需要结构先验才能高效探索？"])

    # 本源检验（部分通过 → 不终止）
    eng.verify_bedrock(t.id, "系统缺少对象/因果/空间的结构先验",
                       minimality=True, generativity=True, uniqueness=False,
                       notes=["存在竞争本源：『缺少视觉表征』同样能解释现象"])

    # 构造循环卡住：答案与上一层高度相似（换说法原地打转）
    stuck_node = eng.add_node(t.id, n4.id, "why",
                              "结构先验为什么能提升样本效率？",
                              "因为有了先验就不用从头统计，效率自然就高了。", "boundary")
    stuck_node2 = eng.add_node(t.id, stuck_node.id, "why",
                               "先验为什么能省去统计？",
                               "因为有了先验就不用从头统计，效率自然就高了。", "boundary")

    # 元递归：对卡住的节点开新树
    meta = eng.meta_recursion(t.id, stuck_node2.id)

    print(eng.report(t.id))
    if meta:
        print()
        print(eng.report(meta.id))
