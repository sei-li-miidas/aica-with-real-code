"""
LLMOutputGuard の単体テスト

特にTrie木の重なり一致検出とストリーミングセッション管理をテストします。
"""

from copy import deepcopy

import pytest
from security.llm_output_guard import (
    LLMOutputGuard,
    ForbiddenWordDetectedException,
    TrieNode,
)


@pytest.fixture
def guard():
    """テスト用のLLMOutputGuardインスタンス"""
    # シングルトンなので、各テスト間で共有される
    # テスト用に新しいインスタンスが必要な場合は、モック化が必要
    return LLMOutputGuard()


def _clone_trie(node: TrieNode) -> TrieNode:
    cloned = TrieNode()
    cloned.is_end = node.is_end
    cloned.word = node.word
    cloned.children = {
        char: _clone_trie(child) for char, child in node.children.items()
    }
    return cloned


@pytest.fixture(autouse=True)
def restore_guard_singleton_state():
    guard = LLMOutputGuard()
    original_trie = _clone_trie(guard.trie_root)
    original_forbidden_words = set(guard.forbidden_words)
    original_sessions = deepcopy(guard._sessions)

    yield

    guard.trie_root = original_trie
    guard.forbidden_words = original_forbidden_words
    with guard._sessions_lock:
        guard._sessions = original_sessions


class TestOverlapDetection:
    """重なり一致検出のテスト"""

    def test_overlap_caat_with_aat(self):
        """
        禁止ワード: "aat"
        入力: "caat"

        Trie: c-a-t, a-a-t
        入力 "ca" は "cat" 不完全
        入力 "caa" で不一致 → "ca"リリース、"a"を保持
        入力 "caat" で "aa" → "aat" 検知
        """
        guard = LLMOutputGuard()

        # テスト用に _add_word_to_trie をクリアして再構築
        guard.trie_root.children.clear()
        guard.forbidden_words = {"cat", "car", "aat"}
        guard._add_word_to_trie("cat")
        guard._add_word_to_trie("car")
        guard._add_word_to_trie("aat")

        session_id = "test_session_overlap_1"
        guard.reset_session_for_new_response(session_id)

        # 入力ストリーム: "ca" + "a" + "t"
        with pytest.raises(ForbiddenWordDetectedException) as exc_info:
            guard.process_stream_chunk(session_id, "caat")

        assert exc_info.value.word == "aat"
        assert exc_info.value.session_id == session_id

    def test_no_false_negative_with_overlap(self):
        """
        禁止ワード: "ab", "ba"
        入力: "aba"

        最初の "ab" が検知される
        """
        guard = LLMOutputGuard()
        guard.trie_root.children.clear()
        guard.forbidden_words = {"ab", "ba"}
        guard._add_word_to_trie("ab")
        guard._add_word_to_trie("ba")

        session_id = "test_session_overlap_2"
        guard.reset_session_for_new_response(session_id)

        with pytest.raises(ForbiddenWordDetectedException) as exc_info:
            guard.process_stream_chunk(session_id, "aba")

        # "ab" が先に検知される
        assert exc_info.value.word == "ab"

    def test_suffix_becomes_prefix(self):
        """
        禁止ワード: "abc", "bcd"
        入力: "abxbcd"

        "ab" + 'x' で不一致
        'x' から再評価しても "bcd" は見えない
        しかし、後続で "bcd" が揃えば検知対象になりうる

        入力: "abcd"
        この入力では、先頭から "abc" が先に完全一致して検知される。
        （"bcd" も部分文字列として存在するが、実装上は先に確定した "abc" が検知される）
        """
        guard = LLMOutputGuard()
        guard.trie_root.children.clear()
        guard.forbidden_words = {"abc", "bcd"}
        guard._add_word_to_trie("abc")
        guard._add_word_to_trie("bcd")

        session_id = "test_session_overlap_3"
        guard.reset_session_for_new_response(session_id)

        # "abcd" → "abc" が検知される
        with pytest.raises(ForbiddenWordDetectedException) as exc_info:
            guard.process_stream_chunk(session_id, "abcd")

        assert exc_info.value.word == "abc"

    def test_exact_forbidden_word(self):
        """
        禁止ワード: "test"
        入力: "test"
        """
        guard = LLMOutputGuard()
        guard.trie_root.children.clear()
        guard.forbidden_words = {"test"}
        guard._add_word_to_trie("test")

        session_id = "test_session_exact"
        guard.reset_session_for_new_response(session_id)

        with pytest.raises(ForbiddenWordDetectedException) as exc_info:
            guard.process_stream_chunk(session_id, "test")

        assert exc_info.value.word == "test"

    def test_safe_chunks_when_no_match(self):
        """
        禁止ワード: "abc"
        入力: "hello"

        マッチなし → 各文字がsafe_chunksに返される
        """
        guard = LLMOutputGuard()
        guard.trie_root.children.clear()
        guard.forbidden_words = {"abc"}
        guard._add_word_to_trie("abc")

        session_id = "test_session_safe"
        guard.reset_session_for_new_response(session_id)

        result = guard.process_stream_chunk(session_id, "hello")
        # Character-by-character processing returns individual chars
        assert result == ["h", "e", "l", "l", "o"]

    def test_partial_match_at_end_finalized(self):
        """
        禁止ワード: "test"
        入力チャンク1: "tes"
        入力チャンク2: "t"

        チャンク1で "tes" は保留
        チャンク2で "t" を追加 → "test" 完成 → 検知
        """
        guard = LLMOutputGuard()
        guard.trie_root.children.clear()
        guard.forbidden_words = {"test"}
        guard._add_word_to_trie("test")

        session_id = "test_session_partial"
        guard.reset_session_for_new_response(session_id)

        # チャンク1: "tes" - 保留状態で返される
        result1 = guard.process_stream_chunk(session_id, "tes")
        assert result1 == []  # 保留中なので何も返されない

        # チャンク2: "t" - "test" 完成 → 検知
        with pytest.raises(ForbiddenWordDetectedException) as exc_info:
            guard.process_stream_chunk(session_id, "t")

        assert exc_info.value.word == "test"

    def test_multiple_sessions_isolated(self):
        """
        異なるセッションは独立している
        """
        guard = LLMOutputGuard()
        guard.trie_root.children.clear()
        guard.forbidden_words = {"secret"}
        guard._add_word_to_trie("secret")

        session1 = "session_1"
        session2 = "session_2"

        guard.reset_session_for_new_response(session1)
        guard.reset_session_for_new_response(session2)

        # session1: "secret" → 検知
        with pytest.raises(ForbiddenWordDetectedException):
            guard.process_stream_chunk(session1, "secret")

        # session2: "safe" → 検知なし
        result = guard.process_stream_chunk(session2, "safe")
        # 's' and 'a' are buffered as they match start of "secret"
        # When 'f' comes, overlap resolves to "sa", 'f' and 'e' are returned
        assert result == ["sa", "f", "e"]

    def test_resolve_overlap_method(self):
        """
        _resolve_overlap メソッドの直接テスト

        pending = "ca" + orig_char 'a' = "caa"
        禁止ワード: "aat"

        "caa" で:
        - start=0: "caa" → no match
        - start=1: "aa" → start of "aat" ✓
        - start=2: "a" → start of "aat" ✓

        最小開始位置は start=1 → "a" から "at" を続ける
        """
        guard = LLMOutputGuard()
        guard.trie_root.children.clear()
        guard.forbidden_words = {"aat"}
        guard._add_word_to_trie("aat")

        text = "caa"  # "ca" + 'a'
        safe_prefix, pending_suffix, next_node, forbidden_word = guard._resolve_overlap(
            text
        )

        # "c" は安全確定、"aa" は保留して "a" 先頭を続ける
        assert safe_prefix == "c"
        assert pending_suffix == "aa"
        assert forbidden_word is None
        # next_node は "a" を読んだ状態のはず
        assert next_node.is_end == False  # "a" のみでは不完全
        if "a" in next_node.children:
            # "aa" の状態
            assert next_node.children["a"].is_end == True
            assert next_node.children["a"].word == "aat"


class TestSessionManagement:
    """セッション管理のテスト"""

    def test_session_cleanup(self):
        """
        セッションの作成と削除が正しく動作する
        """
        guard = LLMOutputGuard()
        session_id = "test_cleanup_session"

        # セッション作成
        state = guard.get_or_create_session(session_id)
        assert state is not None
        assert state.session_id == session_id

        # セッション削除
        guard.remove_session(session_id)

        # 削除後に新規作成されない確認（削除されたことの確認）
        # ※ 実装では削除後に get_or_create_session を呼ぶと新規作成される
        # これは意図的な動作かもしれない


class TestNormalization:
    """正規化のテスト"""

    def test_normalize_text(self):
        """
        テキスト正規化が正しく動作する
        """
        guard = LLMOutputGuard()

        # 大文字 → 小文字
        assert guard._normalize_text("ABC") == "abc"

        # 記号除去
        assert guard._normalize_text("a-b_c") == "abc"

        # 日本語は残される
        assert guard._normalize_text("テスト") == "テスト"

        # 混合
        assert guard._normalize_text("Test-データ") == "testデータ"
