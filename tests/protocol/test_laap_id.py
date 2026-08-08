"""LAAP-ID Ed25519 身份文档签名测试。"""
import base64
import tempfile

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from laap.protocol.laap_id import IdentityDocument


class TestLAAPIdEd25519:
    """覆盖 A4 中 laap_id.py 的 Ed25519 升级行为。"""

    def test_identity_generates_ed25519_keypair(self):
        doc = IdentityDocument()

        public_bytes = base64.b64decode(doc.public_key.encode("ascii"), validate=True)
        assert len(public_bytes) == 32
        # 公钥可被正确解析
        public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
        assert public_key is not None

    def test_identity_sign_verify_roundtrip(self):
        doc = IdentityDocument()

        doc.sign()

        assert doc.signature != ""
        assert doc.verify() is True

    def test_identity_tampered_doc_fails(self):
        doc = IdentityDocument()
        doc.sign()
        doc.name = "Tampered"

        assert doc.verify() is False

    def test_identity_old_format_signature_rejected(self):
        doc = IdentityDocument()
        # 模拟旧格式公钥与签名
        doc.public_key = "a" * 64  # 64 字符十六进制风格
        doc.signature = "sig:laap:" + "b" * 32

        assert doc.verify() is False

    def test_identity_save_and_load_keys(self):
        doc = IdentityDocument()
        original_public_key = doc.public_key

        with tempfile.TemporaryDirectory() as tmpdir:
            doc.save_keys(tmpdir)
            loaded_doc = IdentityDocument(id=doc.id, name=doc.name)
            loaded_doc.load_keys(tmpdir)

            assert loaded_doc.public_key == original_public_key
            loaded_doc.sign()
            assert loaded_doc.verify() is True

    def test_identity_from_dict_preserves_public_key(self):
        doc = IdentityDocument()
        doc.sign()
        data = doc.to_dict()

        restored = IdentityDocument.from_dict(data)

        assert restored.public_key == doc.public_key
        assert restored.verify() is True

    def test_identity_sign_without_private_key_raises(self):
        source = IdentityDocument()
        doc = IdentityDocument(public_key=source.public_key)
        # 仅提供公钥、没有私钥时签名应失败
        with pytest.raises(RuntimeError):
            doc.sign()
