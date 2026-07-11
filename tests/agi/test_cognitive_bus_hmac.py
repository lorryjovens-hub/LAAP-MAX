"""LAAP AGI CognitiveBus HMAC-SHA256 认证测试 (M0-B3)

验证 CognitiveBusSyncNode 的预共享密钥 HMAC-SHA256 认证机制：
  1. 正常签名-验证往返
  2. 伪造签名被拒绝
  3. 无 PSK 时降级到临时密钥（仅开发模式）
  4. 不同 PSK 的节点互相拒绝
  5. 旧的无签名格式被拒绝（向后兼容性）
  6. 实际网络往返：合法消息被接受
"""

from __future__ import annotations

import json
import logging
import os
import socket
import threading
import time

import pytest

from laap.agi.cognitive_bus_sync import (
    CognitiveBusSyncNode,
    HMAC_SIGNATURE_LEN,
    PSK_ENV_VAR,
    SyncMessage,
    SyncMessageType,
    create_sync_network,
)


# ───────────────────────────────────────────────────────────────
# 测试夹具
# ───────────────────────────────────────────────────────────────

PSK_A = "test-psk-shared-secret-key-AAA"
PSK_B = "test-psk-shared-secret-key-BBB"


@pytest.fixture
def clean_psk_env(monkeypatch):
    """清除 LAAP_BUS_PSK 环境变量，避免污染测试"""
    monkeypatch.delenv(PSK_ENV_VAR, raising=False)
    yield


@pytest.fixture
def node_with_psk(clean_psk_env):
    """带固定 PSK 的同步节点（不启动服务器）"""
    return CognitiveBusSyncNode(
        profile_name="test-node",
        display_name="Test Node",
        port=0,  # 不绑定
        pre_shared_key=PSK_A,
    )


def _free_port() -> int:
    """获取一个可用端口"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


# ───────────────────────────────────────────────────────────────
# 测试 1：正常签名-验证往返
# ───────────────────────────────────────────────────────────────

class TestHmacSignVerify:
    """HMAC 签名与验证往返测试"""

    def test_sign_then_verify_roundtrip(self, node_with_psk):
        """测试1: 正常签名-验证往返"""
        payload = b'{"type":"hello","sender_id":"a","payload":{}}'
        signature = node_with_psk._sign(payload)
        assert len(signature) == HMAC_SIGNATURE_LEN
        assert node_with_psk._verify(payload, signature) is True

    def test_sign_produces_deterministic_output(self, node_with_psk):
        """同一 payload 多次签名结果一致（HMAC 是确定性的）"""
        payload = b"consistency-check"
        sig1 = node_with_psk._sign(payload)
        sig2 = node_with_psk._sign(payload)
        assert sig1 == sig2

    def test_sign_different_payloads_differ(self, node_with_psk):
        """不同 payload 产生不同签名"""
        sig_a = node_with_psk._sign(b"payload-a")
        sig_b = node_with_psk._sign(b"payload-b")
        assert sig_a != sig_b

    def test_signature_length_is_32_bytes(self, node_with_psk):
        """HMAC-SHA256 签名长度固定 32 字节"""
        sig = node_with_psk._sign(b"length-check")
        assert len(sig) == 32
        assert len(sig) == HMAC_SIGNATURE_LEN


# ───────────────────────────────────────────────────────────────
# 测试 2：伪造签名被拒绝
# ───────────────────────────────────────────────────────────────

class TestForgedSignatureRejected:
    """伪造签名拒绝测试"""

    def test_forged_signature_rejected(self, node_with_psk):
        """测试2: 伪造签名被拒绝"""
        payload = b'{"type":"causal_rule","sender_id":"evil"}'
        forged = b"\x00" * HMAC_SIGNATURE_LEN  # 全零伪造签名
        assert node_with_psk._verify(payload, forged) is False

    def test_tampered_payload_rejected(self, node_with_psk):
        """签名后篡改 payload 被拒绝"""
        payload = b"original"
        signature = node_with_psk._sign(payload)
        tampered = b"modified"
        assert node_with_psk._verify(tampered, signature) is False

    def test_truncated_signature_rejected(self, node_with_psk):
        """截断的签名被拒绝"""
        payload = b"truncation-test"
        signature = node_with_psk._sign(payload)
        truncated = signature[:16]
        assert node_with_psk._verify(payload, truncated) is False

    def test_random_bytes_signature_rejected(self, node_with_psk):
        """随机字节作为签名被拒绝"""
        import os as _os
        payload = b"random-sig-test"
        random_sig = _os.urandom(HMAC_SIGNATURE_LEN)
        # 极大概率不匹配
        assert node_with_psk._verify(payload, random_sig) is False


# ───────────────────────────────────────────────────────────────
# 测试 3：无 PSK 时降级到临时密钥
# ───────────────────────────────────────────────────────────────

class TestEphemeralKeyFallback:
    """临时密钥降级测试"""

    def test_no_psk_generates_ephemeral_key_with_warning(
        self, clean_psk_env, caplog
    ):
        """测试3: 无 PSK 时降级到临时密钥（仅开发模式）"""
        with caplog.at_level(logging.WARNING, logger="laap.agi.cognitive_bus_sync"):
            node = CognitiveBusSyncNode(
                profile_name="dev-node",
                port=0,
                pre_shared_key=None,
            )
        # 警告已记录
        assert any(
            "ephemeral key" in rec.message and "开发模式" in rec.message
            for rec in caplog.records
        ), f"期望警告日志，实际: {[r.message for r in caplog.records]}"
        # HMAC 密钥已派生
        assert node._hmac_key is not None
        assert len(node._hmac_key) == 32
        # 临时密钥可用于签名验证
        payload = b"dev-mode-test"
        sig = node._sign(payload)
        assert node._verify(payload, sig) is True

    def test_ephemeral_keys_are_unique(self, clean_psk_env):
        """每个无 PSK 节点的临时密钥互不相同"""
        node_a = CognitiveBusSyncNode("a", port=0)
        node_b = CognitiveBusSyncNode("b", port=0)
        assert node_a._hmac_key != node_b._hmac_key
        # 互相验证失败（密钥不同）
        payload = b"cross-check"
        sig_a = node_a._sign(payload)
        assert node_b._verify(payload, sig_a) is False

    def test_psk_from_env_var(self, clean_psk_env, monkeypatch):
        """从 LAAP_BUS_PSK 环境变量读取 PSK"""
        monkeypatch.setenv(PSK_ENV_VAR, PSK_A)
        node = CognitiveBusSyncNode("env-node", port=0)
        # 与显式传入相同 PSK 的节点密钥一致
        explicit = CognitiveBusSyncNode("explicit-node", port=0, pre_shared_key=PSK_A)
        assert node._hmac_key == explicit._hmac_key

    def test_explicit_psk_takes_priority_over_env(self, clean_psk_env, monkeypatch):
        """显式 PSK 参数优先于环境变量"""
        monkeypatch.setenv(PSK_ENV_VAR, PSK_A)
        node = CognitiveBusSyncNode("prio-node", port=0, pre_shared_key=PSK_B)
        explicit_b = CognitiveBusSyncNode("b-node", port=0, pre_shared_key=PSK_B)
        assert node._hmac_key == explicit_b._hmac_key


# ───────────────────────────────────────────────────────────────
# 测试 4：不同 PSK 的节点互相拒绝
# ───────────────────────────────────────────────────────────────

class TestDifferentPskNodesReject:
    """跨节点 PSK 不匹配测试"""

    def test_nodes_with_different_psks_cannot_verify_each_other(
        self, clean_psk_env
    ):
        """不同 PSK 的节点签名互相无法验证"""
        node_a = CognitiveBusSyncNode("a", port=0, pre_shared_key=PSK_A)
        node_b = CognitiveBusSyncNode("b", port=0, pre_shared_key=PSK_B)

        payload = b'{"type":"causal_rule","sender_id":"a"}'
        sig_from_a = node_a._sign(payload)
        # 节点 B 用自己的密钥验证 A 的签名 → 失败
        assert node_b._verify(payload, sig_from_a) is False

        sig_from_b = node_b._sign(payload)
        # 节点 A 用自己的密钥验证 B 的签名 → 失败
        assert node_a._verify(payload, sig_from_b) is False

    def test_nodes_with_same_psk_can_verify_each_other(self, clean_psk_env):
        """相同 PSK 的节点签名互相可验证"""
        node_a = CognitiveBusSyncNode("a", port=0, pre_shared_key=PSK_A)
        node_b = CognitiveBusSyncNode("b", port=0, pre_shared_key=PSK_A)

        payload = b'{"type":"hello"}'
        sig = node_a._sign(payload)
        assert node_b._verify(payload, sig) is True


# ───────────────────────────────────────────────────────────────
# 测试 5：旧的无签名格式被拒绝（向后兼容性）
# ───────────────────────────────────────────────────────────────

class TestLegacyFormatRejected:
    """旧格式拒绝测试（向后兼容性）"""

    def test_short_message_rejected(self, clean_psk_env, caplog):
        """长度 < 32 的消息视为旧格式并拒绝"""
        port = _free_port()
        node = CognitiveBusSyncNode("srv", port=port, pre_shared_key=PSK_A)
        node.start()
        try:
            # 构造一个旧格式消息（无签名，payload 短于 32 字节）
            legacy_payload = b'{"type":"hello"}'  # 16 字节
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect(("127.0.0.1", port))
                length = len(legacy_payload).to_bytes(4, "big")
                s.sendall(length + legacy_payload)
                # 等待服务器处理
                time.sleep(0.3)
            # 节点不应记录任何收到消息（messages_received 保持 0）
            assert node._messages_received == 0
        finally:
            node.stop()

    def test_forged_full_frame_rejected_at_network(self, clean_psk_env, caplog):
        """伪造签名的完整帧在网络上被拒绝"""
        port = _free_port()
        node = CognitiveBusSyncNode("srv", port=port, pre_shared_key=PSK_A)
        node.start()
        try:
            # 构造一个带错误签名的完整帧
            payload = b'{"type":"hello","sender_id":"evil","sender_name":"E","payload":{},"ts":1.0,"ttl":3}'
            forged_sig = b"\x01" * HMAC_SIGNATURE_LEN
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect(("127.0.0.1", port))
                length = len(payload).to_bytes(4, "big")
                s.sendall(length + forged_sig + payload)
                time.sleep(0.3)
            # 消息被丢弃，未路由
            assert node._messages_received == 0
            # "evil" 节点未被加入 peers
            assert "evil" not in node.peers
        finally:
            node.stop()


# ───────────────────────────────────────────────────────────────
# 测试 6：合法消息的实际网络往返
# ───────────────────────────────────────────────────────────────

class TestValidMessageNetworkRoundtrip:
    """合法消息网络往返测试"""

    def test_valid_signed_message_accepted(self, clean_psk_env):
        """合法签名的消息在网络上被接受并路由"""
        port = _free_port()
        node = CognitiveBusSyncNode("srv", port=port, pre_shared_key=PSK_A)
        received_events = []
        node.on_peer_join(lambda pid, info: received_events.append(("join", pid)))
        node.start()
        try:
            # 用相同 PSK 的另一个节点发送消息
            sender = CognitiveBusSyncNode(
                "sender", "Sender", port=0, pre_shared_key=PSK_A
            )
            msg = SyncMessage(
                msg_type=SyncMessageType.HELLO,
                sender_id="sender",
                sender_name="Sender",
                payload={"port": 0, "version": "1.0"},
                timestamp=12345.0,
            )
            sender._send_raw("127.0.0.1", port, msg.to_json())
            # 等待服务器处理
            time.sleep(0.5)
            # 消息被接收并路由
            assert node._messages_received >= 1
            assert "sender" in node.peers
            assert received_events == [("join", "sender")]
        finally:
            node.stop()

    def test_two_nodes_with_same_psk_sync(self, clean_psk_env):
        """两个相同 PSK 的节点可双向同步"""
        port_a = _free_port()
        port_b = _free_port()
        node_a = CognitiveBusSyncNode("a", "A", port=port_a, pre_shared_key=PSK_A)
        node_b = CognitiveBusSyncNode("b", "B", port=port_b, pre_shared_key=PSK_A)
        node_a.add_peer("b", port=port_b)
        node_b.add_peer("a", port=port_a)
        node_a.start()
        node_b.start()
        try:
            # 等待 HELLO 广播和心跳
            time.sleep(1.0)
            # 双方应已发现彼此
            assert "b" in node_a.peers or node_a._messages_received >= 1
            assert "a" in node_b.peers or node_b._messages_received >= 1
        finally:
            node_a.stop()
            node_b.stop()


# ───────────────────────────────────────────────────────────────
# 测试 7：create_sync_network 工厂函数
# ───────────────────────────────────────────────────────────────

class TestCreateSyncNetwork:
    """工厂函数 PSK 传递测试"""

    def test_create_sync_network_passes_psk(self, clean_psk_env):
        """create_sync_network 将 PSK 传递给所有节点"""
        port = _free_port()
        profiles = [
            {"name": "x", "display": "X"},
            {"name": "y", "display": "Y"},
        ]
        nodes = create_sync_network(profiles, base_port=port, pre_shared_key=PSK_A)
        try:
            assert len(nodes) == 2
            # 两个节点使用相同 PSK → 相同 HMAC 密钥
            assert nodes["x"]._hmac_key == nodes["y"]._hmac_key
            # 互相能验证
            payload = b"factory-test"
            sig = nodes["x"]._sign(payload)
            assert nodes["y"]._verify(payload, sig) is True
        finally:
            for n in nodes.values():
                n.stop()

    def test_create_sync_network_different_psks_isolate(self, clean_psk_env):
        """不同 PSK 的网络互相隔离"""
        port1 = _free_port()
        port2 = _free_port()
        profiles = [{"name": "a"}, {"name": "b"}]
        net1 = create_sync_network(profiles, base_port=port1, pre_shared_key=PSK_A)
        net2 = create_sync_network(profiles, base_port=port2, pre_shared_key=PSK_B)
        try:
            payload = b"isolation-test"
            sig1 = net1["a"]._sign(payload)
            # net2 无法验证 net1 的签名
            assert net2["a"]._verify(payload, sig1) is False
        finally:
            for n in list(net1.values()) + list(net2.values()):
                n.stop()
