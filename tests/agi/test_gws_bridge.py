"""
LAAP AGI — M3 B3: GWS Bridge 跨子系统信号广播测试

覆盖:
  - test_broadcast_signal_returns_attention_score: 默认权重下分数计算
  - test_subscribe_receives_winning_signal: 高紧迫度信号胜出并触达订阅者
  - test_attention_policy_custom_weights: 自定义权重产生不同分数
  - test_low_urgency_signal_does_not_win: 低分信号不触发订阅者回调

测试隔离：通过 monkeypatch ``LAAP_HOME`` 环境变量到 ``tmp_path``，并将
``ipc_dir`` 指向临时目录，避免污染真实的 ``~/.laap/`` 与 ``aris_brain/state/ipc``。
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest


# ── 公共 fixture：隔离 LAAP_HOME + ipc_dir ─────────────────────

@pytest.fixture
def isolated_laap_home(tmp_path, monkeypatch):
    """将 LAAP_HOME 指向临时目录，避免污染真实 ``~/.laap/``。"""
    laap_home = tmp_path / "laap_home"
    laap_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LAAP_HOME", str(laap_home))
    yield laap_home


@pytest.fixture
def gws_bridge(isolated_laap_home, tmp_path):
    """构造一个隔离的 GWSBridge 实例（不启动后台线程）。"""
    from laap.agi.gws_bridge import GWSBridge

    ipc_dir = tmp_path / "ipc"
    ipc_dir.mkdir(parents=True, exist_ok=True)
    bridge = GWSBridge(
        conscious_stream=None,
        cognitive_bus=None,
        ipc_dir=str(ipc_dir),
    )
    return bridge


# ═════════════════════════════════════════════════════════════════
# B3.2 / B3.3: broadcast_signal 注意力分数计算
# ═════════════════════════════════════════════════════════════════

def test_broadcast_signal_returns_attention_score(gws_bridge):
    """验证 broadcast_signal 返回基于默认权重的注意力分数。"""
    score = gws_bridge.broadcast_signal(
        source="psi",
        signal_type="need_change",
        payload={"need": "autonomy", "level": 0.8},
        urgency=0.9,
        importance=0.7,
        novelty=0.5,
    )
    # 默认权重: urgency*0.4 + importance*0.4 + novelty*0.2
    #           = 0.9*0.4 + 0.7*0.4 + 0.5*0.2 = 0.36 + 0.28 + 0.10 = 0.74
    assert isinstance(score, float)
    assert abs(score - 0.74) < 1e-6


# ═════════════════════════════════════════════════════════════════
# B3.4: 订阅接口
# ═════════════════════════════════════════════════════════════════

def test_subscribe_receives_winning_signal(gws_bridge):
    """注册订阅者后，高紧迫度信号应触发回调并携带完整信号字段。"""
    received: List[Dict[str, Any]] = []

    def callback(signal: Dict[str, Any]) -> None:
        received.append(signal)

    gws_bridge.subscribe("memory", callback)

    score = gws_bridge.broadcast_signal(
        source="psi",
        signal_type="need_change",
        payload={"need": "autonomy"},
        urgency=0.9,
        importance=0.8,
        novelty=0.7,
    )
    # score = 0.9*0.4 + 0.8*0.4 + 0.7*0.2 = 0.36 + 0.32 + 0.14 = 0.82 > 0.5
    assert score > 0.5
    assert len(received) == 1, "订阅者回调应被调用一次"

    signal = received[0]
    assert signal["source"] == "psi"
    assert signal["signal_type"] == "need_change"
    assert signal["payload"]["need"] == "autonomy"
    assert signal["urgency"] == 0.9
    assert signal["importance"] == 0.8
    assert signal["novelty"] == 0.7
    assert signal["attention_score"] == score
    assert "timestamp" in signal


# ═════════════════════════════════════════════════════════════════
# B3.3: 注意力分配策略可配置
# ═════════════════════════════════════════════════════════════════

def test_attention_policy_custom_weights(gws_bridge):
    """切换 AttentionPolicy 权重后，相同输入应产生不同分数。"""
    from laap.agi.gws_bridge import AttentionPolicy

    # 默认权重下：urgency*0.4 + importance*0.4 + novelty*0.2
    # 输入 (0.5, 1.0, 1.0) → 0.2 + 0.4 + 0.2 = 0.8
    default_score = gws_bridge.broadcast_signal(
        source="memory",
        signal_type="memory_consolidated",
        payload={"episode": "ep-001"},
        urgency=0.5,
        importance=1.0,
        novelty=1.0,
    )
    assert abs(default_score - 0.8) < 1e-6

    # 切换策略：仅看 urgency
    gws_bridge.set_attention_policy(
        AttentionPolicy(
            urgency_weight=1.0,
            importance_weight=0.0,
            novelty_weight=0.0,
        )
    )

    # 自定义权重下：urgency*1.0 + importance*0.0 + novelty*0.0
    # 输入 (0.5, 1.0, 1.0) → 0.5
    custom_score = gws_bridge.broadcast_signal(
        source="memory",
        signal_type="memory_consolidated",
        payload={"episode": "ep-001"},
        urgency=0.5,
        importance=1.0,
        novelty=1.0,
    )
    assert abs(custom_score - 0.5) < 1e-6
    assert default_score != custom_score, \
        "切换 AttentionPolicy 权重后应产生不同的注意力分数"


# ═════════════════════════════════════════════════════════════════
# B3.2: 低分信号不广播
# ═════════════════════════════════════════════════════════════════

def test_low_urgency_signal_does_not_win(gws_bridge):
    """低分信号（attention_score <= 0.5）不应触达订阅者。"""
    received: List[Dict[str, Any]] = []

    def callback(signal: Dict[str, Any]) -> None:
        received.append(signal)

    gws_bridge.subscribe("causal", callback)

    score = gws_bridge.broadcast_signal(
        source="causal",
        signal_type="causal_violation",
        payload={"domain": "physics", "delta": 0.01},
        urgency=0.1,
        importance=0.1,
        novelty=0.1,
    )
    # score = 0.1*0.4 + 0.1*0.4 + 0.1*0.2 = 0.04 + 0.04 + 0.02 = 0.10
    assert score < 0.5, "低紧迫度信号注意力分数应低于竞争阈值"
    assert len(received) == 0, "低分信号不应触发任何订阅者回调"


# ═════════════════════════════════════════════════════════════════
# B3.4: 多子系统可同时订阅
# ═════════════════════════════════════════════════════════════════

def test_multiple_subscribers_receive_signal(gws_bridge):
    """多个子系统订阅同一广播时，所有回调都应被触发。"""
    psi_received: List[Dict[str, Any]] = []
    memory_received: List[Dict[str, Any]] = []
    meta_received: List[Dict[str, Any]] = []

    gws_bridge.subscribe("psi", lambda s: psi_received.append(s))
    gws_bridge.subscribe("memory", lambda s: memory_received.append(s))
    gws_bridge.subscribe("meta_cognitive", lambda s: meta_received.append(s))

    score = gws_bridge.broadcast_signal(
        source="causal",
        signal_type="causal_violation",
        payload={"expected": 0.9, "actual": 0.2},
        urgency=0.8,
        importance=0.9,
        novelty=0.7,
    )
    # score = 0.8*0.4 + 0.9*0.4 + 0.7*0.2 = 0.32 + 0.36 + 0.14 = 0.82 > 0.5
    assert score > 0.5
    assert len(psi_received) == 1
    assert len(memory_received) == 1
    assert len(meta_received) == 1

    # 所有回调应收到相同的信号
    assert psi_received[0]["signal_type"] == "causal_violation"
    assert memory_received[0]["signal_type"] == "causal_violation"
    assert meta_received[0]["signal_type"] == "causal_violation"
