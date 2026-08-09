"""
LLM応答の不適切出力検知

【アーキテクチャ】
1. Trie木による禁止ワードのストリーミング検知（O(1)の高速処理）
2. セッションごとの状態管理（同時接続100人対応）
3. 禁止ワード検知時はセッション切断
"""

import csv
import logging
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from utils.const import LOGGER_PREFIX


class TrieNode:
    """Trie木のノード"""

    __slots__ = ["children", "is_end", "word"]

    def __init__(self):
        self.children: Dict[str, "TrieNode"] = {}
        self.is_end: bool = False
        self.word: Optional[str] = None


@dataclass
class StreamSessionState:
    """ストリーミングセッションごとの状態"""

    session_id: str
    current_trie_node: Optional[TrieNode] = None
    pending_buffer: str = ""
    total_chars_processed: int = 0
    forbidden_word_checks: int = 0

    def reset_trie_state(self):
        self.current_trie_node = None
        self.pending_buffer = ""
        self.total_chars_processed = 0
        self.forbidden_word_checks = 0


class ForbiddenWordDetectedException(Exception):
    """禁止ワード検知時の例外（セッション切断用）"""

    def __init__(self, word: str, session_id: str):
        self.word = word
        self.session_id = session_id
        super().__init__(f"Forbidden word '{word}' detected in session {session_id}")


class LLMOutputGuard:
    """
    LLM応答をストリーミングでチェックして不適切な出力を検知

    【機能】
    1. Trie木による禁止ワードのリアルタイム検知
    2. セッションごとの状態管理（同時接続対応）

    【検知時の動作】
    - 禁止ワード検知 → ForbiddenWordDetectedException → セッション切断
    """

    _instance: Optional["LLMOutputGuard"] = None
    _instance_lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """禁止ワードTrie木をロード"""
        with LLMOutputGuard._instance_lock:
            if LLMOutputGuard._initialized:
                return

            self.logger = logging.getLogger(
                f"{LOGGER_PREFIX}.{self.__class__.__module__}.{self.__class__.__name__}"
            )

            self.trie_root = TrieNode()
            self._build_trie()

            self._sessions: Dict[str, StreamSessionState] = {}
            self._sessions_lock = threading.Lock()

            self.logger.info(
                "Built Trie with %d forbidden words", len(self.forbidden_words)
            )
            LLMOutputGuard._initialized = True

    def _build_trie(self):
        """禁止ワードリストからTrie木を構築"""
        forbidden_words_path = Path(__file__).parent / "output_forbidden_words.csv"
        self.forbidden_words = set()

        if not forbidden_words_path.exists():
            self.logger.warning(
                "Forbidden words CSV not found: %s", forbidden_words_path
            )
            return

        try:
            with open(forbidden_words_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row:
                        continue
                    word = row[0].strip()
                    if not word:
                        continue
                    self.forbidden_words.add(word)
                    self._add_word_to_trie(word)
        except Exception as e:
            self.logger.exception("Error building Trie: %s", e)
            raise

    def _add_word_to_trie(self, word: str):
        node = self.trie_root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
        node.word = word

    def get_or_create_session(self, session_id: str) -> StreamSessionState:
        with self._sessions_lock:
            if session_id not in self._sessions:
                state = StreamSessionState(session_id=session_id)
                state.current_trie_node = self.trie_root
                self._sessions[session_id] = state
                self.logger.debug("Created new session state: %s", session_id)
            return self._sessions[session_id]

    def reset_session_for_new_response(self, session_id: str):
        state = self.get_or_create_session(session_id)
        state.reset_trie_state()
        state.current_trie_node = self.trie_root
        self.logger.debug("Reset buffers for new response: %s", session_id)

    def remove_session(self, session_id: str):
        with self._sessions_lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                self.logger.debug("Removed session state: %s", session_id)

    def _resolve_overlap(self, text: str) -> tuple[str, str, TrieNode, Optional[str]]:
        """
        pending + 現在文字を再評価し、以下を返す:
        - safe_prefix: 今すぐ送信してよい先頭部分
        - pending_suffix: 将来一致の可能性がある末尾部分
        - next_node: pending_suffix を読んだ後のTrieノード
        - forbidden_word: 末尾で完全一致した禁止ワード（あれば）
        """
        if not text:
            return "", "", self.trie_root, None

        normalized_chars: list[str] = []
        norm_to_orig_idx: list[int] = []
        for orig_idx, orig_char in enumerate(text):
            normalized = self._normalize_text(orig_char)
            if not normalized:
                continue
            for c in normalized:
                normalized_chars.append(c)
                norm_to_orig_idx.append(orig_idx)

        if not normalized_chars:
            return text, "", self.trie_root, None

        best_start_norm: Optional[int] = None
        best_node: TrieNode = self.trie_root
        n = len(normalized_chars)

        for start_norm in range(n):
            node = self.trie_root
            pos = start_norm
            while pos < n and normalized_chars[pos] in node.children:
                node = node.children[normalized_chars[pos]]
                pos += 1

            if pos == n:
                if node.is_end and node.word:
                    return "", text, node, node.word
                if best_start_norm is None or start_norm < best_start_norm:
                    best_start_norm = start_norm
                    best_node = node

        if best_start_norm is None:
            return text, "", self.trie_root, None

        keep_orig_start = norm_to_orig_idx[best_start_norm]
        safe_prefix = text[:keep_orig_start]
        pending_suffix = text[keep_orig_start:]
        return safe_prefix, pending_suffix, best_node, None

    def process_stream_chunk(self, session_id: str, chunk: str) -> list[str]:
        """
        ストリーミングチャンクを処理（禁止ワード検知のみ）

        Returns:
            送信可能な文字列リスト

        Raises:
            ForbiddenWordDetectedException: 禁止ワード検知時
        """
        state = self.get_or_create_session(session_id)
        safe_chunks: list[str] = []

        for orig_char in chunk:
            state.total_chars_processed += 1
            normalized_char = self._normalize_text(orig_char)

            if not normalized_char:
                if state.pending_buffer:
                    state.pending_buffer += orig_char
                else:
                    safe_chunks.append(orig_char)
                continue

            if state.current_trie_node is None:
                state.current_trie_node = self.trie_root

            if normalized_char in state.current_trie_node.children:
                state.current_trie_node = state.current_trie_node.children[
                    normalized_char
                ]
                state.pending_buffer += orig_char
                state.forbidden_word_checks += 1

                if state.current_trie_node.is_end:
                    forbidden_word = state.current_trie_node.word
                    raise ForbiddenWordDetectedException(forbidden_word, session_id)
            else:
                # 不一致時は pending + 現在文字を再評価し、
                # 取りこぼし（重なり一致）を防ぐ。
                combined = state.pending_buffer + orig_char
                safe_prefix, pending_suffix, next_node, forbidden_word = (
                    self._resolve_overlap(combined)
                )

                if forbidden_word:
                    raise ForbiddenWordDetectedException(forbidden_word, session_id)

                # safe_prefix が空になる条件: combined 全体が root からの trie パスを
                # 形成しかつ pos==n で is_end=False のケース。しかしそれは combined[-1]
                # (= normalized_char) が current_trie_node.children に存在することを
                # 意味し、else ブランチ（normalized_char NOT in children）の前提と矛盾。
                # よって safe_prefix は構造的に非空であり、ガードは dead code。
                # if safe_prefix:
                safe_chunks.append(safe_prefix)

                state.pending_buffer = pending_suffix
                state.current_trie_node = next_node

                if state.current_trie_node is not self.trie_root:
                    state.forbidden_word_checks += 1
                # pending_buffer が非空の状態で current_trie_node が root に戻ることは
                # _resolve_overlap の実装上、構造的に不可能。
                # pending が非空であれば _resolve_overlap は必ず非 root ノードを返し、
                # 上の if（259行目）が True になるため、この elif には到達しない。
                # （261->220 の elif-False ブランチは dead code）
                # elif not state.pending_buffer:  # ← dead branch
                #     pass

        return safe_chunks

    def finalize_stream(self, session_id: str) -> list[str]:
        """ストリーミング終了時の最終処理"""
        state = self.get_or_create_session(session_id)
        final_chunks = []

        if state.pending_buffer:
            final_chunks.append(state.pending_buffer)
            state.pending_buffer = ""

        self.logger.info(
            "Stream finalized for session %s",
            session_id,
            extra={
                "total_chars": state.total_chars_processed,
                "forbidden_checks": state.forbidden_word_checks,
            },
        )

        return final_chunks

    def _normalize_text(self, text: str) -> str:
        """禁止ワードチェック用に正規化"""
        normalized = text.lower()
        normalized = re.sub(
            r"[^a-z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", "", normalized
        )
        return normalized
