import pytest
from unittest.mock import MagicMock, Mock, patch, call
from datetime import datetime, timedelta
from repositories.rate_limit_repo import RedisRateLimitRepository
from domain.entities.rate_limit_rule import RateLimitRule
from utils.cache_utils import RedisCacheUtil
from utils.enum import RateLimitActionType, RateLimitScope


@pytest.fixture
def fixed_datetime():
    _fixed_time = datetime(2026, 1, 1, 10, 0, 0)
    with patch("repositories.rate_limit_repo.datetime") as mock_dt:
        mock_dt.now.return_value = _fixed_time
        mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        yield _fixed_time


class TestRedisRateLimitRepository:
    @pytest.fixture
    def mock_redis_cache_util(self):
        """
        RedisCacheUtilのモック
        """
        return Mock(spec=RedisCacheUtil)

    @pytest.fixture
    def redis_rate_limit_repo(self, mock_redis_cache_util):
        """
        RedisRateLimitRepositoryのインスタンスを生成
        """
        return RedisRateLimitRepository(redis_cache_util=mock_redis_cache_util)

    def test_build_key_hourly(self, redis_rate_limit_repo, fixed_datetime):
        action_type = RateLimitActionType.CHAT_REQUEST
        scope = RateLimitScope.SESSION
        rule = RateLimitRule(window_hours=1, limit=100)

        key = redis_rate_limit_repo._build_key(fixed_datetime, action_type, scope, rule)
        assert key == "chat_request:session:1h:2026010110"

    def test_build_key_daily(self, redis_rate_limit_repo, fixed_datetime):
        action_type = RateLimitActionType.CHAT_REQUEST
        scope = RateLimitScope.GUEST
        rule = RateLimitRule(window_hours=24, limit=1000)

        key = redis_rate_limit_repo._build_key(fixed_datetime, action_type, scope, rule)
        assert key == "chat_request:guest:24h:20260101"

    def test_build_key_unsupported_window(self, redis_rate_limit_repo, fixed_datetime):
        action_type = RateLimitActionType.CHAT_REQUEST
        scope = RateLimitScope.SESSION
        rule = RateLimitRule(window_hours=3, limit=100)

        with pytest.raises(ValueError, match="Unsupported window_hours: 3"):
            redis_rate_limit_repo._build_key(fixed_datetime, action_type, scope, rule)

    def test_try_increment_within_limit(
        self, redis_rate_limit_repo, mock_redis_cache_util, fixed_datetime
    ):
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [10]  # 制限(100)内
        mock_redis_cache_util.pipeline.return_value = mock_pipeline

        checks = [
            (
                RateLimitActionType.CHAT_REQUEST,
                RateLimitScope.SESSION,
                "session1",
                RateLimitRule(window_hours=1, limit=100),
            ),
            (
                RateLimitActionType.CHAT_REQUEST,
                RateLimitScope.IP,
                "127.0.0.1",
                RateLimitRule(window_hours=1, limit=100),
            ),
        ]

        result = redis_rate_limit_repo.try_increment(checks)

        assert result is True
        assert mock_redis_cache_util.pipeline.call_count == 2

        # 1回目の呼び出し(session)の検証
        mock_pipeline.hincrby.assert_any_call(
            name="chat_request:session:1h:2026010110", key="session1"
        )
        # 2回目の呼び出し(ip)の検証
        mock_pipeline.hincrby.assert_any_call(
            name="chat_request:ip:1h:2026010110", key="127.0.0.1"
        )

        expire_at = fixed_datetime + timedelta(days=7)
        expire_seconds = int((expire_at - fixed_datetime).total_seconds())
        mock_pipeline.expire.assert_has_calls(
            [
                call("chat_request:session:1h:2026010110", expire_seconds),
                call("chat_request:ip:1h:2026010110", expire_seconds),
            ]
        )

    def test_try_increment_exceeded(self, redis_rate_limit_repo, mock_redis_cache_util):
        mock_pipeline_session = MagicMock()
        mock_pipeline_session.execute.return_value = [50]
        mock_pipeline_ip = MagicMock()
        mock_pipeline_ip.execute.return_value = [101]

        mock_redis_cache_util.pipeline.side_effect = [
            mock_pipeline_session,
            mock_pipeline_ip,
        ]

        checks = [
            (
                RateLimitActionType.CHAT_REQUEST,
                RateLimitScope.SESSION,
                "session1",
                RateLimitRule(window_hours=1, limit=100),
            ),
            (
                RateLimitActionType.CHAT_REQUEST,
                RateLimitScope.IP,
                "127.0.0.1",
                RateLimitRule(window_hours=1, limit=100),
            ),
            (
                RateLimitActionType.CHAT_REQUEST,
                RateLimitScope.GUEST,
                None,
                RateLimitRule(window_hours=1, limit=1000),
            ),
        ]

        result = redis_rate_limit_repo.try_increment(checks)

        assert result is False
        assert mock_redis_cache_util.pipeline.call_count == 2

        mock_pipeline_session.hincrby.assert_called_once()
        mock_pipeline_ip.hincrby.assert_called_once()
        mock_pipeline_ip.incr.assert_not_called()

    def test_try_increment_redis_error_fails_open(
        self, redis_rate_limit_repo, mock_redis_cache_util
    ):
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [None]
        mock_redis_cache_util.pipeline.return_value = mock_pipeline

        checks = [
            (
                RateLimitActionType.CHAT_REQUEST,
                RateLimitScope.SESSION,
                "session1",
                RateLimitRule(window_hours=1, limit=100),
            )
        ]

        result = redis_rate_limit_repo.try_increment(checks)

        assert result is True
