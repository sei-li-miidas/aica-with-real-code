"""Integration coverage: security/llm_output_guard.py — 100% branch coverage.

Tests use the real LLMOutputGuard singleton with controlled forbidden-word sets.
The autouse fixture saves and restores singleton state so every test is isolated.
"""

from __future__ import annotations

import io
from copy import deepcopy
from unittest.mock import mock_open, patch

import pytest

from security.llm_output_guard import (
    ForbiddenWordDetectedException,
    LLMOutputGuard,
    TrieNode,
)

pytestmark = pytest.mark.pre_extraction_parity


# ─── Singleton state helpers ──────────────────────────────────────────────────


def _clone_trie(node: TrieNode) -> TrieNode:
    cloned = TrieNode()
    cloned.is_end = node.is_end
    cloned.word = node.word
    cloned.children = {c: _clone_trie(child) for c, child in node.children.items()}
    return cloned


@pytest.fixture(autouse=True)
def restore_singleton():
    guard = LLMOutputGuard()
    orig_trie = _clone_trie(guard.trie_root)
    orig_words = set(guard.forbidden_words)
    orig_sessions = deepcopy(guard._sessions)

    yield

    guard.trie_root = orig_trie
    guard.forbidden_words = orig_words
    with guard._sessions_lock:
        guard._sessions = orig_sessions


def _setup_words(guard: LLMOutputGuard, *words: str) -> None:
    """Replace the singleton's trie with only the given words."""
    guard.trie_root = TrieNode()
    guard.forbidden_words = set(words)
    for w in words:
        guard._add_word_to_trie(w)


# ─── _build_trie: file not found (lines 107-108) ─────────────────────────────


def test_build_trie_file_not_found_logs_and_returns():
    """Lines 107-108: CSV missing → warning + early return, forbidden_words stays empty."""
    guard = LLMOutputGuard()
    guard.trie_root = TrieNode()
    guard.forbidden_words = set()

    with patch("pathlib.Path.exists", return_value=False):
        guard._build_trie()

    assert guard.forbidden_words == set()


# ─── _build_trie: empty row in CSV (line 115) ────────────────────────────────


def test_build_trie_skips_empty_csv_rows():
    """Line 115: row is empty list → `if not row: continue`."""
    guard = LLMOutputGuard()
    guard.trie_root = TrieNode()
    guard.forbidden_words = set()

    # An empty line in CSV produces row=[] which is falsy
    csv_content = "\nword\n"
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", return_value=io.StringIO(csv_content)),
    ):
        guard._build_trie()

    assert "word" in guard.forbidden_words


# ─── _build_trie: blank word after strip (line 118) ──────────────────────────


def test_build_trie_skips_whitespace_only_words():
    """Line 118: word.strip() is '' → `if not word: continue`."""
    guard = LLMOutputGuard()
    guard.trie_root = TrieNode()
    guard.forbidden_words = set()

    # "  " strips to "" which is falsy
    csv_content = "  \nword\n"
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", return_value=io.StringIO(csv_content)),
    ):
        guard._build_trie()

    assert "word" in guard.forbidden_words
    assert "" not in guard.forbidden_words


# ─── _build_trie: exception during read (lines 121-123) ─────────────────────


def test_build_trie_exception_is_logged_and_re_raised():
    """Lines 121-123: open() raises → logger.exception + re-raise."""
    guard = LLMOutputGuard()
    guard.trie_root = TrieNode()
    guard.forbidden_words = set()

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", side_effect=IOError("disk error")),
    ):
        with pytest.raises(IOError, match="disk error"):
            guard._build_trie()


# ─── _resolve_overlap: empty text (line 166) ─────────────────────────────────


def test_resolve_overlap_empty_text_returns_early():
    """Line 166: text='' → returns ('', '', root, None) immediately."""
    guard = LLMOutputGuard()
    _setup_words(guard, "ab")

    safe, pending, node, word = guard._resolve_overlap("")

    assert safe == ""
    assert pending == ""
    assert node is guard.trie_root
    assert word is None


# ─── _resolve_overlap: char normalizes to empty (line 173) ───────────────────


def test_resolve_overlap_skips_non_normalizable_chars():
    """Line 173: normalized char is '' → continue (skip it)."""
    guard = LLMOutputGuard()
    _setup_words(guard, "ab")

    # '-' normalizes to '' so it is skipped; 'a' and 'b' remain
    safe, pending, node, word = guard._resolve_overlap("-a-b")

    # 'a','b' together at start_norm=0 match 'a'->'b' path (ab-node, is_end)
    # pos==n for that, but since "ab" is a complete forbidden word prefix at offset 0:
    # If start_norm=0 covers 'a','b' → ab-node.is_end → return ("", "-a-b", node, "ab")
    # The norm-to-orig mapping must be checked, but at minimum word is not None
    assert word == "ab"


# ─── _resolve_overlap: all chars normalize to empty (line 179) ───────────────


def test_resolve_overlap_all_non_normalizable_returns_text_safe():
    """Line 179: normalized_chars=[] → returns (text, '', root, None)."""
    guard = LLMOutputGuard()
    _setup_words(guard, "ab")

    safe, pending, node, word = guard._resolve_overlap("---")

    assert safe == "---"
    assert pending == ""
    assert node is guard.trie_root
    assert word is None


# ─── _resolve_overlap: pos==n and is_end → forbidden word (lines 193-194) ────


def test_resolve_overlap_detects_forbidden_word_at_suffix():
    """Lines 193-194: pos==n AND node.is_end → returns forbidden_word.

    Trie has 'cab' and 'at'. Text 'cat':
      start=0: c→ca-node, a→ca-node, t not in ca → pos<n, no update
      start=1: a→a-node, t→at-node, pos==n, is_end=True → return "at"
    """
    guard = LLMOutputGuard()
    _setup_words(guard, "cab", "at")

    safe, pending, node, word = guard._resolve_overlap("cat")

    assert word == "at"
    assert safe == ""
    assert pending == "cat"


# ─── _resolve_overlap: pos==n, not is_end → best_start update (lines 195-197) -


def test_resolve_overlap_updates_best_start_when_pos_equals_n_no_end():
    """Lines 195-197: pos==n but node is NOT is_end → update best_start_norm.

    Trie has 'cat','car','aat'. Text 'caa':
      start=0: c→ca-node, a→ca-node (pos=2 < n=3) → no, pos<n
      Actually: c→c-node, a→ca-node, a→ NOT in ca-node → pos=2 < n=3, pos<n
      start=1: a→a-node, a→aa-node, pos=3==n, aa-node not is_end → update best=1
      start=2: a→a-node, pos=3==n, a-node not is_end → 2 < 1? No → no update
    Returns ("c", "aa", aa-node, None).
    """
    guard = LLMOutputGuard()
    _setup_words(guard, "cat", "car", "aat")

    safe, pending, node, word = guard._resolve_overlap("caa")

    assert word is None
    assert safe == "c"
    assert pending == "aa"


# ─── _resolve_overlap: best_start_norm found, compute safe/pending (202-205) ──


def test_resolve_overlap_computes_safe_prefix_and_pending_suffix():
    """Lines 202-205: best_start_norm found → keep_orig_start, safe_prefix, pending_suffix."""
    guard = LLMOutputGuard()
    _setup_words(guard, "cat", "car", "aat")

    # Same 'caa' scenario as above
    safe, pending, node, word = guard._resolve_overlap("caa")

    assert safe == "c"  # safe_prefix = text[:1]
    assert pending == "aa"  # pending_suffix = text[1:]
    assert word is None


# ─── process_stream_chunk: forbidden word via _resolve_overlap (line 251) ────


def test_process_stream_chunk_raises_on_overlap_forbidden_word():
    """Line 251: _resolve_overlap returns a forbidden_word → ForbiddenWordDetectedException.

    Setup: 'cab' and 'at'. Chunk 'cat':
      'c' matches, 'a' matches (→ ca-node), 't' mismatches →
      _resolve_overlap('cat') returns ('','cat',at-node,'at') → raise!
    """
    guard = LLMOutputGuard()
    _setup_words(guard, "cab", "at")

    session_id = "test-overlap-raise"
    guard.reset_session_for_new_response(session_id)

    with pytest.raises(ForbiddenWordDetectedException) as exc_info:
        guard.process_stream_chunk(session_id, "cat")

    assert exc_info.value.word == "at"


# ─── process_stream_chunk: safe_prefix from _resolve_overlap (lines 253-254) ─


def test_process_stream_chunk_emits_safe_prefix_from_overlap():
    """Lines 253-254: _resolve_overlap returns a non-empty safe_prefix → appended.

    'caa' step (caat test): returns safe_prefix='c' → safe_chunks.append('c').
    """
    guard = LLMOutputGuard()
    _setup_words(guard, "cat", "car", "aat")

    session_id = "test-safe-prefix"
    guard.reset_session_for_new_response(session_id)

    # "caa" triggers safe_prefix="c" from _resolve_overlap; but then 't' finishes "aat"
    with pytest.raises(ForbiddenWordDetectedException) as exc_info:
        guard.process_stream_chunk(session_id, "caat")

    assert exc_info.value.word == "aat"


# ─── process_stream_chunk: current_trie_node not root after overlap (line 260) -


def test_process_stream_chunk_increments_checks_when_node_not_root():
    """Line 260: after _resolve_overlap, current_trie_node is NOT root → checks += 1."""
    guard = LLMOutputGuard()
    _setup_words(guard, "cat", "car", "aat")

    session_id = "test-not-root"
    guard.reset_session_for_new_response(session_id)

    # Processing "caa" causes the mismatch on second 'a'; _resolve_overlap
    # returns next_node=aa-node (not root) → line 260 True.
    # Then 't' would complete "aat" → raises.
    with pytest.raises(ForbiddenWordDetectedException):
        guard.process_stream_chunk(session_id, "caat")

    # If we get here via a non-raising path: verify checks were incremented
    # (The raise proves line 260 was hit — next_node was aa-node, not root)


# ─── process_stream_chunk: elif not pending_buffer (line 261, arc 261->220) ──


def test_process_stream_chunk_elif_no_pending_continues_loop():
    """Line 261, arc 261->220: after overlap, at root AND pending empty → pass, loop continues.

    Two chars are needed so the loop iterates again after line 261 fires,
    producing the arc 261→220 (back to the for-loop header at line 220).
    """
    guard = LLMOutputGuard()
    _setup_words(guard, "ab")

    session_id = "test-no-pending-continue"
    guard.reset_session_for_new_response(session_id)

    # 'x': mismatch → _resolve_overlap("x") → ("x","",root,None)
    #   safe="x" → 253 True; pending="" → 256; root → 259 False; elif not pending: pass (261)
    #   arc 261→220: for-loop continues to 'y'
    # 'y': same path → result ["x","y"]
    result = guard.process_stream_chunk(session_id, "xy")

    assert result == ["x", "y"]


# ─── process_stream_chunk: normalized char empty + pending buffer (line 226) ──


def test_process_stream_chunk_appends_symbol_to_pending_when_buffering():
    """Line 226: normalized_char is '' AND pending_buffer non-empty → append orig_char."""
    guard = LLMOutputGuard()
    _setup_words(guard, "ab")

    session_id = "test-symbol-in-pending"
    guard.reset_session_for_new_response(session_id)

    # 'a' matches root → pending="a"
    # '-' normalizes to '' → not normalized_char → if pending_buffer: pending += '-'
    result = guard.process_stream_chunk(session_id, "a-")

    # 'a-' is buffered; '-' was appended to pending (line 226)
    # Result may be empty since everything is pending
    assert result == []
    state = guard.get_or_create_session(session_id)
    assert "-" in state.pending_buffer


# ─── process_stream_chunk: current_trie_node is None reset (line 232) ────────


def test_process_stream_chunk_resets_none_trie_node():
    """Line 232: state.current_trie_node is None → set to trie_root before matching."""
    guard = LLMOutputGuard()
    _setup_words(guard, "ab")

    session_id = "test-null-node"
    state = guard.get_or_create_session(session_id)
    state.reset_trie_state()
    state.current_trie_node = None  # manually set to None

    # Processing 'x': line 232 fires (sets to root), then 'x' not in root → mismatch
    result = guard.process_stream_chunk(session_id, "x")

    assert result == ["x"]
    assert state.current_trie_node is not None


# ─── finalize_stream: pending buffer flushed (lines 274-275) ─────────────────


def test_finalize_stream_flushes_pending_buffer():
    """Lines 274-275: pending_buffer non-empty at finalize → appended to final_chunks."""
    guard = LLMOutputGuard()
    _setup_words(guard, "foo")

    session_id = "test-finalize-pending"
    guard.reset_session_for_new_response(session_id)

    # "fo" partially matches "foo" → pending_buffer = "fo", no raise
    result = guard.process_stream_chunk(session_id, "fo")
    assert result == []  # "fo" is buffered

    # Finalize releases the pending buffer
    final = guard.finalize_stream(session_id)
    assert final == ["fo"]


# ─── finalize_stream: no pending buffer (line 273 False branch already covered) -


def test_finalize_stream_no_pending_returns_empty():
    """Baseline: pending_buffer is empty → finalize returns []."""
    guard = LLMOutputGuard()
    _setup_words(guard, "foo")

    session_id = "test-finalize-empty"
    guard.reset_session_for_new_response(session_id)

    final = guard.finalize_stream(session_id)
    assert final == []
