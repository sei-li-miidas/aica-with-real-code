import pytest
from unittest.mock import AsyncMock, Mock, patch

pytestmark = pytest.mark.pre_extraction_parity

from repositories.api_repo import AICAAPIRepository
from repositories.chat_repo import ChatRepository
from repositories.position_repo import PositionRepository
from repositories.user_repo import UserRepository
from repositories.action_log_repo import ActionLogRepository
from services.position_service import PositionService


# PositionRepositoryをモック化
@pytest.fixture
def mock_position_repository():
    return Mock()


# APIRepositoryをモック化
@pytest.fixture
def mock_api_repository():
    return AsyncMock()


# ChatRepositoryをモック化
@pytest.fixture
def mock_chat_repository():
    return Mock()


# UserRepositoryをモック化
@pytest.fixture
def mock_user_repository():
    return Mock()


# ActionLogRepositoryをモック化
@pytest.fixture
def mock_action_log_repository():
    return AsyncMock()


@pytest.mark.asyncio
@patch("services.position_service.decrypt")
async def test_get_position_detail(
    mock_decrypt,
    mock_position_repository,
    mock_api_repository,
    mock_chat_repository,
    mock_user_repository,
    mock_action_log_repository,
):
    # PositionServiceのインスタンスを生成し、依存を注入
    position_svc = PositionService(
        mock_position_repository,
        mock_api_repository,
        mock_chat_repository,
        mock_user_repository,
        mock_action_log_repository,
    )

    # 各モックメソッドの戻り値を設定
    mock_decrypt.return_value = "decrypted_position_id"
    mock_position_repository.get_position_detail.return_value = None
    mock_api_repository.post.return_value = (None, {"Position": "Test Position Data"})
    mock_position_repository.save_position_detail.return_value = None
    mock_user_repository.get_applied_position_ids.return_value = None

    # テスト実行
    result = await position_svc.get_position_detail("encrypted_position_id")

    # 結果を確認
    assert result == {"Position": "Test Position Data", "Applied": False}

    # モックのメソッドが一度だけ特定の引数で呼び出されたことを確認
    mock_api_repository.post.assert_called_once_with(
        "positions/detail/decrypted_position_id"
    )
    mock_position_repository.save_position_detail.assert_called_once_with(
        "decrypted_position_id", {"Position": "Test Position Data", "Applied": False}
    )
