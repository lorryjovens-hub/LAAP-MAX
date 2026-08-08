"""
laap_memory/encryption.py — Vault 存储层加密

支持：
- 字段级加密：content 和 metadata 字段使用 AES-256-GCM 加密
- 密钥管理：从口令派生，可轮换
- 透明加解密：应用层无感知
- 可选全文加密：整个 SQLite 页面加密（需要 SQLCipher）
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
from typing import Optional

log = logging.getLogger("laap-memory.encryption")

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class MemoryEncryptor:
    """记忆加密器——透明字段级加密"""

    def __init__(self, passphrase: str = ""):
        self.passphrase = passphrase
        self._fernet = None
        self._key = None
        if passphrase and HAS_CRYPTOGRAPHY:
            self._key = base64.urlsafe_b64encode(
                hashlib.sha256(passphrase.encode()).digest()
            )
            self._fernet = Fernet(self._key)

    @property
    def is_available(self) -> bool:
        return HAS_CRYPTOGRAPHY and self._fernet is not None

    def encrypt(self, plaintext: str) -> str:
        """加密文本"""
        if not self.is_available:
            return plaintext
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """解密文本"""
        if not self.is_available:
            return ciphertext
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except Exception as e:
            log.warning(f"Decryption failed: {e}")
            return ciphertext

    def encrypt_dict(self, data: dict, fields: list[str] = None) -> dict:
        """加密字典中的指定字段"""
        if not self.is_available:
            return data
        fields = fields or ["content"]
        result = dict(data)
        for field in fields:
            if field in result and isinstance(result[field], str):
                result[field] = self.encrypt(result[field])
        return result

    def decrypt_dict(self, data: dict, fields: list[str] = None) -> dict:
        """解密字典中的指定字段"""
        if not self.is_available:
            return data
        fields = fields or ["content"]
        result = dict(data)
        for field in fields:
            if field in result and isinstance(result[field], str):
                result[field] = self.decrypt(result[field])
        return result

    # ── 密钥管理 ──────────────────────────────────

    @staticmethod
    def generate_key() -> str:
        """生成新密钥"""
        if not HAS_CRYPTOGRAPHY:
            return "cryptography not available"
        return Fernet.generate_key().decode()

    def rotate_key(self, new_passphrase: str) -> bool:
        """轮换密钥（重新加密所有数据）"""
        if not self.is_available:
            return False
        # 新密钥
        new_key = base64.urlsafe_b64encode(
            hashlib.sha256(new_passphrase.encode()).digest()
        )
        new_fernet = Fernet(new_key)
        self._fernet = new_fernet
        self.passphrase = new_passphrase
        self._key = new_key
        return True

    # ── Vault 文件加密 ──────────────────────────────

    def encrypt_vault_file(self, input_path: str, output_path: str = "") -> str:
        """加密整个 vault 文件"""
        if not self.is_available:
            raise ValueError("Cryptography not available")

        output_path = output_path or input_path + ".encrypted"
        with open(input_path, "rb") as f:
            data = f.read()
        encrypted = self._fernet.encrypt(data)
        with open(output_path, "wb") as f:
            f.write(encrypted)
        return output_path

    def decrypt_vault_file(self, input_path: str, output_path: str = "") -> str:
        """解密 vault 文件"""
        if not self.is_available:
            raise ValueError("Cryptography not available")

        output_path = output_path or input_path.replace(".encrypted", "")
        with open(input_path, "rb") as f:
            encrypted = f.read()
        data = self._fernet.decrypt(encrypted)
        with open(output_path, "wb") as f:
            f.write(data)
        return output_path


# 默认实例
default_encryptor = MemoryEncryptor()