# 引き継ぎ: task-1-stream-event-processor

## 概要

`StreamEventProcessor` を `server/src/aica_agent/services/chat/stream_event_processor.py` に新規作成した。
`chat_service_refactored.py` の stream event ループを `StreamEventProcessor.process()` へ移し、
`ChatService.chat()` はその結果を `async for` で受け取るだけになった。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat/stream_event_processor.py` | 新規作成。StreamEventProcessor クラス。 |
| `server/src/aica_agent/services/chat_service_refactored.py` | StreamEventProcessor をインポートし、__init__ で生成・注入。chat() のインライン stream ループを processor.process() に置換。_update_continuation_state / _update_active_agent / _append_stop_at_tool_outputs_callback の 3 コールバックメソッドを追加。 |
| `server/tests/unit/services/chat/test_stream_event_processor.py` | 新規作成。25 テスト、branch coverage 100%。 |
| `server/tests/unit/services/test_chat_service_refactored.py` | `_FakeRunStream.tool_replay_items` の初期化を `tool_replay_items or []` → `[] if tool_replay_items is None else list(tool_replay_items)` に変更（明示的 None チェックに統一）。 |

## 新しいAPI / ヘルパー / フィクスチャ

### StreamEventProcessor

```python
class StreamEventProcessor:
    def __init__(
        self,
        chat_persistence: ChatPersistence,
        is_stop_at_tool: Callable[[Any], bool],
        append_stop_at_tool_outputs: Callable[[list[dict[str, Any]], bool], None],
        update_active_agent: Callable[[str], None],
        update_continuation_state: Callable[[Any], None],
    ) -> None: ...

    async def process(
        self,
        run_stream: LLMRunStream,
        chat_response: ChatStreamResponse,
        session_status: ChatSessionStatus,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]: ...
```

`process()` は `LLMRunStream.stream_events()` を反復し、`raw_response_event` は yield、
`run_item_stream_event` は `ChatPersistence.save_chat_history()` + `is_stop_at_tool` へ dispatch する。
`finally` で `continuation_state` / `agent_state` 収集・コールバック呼び出し・`aclose()` を実行する。

### ChatService に追加したコールバックメソッド

| メソッド | シグネチャ | 概要 |
| --- | --- | --- |
| `_update_continuation_state` | `(state: object) -> None` | `_conv_state.previous_response_ids[chat_key] = state` |
| `_update_active_agent` | `(agent_name: str) -> None` | `_conv_state.active_agent_name` 更新 + `legacy._active_agent_name` 同期 |
| `_append_stop_at_tool_outputs_callback` | `(tool_replay_items, stop_at_tool_exists) -> None` | 既存 `_append_stop_at_tool_outputs(legacy, ...)` を呼ぶラッパー |

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| コールバックでインライン実装を呼ぶ | task-2 (ToolEventHandler) / task-3 (StreamGuard) はまだ抽出しないため、stream ループ本体だけを分離する最小変更で parity を維持する。 | `ChatService` の `self` を processor に渡す: 依存が広くなるため却下。 |
| `_stream_event_processor` を `__init__` で生成 | コールバックはバウンドメソッドなので、インスタンスごとに正しく機能する。per-turn 生成は不要。 | per-turn で毎回生成: 余分なオブジェクト生成になるため却下。 |
| `run_stream = None` を維持 | `run_stream.usage` を後続 try ブロックで参照するため、変数スコープを保持する。 | — |

## 互換性メモ

- `pre_extraction_parity` は 173 passed を維持（ベースラインと同一）。
- `rollback_runner` は 29 passed を維持（ベースラインと同一）。
- `StreamEventProcessor.process()` は `aclose()` の責任を内部 finally で持つため、呼び出し元 (`chat()`) は `run_stream.aclose()` を二重呼び出ししない。
- `gate_a_scenario_matrix.md` の `real-refactored evidence` はこの task では更新しない（task-2 / task-3 / task-4 scope のまま `pending-phase-4`）。
- `continuation_state` の存在チェックを truthiness (`if run_stream.continuation_state`) から `is not None` に変更した。`ResponsesAgentRunner` は `last_response_id`（文字列）を `continuation_state` に map するため、空文字列が有効な値になりうる。falsy な非 None 値を誤って skip しないようにするための意味的修正。

## 次タスクへのフォローアップ

- task-2-tool-event-handler: `ChatPersistence.save_chat_history()` 呼び出しと `is_stop_at_tool` コールバックを `ToolEventHandler` に移す。`StreamEventProcessor` は `ToolEventHandler` を受け取る形に変更する。
- task-3-stream-guard-security: `raw_response_event` を `StreamGuard` に渡す処理を分離する。
- `_append_stop_at_tool_outputs` と `_append_stop_at_tool_outputs_callback` の二重構造は、task-2 完了後に整理できる。

## 未解決の質問

なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
