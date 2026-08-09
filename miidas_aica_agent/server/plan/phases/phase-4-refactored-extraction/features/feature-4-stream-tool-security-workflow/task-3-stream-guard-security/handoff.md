# 引き継ぎ: task-3-stream-guard-security

## 概要

`StreamGuard` を新規作成し、`StreamEventProcessor` の `raw_response_event` ブランチを `StreamGuard` 経由の
セキュリティ検査に切り替えた。`chat_service_refactored.py` は ターンごとに `StreamGuard` を生成して
`stream_event_processor.process()` に渡す。セキュリティ検知時は `_handle_security_detection` が
`ChatPersistence.block_session()` を呼び ERROR レスポンスを返す。`PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security` 33 passed。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat/stream_guard.py` | 新規作成。`StreamGuard` クラス。LLMOutputGuard への委譲、process_chunk/finalize/cleanup/reset インターフェース |
| `server/src/aica_agent/services/chat/chat_persistence.py` | `is_session_created()` と `block_session()` メソッドを追加 |
| `server/src/aica_agent/services/chat/stream_event_processor.py` | `process()` に `stream_guard: StreamGuard | None = None` パラメータを追加。`raw_response_event` ブランチを StreamGuard 経由に変更 |
| `server/src/aica_agent/services/chat_service_refactored.py` | ターンごとに `StreamGuard` を生成して `stream_event_processor.process()` に渡す。`finalize()` と `cleanup()` を呼ぶ。`get_session_id` import 追加 |
| `server/tests/integration/chat_service_contract/conftest.py` | `chat_service_container_security` フィクスチャを追加（real-refactored サポート） |
| `server/tests/integration/chat_service_contract/test_security_cleanup.py` | `real-refactored` variant の skip を除去。`chat_service_container_security` フィクスチャに切り替え。`_setup_runner_mock` ヘルパー追加 |
| `server/tests/unit/services/chat/test_stream_guard.py` | 新規作成。StreamGuard の unit tests（100% branch coverage、20 tests） |
| `server/tests/integration/chat_service_contract/test_refactored_bootstrap_shell.py` | passthrough guard mock を追加（StreamGuard 導入前のテスト期待値を維持） |
| `server/tests/unit/services/test_chat_service_refactored.py` | passthrough guard mock を追加（StreamGuard 導入前のテスト期待値を維持） |

## 新しいAPI / ヘルパー / フィクスチャ

### `StreamGuard`（`services/chat/stream_guard.py`）

```python
class StreamGuard:
    def __init__(self, llm_output_guard, chat_persistence, session_id: str): ...
    def reset(self) -> None: ...
    async def process_chunk(item_id, delta, chat_response, session_status) -> AsyncGenerator: ...
    async def finalize(chat_response, session_status) -> AsyncGenerator: ...
    def cleanup(self) -> None: ...
```

### `ChatPersistence` 追加メソッド

```python
def is_session_created(self) -> bool: ...
def block_session(self) -> None: ...
```

### テストフィクスチャ

- `chat_service_container_security`: セキュリティテスト専用の 3-variant フィクスチャ（legacy / delegating-refactored / real-refactored）
- `_setup_runner_mock(variant, chat_svc, svc, events_sdk, events_normalized)`: variant に応じてランナーモックを設定するヘルパー

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| `finalize()` を `StreamEventProcessor` の外側（`chat_service_refactored.py`）で呼ぶ | `StreamEventProcessor.process()` の `finally` ブロックでは `yield` が `return` 後に使えないため | `finally` 内で finalize を呼ぶ設計（Python の制約で不可） |
| `StreamGuard` をターンごとに fresh 生成する | `llm_output_guard` がテストで差し替えられる可能性があるため毎ターン legacy から取得する | インスタンス生成時に固定する（テスト差し替えに対応できない） |
| `session_id` を `StreamGuard` 生成時に `get_session_id()` で固定する | GeneratorExit 時に ContextVar が変更済みでも正しい ID でクリーンアップできる | ContextVar をそのまま使う（キャンセル時に誤った ID でクリーンアップされる可能性） |
| `_last_item_id` を `StreamGuard` 内で管理する | `finalize()` 時に保留バッファの item_id が必要だが caller から渡すのは煩雑 | `StreamEventProcessor` 側で current_item_id を追跡して finalize に渡す |
| セキュリティ検知後の `finalize()` は skip する（`stream_guard.security_detected` で判定） | process_chunk 内で cleanup 済みのため二重 finalize 不要 | 常に finalize を呼ぶ（再作成された空セッションを cleanup する必要が生じる） |

## 互換性メモ

- `StreamEventProcessor.process()` の `stream_guard` パラメータはデフォルト `None` のため、既存の呼び出し元への影響なし
- `ChatPersistence` に追加した `is_session_created()` / `block_session()` は pure addition（既存 API に変更なし）
- `delegating-refactored` variant は legacy の `chat()` に委譲するため、legacy の security 動作を継続する（変更なし）

## 次タスクへのフォローアップ

- task-4 (WorkflowChatHandler): `test_workflow_side_effects.py` の `real-refactored` 9 variants がまだ skipped。task-4 完了後に `chat_service_container_security` 相当のフィクスチャで unlock する予定
- `finalize()` の `_finalize_security_stopped` フラグ: 現在の実装では finalize 中のセキュリティ検知後も END response が出ないようにしているが、finalize 後の token usage 記録もスキップされる。この挙動は legacy と一致している

## 未解決の質問

- なし

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
