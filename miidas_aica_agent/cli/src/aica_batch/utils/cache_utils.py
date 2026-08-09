import json
import logging
from abc import ABC, abstractmethod
from typing import Any

import redis

from utils.const import LOGGER_PREFIX


class CacheUtil(ABC):
    """
    キャッシュリポジトリの抽象クラス
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(
            f"{LOGGER_PREFIX}.{self.__class__.__module__}.{self.__class__.__name__}"
        )

    @abstractmethod
    def get(self, key: str) -> Any | None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, *keys: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_hash_values(self, key: str) -> list[str]:
        raise NotImplementedError


class RedisCacheUtil(CacheUtil):
    """
    Redis を利用してデータを保存・取得する実装
    """

    def __init__(
        self,
        host: str,
        port: int,
    ) -> None:
        super().__init__()

        if host is None:
            raise ValueError("Redis host must be provided")

        if not isinstance(port, int):
            raise TypeError("Redis port must be int")
        if port <= 0:
            raise ValueError("Redis port must be a positive integer")

        self._host: str = host
        self._port: int = port

        self._client = redis.Redis(host=host, port=port, decode_responses=True)

    def get(self, key: str) -> Any | None:
        """
        Redis から値を取得し、可能なら JSON を復元する。

        Args:
            key: 取得するキー

        Returns:
            保存された値。存在しない場合やエラー時は None
        """
        try:
            raw_value = self._client.get(name=key)
        except redis.RedisError:
            self._logger.exception("Redis 取得失敗: %s", key)
            return None

        if raw_value is None:
            return None

        try:
            return json.loads(raw_value)
        except (TypeError, ValueError):
            return raw_value

    def delete(self, *keys: str) -> int:
        """
        指定したキーを削除する。

        Args:
            keys: 削除するキー群

        Returns:
            削除された件数（0 または 1）
        """
        try:
            deleted = self._client.delete(*keys)
            return int(deleted)
        except redis.RedisError:
            self._logger.exception("Redis 削除失敗: %s", keys)
            return 0

    def get_hash_values(self, key: str) -> list[str]:
        """
        指定したハッシュの全フィールドの値を取得する。

        Args:
            key: ハッシュ名

        Returns:
            ハッシュ内の値リスト。ハッシュが存在しない場合は空リスト。
        """
        try:
            return self._client.hvals(key)
        except redis.RedisError:
            self._logger.exception("Redis HVALS 失敗: key=%s", key)
            return []
