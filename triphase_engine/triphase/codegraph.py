"""triphase.codegraph — Ternary Code Graph 三值代码知识图。

把工程纪律从 prompt 软约束变成表示结构上的守恒律：

1. 验证态守恒：每个实体携带 {VERIFIED(+1), UNVERIFIED(0), BROKEN(-1)}，
   ``mark_complete`` 硬约束——存在未验证依赖时禁止标记完成；
2. 扰动传播：修改 = 在该节点注入相位翻转，沿依赖边按
   耦合强度 × 极性 × 衰减传播，输出按影响排序的回归风险清单；
3. 三态修复闭环：写(+1 构建) → 验(0 悬置) → 判(+1/-1 收敛)。
"""

from __future__ import annotations

import logging
import math
import time
from collections import deque
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class VerificationState(IntEnum):
    BROKEN = -1
    UNVERIFIED = 0
    VERIFIED = 1


class DependencyUnverifiedError(RuntimeError):
    """守恒律违例：试图在未验证 / 已破坏的依赖上完成构建。"""


@dataclass
class CodeNode:
    node_id: str
    kind: str                       # function / class / module / contract / test
    state: VerificationState = VerificationState.UNVERIFIED
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)


@dataclass
class CodeEdge:
    """src → dst 表示 "dst 依赖 src"（改动沿 src → dst 传播）。"""

    source: str
    target: str
    coupling: float = 1.0           # 耦合强度 ∈ [0, 1]
    polarity: int = 1               # +1 行为同向 / -1 行为反向（如取反包装器）

    def __post_init__(self) -> None:
        if not 0.0 <= self.coupling <= 1.0:
            raise ValueError("coupling ∈ [0,1]")
        if self.polarity not in (1, -1):
            raise ValueError("polarity 必须为 ±1")


@dataclass
class ImpactEntry:
    node_id: str
    risk: float         # 带符号风险强度：|值|=爆炸半径，符号=行为变化方向
    depth: int
    path: list[str]


class TernaryCodeGraph:
    """三值代码知识图。"""

    def __init__(self, propagation_decay: float = 0.7, max_depth: int = 8) -> None:
        if not 0.0 < propagation_decay <= 1.0:
            raise ValueError("propagation_decay ∈ (0,1]")
        self.nodes: dict[str, CodeNode] = {}
        self.edges: list[CodeEdge] = []
        self.propagation_decay = propagation_decay
        self.max_depth = max_depth
        # src → [edge]（传播方向）；dst → [edge]（依赖查询方向）
        self._out: dict[str, list[CodeEdge]] = {}
        self._in: dict[str, list[CodeEdge]] = {}

    # ------------------------------------------------------------ 建图

    def add_node(self, node_id: str, kind: str, **metadata: Any) -> CodeNode:
        node = self.nodes.get(node_id)
        if node is None:
            node = CodeNode(node_id=node_id, kind=kind, metadata=metadata)
            self.nodes[node_id] = node
        else:
            node.metadata.update(metadata)
        return node

    def add_edge(self, source: str, target: str,
                 coupling: float = 1.0, polarity: int = 1) -> CodeEdge:
        if source not in self.nodes or target not in self.nodes:
            raise KeyError("边端点必须先注册为节点")
        edge = CodeEdge(source, target, coupling, polarity)
        self.edges.append(edge)
        self._out.setdefault(source, []).append(edge)
        self._in.setdefault(target, []).append(edge)
        return edge

    # ------------------------------------------------------------ 三态守恒

    def verify(self, node_id: str, passed: bool) -> VerificationState:
        """测试裁决：通过 → VERIFIED；失败 → BROKEN。"""
        node = self.nodes[node_id]
        node.state = VerificationState.VERIFIED if passed else VerificationState.BROKEN
        node.updated_at = time.time()
        logger.info("节点 %s 验证: %s", node_id, node.state.name)
        return node.state

    def invalidate(self, node_id: str) -> None:
        """代码被修改 → 回到悬置态（0 相是一等状态，不是 overhead）。"""
        self.nodes[node_id].state = VerificationState.UNVERIFIED
        self.nodes[node_id].updated_at = time.time()

    def dependencies_of(self, node_id: str) -> list[str]:
        return [e.source for e in self._in.get(node_id, [])]

    def mark_complete(self, node_id: str) -> None:
        """守恒律：所有依赖 VERIFIED 才允许完成，否则抛硬异常。"""
        node = self.nodes[node_id]
        if node.state is VerificationState.BROKEN:
            raise DependencyUnverifiedError(f"节点 {node_id} 处于 BROKEN 态")
        bad = [
            dep for dep in self.dependencies_of(node_id)
            if self.nodes[dep].state is not VerificationState.VERIFIED
        ]
        if bad:
            raise DependencyUnverifiedError(
                f"节点 {node_id} 存在未验证依赖 {bad}，禁止标记完成"
            )
        node.state = VerificationState.VERIFIED
        logger.info("节点 %s 守恒检查通过，标记完成", node_id)

    # ------------------------------------------------------------ 扰动传播

    def impact_analysis(self, changed_node: str) -> list[ImpactEntry]:
        """改动爆炸半径：相位翻转沿依赖边传播，输出排序风险清单。

        传播模型：I_dst += I_src × coupling × decay；
        符号 = 路径极性乘积（行为同向 / 反向）。
        """
        if changed_node not in self.nodes:
            raise KeyError(changed_node)
        self.invalidate(changed_node)

        best: dict[str, ImpactEntry] = {}
        queue: deque[tuple[str, float, int, list[str]]] = deque()
        queue.append((changed_node, 1.0, 0, [changed_node]))

        while queue:
            current, intensity, depth, path = queue.popleft()
            if depth >= self.max_depth or abs(intensity) < 1e-4:
                continue
            for edge in self._out.get(current, []):
                nxt_intensity = intensity * edge.coupling * self.propagation_decay * edge.polarity
                nxt_path = path + [edge.target]
                prev = best.get(edge.target)
                if prev is None or abs(nxt_intensity) > abs(prev.risk):
                    best[edge.target] = ImpactEntry(
                        node_id=edge.target,
                        risk=nxt_intensity,
                        depth=depth + 1,
                        path=nxt_path,
                    )
                    queue.append((edge.target, nxt_intensity, depth + 1, nxt_path))

        return sorted(best.values(), key=lambda e: abs(e.risk), reverse=True)

    def unverified_ratio(self) -> float:
        """元认知遥测输入：UNVERIFIED/BROKEN 依赖占比。"""
        if not self.nodes:
            return 0.0
        bad = sum(1 for n in self.nodes.values()
                  if n.state is not VerificationState.VERIFIED)
        return bad / len(self.nodes)

    def stats(self) -> dict[str, int]:
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "verified": sum(n.state is VerificationState.VERIFIED for n in self.nodes.values()),
            "unverified": sum(n.state is VerificationState.UNVERIFIED for n in self.nodes.values()),
            "broken": sum(n.state is VerificationState.BROKEN for n in self.nodes.values()),
        }
