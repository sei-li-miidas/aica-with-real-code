import pytest
from unittest.mock import Mock
from datetime import date
from commands.aggregate_and_delete_rate_limits import (
    AggregateAndDeleteRateLimits,
    RateLimitConfig,
)
from repositories.rate_limit_archive_repo import RedisRateLimitArchiveRepository
from utils.enum import RateLimitActionType, RateLimitScope

# テスト用のRateLimitConfig
TEST_CONFIG: RateLimitConfig = {
    "chat_request": {
        "session": [{"window_hours": 1, "limit": 10}],
        "guest": [{"window_hours": 24, "limit": 100}],
    },
    "position_detail": {"ip": [{"window_hours": 1, "limit": 50}]},
    "position_search": {},
    "load_more_positions": {},
}


class TestAggregateAndDeleteRateLimits:
    @pytest.fixture
    def mock_repo(self):
        """RedisRateLimitArchiveRepositoryのモック"""
        return Mock(spec=RedisRateLimitArchiveRepository)

    def test_execute_full_flow(self, mock_repo):
        """正常系のフロー：前日分の集計と削除が実行される"""
        target_date = date(2025, 12, 24)

        command = AggregateAndDeleteRateLimits(
            rate_limit_archive_repository=mock_repo, rate_limit=TEST_CONFIG
        )

        # 実行
        command.execute(target_date=target_date)

        # 検証：aggregate_to_stats がルール数分呼ばれたか
        # 今回の設定では3つのルールがあるので3回
        assert mock_repo.aggregate_to_stats.call_count == 3

        # 具体的な呼び出し内容の確認
        mock_repo.aggregate_to_stats.assert_any_call(
            target_date, RateLimitActionType.CHAT_REQUEST, RateLimitScope.SESSION, 1, 10
        )
        mock_repo.aggregate_to_stats.assert_any_call(
            target_date, RateLimitActionType.CHAT_REQUEST, RateLimitScope.GUEST, 24, 100
        )
        mock_repo.aggregate_to_stats.assert_any_call(
            target_date, RateLimitActionType.POSITION_DETAIL, RateLimitScope.IP, 1, 50
        )

        # 検証：最後に削除処理が1回だけ呼ばれたか
        mock_repo.delete_old_records.assert_called_once_with(
            target_date,
            [
                (RateLimitActionType.CHAT_REQUEST, RateLimitScope.SESSION, 1, 10),
                (RateLimitActionType.CHAT_REQUEST, RateLimitScope.GUEST, 24, 100),
                (RateLimitActionType.POSITION_DETAIL, RateLimitScope.IP, 1, 50),
            ],
        )

    def test_execute_error_handling(self, mock_repo):
        """リポジトリでエラーが発生した場合、例外がスローされること"""
        # 準備
        mock_repo.aggregate_to_stats.side_effect = Exception("Valkey Error")

        command = AggregateAndDeleteRateLimits(
            rate_limit_archive_repository=mock_repo, rate_limit=TEST_CONFIG
        )

        # 実行 & 検証
        with pytest.raises(Exception) as excinfo:
            command.execute(target_date=date(2025, 12, 24))

        assert "Valkey Error" in str(excinfo.value)
