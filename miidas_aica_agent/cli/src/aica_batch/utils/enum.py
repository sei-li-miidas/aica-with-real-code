from enum import IntEnum, StrEnum
import os


class EncryptKeyType(IntEnum):
    POSITION = 1
    PROFILE = 2

    def get_key(self) -> str:
        """暗号化キータイプに対応するキーを取得"""
        if self == self.POSITION:
            key = os.environ.get("AICA_PYTHON_FERNET_AES_128_CBC_KEY_LV3")
            key_name = "AICA_PYTHON_FERNET_AES_128_CBC_KEY_LV3"
        elif self == self.PROFILE:
            key = os.environ.get("AICA_PYTHON_FERNET_AES_128_CBC_KEY_LV5")
            key_name = "AICA_PYTHON_FERNET_AES_128_CBC_KEY_LV5"
        else:
            raise ValueError(f"Invalid EncryptKeyType value: {self}")
        if not key:
            raise ValueError(
                f"Environment variable '{key_name}' is not set or is empty."
            )
        return key


class RateLimitScope(StrEnum):
    SESSION = "session"
    IP = "ip"
    GUEST = "guest"


class RateLimitActionType(StrEnum):
    CHAT_REQUEST = "chat_request"
    POSITION_DETAIL = "position_detail"
    POSITION_SEARCH = "position_search"
    LOAD_MORE_POSITIONS = "load_more_positions"
