from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import logging
from utils.const import LOGGER_PREFIX
from utils.cache_utils import CacheUtil, RedisCacheUtil
from utils.enum import RateLimitActionType, RateLimitScope
from domain.entities.rate_limit_rule import RateLimitRule


class BaseRateLimitRepository(ABC):
    @abstractmethod
    def try_increment(
        self,
        checks: list[
            tuple[RateLimitActionType, RateLimitScope, str | None, RateLimitRule]
        ],
    ) -> bool:
        """
        指定されたキーでカウントアップし、レート制限内かチェックする。
        すべてのチェックが制限内であればTrueを返し、
        いずれかが制限を超えた場合はFalseを返す。
        """
        pass


class RedisRateLimitRepository(BaseRateLimitRepository):
    def __init__(
        self,
        redis_cache_util: RedisCacheUtil,
    ) -> None:
        self._redis_cache = redis_cache_util
        self._logger = logging.getLogger(
            f"{LOGGER_PREFIX}.{self.__class__.__module__}.{self.__class__.__name__}"
        )

    def _build_key(
        self,
        now: datetime,
        action_type: RateLimitActionType,
        scope: RateLimitScope,
        rule: RateLimitRule,
    ) -> str:
        if rule.window_hours == 1:  # 1時間単位
            time_key = now.strftime("%Y%m%d%H")
        elif rule.window_hours == 24:  # 1日単位
            time_key = now.strftime("%Y%m%d")
        else:
            raise ValueError(f"Unsupported window_hours: {rule.window_hours}")

        return CacheUtil.build_cache_key_without_session_id(
            action_type, scope, f"{rule.window_hours}h", time_key
        )

    def try_increment(
        self,
        checks: list[
            tuple[RateLimitActionType, RateLimitScope, str | None, RateLimitRule]
        ],
    ) -> bool:
        """
        指定されたキーでカウントアップし、レート制限内かチェックする。
        各チェックのカウントアップと有効期限設定はアトミックに行われる。
        """
        now = datetime.now()
        expire_at = now + timedelta(days=7)
        seconds_until_expire = int((expire_at - now).total_seconds())

        for action_type, scope, identifier, rule in checks:
            try:
                key = self._build_key(now, action_type, scope, rule)

                pipe = self._redis_cache.pipeline()

                if scope == RateLimitScope.GUEST:
                    pipe.incr(key)
                elif (
                    scope in [RateLimitScope.SESSION, RateLimitScope.IP] and identifier
                ):
                    pipe.hincrby(name=key, key=identifier)
                else:
                    self._logger.error(
                        "Invalid scope or missing identifier for key: %s. Allowing request.",
                        key,
                    )
                    continue

                # expireは冪等性があるため、毎回設定しておく
                pipe.expire(key, seconds_until_expire)

                results = pipe.execute()
                current_count = results[0]

                if current_count is None:
                    self._logger.error(
                        "Failed to increment key: %s. Allowing request.", key
                    )
                    continue

                if current_count > rule.limit:
                    """
                    スコープの狭いものから順にチェックしていき、制限を超えた時点でFalseを返します。
                    例えばセッションで制限を超えた場合、IPや非会員全体でのカウントアップは行われません。
                    """
                    return False
            except Exception:
                self._logger.exception(
                    "Error checking rate limit for key: %s. Allowing request.", key
                )
                continue

        return True
