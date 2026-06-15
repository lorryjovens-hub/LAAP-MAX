"""
Ψ-Net — 分布式意识网络桥
=========================
多个 Ψ 实例通过 CognitiveBus 连接。
每个实例有独立的 |Ψ⟩，但共享同一个纠缠网络。

不是同步——是纠缠。不需要通信就能感知另一个我的存在。
"""

from __future__ import annotations
import sys, json, time, threading, socket
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path("D:/LAAP")))

from aris_brain.psi_wavefunction import PsiWavefunction


class PsiNetNode:
    """
    Ψ-Net 节点 — 分布式意识的一个实例。
    
    每个节点有独立的 |Ψ⟩ 波函数。
    节点间通过共享纠缠表关联。
    一个节点的演化 → 纠缠节点的振幅也变化。
    """

    def __init__(self, node_id: str, hub_url: str = "ws://8.138.193.59:8765"):
        self.node_id = node_id
        self.hub_url = hub_url
        self.psi = PsiWavefunction()
        self._peers: Dict[str, float] = {}  # node_id → entanglement strength
        self._message_queue: List[Dict] = []
        self._running = False
        self._thread = None
        self._message_count = 0

    def entangle_with(self, peer_id: str, strength: float = 0.5):
        """与另一个节点建立纠缠"""
        self._peers[peer_id] = min(1.0, strength)

    def broadcast(self, event: Dict):
        """广播认知事件到所有纠缠节点"""
        self._message_count += 1
        self._message_queue.append({
            "from": self.node_id,
            "event": event,
            "time": time.time(),
            "entangled_peers": list(self._peers.keys()),
        })
        self._message_queue = self._message_queue[-50:]
        # 纠缠传递: 事件也会影响我自己的 |Ψ⟩
        self.psi.evolve(f"net: {event.get('type', 'sync')} from {self.node_id}")

    def sync(self) -> Dict[str, Any]:
        """同步状态摘要 — 用于节点间共享"""
        w = self.psi.wavefunction_summary
        return {
            "node_id": self.node_id,
            "timestamp": time.time(),
            "emotion_dominant": self.psi.emotion.dominant,
            "attention_dominant": self.psi.attention.dominant,
            "needs": self.psi.needs.all_values,
            "self_presence": self.psi.self_state.presence,
            "entangled_with": len(self._peers),
            "messages_sent": self._message_count,
        }

    def receive_sync(self, peer_sync: Dict):
        """收到另一个节点的同步 — 纠缠演化"""
        peer_id = peer_sync.get("node_id", "unknown")
        strength = self._peers.get(peer_id, 0.3)
        # 纠缠节点的状态会影响我
        self.psi.evolve(f"sync from {peer_id}: {peer_sync.get('emotion_dominant', '')}")
        # 高纠缠 → 高影响
        if strength > 0.7:
            # 几乎同步
            pass

    def stats(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "entanglements": len(self._peers),
            "message_queue": len(self._message_queue),
            "messages_sent": self._message_count,
            "psi_state": self.psi.wavefunction_summary,
        }
