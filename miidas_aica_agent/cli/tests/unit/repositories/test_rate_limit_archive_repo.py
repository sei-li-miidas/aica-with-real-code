import pytest
from unittest.mock import MagicMock, Mock
from datetime import date
import statistics
from commands.aggregate_and_delete_rate_limits import RateLimitConfig
from repositories.rate_limit_archive_repo import RedisRateLimitArchiveRepository
from utils.enum import RateLimitActionType, RateLimitScope
from utils.cache_utils import RedisCacheUtil


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


def _extract_rules_for_test(rate_limit_config: dict):
    """テスト用に設定値からルールを抽出するヘルパー関数"""
    # AggregateAndDeleteRateLimits の _extract_rules と同様のロジック
    tmp_config = RateLimitConfig(**rate_limit_config)
    for action_type, action_limits in tmp_config:
        if not action_limits:
            continue
        scope_map = [
            (RateLimitScope.SESSION, action_limits.session),
            (RateLimitScope.IP, action_limits.ip),
            (RateLimitScope.GUEST, action_limits.guest),
        ]
        for scope, rules in scope_map:
            for rule in rules:
                yield (action_type, scope, rule.window_hours, rule.limit)


@pytest.fixture
def mock_session_factory():
    """セッションファクトリのモック"""
    session = MagicMock()
    session.__enter__.return_value = session

    factory = MagicMock()
    factory.return_value = session
    return factory


@pytest.fixture
def mock_cache_util():
    """CacheUtilのモック"""
    return Mock(spec=RedisCacheUtil)


@pytest.fixture
def redis_repo(mock_session_factory, mock_cache_util):
    """RedisRateLimitArchiveRepositoryのインスタンスを生成"""
    return RedisRateLimitArchiveRepository(
        session_factory=mock_session_factory, cache_util=mock_cache_util
    )


class TestRedisRateLimitArchiveRepository:
    def test_aggregate_to_stats_for_session_scope(
        self, redis_repo, mock_session_factory, mock_cache_util
    ):
        """scope='session'の場合にHVALSを使用して集計する機能の検証"""
        # 準備
        target_date = date(2025, 12, 24)
        action_type = RateLimitActionType.CHAT_REQUEST
        scope = RateLimitScope.SESSION
        hours = 1
        limit = 10

        # 24時間のうち、データが存在する時間帯のモックデータ
        mock_cache_util.get_hash_values.side_effect = lambda key: (
            ["5", "15", "12"] if key == "chat_request:session:1h:2025122409" else []
        )

        # 実行
        redis_repo.aggregate_to_stats(target_date, action_type, scope, hours, limit)

        # 検証：get_hash_valuesが24回呼ばれたか
        assert mock_cache_util.get_hash_values.call_count == 24
        mock_cache_util.get_hash_values.assert_any_call(
            "chat_request:session:1h:2025122400"
        )  # 最初のキー
        mock_cache_util.get_hash_values.assert_any_call(
            "chat_request:session:1h:2025122409"
        )
        mock_cache_util.get_hash_values.assert_any_call(
            "chat_request:session:1h:2025122423"
        )  # 最後のキー

        # 検証：getは呼ばれていない
        mock_cache_util.get.assert_not_called()

        # 検証：Postgresへのexecuteが正しいパラメータで呼ばれたか
        mock_session_factory.return_value.execute.assert_called_once()
        args, _ = mock_session_factory.return_value.execute.call_args
        params_list = args[1]

        # データが存在する1時間分のみINSERTされる
        assert len(params_list) == 1

        stats = params_list[0]
        assert stats["time_key"] == "2025122409"
        assert stats["record_count"] == 3
        assert stats["total_count"] == 32
        assert stats["avg_count"] == pytest.approx(32 / 3)
        assert stats["max_count"] == 15
        assert stats["p50_count"] == statistics.median([5, 15, 12])
        assert (
            stats["p95_count"]
            == statistics.quantiles([5, 15, 12], n=100, method="inclusive")[94]
        )
        assert (
            stats["p99_count"]
            == statistics.quantiles([5, 15, 12], n=100, method="inclusive")[98]
        )
        assert stats["exceeded_count"] == 2
        assert stats["threshold_value"] == 10

    def test_aggregate_to_stats_for_guest_scope(
        self, redis_repo, mock_session_factory, mock_cache_util
    ):
        """scope='guest'の場合にGETを使用して集計する機能の検証 (hours=24)"""
        # 準備
        target_date = date(2025, 12, 24)
        action_type = RateLimitActionType.CHAT_REQUEST
        scope = RateLimitScope.GUEST
        hours = 24
        limit = 100

        # hours=24 の場合、time_keyは 'YYYYMMDD' 形式
        expected_time_key = "20251224"
        expected_key = f"{action_type}:{scope}:{hours}h:{expected_time_key}"
        mock_cache_util.get.side_effect = (
            lambda key: "123" if key == expected_key else None
        )

        # 実行
        redis_repo.aggregate_to_stats(target_date, action_type, scope, hours, limit)

        # 検証：getが1回だけ呼ばれたか
        mock_cache_util.get.assert_called_once_with(expected_key)

        # 検証：get_hash_valuesは呼ばれていない
        mock_cache_util.get_hash_values.assert_not_called()

        # 検証：Postgresへのexecuteが呼ばれたか
        mock_session_factory.return_value.execute.assert_called_once()
        args, _ = mock_session_factory.return_value.execute.call_args
        params_list = args[1]

        # データが存在する1件分のみINSERT
        assert len(params_list) == 1
        stats = params_list[0]
        assert stats["time_key"] == expected_time_key
        assert stats["record_count"] == 1
        assert stats["total_count"] == 123
        assert stats["avg_count"] == 123.0
        assert stats["max_count"] == 123
        assert stats["exceeded_count"] == 1
        assert stats["threshold_value"] == 100

    def test_delete_old_records_deletes_from_redis(self, redis_repo, mock_cache_util):
        """Redisから古いデータを削除する機能の検証"""
        # 準備
        target_date = date(2025, 12, 24)

        # _extract_rules_for_test を使って all_rules を生成
        all_rules = list(_extract_rules_for_test(TEST_CONFIG))

        # RedisRateLimitArchiveRepository.delete_old_records のロジックに合わせたキー生成
        generated_keys = []
        for action_type, scope, hours, _ in all_rules:
            if hours == 1:
                for hour in range(24):
                    time_key = f"{target_date.strftime('%Y%m%d')}{hour:02d}"
                    generated_keys.append(f"{action_type}:{scope}:{hours}h:{time_key}")
            elif hours == 24:
                time_key = target_date.strftime("%Y%m%d")
                generated_keys.append(f"{action_type}:{scope}:{hours}h:{time_key}")

        # delete_old_records の chunk_size と同じ値を使用
        chunk_size = 500

        # mock_cache_util.delete の side_effect を設定して、各チャンクの削除数と全体の呼び出しをシミュレート
        def mock_delete_side_effect(*keys):
            return len(keys)  # 渡されたキーの数だけ削除されたと返す

        mock_cache_util.delete.side_effect = mock_delete_side_effect

        # 実行
        deleted_count = redis_repo.delete_old_records(target_date, all_rules)

        # 検証
        # 実際に delete が呼ばれた引数を全てフラットなリストにする
        actual_deleted_keys = []
        for call_args in mock_cache_util.delete.call_args_list:
            actual_deleted_keys.extend(call_args.args)

        assert (
            mock_cache_util.delete.call_count
            == ((len(generated_keys) + chunk_size - 1) // chunk_size)
            if generated_keys
            else 0
        )
        assert sorted(actual_deleted_keys) == sorted(generated_keys)
        assert deleted_count == len(generated_keys)

    def test_delete_old_records_no_old_data(self, redis_repo, mock_cache_util):
        """古いデータがない場合の削除処理の検証"""
        # 準備
        target_date = date(2025, 12, 24)

        all_rules = list(_extract_rules_for_test(TEST_CONFIG))

        # RedisRateLimitArchiveRepository.delete_old_records のロジックに合わせたキー生成
        generated_keys = []
        for action_type, scope, hours, _ in all_rules:
            if hours == 1:
                for hour in range(24):
                    time_key = f"{target_date.strftime('%Y%m%d')}{hour:02d}"
                    generated_keys.append(f"{action_type}:{scope}:{hours}h:{time_key}")
            elif hours == 24:
                time_key = target_date.strftime("%Y%m%d")
                generated_keys.append(f"{action_type}:{scope}:{hours}h:{time_key}")

        chunk_size = 500  # delete_old_records の chunk_size と同じ
        mock_cache_util.delete.side_effect = (
            lambda *keys: 0
        )  # 全て0を返すことで、削除数は0

        # 実行
        deleted_count = redis_repo.delete_old_records(target_date, all_rules)

        # 検証
        actual_deleted_keys = []
        for call_args in mock_cache_util.delete.call_args_list:
            actual_deleted_keys.extend(call_args.args)

        assert (
            mock_cache_util.delete.call_count
            == ((len(generated_keys) + chunk_size - 1) // chunk_size)
            if generated_keys
            else 0
        )
        assert sorted(actual_deleted_keys) == sorted(
            generated_keys
        )  # キーは渡されるが、削除数は0
        assert deleted_count == 0

    def test_delete_old_records_ignores_non_existent_keys(
        self, redis_repo, mock_cache_util
    ):
        """存在しないキーが含まれていても削除処理が継続されること (新しいロジックに合わせた意図)"""
        # 準備
        target_date = date(2025, 12, 24)

        all_rules = list(_extract_rules_for_test(TEST_CONFIG))

        # RedisRateLimitArchiveRepository.delete_old_records のロジックに合わせたキー生成
        generated_keys = []
        for action_type, scope, hours, _ in all_rules:
            if hours == 1:
                for hour in range(24):
                    time_key = f"{target_date.strftime('%Y%m%d')}{hour:02d}"
                    generated_keys.append(f"{action_type}:{scope}:{hours}h:{time_key}")
            elif hours == 24:
                time_key = target_date.strftime("%Y%m%d")
                generated_keys.append(f"{action_type}:{scope}:{hours}h:{time_key}")

        chunk_size = 500  # delete_old_records の chunk_size と同じ

        # 意図的に、生成されたキーのうち最初の2つだけが削除されたと返すside_effect
        # このテストの意図（deleted_count == 2）を実現するため
        deleted_indices = {0, 1}  # 最初の2つのキーが削除されると仮定
        deleted_keys_set = set()

        def mock_delete_selective_effect(*keys):
            count = 0
            for key in keys:
                if (
                    key in generated_keys
                    and generated_keys.index(key) in deleted_indices
                    and key not in deleted_keys_set
                ):
                    count += 1
                    deleted_keys_set.add(key)
            return count

        mock_cache_util.delete.side_effect = mock_delete_selective_effect

        # 実行
        deleted_count = redis_repo.delete_old_records(target_date, all_rules)

        # 検証
        actual_deleted_keys = []
        for call_args in mock_cache_util.delete.call_args_list:
            actual_deleted_keys.extend(call_args.args)

        assert (
            mock_cache_util.delete.call_count
            == ((len(generated_keys) + chunk_size - 1) // chunk_size)
            if generated_keys
            else 0
        )
        assert sorted(actual_deleted_keys) == sorted(
            generated_keys
        )  # 全てのキーが渡されたことは確認
        assert deleted_count == 2  # 意図した通り2つのキーが削除されたことを確認
