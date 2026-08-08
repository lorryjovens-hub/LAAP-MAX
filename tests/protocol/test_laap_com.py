"""LAAP-COM Ed25519 签名测试。"""
import base64

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from laap.protocol.laap_com import Message, sign, verify


class TestLAAPComEd25519:
    """覆盖 A4 要求的 Ed25519 签名/验签行为。"""

    def test_sign_verify_roundtrip_succeeds(self):
        private_key = Ed25519PrivateKey.generate()
        message = b"hello laap"

        signature = sign(private_key, message)

        assert verify(private_key.public_key(), message, signature) is True

    def test_tampered_message_fails_verification(self):
        private_key = Ed25519PrivateKey.generate()
        message = b"hello laap"
        signature = sign(private_key, message)

        assert verify(private_key.public_key(), b"tampered", signature) is False

    def test_wrong_key_fails_verification(self):
        private_key = Ed25519PrivateKey.generate()
        other_private_key = Ed25519PrivateKey.generate()
        message = b"hello laap"
        signature = sign(private_key, message)

        assert verify(other_private_key.public_key(), message, signature) is False

    def test_signature_length_is_64_bytes(self):
        private_key = Ed25519PrivateKey.generate()

        signature = sign(private_key, b"hello")

        assert len(signature) == 64

    def test_rejects_short_legacy_signature(self):
        private_key = Ed25519PrivateKey.generate()

        assert verify(private_key.public_key(), b"msg", b"legacy-16-hex") is False


class TestLAAPComMessageSign:
    """Message 对象级别的签名与验证。"""

    def test_message_sign_verify_roundtrip(self):
        private_key = Ed25519PrivateKey.generate()
        msg = Message(sender="did:laap:abc", recipient="did:laap:def", payload={"x": 1})

        msg.sign(private_key)

        assert len(msg.signature) > 0
        assert msg.verify(private_key.public_key()) is True

    def test_message_tampered_payload_fails(self):
        private_key = Ed25519PrivateKey.generate()
        msg = Message(sender="did:laap:abc", recipient="did:laap:def", payload={"x": 1})
        msg.sign(private_key)

        msg.payload = {"x": 2}

        assert msg.verify(private_key.public_key()) is False

    def test_message_no_signature_returns_false(self):
        private_key = Ed25519PrivateKey.generate()
        msg = Message(sender="did:laap:abc", payload={"x": 1})

        assert msg.verify(private_key.public_key()) is False

    def test_message_signature_is_base64_64_bytes(self):
        private_key = Ed25519PrivateKey.generate()
        msg = Message(sender="did:laap:abc", payload={"x": 1})

        msg.sign(private_key)

        raw = base64.b64decode(msg.signature.encode("ascii"), validate=True)
        assert len(raw) == 64

    def test_message_sign_without_key_clears_signature(self):
        """未提供密钥时不再生成伪签名，保持为空字符串。"""
        msg = Message(sender="did:laap:abc", payload={"x": 1})

        msg.sign()

        assert msg.signature == ""
