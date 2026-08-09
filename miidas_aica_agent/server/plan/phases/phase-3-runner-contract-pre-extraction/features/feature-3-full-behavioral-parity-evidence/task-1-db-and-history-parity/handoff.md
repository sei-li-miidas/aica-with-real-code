# 引き継ぎ: task-1-db-and-history-parity

## 概要

変更内容と、次のタスクが前提にしてよい内容を記載する。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/tests/integration/chat_service_contract/conftest.py` | `SimpleNamespace` スタブを `Mock(spec=ChatRepository)` / `MagicMock()` に置き換え。`container.chat_repository.override(providers.Object(mock))` パターンを導入。 |
| `server/tests/integration/chat_service_contract/test_history_mapping.py` | fixture-schema-only テストを完全な behavioral テスト 3 本に置き換え。USER/ASSISTANT/TOOL DB history → SDK input shape の mapping、および load_previous_chat_histories() のペイロード shape を runtime で検証する。 |
| `server/tests/integration/chat_service_contract/test_db_side_effects.py` | fixture-schema-only テストを完全な behavioral テスト 6 本に置き換え。session 作成、history save（USER/DEVELOPER/ASSISTANT）、tool output update、retry error save の DB write を runtime で検証する。 |
| `server/plan/phases/gate_a_scenario_matrix.md` | `history mapping` と `DB side effects` の `legacy evidence` を `fixture-schema only` → `pass` に更新。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `_inner(chat_svc)`: `getattr(chat_svc, "_legacy_chat_service", chat_svc)` — delegating adapter のラッパーを透過して private attrs にアクセスするためのヘルパー。各テストファイル内に定義。
- `_EmptyRunResult` (`test_history_mapping.py`): `_run_streamed` シームをスタブするための async generator クラス。events は何も yield しない。
- `_FakeRunResult(events)` (`test_db_side_effects.py`): 指定イベントリストを replay する async generator クラス。`MessageOutputItem`、`ToolCallItem`、`ToolCallOutputItem` 実インスタンスを包む run_item_stream_event をサポート。
- `_make_run_item_event(item)` (`test_db_side_effects.py`): `SimpleNamespace(type="run_item_stream_event", item=item)` ファクトリー。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| `_run_streamed` シームへのアクセスに `_inner()` を導入 | `chat_service_refactored.ChatService` は legacy svc を `_legacy_chat_service` 属性にラップする。`_run_streamed` シームは内側にある | 外側ラッパーの method をオーバーライド (不要な複雑性) |
| `asyncio.sleep` を `AsyncMock` でパッチ | retry ループは `MAX_LLM_RETRY_COUNT=5` 回、最大 8s の exponential backoff で `asyncio.sleep` を呼ぶ | 実際の sleep (テスト 40s 超) |
| `ToolCallOutputItem(agent, raw_item, output)` のコンストラクタ引数 | openai-agents SDK `ToolCallOutputItem` は positional 引数として `(agent, raw_item, output)` を取る | kwargs 指定 (不可) |

## 互換性メモ

- `delegating-refactored` variant は `init_session()` と `chat()` を外側 wrapper で呼び、private attrs を `_inner()` 経由でアクセスする。内部実装が移動した場合は `_legacy_chat_service` のネーミングを見直す必要がある。
- `real-refactored` variant は現在 `pytest.mark.skip` 。Phase 4 bootstrap 後に実装する。

## カバレッジ状況

コマンド: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing`

| 計測対象 | Stmts | Miss | Branch | BrPart | Coverage |
| --- | --- | --- | --- | --- | --- |
| このタスクのテストのみ | 779 | 450 | 346 | 63 | 38% |
| `pre_extraction_parity` スイート全体 | 779 | 450 | 346 | 63 | 38% |

task-1 で新たにカバーされた主要パス（ベースライン計測）:
- `init_session()` 正常パス（既存セッション再開・新規セッション両方）
- `chat()` 2 ターン目の session 作成・ USER/DEVELOPER ヒストリ保存パス
- `_save_user_or_developer_message` → `_save_chat_histories` → `add_chat_histories` パス
- `_convert_to_llm_messages` の USER/ASSISTANT/TOOL ロール変換パス
- `chat()` の retry ループ（全試行失敗 → DEVELOPER エラー保存）
- `load_previous_chat_histories()` の USER/ASSISTANT 単純パス

未カバーのパス（意図的スコープ外）:
- `__init__`、エージェントクローン補助ヘルパー（L62–250）
- `chat()` 内のポジション詳細・ワークフロー分岐、エラー早期 return（L365–494）
- ストリーミングイベントハンドラ（tool-call 処理、session ブロックガード）（L661–988）
- `_prepare_for_chat_turn` ポジション詳細分岐、`_get_position_detail`（L1125–1266）
- `_convert_to_llm_messages` ツール出力エッジケース（ポジション検索 fake 等）（L1291–1557）
- `load_previous_chat_histories` ツール・ポジション検索分岐（L1686–1973）
- `_extract_selected_jobtypes`、`_generate_position_search_fake_result` 等（L2026–2370）

`chat_service.py` branch coverage: task-1 完了時点で 38%。残りは task-2〜5 がカバーする。

## 次タスクへのフォローアップ

- Phase 4 完了後、`real-refactored` variant の skip を解除して全 3 variant を通す。
- `test_history_mapping_tool_call_to_sdk_function_call` の fixture JSON に `arguments` と `output` の期待値を追記することを検討する。

## 未解決の質問

- なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
