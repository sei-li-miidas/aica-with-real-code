"""
暗号化・復号化
"""

import base64
import hashlib
from cryptography.fernet import Fernet

from utils.enum import EncryptKeyType


def create_secret_key(session_id: str, key_type: EncryptKeyType) -> bytes:
    key_material = (key_type.get_key() + session_id).encode()
    sha256 = hashlib.sha256(key_material).digest()
    return base64.urlsafe_b64encode(sha256)


def encrypt(key: bytes, real_id: str) -> str:
    f = Fernet(key)
    return f.encrypt(real_id.encode()).decode()


def decrypt(key: bytes, encrypted_id: str) -> str:
    f = Fernet(key)
    return f.decrypt(encrypted_id.encode()).decode()
