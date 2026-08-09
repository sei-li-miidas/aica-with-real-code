from unittest.mock import Mock, patch

import pytest

from security.llm_output_guard import (
    ForbiddenWordDetectedException,
    LLMOutputGuard,
    TrieNode,
)

pytestmark = pytest.mark.pre_extraction_parity


@pytest.fixture
def raw_guard():
    guard = object.__new__(LLMOutputGuard)
    guard.logger = Mock()
    guard.trie_root = TrieNode()
    guard._sessions = {}
    guard._sessions_lock = Mock()
    return guard


def _prepare_lock(guard):
    class _Lock:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    guard._sessions_lock = _Lock()


def test_build_trie_returns_when_csv_missing(raw_guard):
    with patch("security.llm_output_guard.Path.exists", return_value=False):
        raw_guard._build_trie()

    assert raw_guard.forbidden_words == set()
    raw_guard.logger.warning.assert_called_once()


def test_build_trie_skips_empty_rows_and_blank_words(raw_guard):
    csv_data = "\n   \nabc\n"
    with (
        patch("security.llm_output_guard.Path.exists", return_value=True),
        patch(
            "builtins.open",
            new_callable=pytest.importorskip("unittest.mock").mock_open,
            read_data=csv_data,
        ),
    ):
        raw_guard._build_trie()

    assert raw_guard.forbidden_words == {"abc"}
    assert "a" in raw_guard.trie_root.children


def test_build_trie_logs_and_reraises_on_error(raw_guard):
    with (
        patch("security.llm_output_guard.Path.exists", return_value=True),
        patch("builtins.open", side_effect=RuntimeError("open failed")),
    ):
        with pytest.raises(RuntimeError, match="open failed"):
            raw_guard._build_trie()

    raw_guard.logger.exception.assert_called_once()


def test_resolve_overlap_with_empty_text(raw_guard):
    safe, pending, node, forbidden = raw_guard._resolve_overlap("")
    assert safe == ""
    assert pending == ""
    assert node is raw_guard.trie_root
    assert forbidden is None


def test_resolve_overlap_with_non_normalized_only_text(raw_guard):
    safe, pending, node, forbidden = raw_guard._resolve_overlap("!!@@")
    assert safe == "!!@@"
    assert pending == ""
    assert node is raw_guard.trie_root
    assert forbidden is None


def test_resolve_overlap_detects_forbidden_word_at_end(raw_guard):
    raw_guard._add_word_to_trie("abc")

    safe, pending, node, forbidden = raw_guard._resolve_overlap("abc")

    assert safe == ""
    assert pending == "abc"
    assert node.is_end is True
    assert forbidden == "abc"


def test_resolve_overlap_returns_partial_suffix(raw_guard):
    raw_guard._add_word_to_trie("aat")

    safe, pending, node, forbidden = raw_guard._resolve_overlap("caa")

    assert safe == "c"
    assert pending == "aa"
    assert forbidden is None
    assert node is not raw_guard.trie_root


def test_process_stream_chunk_appends_non_normalized_when_pending_exists(raw_guard):
    _prepare_lock(raw_guard)
    raw_guard._add_word_to_trie("ab")
    state = raw_guard.get_or_create_session("s-1")
    state.pending_buffer = "a"

    chunks = raw_guard.process_stream_chunk("s-1", "!")

    assert chunks == []
    assert state.pending_buffer == "a!"


def test_process_stream_chunk_initializes_none_current_node(raw_guard):
    _prepare_lock(raw_guard)
    state = raw_guard.get_or_create_session("s-2")
    state.current_trie_node = None

    chunks = raw_guard.process_stream_chunk("s-2", "x")

    assert chunks == ["x"]
    assert state.current_trie_node is raw_guard.trie_root


def test_process_stream_chunk_raises_when_resolve_overlap_returns_forbidden(raw_guard):
    _prepare_lock(raw_guard)
    raw_guard.get_or_create_session("s-3")

    with patch.object(
        raw_guard,
        "_resolve_overlap",
        return_value=("", "", raw_guard.trie_root, "badword"),
    ):
        with pytest.raises(ForbiddenWordDetectedException) as exc:
            raw_guard.process_stream_chunk("s-3", "x")

    assert exc.value.word == "badword"


def test_process_stream_chunk_increments_checks_when_overlap_keeps_non_root(raw_guard):
    _prepare_lock(raw_guard)
    state = raw_guard.get_or_create_session("s-4")
    before = state.forbidden_word_checks
    node = TrieNode()

    with patch.object(
        raw_guard, "_resolve_overlap", return_value=("x", "a", node, None)
    ):
        chunks = raw_guard.process_stream_chunk("s-4", "x")

    assert chunks == ["x"]
    assert state.forbidden_word_checks == before + 1


def test_remove_session_deletes_existing_state(raw_guard):
    _prepare_lock(raw_guard)
    raw_guard.get_or_create_session("s-5")

    raw_guard.remove_session("s-5")

    assert "s-5" not in raw_guard._sessions


def test_finalize_stream_flushes_pending_buffer(raw_guard):
    _prepare_lock(raw_guard)
    state = raw_guard.get_or_create_session("s-6")
    state.pending_buffer = "tail"

    final_chunks = raw_guard.finalize_stream("s-6")

    assert final_chunks == ["tail"]
    assert state.pending_buffer == ""


def test_process_stream_chunk_appends_non_normalized_when_pending_empty(raw_guard):
    """non-normalized char with empty pending_buffer → char goes to safe_chunks directly (line 228)."""
    _prepare_lock(raw_guard)
    state = raw_guard.get_or_create_session("s-7")
    assert state.pending_buffer == ""

    chunks = raw_guard.process_stream_chunk("s-7", "!")

    assert chunks == ["!"]
    assert state.pending_buffer == ""
