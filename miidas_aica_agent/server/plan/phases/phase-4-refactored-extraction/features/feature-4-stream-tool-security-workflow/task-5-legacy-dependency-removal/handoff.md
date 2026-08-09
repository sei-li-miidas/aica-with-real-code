# 引き継ぎ: task-5-legacy-dependency-removal

## 概要

`chat_service_refactored.py` から `LegacyChatService` の import / instantiation / delegation をすべて除去した。
`init_session()` と `summarize_position_detail_chat()` は legacy に委譲せず、ネイティブ実装を持つ。
`chat()` は task-4 以降すでに legacy を呼ばず、この task ではその不変条件を維持した。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat_service_refactored.py` | `LegacyChatService` import 削除、`from services.chat_service import ...` 削除、`_legacy_chat_service` 属性削除、`init_session()` をネイティブ実装 (legacy 行 218-304 を移植)、`summarize_position_detail_chat()` をネイティブ実装 (legacy 行 1179-1265 を移植)、`_json_default` / `DEFAULT_ERROR_MESSAGE` / `POSITION_CHAT_DETAIL_MESSAGE_ID_PREFIX` をローカル定義、`LLMOutputGuard()` を直接インスタンス化、`WorkflowChatHandler` の `get_provider` を `lambda: self._conv_state.model_name` に変更、`ToolEventHandler` が `self._position_repository` / `self._rate_limit_service` / `self._workflow_service` を直接参照、property alias 群 (`_active_agent_name`, `_session_created`, `_should_save`, `_conversation`, `_chat_histories`, `_position_id`, `_previous_response_ids`, `_provider`) 追加、後方互換メソッド群 (`_process_jobtype_search_result`, `_serialize_tool_output_for_storage`, `_parse_tool_output`, `_handle_security_detection`) 追加、`HistoryMapper.process_jobtype_search_result` にクロージャを設定してパッチ可能性を確保 |
| `server/tests/unit/services/test_chat_service_refactored.py` | 全テストを `_legacy_chat_service` 参照なしに書き換え。`test_init_session_has_no_legacy_chat_service`、`test_init_session_populates_conv_state`、`test_summarize_position_detail_chat_is_native_no_legacy` を追加。`test_chat_service_refactored_has_no_legacy_import` で `LegacyChatService` / `_legacy_chat_service` 非存在を静的に検証 |
| `server/tests/integration/chat_service_contract/test_summary_rollback.py` | `_exercise_summary_behavior()` 内で `services.chat_service_refactored.decrypt` / `services.chat_service_refactored.datetime` を追加 patch |

## 新しいAPI / ヘルパー / フィクスチャ

- `ChatService._extract_position_search_tool_name(tool_calls)`: position search ツールコール名を取得する補助メソッド。
- `ChatService._extract_selected_jobtypes(tool_calls)`: selected jobtypes を取得する補助メソッド。
- `ChatService._find_last_non_position_guide_agent(histories)`: 最後の非 POSITION_GUIDE エージェントを探す補助メソッド。
- `ChatService._create_position_agent_if_not_exist(position_id, histories)`: `init_session()` での position agent 初期化ヘルパー。
- property alias 群: `_conv_state` プロパティを代理し、contract tests の `_inner()` ヘルパーとの互換性を維持する。
- `HistoryMapper.process_jobtype_search_result` クロージャ: `_process_jobtype_search_result` の `patch.object` パッチが実行時に反映されるようにする遅延バインディング。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| `_legacy_chat_service` を完全削除 | task-5 の完了条件が「import / instantiate / delegate しない」であるため、属性として残すことは条件を満たさない | attribute を None に変更する案は検討したが条件違反 |
| property alias 群を `_conv_state` に代理させる | contract tests が `_inner(svc)._conversation` などを直接参照するため、インターフェース変更なしに内部構造を変更できる | alias なしの場合は contract tests を大量修正する必要がある |
| `HistoryMapper.process_jobtype_search_result` にクロージャを設定 | `_history_mapper` への binding が `__init__` 時に固定されると `patch.object(svc, "_process_jobtype_search_result", ...)` が mapper 内のコールに反映されない | 毎呼び出し時に `self._process_jobtype_search_result` 経由で参照させる代替案は `HistoryMapper` 側の変更が必要で change-minimal 原則に反する |
| `LLMOutputGuard()` を直接インスタンス化 | legacy への依存なしに guard を保持する必要がある。テストでは `chat_svc.llm_output_guard = passthrough_guard` で上書き可能 | legacy から alias を取る案は legacy 削除後に再作業が必要になる |

## 互換性メモ

- `_inner()` helper は `getattr(chat_svc, "_legacy_chat_service", chat_svc)` を返すが、`_legacy_chat_service` が存在しないため `chat_svc` 自体が返される。property alias 群によりアクセスが継続する。
- `rollback_di` の `test_refactored_adapter_forwards_workflow_request_types` は task-5 着手前から失敗しており、pre-existing failure として扱う。

## 次タスクへのフォローアップ

- `gate_a_scenario_matrix.md` の `summary rollback` 行の `real-refactored evidence` を `pass` に更新済み。
- Phase 5 での `_conv_state` プロパティ群の整理時に、property alias を削除してコードを簡素化できる。

## 未解決の質問

なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
