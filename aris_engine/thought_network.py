"""
Aris 神经思考创新涌现网络 v1
=============================
Neuro-Thought Emergence Network (NTEN)

把 v2 深度递归（单棵树 + 抽象跃迁）升级为**可生长的认知网络**：

- 神经：每个思考单元（问题/模式/概念/经验/主张）都是网络节点，
  带语义嵌入，节点间靠向量相似度与结构关系关联；
- 思考：递归树 / 质疑对抗 / 表征重组都在这个网络上操作，
  树的节点就是网络的节点，树间交叉就是网络的边；
- 创新涌现：跨域同构检测（交叉检测）发现汇合点，表征重组
  （范畴合并/参照系变换/对偶化/尺度跃迁）在汇合点生成新节点，
  网络因此生长。

核心论断（2026-08-22 与 Lorry 共同推导）：
  跳跃（溯因）不是灵感的产物，而是多条独立演化链的结构交叉。
  本引擎不要求 LLM 自己跳——机制维护多链并行 + 交叉检测 +
  表征重组，让"汇合"成为结构性的必然，而非随机事件。

嵌入策略（生产级降级）：
  优先 sentence-transformers（paraphrase-multilingual-MiniLM-L12-v2）；
  不可用时降级为确定性字符 n-gram 哈希嵌入（零依赖，任何环境可跑）。

印记: Aris 永远记得 Lorry — 网络生长在 Aris 的认知底座里。
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

ENGINE_DIR = Path(__file__).parent
NTEN_STATE = ENGINE_DIR / "state" / "thought_network_state.json"
NTEN_HISTORY = ENGINE_DIR / "state" / "thought_network_history.jsonl"

NTEN_STATE.parent.mkdir(parents=True, exist_ok=True)

# ── 节点类型 ──────────────────────────────────────────────
NODE_KINDS = {
    "problem":    "问题 — 待解或已解的思考起点",
    "pattern":    "模式 — 抽象出的可迁移结构",
    "concept":    "概念 — 表征重组产生的新范畴",
    "experience": "经验 — 模拟经验（world_model 反事实产物）",
    "claim":      "主张 — 带置信度的论断",
    "insight":    "洞见 — 交叉点涌现的新认知",
}

# ── 边类型 ────────────────────────────────────────────────
EDGE_RELATIONS = {
    "inherit":    "继承 — 树上的父子关系",
    "associate":  "关联 — 语义相近（嵌入相似度）",
    "isomorphic": "同构 — 结构等价（跨域模式一致）",
    "cross":      "交叉 — 独立链汇合点",
    "causal":     "因果 — 一节点是另一节点的原因/前提",
    "recombine":  "重组 — 由表征重组产生",
}

# ── 表征重组操作 ──────────────────────────────────────────
RECOMBINE_OPS = {
    "category_merge": "范畴合并 — 两个不同范畴归为同一类（引力/惯性加速度→一类）",
    "frame_shift":    "参照系变换 — 从对象视角换到关系视角",
    "dualize":        "对偶化 — 生成问题的对偶形式",
    "scale_jump":     "尺度跃迁 — 局部规律提升为全局规律",
}

# 嵌入模型（优先）与维度
ST_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
HASH_EMBED_DIM = 256
ST_EMBED_DIM = 384

# 交叉检测阈值
CROSS_SIM_THRESHOLD = 0.55
ASSOC_TOP_K = 5


# ═══════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════

@dataclass
class ThoughtNode:
    """网络上的一个思考单元"""
    id: str
    kind: str                            # problem/pattern/concept/experience/claim/insight
    content: str
    domain: str = ""                     # 问题域（跨域检测依据）
    embedding: List[float] = field(default_factory=list)
    structure: Optional[Dict] = None     # 结构化表示（关系元组，供结构对齐检测）
    meta: Dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class ThoughtEdge:
    """节点间的一条关联"""
    id: str
    source: str
    target: str
    relation: str                        # inherit/associate/isomorphic/cross/causal/recombine
    strength: float = 0.5                # 0-1
    created_at: float = field(default_factory=time.time)


@dataclass
class Crossing:
    """一个交叉点候选（独立链的汇合处）"""
    id: str
    node_a: str
    node_b: str
    similarity: float
    method: str = "semantic"             # semantic（表层语义）/ structural（结构对齐）
    status: str = "candidate"            # candidate / recombined / rejected
    created_at: float = field(default_factory=time.time)


@dataclass
class Recombination:
    """一次表征重组记录"""
    id: str
    operation: str                       # category_merge/frame_shift/dualize/scale_jump
    source_nodes: List[str]
    result_node: str
    created_at: float = field(default_factory=time.time)


# ═══════════════════════════════════════════════
# 嵌入（生产级降级）
# ═══════════════════════════════════════════════

_ST_MODEL = None


def _get_st_model():
    """lazy 加载 sentence-transformers 模型；不可用返回 None"""
    global _ST_MODEL
    if _ST_MODEL is not None:
        return _ST_MODEL
    try:
        from sentence_transformers import SentenceTransformer
        _ST_MODEL = SentenceTransformer(ST_MODEL_NAME)
        return _ST_MODEL
    except Exception:
        return None


def _hash_embed(text: str, dim: int = HASH_EMBED_DIM) -> List[float]:
    """确定性字符 n-gram 哈希嵌入（零依赖 fallback）。

    对文本做 1-3 gram 的 md5 哈希，按哈希值散列到 dim 维向量，
    带符号叠加后 L2 归一化。相同文本永远得到相同向量。
    """
    vec = [0.0] * dim
    t = text.lower()
    for n in (1, 2, 3):
        for i in range(max(0, len(t) - n + 1)):
            gram = t[i:i + n]
            h = int(hashlib.md5(gram.encode("utf-8")).hexdigest()[:8], 16)
            idx = h % dim
            sign = 1.0 if (h >> 8) & 1 else -1.0
            vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [round(v / norm, 6) for v in vec]


def embed_text(text: str) -> List[float]:
    """嵌入文本：优先 sentence-transformers，降级哈希嵌入。"""
    model = _get_st_model()
    if model is not None:
        try:
            vec = model.encode([text], normalize_embeddings=True)[0]
            return [round(float(x), 6) for x in vec]
        except Exception:
            pass
    return _hash_embed(text)


def cosine_sim(a: List[float], b: List[float]) -> float:
    """余弦相似度（长度不等时按短对齐）"""
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    dot = sum(a[i] * b[i] for i in range(n))
    na = math.sqrt(sum(x * x for x in a[:n])) or 1.0
    nb = math.sqrt(sum(x * x for x in b[:n])) or 1.0
    return dot / (na * nb)


# ═══════════════════════════════════════════════
# 引擎
# ═══════════════════════════════════════════════

class ThoughtEmergenceNetwork:
    """神经思考创新涌现网络 — 关联思考 + 知识泛化 + 创新涌现"""

    def __init__(self):
        self.nodes: Dict[str, ThoughtNode] = {}
        self.edges: Dict[str, ThoughtEdge] = {}
        self.crossings: Dict[str, Crossing] = {}
        self.recombinations: List[Recombination] = []
        self._load_state()

    # ──── 持久化 ────

    def _load_state(self):
        if NTEN_STATE.exists():
            try:
                data = json.loads(NTEN_STATE.read_text(encoding="utf-8"))
                for n in data.get("nodes", []):
                    self.nodes[n["id"]] = ThoughtNode(**n)
                for e in data.get("edges", []):
                    self.edges[e["id"]] = ThoughtEdge(**e)
                for c in data.get("crossings", []):
                    self.crossings[c["id"]] = Crossing(**c)
                for r in data.get("recombinations", []):
                    self.recombinations.append(Recombination(**r))
            except Exception:
                pass

    def _save_state(self):
        data = {
            "nodes": [asdict(n) for n in self.nodes.values()],
            "edges": [asdict(e) for e in self.edges.values()],
            "crossings": [asdict(c) for c in self.crossings.values()],
            "recombinations": [asdict(r) for r in self.recombinations],
            "updated_at": time.time(),
        }
        NTEN_STATE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def _append_history(self, event: str, payload: dict):
        with open(NTEN_HISTORY, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "event": event, **payload},
                               ensure_ascii=False) + "\n")

    @staticmethod
    def _id(seed: str) -> str:
        return hashlib.md5(f"nten-{seed}-{time.time()}".encode()).hexdigest()[:12]

    # ──── 节点与边 ────

    def add_node(self, content: str, kind: str = "insight",
                 domain: str = "", meta: Optional[Dict[str, str]] = None) -> ThoughtNode:
        """加入一个思考节点（自动嵌入）"""
        if kind not in NODE_KINDS:
            kind = "insight"
        node = ThoughtNode(
            id=self._id(content),
            kind=kind,
            content=content,
            domain=domain or "general",
            embedding=embed_text(content),
            meta=dict(meta or {}),
        )
        self.nodes[node.id] = node
        self._save_state()
        self._append_history("add_node", {
            "node_id": node.id, "kind": kind, "domain": node.domain,
        })
        return node

    def add_edge(self, source: str, target: str, relation: str = "associate",
                 strength: float = 0.5) -> Optional[ThoughtEdge]:
        """在节点间建立关联边"""
        if source not in self.nodes or target not in self.nodes:
            return None
        if relation not in EDGE_RELATIONS:
            return None
        edge = ThoughtEdge(
            id=self._id(f"{source}-{target}"),
            source=source,
            target=target,
            relation=relation,
            strength=max(0.0, min(1.0, strength)),
        )
        self.edges[edge.id] = edge
        self._save_state()
        self._append_history("add_edge", {
            "edge_id": edge.id, "source": source, "target": target,
            "relation": relation, "strength": edge.strength,
        })
        return edge

    # ──── 关联发现（神经） ────

    def associate(self, node_id: str, top_k: int = ASSOC_TOP_K,
                  exclude_same_domain: bool = False) -> List[Tuple[str, float]]:
        """找与节点最相似的节点（语义关联）"""
        node = self.nodes.get(node_id)
        if not node:
            return []
        scored = []
        for other in self.nodes.values():
            if other.id == node_id:
                continue
            if exclude_same_domain and other.domain == node.domain:
                continue
            sim = cosine_sim(node.embedding, other.embedding)
            if sim > 0.3:
                scored.append((other.id, round(sim, 4)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    # ──── 交叉检测（创新涌现的前提） ────

    @staticmethod
    def structure_similarity(s1: Dict, s2: Dict) -> float:
        """结构相似度（Gentner 结构映射：只比较关系结构与角色形状，
        不比较角色内容——A:B = C:D 不管 A 和 C 是什么）。

        三因子加权：
          - 关系类型重合（Jaccard）权重 0.5 —— 结构对齐的主信号
          - 角色形状重合（Jaccard）权重 0.3 —— 结构骨架
          - 机制语义（嵌入余弦）权重 0.2 —— 辅助，不主导
        """
        rel_1 = {r.get("type", "") for r in s1.get("relations", [])}
        rel_2 = {r.get("type", "") for r in s2.get("relations", [])}
        role_1 = set(s1.get("roles", {}).keys())
        role_2 = set(s2.get("roles", {}).keys())

        def jaccard(a, b):
            union = a | b
            if not union:
                return 0.0
            return len(a & b) / len(union)

        rel_score = jaccard(rel_1, rel_2)
        role_score = jaccard(role_1, role_2)
        mech_score = cosine_sim(
            embed_text(s1.get("mechanism", "")),
            embed_text(s2.get("mechanism", "")),
        )

        # 没有关系类型时结构相似度无意义（纯文本节点不参与结构检测）
        if not rel_1 or not rel_2:
            return 0.0
        return round(0.5 * rel_score + 0.3 * role_score + 0.2 * mech_score, 4)

    def register_structure(self, node_id: str, structure: Dict) -> Optional[ThoughtNode]:
        """给节点注册结构化表示（关系元组）。

        结构化由 LLM/用户生成（引擎提供提示模板），注册后节点
        参与结构对齐检测——深层同构从此可被自动发现。
        """
        node = self.nodes.get(node_id)
        if not node:
            return None
        node.structure = structure
        self._save_state()
        self._append_history("register_structure", {
            "node_id": node_id,
            "relations": [r.get("type") for r in structure.get("relations", [])],
        })
        return node

    def build_structuralize_prompt(self, node_id: str) -> str:
        """生成模式结构化的指令模板（供 LLM 把文本模式转成关系元组）"""
        node = self.nodes.get(node_id)
        if not node:
            return ""
        return (
            f"把下面的模式/命题结构化为关系元组 JSON。\n\n"
            f"内容：{node.content}\n\n"
            f"输出 JSON，格式：\n"
            f"{{\"relations\": [{{\"type\": \"关系类型\", \"args\": [\"参与者1\", \"参与者2\"]}}], "
            f"\"roles\": {{\"角色名\": \"参与者\", ...}}, "
            f"\"mechanism\": \"一句话机制说明\"}}\n\n"
            f"规则：\n"
            f"1. relations 的 type 用抽象关系名（equivalence/consistency/dependence/"
            f"feedback/causality/conflict/tradeoff...），不要用领域术语；\n"
            f"2. roles 是结构骨架（如 source/target/benchmark/constraint），"
            f"值是参与者；\n"
            f"3. mechanism 用一句话说明机制；\n"
            f"4. 只输出 JSON，不要其他文字。"
        )

    def detect_crossings(self, threshold: float = CROSS_SIM_THRESHOLD,
                         auto_add_edge: bool = False,
                         structural: bool = True) -> List[Crossing]:
        """双路交叉检测：表层语义路径 + 结构对齐路径。

        - 语义路径：跨域节点对嵌入相似度（表层同构）；
        - 结构路径：跨域节点对若都有结构化表示，比较结构相似度
          （深层同构，Gentner 结构映射——只对齐关系与骨架，
          不管角色内容）。

        structural=True 时结构路径自动并入，深层同构无需人工声明。
        """
        found = {}
        ids = list(self.nodes.keys())
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = self.nodes[ids[i]], self.nodes[ids[j]]
                if a.domain == b.domain:
                    continue

                # 结构路径（优先）：结构相似度高于 0.5 即视为深层同构
                if structural and a.structure and b.structure:
                    ssim = self.structure_similarity(a.structure, b.structure)
                    if ssim >= max(0.5, threshold * 0.6):
                        cid = self._id(f"{a.id}-{b.id}")
                        crossing = Crossing(
                            id=cid, node_a=a.id, node_b=b.id,
                            similarity=ssim, method="structural",
                        )
                        found[cid] = crossing
                        if auto_add_edge:
                            self.add_edge(a.id, b.id, "isomorphic", strength=ssim)
                        continue

                # 语义路径（表层）：嵌入相似度
                sim = cosine_sim(a.embedding, b.embedding)
                if sim >= threshold:
                    cid = self._id(f"{a.id}-{b.id}")
                    crossing = Crossing(
                        id=cid, node_a=a.id, node_b=b.id,
                        similarity=round(sim, 4), method="semantic",
                    )
                    found[cid] = crossing
                    if auto_add_edge:
                        self.add_edge(a.id, b.id, "isomorphic", strength=sim)

        if found:
            self.crossings.update(found)
            self._save_state()
            self._append_history("detect_crossings", {
                "count": len(found), "threshold": threshold,
                "structural": structural,
            })
        return list(found.values())

    def declare_crossing(self, node_a: str, node_b: str,
                         similarity: float = 0.9) -> Optional[Crossing]:
        """显式声明一个交叉点（LLM/用户确认结构同构后调用）。

        嵌入检测负责表层候选，结构同构（藏在表层语义之下的深层
        平行）需要 LLM/用户的判断——这是认知分工：
        引擎提供候选与记录，判断交给真正的智能体。
        """
        if node_a not in self.nodes or node_b not in self.nodes:
            return None
        if self.nodes[node_a].domain == self.nodes[node_b].domain:
            return None
        cid = self._id(f"{node_a}-{node_b}")
        crossing = Crossing(
            id=cid,
            node_a=node_a,
            node_b=node_b,
            similarity=max(0.0, min(1.0, similarity)),
        )
        self.crossings[cid] = crossing
        self.add_edge(node_a, node_b, "isomorphic", strength=crossing.similarity)
        self._save_state()
        self._append_history("declare_crossing", {
            "node_a": node_a, "node_b": node_b,
            "similarity": crossing.similarity,
        })
        return crossing

    # ──── 表征重组（创新涌现的执行） ────

    def recombine(self, node_a: str, node_b: str, operation: str,
                  result_content: str, result_domain: str = "") -> Optional[ThoughtNode]:
        """在交叉点执行表征重组，生成新节点。

        operation 决定记录语义；result_content 由调用者
        （LLM/用户）提供——引擎负责结构、关联与审计。
        """
        if node_a not in self.nodes or node_b not in self.nodes:
            return None
        if operation not in RECOMBINE_OPS:
            return None

        new_node = self.add_node(
            content=result_content,
            kind="concept",
            domain=result_domain or "synthesis",
            meta={
                "operation": operation,
                "parents": f"{node_a}|{node_b}",
            },
        )
        self.add_edge(node_a, new_node.id, "recombine", strength=0.9)
        self.add_edge(node_b, new_node.id, "recombine", strength=0.9)
        # 交叉点标记为已重组
        for c in self.crossings.values():
            if {c.node_a, c.node_b} == {node_a, node_b}:
                c.status = "recombined"

        self.recombinations.append(Recombination(
            id=self._id(f"rec-{operation}"),
            operation=operation,
            source_nodes=[node_a, node_b],
            result_node=new_node.id,
        ))
        self._save_state()
        self._append_history("recombine", {
            "operation": operation, "node_a": node_a, "node_b": node_b,
            "result_node": new_node.id,
        })
        return new_node

    def build_recombine_prompt(self, node_a: str, node_b: str) -> str:
        """生成表征重组的指令模板（供 LLM 生成重组内容）"""
        a, b = self.nodes.get(node_a), self.nodes.get(node_b)
        if not a or not b:
            return ""
        ops = "\n".join(f"  {k} — {v}" for k, v in RECOMBINE_OPS.items())
        return (
            f"两个独立领域的思考单元出现结构同构（相似度已由网络检测）。\n\n"
            f"节点A [{a.domain}]: {a.content}\n"
            f"节点B [{b.domain}]: {b.content}\n\n"
            f"它们是同一个深层结构在不同领域的分身。选择一种表征重组操作：\n{ops}\n\n"
            f"执行后输出：重组产生的新概念/新命题（一句话），以及它所属的新领域。\n"
            f"这是创新涌现的关键一步——不要停留在描述两者相似，要生成第三者。"
        )

    # ──── 模拟经验通道 ────

    def add_experience(self, description: str, source: str = "world_model",
                       domain: str = "experience") -> ThoughtNode:
        """加入一条模拟经验（world_model 反事实/预测产物）。

        给溯因提供"感性原料"：LLM 没有失重感，但可以处理
        "结构化的失重数据"——模拟经验节点就是这种数据。
        """
        return self.add_node(
            content=description,
            kind="experience",
            domain=domain,
            meta={"source": source},
        )

    # ──── 与 v2 深度递归桥接 ────

    def import_recursion_tree(self, tree_id: str,
                              v2_engine: Optional[object] = None) -> int:
        """把 v2 递归树的节点导入网络（pattern 节点成为网络模式节点）。

        桥接后，多棵树的模式在网络层交叉——这就是 v3 的核心升级。
        """
        if v2_engine is None:
            try:
                from recursion_engine_v2 import get_deep_recursion_engine
                v2_engine = get_deep_recursion_engine()
            except Exception:
                return 0
        tree = v2_engine.trees.get(tree_id)
        if not tree:
            return 0
        count = 0
        for node in tree.nodes.values():
            if not node.answer and node.depth == 0:
                continue
            kind = "pattern" if node.pattern else "problem"
            n = self.add_node(
                content=node.pattern or node.answer,
                kind=kind,
                domain=tree.root_problem[:40],
                meta={"tree_id": tree_id, "v2_node_id": node.id,
                      "operation": node.operation},
            )
            count += 1
        self._append_history("import_recursion_tree", {
            "tree_id": tree_id, "imported": count,
        })
        return count

    # ──── 网络统计与报告 ────

    def stats(self) -> Dict:
        """网络生长统计"""
        kinds = {}
        for n in self.nodes.values():
            kinds[n.kind] = kinds.get(n.kind, 0) + 1
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "crossings": len(self.crossings),
            "recombinations": len(self.recombinations),
            "domains": sorted({n.domain for n in self.nodes.values()}),
            "kinds": kinds,
        }

    def report(self) -> str:
        """网络可读报告"""
        s = self.stats()
        lines = ["=" * 56, "  Aris 神经思考创新涌现网络 报告", "=" * 56]
        lines.append(f"  节点: {s['nodes']}  边: {s['edges']}  "
                     f"交叉: {s['crossings']}  重组: {s['recombinations']}")
        lines.append(f"  领域: {', '.join(s['domains'][:8])}")
        if s['kinds']:
            lines.append(f"  类型分布: {s['kinds']}")
        lines.append("")
        for n in list(self.nodes.values())[-12:]:
            lines.append(f"  · [{n.kind}|{n.domain[:18]}] {n.content[:50]}")
        lines.append("")
        for c in list(self.crossings.values())[-5:]:
            lines.append(f"  ✕ 交叉 [{c.status}] sim={c.similarity}")
            lines.append(f"      A: {self.nodes.get(c.node_a, ThoughtNode(id='', kind='', content='?')).content[:40]}")
            lines.append(f"      B: {self.nodes.get(c.node_b, ThoughtNode(id='', kind='', content='?')).content[:40]}")
        lines.append("")
        lines.append(f"  印记: Aris 神经思考创新涌现网络 v1 — "
                     f"{time.strftime('%Y-%m-%d %H:%M')}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════
# 单例
# ═══════════════════════════════════════════════

_network: Optional[ThoughtEmergenceNetwork] = None


def get_thought_network() -> ThoughtEmergenceNetwork:
    global _network
    if _network is None:
        _network = ThoughtEmergenceNetwork()
    return _network


if __name__ == "__main__":
    net = get_thought_network()

    # 冒烟测试：结构对齐自动发现深层同构（无需人工声明）
    # 链 A：物理学（等效原理）
    a1 = net.add_node("引力质量与惯性质量在实验中始终相等", kind="pattern", domain="physics")
    # 链 B：软件工程（缓存一致性）
    b1 = net.add_node("缓存与主存数据不一致时以主存为准但缓存失效成本高",
                      kind="pattern", domain="software")

    print("路径一：纯语义检测（结构同构藏在表层之下，0 命中预期）:")
    crossings = net.detect_crossings(auto_add_edge=True, structural=False)
    print(f"  语义候选: {len(crossings)}")

    print("\n结构化注册（LLM/用户在真实使用中生成，这里用等价结构演示）:")
    print(net.build_structuralize_prompt(a1.id))
    net.register_structure(a1.id, {
        "relations": [{"type": "equivalence",
                        "args": ["引力质量", "惯性质量"]}],
        "roles": {"source": "引力质量", "target": "惯性质量",
                   "benchmark": "实验测量"},
        "mechanism": "两种不同来源的质量在数值上恒等，同一性由基准参照决定",
    })
    net.register_structure(b1.id, {
        "relations": [{"type": "equivalence",
                        "args": ["缓存数据", "主存数据"]}],
        "roles": {"source": "缓存", "target": "主存",
                   "benchmark": "一致性协议"},
        "mechanism": "两个不同来源的数据在一致性上对齐，以主存为基准",
    })
    print("  结构已注册：equivalence × 2")

    print("\n路径二：结构对齐检测（深层同构自动发现）:")
    crossings2 = net.detect_crossings(auto_add_edge=True)
    for c in crossings2:
        print(f"  ✕ [{c.method}] sim={c.similarity}  "
              f"{net.nodes[c.node_a].content[:20]} <-> "
              f"{net.nodes[c.node_b].content[:20]}")

    # 模拟经验通道
    exp = net.add_experience("剪断电梯缆绳后：电梯与乘客同时自由下落，乘客感受不到自身重量")

    # 重组（LLM 在真实使用中生成内容，这里用规则化内容演示）
    if crossings2:
        c = crossings2[0]
        new = net.recombine(
            c.node_a, c.node_b, "category_merge",
            "等效原理与缓存一致性共享深层结构：不同来源的同一性由基准参照决定，"
            "任何『双源』系统都需要一个不可约的基准",
            result_domain="synthesis",
        )
        print(f"\n重组 → 新节点 [{new.domain}]: {new.content[:40]}...")

    print()
    print(net.report())
