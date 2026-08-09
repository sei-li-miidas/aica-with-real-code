import json
import logging
from abc import ABC, abstractmethod
from typing import Any

import redis

from utils.const import LOGGER_PREFIX
from utils.log_utils import get_session_id


class CacheUtil(ABC):
    """
    キャッシュリポジトリの抽象クラス
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(
            f"{LOGGER_PREFIX}.{self.__class__.__module__}.{self.__class__.__name__}"
        )

    @abstractmethod
    def save(
        self,
        key: str,
        value: Any,
        expire_seconds: int | None = None,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get(self, key: str) -> Any | None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> int:
        raise NotImplementedError

    @staticmethod
    def build_cache_key(*keys: str) -> str:
        """
        任意のキー群を連結してキャッシュキーを組み立てる。None は許可しません。
        """
        if any(k is None for k in keys):
            raise ValueError("cache key parts must not be None")
        parts = [k for k in keys]
        return ":".join(parts)

    @staticmethod
    def build_cache_key_with_session_id(*keys: str) -> str:
        """
        セッションIDを自動で含めたキャッシュキーを作成する。
        先頭にセッションIDを付与し、他のキー要素は任意に続ける。
        """
        session_id = get_session_id() or "anonymous"
        return CacheUtil.build_cache_key(session_id, *keys)

    @staticmethod
    def build_cache_key_without_session_id(*keys: str) -> str:
        """
        セッションIDなしでキャッシュキーを作成する。
        """
        return CacheUtil.build_cache_key(*keys)

    def get_cached_dict(self, key: str) -> dict[str, Any]:
        """
        キャッシュから dict を安全に取得するヘルパー。
        dict でない場合は空 dict を返す。
        """
        cached = self.get(key)
        return cached if isinstance(cached, dict) else {}

    def get_cached_list(self, key: str) -> list[Any]:
        """
        キャッシュから list を安全に取得するヘルパー。
        list でない場合は空リストを返す。
        """
        cached = self.get(key)
        return cached if isinstance(cached, list) else []


class RedisCacheUtil(CacheUtil):
    """
    Redis を利用してデータを保存・取得する実装
    """

    def __init__(
        self,
        host: str,
        port: int,
        default_ttl: int,
    ) -> None:
        super().__init__()

        if host is None:
            raise ValueError("Redis host must be provided")

        if not isinstance(port, int):
            raise TypeError("Redis port must be int")
        if port <= 0:
            raise ValueError("Redis port must be a positive integer")

        if not isinstance(default_ttl, int):
            raise TypeError("Redis ttl must be int")
        if default_ttl < 0:
            raise ValueError("Redis ttl must be zero or a positive integer")

        self._host: str = host
        self._port: int = port
        self._default_ttl: int = default_ttl

        self._client = redis.Redis(host=host, port=port, decode_responses=True)

    def save(
        self,
        key: str,
        value: Any,
        expire_seconds: int | None = None,
    ) -> bool:
        """
        任意の値を Redis に保存する。シリアライズできない場合は失敗します。

        Args:
            key: 保存先のキー
            value: 保存する値（str/bytes 以外は JSON 化を試みる）
            expire_seconds: 期限（秒）。None の場合は default_ttl を使用し、0 以下の場合は永続化

        Returns:
            保存に成功したか
        """
        try:
            serialized = self._serialize(value)
        except (TypeError, ValueError):
            self._logger.exception("Redis に保存する値のシリアライズに失敗: %s", key)
            return False

        try:
            ttl = expire_seconds if expire_seconds is not None else self._default_ttl
            ttl = ttl if ttl and ttl > 0 else None
            result = self._client.set(name=key, value=serialized, ex=ttl)
            return bool(result)
        except redis.RedisError:
            self._logger.exception("Redis 保存失敗: %s", key)
            return False

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

    def delete(self, key: str) -> int:
        """
        指定したキーを削除する。

        Args:
            key: 削除するキー

        Returns:
            削除された件数（0 または 1）
        """
        try:
            deleted = self._client.delete(key)
            return int(deleted)
        except redis.RedisError:
            self._logger.exception("Redis 削除失敗: %s", key)
            return 0

    def incr(self, key: str) -> int | None:
        """
        指定したキーの値を 1 増やす。

        Args:
            key: 対象のキー

        Returns:
            インクリメント後の値。エラー時は None
        """
        try:
            return self._client.incr(key)
        except redis.RedisError:
            self._logger.exception("Redis INCR 失敗: %s", key)
            return None

    def hincrby(self, key: str, field: str, increment: int = 1) -> int | None:
        """
        指定したハッシュのフィールドの値を指定した数だけ増やす。

        Args:
            key: ハッシュ名
            field: ハッシュ内のフィールド
            increment: 増加数

        Returns:
            インクリメント後の値。エラー時は None
        """
        try:
            return self._client.hincrby(key, field, increment)
        except redis.RedisError:
            self._logger.exception("Redis HINCRBY 失敗: key=%s, field=%s", key, field)
            return None

    def expire(self, key: str, seconds: int) -> bool:
        """
        キーに有効期限（秒数）を設定する。

        Args:
            key: 対象のキー
            seconds: 有効期限（秒数）

        Returns:
            設定に成功したか
        """
        try:
            return self._client.expire(key, seconds)
        except redis.RedisError:
            self._logger.exception("Redis EXPIRE 失敗: %s", key)
            return False

    def pipeline(self) -> "redis.client.Pipeline":
        """
        Redis パイプラインオブジェクトを返す。

        Returns:
            パイプラインオブジェクト
        """
        return self._client.pipeline()

    @staticmethod
    def _serialize(value: Any) -> str | bytes:
        """Redis に保存できる形（文字列または JSON 文字列）へ変換する。"""
        if isinstance(value, (str, bytes)):
            return value
        return json.dumps(value, ensure_ascii=False)
