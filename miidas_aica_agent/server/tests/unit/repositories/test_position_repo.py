"""
PositionRepository の単体テスト

アーキテクチャ上の注記 (Feature #78051):
- ユーザーの検索条件が UserProfile.job_search_filter (DB) から外部API管理に変更
- PositionRepository._load_user_preference_from_db() の DB フォールバック機構を削除
- 検索条件は外部APIで管理（PositionService.current_search_filter()）
- 本リポジトリのキャッシュ対象: ポジション検索結果のID群のみ

テスト移行:
  削除: test_user_preferences_are_session_scoped (DB ベース)
  追加: test_position_search_result_includes_search_filters (APIレスポンス検証)

  削除: test_get_user_preferences_loads_from_db (DB フォールバック)
  追加: test_cache_persistence_across_tool_calls (ポジションID キャッシュ隔離)

  削除: test_load_user_preference_from_db_* (エラーケース)
  追加: test_cache_miss_returns_empty_list, test_cache_separate_per_session

注: SearchFilters はキャッシュされず、外部APIレスポンスとしてのみ扱われる
"""

from threading import Thread

import fakeredis
import pytest

from repositories.position_repo import PositionRepository
from utils.cache_utils import RedisCacheUtil
from utils.log_utils import set_session_id, clear_session_id


@pytest.fixture(scope="module")
def fake_redis_server():
    server = fakeredis.TcpFakeServer(("127.0.0.1", 0), server_type="redis")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture
def cache_util(fake_redis_server):
    host, port = fake_redis_server.server_address
    return RedisCacheUtil(host=host, port=port, default_ttl=5)


@pytest.fixture(autouse=True)
def clear_redis(cache_util):
    cache_util._client.flushall()


@pytest.fixture
def repo(cache_util):
    return PositionRepository(
        cache_util=cache_util,
    )


@pytest.fixture(autouse=True)
def session_scope():
    set_session_id("test-session")
    yield
    clear_session_id()


def test_search_result_cache(repo: PositionRepository):
    # save_search_result_position_ids / get_cached_position_search_result の動作確認
    count = repo.save_search_result_position_ids("tool-1", [1, 2, 2, 3])
    assert count == 3
    assert repo.get_cached_position_search_result("tool-1") == [1, 2, 3]


def test_missing_cached_search_result_returns_empty(repo: PositionRepository):
    # get_cached_position_search_result キャッシュが空の場合は空リストを返すことを確認
    assert repo.get_cached_position_search_result("not-exist") == []


def test_save_search_result_position_ids_returns_zero_when_empty(
    repo: PositionRepository,
):
    # save_search_result_position_ids が空リストでは 0 を返すことを確認
    assert repo.save_search_result_position_ids("tool-empty", []) == 0
    assert repo.get_cached_position_search_result("tool-empty") == []


def test_remove_search_result_positions_ids_removes_empty(repo: PositionRepository):
    # remove_search_result_positions_ids で空になったらキーを削除することを確認
    repo.save_search_result_position_ids("tool-2", [10, 11])
    remaining = repo.remove_search_result_positions_ids("tool-2", [10, 11])
    assert remaining == 0
    assert repo.get_cached_position_search_result("tool-2") == []


def test_remove_search_result_positions_ids_leaves_remaining(repo: PositionRepository):
    # 部分削除後に残りの件数を返すことを確認
    repo.save_search_result_position_ids("tool-3", [5, 6, 7])
    remaining = repo.remove_search_result_positions_ids("tool-3", [7])
    assert remaining == 2
    assert repo.get_cached_position_search_result("tool-3") == [5, 6]


def test_process_and_cache_positions_encrypts(monkeypatch, repo: PositionRepository):
    # process_and_cache_positions が ID を暗号化することを確認
    monkeypatch.setattr("repositories.position_repo.encrypt", lambda *_args: "enc-id")
    positions = [{"ID": 123, "Name": "abc"}]
    processed = repo.process_and_cache_positions(positions)
    assert processed[0]["ID"] == "enc-id"


def test_process_and_cache_positions_returns_empty_on_encrypt_error(
    monkeypatch, repo: PositionRepository
):
    # 暗号化で例外が発生した場合は空リストを返すことを確認
    def boom(*_args):
        raise Exception("boom")

    monkeypatch.setattr("repositories.position_repo.encrypt", boom)
    assert repo.process_and_cache_positions([{"ID": 1}]) == []


def test_process_and_cache_positions_returns_empty_when_input_empty(
    repo: PositionRepository,
):
    # 入力が空のときは空リストを返すことを確認
    assert repo.process_and_cache_positions([]) == []


def test_process_position_search_result(monkeypatch, repo: PositionRepository):
    # process_position_search_result が ID をキャッシュし、ポジションとレコメンドを暗号化することを確認
    monkeypatch.setattr("repositories.position_repo.encrypt", lambda *_args: "enc")
    search_result = {
        "AllPositionIds": [1, 2, 2],
        "Positions": [{"ID": 1}],
        "Recommendations": [{"Theme": "abc"}],
    }
    processed = repo.process_position_search_result("tool-x", search_result)
    assert processed["TotalPositionCount"] == 2
    assert processed["Positions"][0]["ID"] == "enc"
    assert processed["Recommendations"][0]["Theme"] == "enc"
    # cached search results are stored
    assert repo.get_cached_position_search_result("tool-x") == [1, 2]


def test_position_detail_cache_is_global(repo: PositionRepository):
    # save_position_detail / get_position_detail のキャッシュ確認
    detail = {"id": "p-1"}
    repo.save_position_detail("p-1", detail)
    assert repo.get_position_detail("p-1") == detail


def test_company_detail_cache(repo: PositionRepository):
    # save_company_detail / get_company_detail のキャッシュ確認
    company = {"name": "Acme"}
    repo.save_company_detail("c-1", company)
    assert repo.get_company_detail("c-1") == company


def test_business_detail_cache(repo: PositionRepository):
    # save_business_detail / get_business_detail のキャッシュ確認
    business = {"sector": "Tech"}
    repo.save_business_detail("b-1", business)
    assert repo.get_business_detail("b-1") == business


# ============================================================================
# 新規テスト: job_search_filter 削除後のポジション検索結果キャッシュ検証
# (SearchFilters は外部API管理のため、ここではレスポンス整合性のみ検証)
# ============================================================================


def test_position_search_result_includes_search_filters(
    monkeypatch, repo: PositionRepository
):
    """
    外部APIから返却された SearchFilters と JobtypeNamesWithSameSearchFilters が
    process_position_search_result() 経由で正しく返却されることを確認する。
    キャッシュ保存ではなく、レスポンス整合性の検証。
    置換対象: test_user_preferences_are_session_scoped (DB ベース)
    """
    monkeypatch.setattr("repositories.position_repo.encrypt", lambda *_args: "enc")
    search_result = {
        "AllPositionIds": [1, 2],
        "Positions": [{"ID": 1}],
        "Recommendations": [],
        "SearchFilters": {"LocationType": "OFFICE", "SalaryMin": 5000000},
        "JobtypeNamesWithSameSearchFilters": ["IT", "Finance"],
    }
    processed = repo.process_position_search_result("tool-filters", search_result)

    # SearchFilters が外部APIレスポンスとしてそのまま返却されることを確認
    assert processed.get("SearchFilters") == {
        "LocationType": "OFFICE",
        "SalaryMin": 5000000,
    }
    # JobtypeNamesWithSameSearchFilters も同様に返却されることを確認
    assert processed.get("JobtypeNamesWithSameSearchFilters") == ["IT", "Finance"]


def test_position_search_result_handles_missing_search_filters(
    monkeypatch, repo: PositionRepository
):
    """
    外部APIレスポンスに SearchFilters が含まれない場合でも
    結果処理が破綻しないことを確認する（後方互換性）。
    """
    monkeypatch.setattr("repositories.position_repo.encrypt", lambda *_args: "enc")
    search_result = {
        "AllPositionIds": [1],
        "Positions": [{"ID": 1}],
        "Recommendations": [],
        # SearchFilters または JobtypeNamesWithSameSearchFilters なし
    }
    processed = repo.process_position_search_result("tool-no-filters", search_result)

    # 外部APIレスポンスに含まれていなくても処理は成功すべき
    assert processed.get("SearchFilters") is None
    assert processed.get("JobtypeNamesWithSameSearchFilters") is None


def test_cache_persistence_across_tool_calls(repo: PositionRepository):
    """
    ポジション検索結果のID群が複数のツール呼び出しで
    独立してキャッシュできることを確認する。
    セッション単位のキャッシュ隔離が正しく機能することを確認する。
    置換対象: test_get_user_preferences_loads_from_db
    """
    # 最初のツール呼び出しからポジションID を保存
    result_1 = repo.process_position_search_result(
        "tool-call-1",
        {"AllPositionIds": [10, 20], "Positions": [], "Recommendations": []},
    )
    cached_1 = repo.get_cached_position_search_result("tool-call-1")
    assert cached_1 == [10, 20]

    # 同一セッション内の 2 番目のツール呼び出しからポジションID を保存
    result_2 = repo.process_position_search_result(
        "tool-call-2",
        {"AllPositionIds": [30, 40], "Positions": [], "Recommendations": []},
    )
    cached_2 = repo.get_cached_position_search_result("tool-call-2")
    assert cached_2 == [30, 40]

    # 両方のポジションID が独立にキャッシュされているはず
    assert repo.get_cached_position_search_result("tool-call-1") == [10, 20]
    assert repo.get_cached_position_search_result("tool-call-2") == [30, 40]


def test_cache_miss_returns_empty_list(repo: PositionRepository):
    """
    ポジション検索結果 ID のキャッシュミス時に None ではなく空リストを返すことを確認する。
    DB フォールバックが削除されたため、これが予期される動作である。
    置換対象: test_load_user_preference_from_db_error
    """
    # DB フォールバックなし - ポジション検索結果IDのキャッシュミス時に空リストを返すはず
    result = repo.get_cached_position_search_result("nonexistent-tool-call")
    assert result == []
    assert isinstance(result, list)


def test_cache_separate_per_session(repo: PositionRepository, cache_util):
    """
    set_session_id() でポジション検索結果 ID がセッション単位で正しく隔離されることを確認する。
    DB フォールバックが削除されたため、セッションは独立したキャッシュを持つ必要がある。
    """
    # 現在のセッションがポジション検索結果ID を保存
    repo.save_search_result_position_ids("tool-session-1", [100, 101])
    assert repo.get_cached_position_search_result("tool-session-1") == [100, 101]

    # 新しいセッションをシミュレート
    clear_session_id()
    set_session_id("test-session-2")

    # 新しいセッションは前のセッションのキャッシュを見えてはいけない
    assert repo.get_cached_position_search_result("tool-session-1") == []

    # 他のテストのためにリセット
    clear_session_id()
    set_session_id("test-session")
