import pytest

from security.llm_output_guard import LLMOutputGuard


@pytest.fixture(autouse=True)
def _reset_llm_output_guard_singleton():
    """LLMOutputGuard はシングルトンなのでテスト間でインスタンス属性が持続する。

    各テスト後にインスタンス属性のモックと _sessions の状態をリセットして
    後続テストへの汚染を防ぐ。
    """
    yield
    guard = LLMOutputGuard()
    for attr in (
        "reset_session_for_new_response",
        "process_stream_chunk",
        "finalize_stream",
        "remove_session",
    ):
        guard.__dict__.pop(attr, None)
    with guard._sessions_lock:
        guard._sessions.clear()
