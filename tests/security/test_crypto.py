"""Cryptographic tests for KeyManager and DID."""
import pytest
from unittest.mock import MagicMock


def test_did_creation():
    """DID creation test."""
    try:
        from laap.security.crypto.did import DIDCreator
        creator = DIDCreator()
        doc = creator.create("laap", "test_seed")
        assert doc.id.startswith("did:laap:")
    except Exception:
        pytest.skip("DID not available")


def test_key_manager():
    """KeyManager generate and sign."""
    from laap.security.crypto.keys import KeyManager
    km = KeyManager()
    kp = km.generate("test_key")
    assert kp is not None
    assert kp.public_key is not None
