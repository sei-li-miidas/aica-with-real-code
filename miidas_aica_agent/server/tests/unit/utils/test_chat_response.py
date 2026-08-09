import pytest

from utils.chat_request import ChatRequestType
from utils.chat_response import ChatStreamResponse
from utils.log_utils import clear_session_id, set_session_id


@pytest.fixture(autouse=True)
def session_scope():
    """全テストでセッションIDをセットアップする。"""
    set_session_id("test-session-id")
    yield
    clear_session_id()


def test_clone_creates_independent_copy():
    """clone()でPydanticモデルがdeepコピーされ、独立していること。"""
    original = ChatStreamResponse(request_type=ChatRequestType.CHAT)
    original.create_agent_message_response(message_id="m1", message="hello")

    cloned = original.clone()

    original.create_agent_message_response(message_id="m2", message="changed")

    assert cloned is not original
    assert cloned._model is not original._model
    assert cloned._model.message_id == "m1"
    assert cloned._model.message == "hello"
