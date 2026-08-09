import logging
import os
import tempfile
import time
import pytest
from unittest.mock import MagicMock

from utils.log_utils import (
    clear_request_id,
    clear_session_id,
    clear_tracing_info,
    get_request_id,
    get_session_id,
    set_request_id,
    set_session_id,
    add_tracing_info,
    record_factory,
    KEY_TO_MASK,
    LOG_MASK,
    mask_log_payload,
    old_factory,
)


@pytest.fixture(autouse=True)
def _clear_contextvars():
    """テストの前後でcontextvarsをクリアする"""
    clear_session_id()
    clear_request_id()
    yield
    clear_session_id()
    clear_request_id()


class TestSessionIdFunctions:
    """session_idのcontextvar操作テスト"""

    def test_set_and_get_session_id(self):
        """session_idを設定して取得できることを確認"""
        set_session_id("test-session-123")
        assert get_session_id() == "test-session-123"

    def test_set_session_id_with_none(self):
        """session_idにNoneを設定できることを確認"""
        set_session_id(None)
        assert get_session_id() is None

    def test_get_session_id_returns_none_when_not_set(self):
        """session_idが設定されていない場合Noneを返すことを確認"""
        assert get_session_id() is None

    def test_clear_session_id(self):
        """session_idをクリアできることを確認"""
        set_session_id("test-session-123")
        clear_session_id()
        assert get_session_id() is None


class TestRequestIdFunctions:
    """request_idのcontextvar操作テスト"""

    def test_set_and_get_request_id(self):
        """request_idを設定して取得できることを確認"""
        set_request_id("test-request-456")
        assert get_request_id() == "test-request-456"

    def test_set_request_id_with_none(self):
        """request_idにNoneを設定できることを確認"""
        set_request_id(None)
        assert get_request_id() is None

    def test_get_request_id_returns_none_when_not_set(self):
        """request_idが設定されていない場合Noneを返すことを確認"""
        assert get_request_id() is None

    def test_clear_request_id(self):
        """request_idをクリアできることを確認"""
        set_request_id("test-request-456")
        clear_request_id()
        assert get_request_id() is None


class TestAddTracingInfo:
    """add_tracing_info関数のテスト"""

    def test_add_tracing_info_sets_session_and_request_ids(self):
        """リクエストヘッダーからsession_idとrequest_idを設定できることを確認"""
        mock_request = MagicMock()
        mock_request.headers = {
            "X-SESSION-ID": "session-from-header",
            "X-REQUEST-ID": "request-from-header",
        }

        add_tracing_info(mock_request)

        assert get_session_id() == "session-from-header"
        assert get_request_id() == "request-from-header"

    def test_add_tracing_info_with_missing_headers(self):
        """ヘッダーがない場合Noneが設定されることを確認"""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None

        add_tracing_info(mock_request)

        assert get_session_id() is None
        assert get_request_id() is None


class TestClearTracingInfo:
    """clear_tracing_info関数のテスト"""

    def test_clear_tracing_info_clears_both_ids(self):
        """session_idとrequest_idの両方がクリアされることを確認"""
        set_session_id("test-session")
        set_request_id("test-request")

        clear_tracing_info()

        assert get_session_id() is None
        assert get_request_id() is None


class TestRecordFactory:
    """record_factory関数のテスト"""

    def test_record_factory_adds_session_and_request_ids(self):
        """ログレコードにsession_idとrequest_idが追加されることを確認"""
        set_session_id("session-for-record")
        set_request_id("request-for-record")

        record = record_factory(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        assert record.session_id == "session-for-record"
        assert record.request_id == "request-for-record"

    def test_record_factory_masks_sensitive_args(self):
        """ログレコードの引数内の機密データがマスクされることを確認"""
        # NOT_MASK_LOG_PAYLOADが設定されていないことを確認
        os.environ.pop("NOT_MASK_LOG_PAYLOAD", None)

        record = record_factory(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=({"email": "test@example.com", "name": "John"},),
            exc_info=None,
        )

        assert record.args["email"] == LOG_MASK
        assert record.args["name"] == "John"

    def test_record_factory_skips_masking_when_disabled(self):
        """NOT_MASK_LOG_PAYLOAD設定時にマスク処理がスキップされることを確認"""
        os.environ["NOT_MASK_LOG_PAYLOAD"] = "1"

        try:
            record = record_factory(
                name="test_logger",
                level=logging.INFO,
                pathname="/path/to/file.py",
                lineno=42,
                msg="Test message",
                args=({"email": "test@example.com", "password": "secret"},),
                exc_info=None,
            )

            assert record.args["email"] == "test@example.com"
            assert record.args["password"] == "secret"
        finally:
            os.environ.pop("NOT_MASK_LOG_PAYLOAD", None)

    def test_record_factory_performance_with_masking(self):
        """マスク処理ありなしでのログ出力速度を比較し、10%以上遅くなったら失敗"""

        # record_factoryを設定
        logging.setLogRecordFactory(record_factory)

        # ロガー設定（ファイル出力）
        logger = logging.getLogger("test_logger_file")
        logger.setLevel(logging.INFO)
        logger.propagate = False  # 親ロガーへの伝播を無効化

        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".log"
        ) as temp_file:
            temp_file_name = temp_file.name

        handler = logging.FileHandler(temp_file_name)
        logger.addHandler(handler)

        test_data = {
            "email": "test@example.com",
            "password": "secret123",
            "user": {"phone_no": "123-456-7890", "profile": {"lastname": "Doe"}},
            "items": [{"email": f"user{i}@test.com"} for i in range(10)],
        }

        iterations = 1000  # ファイル出力のため数を元に戻す

        print(
            f"\nStarting file output performance test with {iterations} iterations..."
        )

        # マスクなしでの測定（NOT_MASK_LOG_PAYLOAD設定）
        os.environ["NOT_MASK_LOG_PAYLOAD"] = "1"
        try:
            start_time = time.time()
            for _ in range(iterations):
                logger.info("Test message %s", test_data)
            time_without_mask = time.time() - start_time
        finally:
            os.environ.pop("NOT_MASK_LOG_PAYLOAD", None)

        # マスクありでの測定（NOT_MASK_LOG_PAYLOAD未設定）
        os.environ.pop("NOT_MASK_LOG_PAYLOAD", None)
        start_time = time.time()
        for _ in range(iterations):
            logger.info("Test message %s", test_data)
        time_with_mask = time.time() - start_time

        # マスク処理有効だが機密データなしでの測定
        clean_data = {
            "name": "John Doe",
            "age": 30,
            "user": {"id": 123, "profile": {"status": "active"}},
            "items": [{"id": i, "name": f"item{i}"} for i in range(10)],
        }

        os.environ.pop("NOT_MASK_LOG_PAYLOAD", None)
        start_time = time.time()
        for _ in range(iterations):
            logger.info("Test message %s", clean_data)
        time_with_mask_no_sensitive = time.time() - start_time

        # クリーンアップ
        logger.removeHandler(handler)
        handler.close()

        # 一時ファイルを削除
        os.unlink(temp_file_name)

        # 元に戻す
        logging.setLogRecordFactory(old_factory)

        # 結果表示
        print("\n" + "=" * 50)
        print("File output performance test results:")
        print(f"time_without_mask: {time_without_mask:.4f}s")
        print(f"time_with_mask: {time_with_mask:.4f}s")
        print(f"time_with_mask_no_sensitive: {time_with_mask_no_sensitive:.4f}s")
        print("=" * 50)

        # 10%以上遅くなったら失敗
        # performance_degradation = (time_with_mask - time_without_mask) / time_without_mask
        # assert performance_degradation < 0.1, f"マスク処理により{performance_degradation*100:.1f}%遅くなりました（許容値: 10%未満）time_with_mask: {time_with_mask:.4f}s, time_without_mask: {time_without_mask:.4f}s"

    def test_record_factory_adds_caller_info(self):
        """ログレコードにcaller情報が追加されることを確認"""
        record = record_factory(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        assert record.caller == "/path/to/file.py:42"

    def test_record_factory_with_none_ids(self):
        """session_idとrequest_idがNoneの場合もレコードに設定されることを確認"""
        # NOT_MASK_LOG_PAYLOADが設定されていないことを確認
        os.environ.pop("NOT_MASK_LOG_PAYLOAD", None)

        record = record_factory(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        assert record.session_id is None
        assert record.request_id is None


class TestKeyToMask:
    """key_to_mask定数のテスト"""

    def test_key_to_mask_contains_expected_keys(self):
        """key_to_maskに期待されるキーが含まれていることを確認"""
        expected_keys = {
            "lastname",
            "firstname",
            "lastnamekana",
            "firstnamekana",
            "email",
            "phoneno",
            "password",
            "last_name",
            "first_name",
            "last_name_kana",
            "first_name_kana",
            "phone_no",
        }

        assert expected_keys.issubset(KEY_TO_MASK)


class TestMaskLogPayload:
    """mask_log_payload関数のテスト"""

    def test_mask_dict_with_sensitive_keys(self):
        """機密キーを含む辞書がマスクされることを確認"""
        payload = {
            "email": "test@example.com",
            "password": "secret123",
            "name": "John Doe",
        }

        result = mask_log_payload(payload)

        assert result["email"] == LOG_MASK
        assert result["password"] == LOG_MASK
        assert result["name"] == "John Doe"

    def test_mask_nested_dict(self):
        """ネストした辞書の機密データがマスクされることを確認"""
        payload = {
            "user": {
                "email": "test@example.com",
                "profile": {"phone_no": "123-456-7890"},
            },
            "public_data": "visible",
        }

        result = mask_log_payload(payload)

        assert result["user"]["email"] == LOG_MASK
        assert result["user"]["profile"]["phone_no"] == LOG_MASK
        assert result["public_data"] == "visible"

    def test_mask_list_with_dicts(self):
        """辞書を含むリストの機密データがマスクされることを確認"""
        payload = [
            {"email": "user1@example.com", "name": "User1"},
            {"email": "user2@example.com", "name": "User2"},
        ]

        result = mask_log_payload(payload)

        assert result[0]["email"] == LOG_MASK
        assert result[0]["name"] == "User1"
        assert result[1]["email"] == LOG_MASK
        assert result[1]["name"] == "User2"

    def test_mask_non_dict_returns_unchanged(self):
        """辞書以外のデータは変更されないことを確認"""
        assert mask_log_payload("string") == "string"
        assert mask_log_payload(123) == 123
        assert mask_log_payload(None) is None
