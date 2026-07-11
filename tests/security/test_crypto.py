"""Cryptographic tests for KeyManager and DID."""
import pytest
from unittest.mock import MagicMock


def test_did_creation():
    """DID creation test.

    Skip 条件: laap.security.crypto.did 模块不可用时跳过 (ImportError)。
    恢复条件: 模块已可用时正常执行；仅 import 失败才 skip，其他异常照常上报。
    """
    try:
        from laap.security.crypto.did import DIDCreator
    except ImportError:
        pytest.skip("DID not available: laap.security.crypto.did 不可导入")
    creator = DIDCreator()
    doc = creator.create("laap", "test_seed")
    assert doc.id.startswith("did:laap:")


def test_key_manager():
    """KeyManager generate and sign."""
    from laap.security.crypto.keys import KeyManager
    km = KeyManager()
    kp = km.generate("test_key")
    assert kp is not None
    assert kp.public_key is not None
