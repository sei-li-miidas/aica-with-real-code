# 引き継ぎ: task-2-history-mapper

## 概要

`HistoryMapper` を `services/chat/history_mapper.py` に新規作成し、
`chat_service_refactored.ChatService` に接続した。
DB の読み書きなし・副作用なし・`ConversationState` 依存なしの純粋データ変換コンポーネント。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat/history_mapper.py` | 新規作成。`HistoryMapper` クラス、`_generate_position_search_fake_result` ヘルパー、`POSITION_SEARCH_FAKE_RESULT` 定数を含む |
| `server/src/aica_agent/services/chat_service_refactored.py` | `HistoryMapper` を `__init__` で初期化。`check_if_previous_chat_histories_exist` と `load_previous_chat_histories` を legacy 委譲から `HistoryMapper` 経由の実装へ切り替え |
| `server/tests/unit/services/chat/test_history_mapper.py` | 新規作成。`HistoryMapper` の 100% branch coverage unit tests（63 テスト） |
| `server/tests/integration/chat_service_contract/conftest.py` | `chat_service_container_history_parity` フィクスチャを追加。`real-refactored` を含む全 3 variant を解決する |
| `server/tests/integration/chat_service_contract/test_history_mapping.py` | `chat_service_container` → `chat_service_container_history_parity` に切り替え。`_EmptyRunStream` クラスを追加し、`real-refactored` variant で `LLMRunner.run_streamed` をモックするよう各テストを更新 |
| `server/tests/integration/chat_service_contract/test_previous_history_contract.py` | `_patch_decrypt` コンテキストマネージャを追加。`delegating-refactored` variant で `services.chat_service_refactored.decrypt` をパッチするよう更新 |
| `server/plan/phases/gate_a_scenario_matrix.md` | `history mapping` 行の `real-refactored evidence` を `pending-phase-4` から `pass` に更新 |

## 新しい API / ヘルパー / フィクスチャ

- `HistoryMapper.convert_to_llm_messages(histories, *, position_id, create_position_agent_callback)` — DB ChatHistory リストを LLM 会話入力形式に変換
- `HistoryMapper.parse_tool_output(output)` — ツール実行結果（JSON 文字列・dict・list など）を dict にパース
- `HistoryMapper.process_jobtype_search_result(tool_call_id, tool_call_name, tool_call_arguments, jobtypes)` — 職種検索結果をフロントエンド向け構造に変換
- `HistoryMapper.format_previous_chat_histories(histories, limit)` — DB ChatHistory をフロントエンド向けペイロードに変換
- `_generate_position_search_fake_result(count)` — モジュールレベルヘルパー。件数付きフェイク結果メッセージを生成
- `POSITION_SEARCH_FAKE_RESULT` — モジュールレベル定数。parse 失敗時の fallback メッセージ
- `chat_service_container_history_parity` fixture — `real-refactored` を含む全 3 variant で history mapping tests を実行するための専用フィクスチャ

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| `HistoryMapper` を純粋データ変換コンポーネントとして実装 | DB 読み書きなし・副作用なし・`ConversationState` 依存なし。REST history path が stateless のまま維持される | `ConversationState` に統合する案もあったが、責務分離と testability の観点で却下 |
| `ChatRepository` をモジュールトップで import | `clone_chat_history` スタティックメソッドのみを使用。循環 import は発生しないためモジュールトップの通常 import で問題なし | lazy import も検討したが不要と判断 |
| `chat_service_container_history_parity` フィクスチャを分離 | `chat_service_container` のグローバル `pytest.skip("pending-phase-4: real-refactored evidence")` を維持する必要があった。他のテスト（`test_db_side_effects.py` 等）は real-refactored で `svc._run_streamed` を使うため、グローバルに skip を除去すると失敗する | `chat_service_container` を変更して全テストで real-refactored を有効にする案は他テストの failure を引き起こすため却下 |
| `_EmptyRunStream` クラスを追加して `LLMRunner.run_streamed` をモック | real-refactored variant では `_run_streamed` ではなく `_llm_runner.run_streamed` を使う。型が異なるため専用のフェイクが必要 | `_EmptyRunResult` を再利用する案はインターフェースが合わないため却下 |
| `test_previous_history_contract.py` に `_patch_decrypt` を追加 | `load_previous_chat_histories` が legacy 委譲から `HistoryMapper` 直接呼び出しへ変わり、`decrypt` の呼び出し元が `services.chat_service_refactored` になった。既存テストは `services.chat_service.decrypt` をパッチしていたため更新が必要 | delegating-refactored / real-refactored では `services.chat_service_refactored.decrypt` をパッチするよう分岐 |

## 互換性メモ

- `chat_service.py`（legacy）は変更なし。`_bridge_state_from_legacy()` / `_sync_scalars_from_legacy()` も維持。
- `init_session()` は引き続き legacy `_convert_to_llm_messages` に委譲する（feature-3 以降で置き換え予定）。
- `HistoryMapper.convert_to_llm_messages` は今後 feature-3 で `init_session()` の legacy 委譲を置き換える際に使用する。

## 次タスクへのフォローアップ

- feature-3（persistence/turn-preparation 抽出）では `init_session()` 内の `_convert_to_llm_messages` 呼び出しを `HistoryMapper.convert_to_llm_messages` に置き換える。
- そのタイミングで `_bridge_state_from_legacy()` / `_sync_scalars_from_legacy()` ブリッジを削除できる。
- `chat_service_container` の `real-refactored` の `pytest.skip` を除去するのは、各テストが real-refactored で動作するようになった後（feature-4 以降）。

## 未解決の質問

なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
