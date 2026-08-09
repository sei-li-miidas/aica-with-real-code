"""
暗号化・復号化
"""

import base64
import hashlib
from cryptography.fernet import Fernet

from utils.enum import EncryptKeyType
from utils.log_utils import get_session_id


def create_secret_key(key_type: EncryptKeyType) -> bytes:
    session_id = get_session_id()
    key_material = (key_type.get_key() + session_id).encode()
    sha256 = hashlib.sha256(key_material).digest()
    return base64.urlsafe_b64encode(sha256)


def encrypt(key_type: EncryptKeyType, plain_value: str) -> str:
    key = create_secret_key(key_type)
    f = Fernet(key)
    return f.encrypt(plain_value.encode()).decode()


def decrypt(key_type: EncryptKeyType, encrypted_value: str) -> str:
    key = create_secret_key(key_type)
    f = Fernet(key)
    return f.decrypt(encrypted_value.encode()).decode()
