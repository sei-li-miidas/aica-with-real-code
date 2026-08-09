# テスト移行マップ: task-3-test-migration-map

## 目的

`server/tests/unit/services/test_chat_service.py` の legacy private/public テストを、Phase 4 の component 抽出タスクへ漏れなく割り当てる。
この文書は、Phase 4 extraction task が「どの legacy テストを、どこへ移すか」を判断する source of truth とする。

## 前提

- **パス基準**: すべてのテストファイルパスは repo root からの相対パス。（cd server は不要、pytest コマンドでそのまま使用可能）
- 対象 legacy テストファイル: `server/tests/unit/services/test_chat_service.py`
  - これは legacy `ChatService` の unit tests であり、Phase 4 で component unit tests へ**移行される側**のファイル。
  - `server/tests/integration/chat_service_contract/` とは別物。contract tests は Phase 3 で作成した characterization tests であり、parity gate の verification コマンドで実行される。
- 上記ファイルの集計結果: 14 test classes / 62 tests
- Phase 3 の contract source of truth: `server/plan/phases/gate_a_scenario_matrix.md`
- `real-refactored evidence` は本タスクでは作成せず、`pending-phase-4` を維持する

## 本マップの位置づけ（重要）

本マップは **移行の最低限（floor）** を定義する。以下は本マップの対象外であり、Phase 4 owner が別途保証する必要がある:

- legacy テストでカバーされていない branch / edge case
- 新 component interface から導出される boundary テスト（interface/input-output/side-effect の列挙から導出）
- 100% に近い branch coverage の達成

**migration target が `pass` になるだけでは coverage の完全性は保証されない。**  
Phase 4 全タスクの coverage gate は `server/plan/phases/phase-4-refactored-extraction/README.md` の Coverage Policy セクションで定義する。

## Legacy テスト在庫（集計）

| Legacy test class | Tests | 主な責務 |
| --- | --- | --- |
| `TestGetMessageRole` | 2 | request type ごとの message role 判定 |
| `TestCheckIfPreviousChatHistoriesExist` | 1 | history existence read-only path |
| `TestLoadPreviousChatHistories` | 15 | history mapping/filtering/limit/greeting/tool result 表示 |
| `TestInitSession` | 17 | session 初期化/agent clone/history load/previous_response_id |
| `TestSummarizePositionDetailChat` | 8 | summary path の継続性 |
| `TestToolOutputNormalization` | 4 | tool output parse/serialize |
| `TestChatStreamingCompatibility` | 2 | streamed event compatibility |
| `TestChatJobtypeSearchFlow` | 2 | job type search flow |
| `TestChatStopAtToolFlow` | 1 | stop-at-tool replay |
| `TestHandleToolCallItem` | 1 | tool call item 処理 |
| `TestExtractSelectedJobtypes` | 3 | selected jobtypes 抽出 |
| `TestWorkflowSubmitted` | 2 | workflow submitted |
| `TestWorkflowCancelled` | 3 | workflow cancelled |
| `TestChatWorkflowTraversal` | 1 | workflow traversal security |

## Migration Map

状態語彙:
- `pass`: Phase 3 で required command の pass evidence がある
- `fixture-schema-only`: Phase 3 は fixture schema の確認に留まり、runtime invariant は Phase 4 owner が引き継ぐ
- `pending-phase-4`: 移行先 unit/integration test は Phase 4 owner が実装

| Legacy private method / behavior | Legacy test file | Migration target | Rationale | Owner task | Required marker | Matrix scenario | Phase 3 evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `_get_message_role()` | `server/tests/unit/services/test_chat_service.py` (`TestGetMessageRole`) | `TurnPreparer` / `server/tests/unit/services/chat/test_turn_preparer.py` | role 判定は turn preparation の責務 | feature-3-persistence-turn-preparation / task-2-turn-preparer | `pre_extraction_parity`, `rollback_runner` | usage propagation（component unit 移行対象） | `pending-phase-4` |
| `_filter_and_limit_histories()` / greeting 含む history shaping | `server/tests/unit/services/test_chat_service.py` (`TestLoadPreviousChatHistories`) | `HistoryMapper` / `server/tests/unit/services/chat/test_history_mapper.py` | history mapping/filter/limit/greeting は history mapper の責務 | feature-2-state-history-extraction / task-2-history-mapper | `pre_extraction_parity`, `rollback_di` | history mapping | `fixture-schema-only` |
| `check_if_previous_chat_histories_exist()` read-only path | `server/tests/unit/services/test_chat_service.py` (`TestCheckIfPreviousChatHistoriesExist`) | integration contract 維持 (`server/tests/integration/chat_service_contract/test_di_lifecycle.py`) + 必要なら `HistoryMapper` 補助 test | public read-only API。DI/history contract で担保 | feature-2-state-history-extraction / task-2-history-mapper | `pre_extraction_parity`, `rollback_di` | history mapping | `fixture-schema-only` |
| `init_session()` orchestration | `server/tests/unit/services/test_chat_service.py` (`TestInitSession`) | refactored `ChatService` integration test + `ConversationState`/`LLMRunner` unit tests | init/session lifecycle は shell + state + runner 境界の協調責務 | feature-1-refactored-bootstrap / task-2-bootstrap-behavioral-proof | `pre_extraction_parity`, `rollback_di` | DI lifecycle | `pass` |
| real refactored 実行証明の前提（delegating 復元時 fail を含む） | `server/tests/unit/services/test_chat_service.py`（streaming/init 周辺の前提テスト） | Phase 4 bootstrap behavioral proof (`server/tests/integration/chat_service_contract/test_no_legacy_dependency.py`) | legacy dependency reintroduction は unit ではなく bootstrap behavioral proof で判定する | feature-1-refactored-bootstrap / task-2-bootstrap-behavioral-proof | `pre_extraction_bootstrap`, `pre_extraction_parity` | legacy dependency reintroduction | `fixture-schema-only` |
| `summarize_position_detail_chat()` | `server/tests/unit/services/test_chat_service.py` (`TestSummarizePositionDetailChat`) | contract test 中心 (`server/tests/integration/chat_service_contract/test_summary_rollback.py`) + 必要最小 unit | summary path は runtime switching 外側で維持 | phase-5-final-parity / feature-3-final-matrix-gate / task-1-final-matrix-gate | `rollback_summary`, `pre_extraction_parity` | summary rollback | `fixture-schema-only` |
| `_parse_tool_output()` / tool output serialize | `server/tests/unit/services/test_chat_service.py` (`TestToolOutputNormalization`) | `ToolEventHandler` / `server/tests/unit/services/chat/test_tool_event_handler.py` | tool output normalization は tool handler 責務 | feature-4-stream-tool-security-workflow / task-2-tool-event-handler | `pre_extraction_parity`, `rollback_runner` | tool result response shape | `fixture-schema-only` |
| chat history write/update side effects | `server/tests/unit/services/test_chat_service.py` (ToolOutput/InitSession/Chat flow 周辺) | `ChatPersistence` / `server/tests/unit/services/chat/test_chat_persistence.py` | DB write side effects を persistence component に分離 | feature-3-persistence-turn-preparation / task-1-chat-persistence | `pre_extraction_parity`, `rollback_runner` | DB side effects | `fixture-schema-only` |
| streamed event compatibility (`run_streamed`, handoff, usage) | `server/tests/unit/services/test_chat_service.py` (`TestChatStreamingCompatibility`) | `LLMRunner` + `StreamEventProcessor` / `server/tests/unit/services/chat/test_llm_runner.py`, `server/tests/unit/services/chat/test_stream_event_processor.py` | runner 境界と event 消費責務を分離 | feature-1-refactored-bootstrap / task-1-real-refactored-shell, feature-4-stream-tool-security-workflow / task-1-stream-event-processor | `pre_extraction_parity`, `pre_extraction_bootstrap`, `rollback_runner` | runner event normalization, usage propagation | `pass` |
| stop-at-tool replay | `server/tests/unit/services/test_chat_service.py` (`TestChatStopAtToolFlow`) | `ToolEventHandler` / `server/tests/unit/services/chat/test_tool_event_handler.py` | `tool_replay_items` の再入力責務 | feature-4-stream-tool-security-workflow / task-2-tool-event-handler | `pre_extraction_parity`, `rollback_runner` | stop-at-tool replay | `pass` |
| job type result/selection extraction | `server/tests/unit/services/test_chat_service.py` (`TestChatJobtypeSearchFlow`, `TestExtractSelectedJobtypes`) | `ToolEventHandler` + `WorkflowChatHandler` / `server/tests/unit/services/chat/test_tool_event_handler.py`, `server/tests/unit/services/chat/test_workflow_chat_handler.py` | tool result shape と workflow preprocessing の分界点 | feature-4-stream-tool-security-workflow / task-2-tool-event-handler, task-4-workflow-chat-handler | `pre_extraction_parity`, `rollback_runner`, `rollback_security` | workflow side effects, tool result response shape | `fixture-schema-only` |
| tool call item handling | `server/tests/unit/services/test_chat_service.py` (`TestHandleToolCallItem`) | `ToolEventHandler` / `server/tests/unit/services/chat/test_tool_event_handler.py` | tool input parse/rate-limit/dispatch を handler へ収束 | feature-4-stream-tool-security-workflow / task-2-tool-event-handler | `pre_extraction_parity`, `rollback_runner` | tool result response shape | `fixture-schema-only` |
| workflow submitted/cancelled | `server/tests/unit/services/test_chat_service.py` (`TestWorkflowSubmitted`, `TestWorkflowCancelled`) | `WorkflowChatHandler` / `server/tests/unit/services/chat/test_workflow_chat_handler.py` | workflow public API の preprocessing と state 更新を分離 | feature-4-stream-tool-security-workflow / task-4-workflow-chat-handler | `pre_extraction_parity`, `rollback_security` | workflow side effects | `fixture-schema-only` |
| workflow traversal security / cancellation cleanup 周辺 | `server/tests/unit/services/test_chat_service.py` (`TestChatWorkflowTraversal`) | `StreamGuard` + `WorkflowChatHandler` / `server/tests/unit/services/chat/test_stream_guard.py`, `server/tests/unit/services/chat/test_workflow_chat_handler.py` | security detection と workflow interaction の境界 | feature-4-stream-tool-security-workflow / task-3-stream-guard-security, task-4-workflow-chat-handler | `pre_extraction_parity`, `rollback_security` | security block cleanup, cancellation cleanup | `fixture-schema-only` |

## Contract Scenario 連携（Phase 3 → Phase 4）

| Contract scenario | Phase 3 characterization source | Phase 4 migration target |
| --- | --- | --- |
| runner event normalization | `server/tests/integration/chat_service_contract/test_runner_contract.py` | `LLMRunner`, `StreamEventProcessor` |
| stop-at-tool replay | `server/tests/integration/chat_service_contract/test_runner_contract.py` | `ToolEventHandler` |
| usage propagation | `server/tests/integration/chat_service_contract/test_runner_contract.py` | `StreamEventProcessor` |
| history mapping | `server/tests/integration/chat_service_contract/test_history_mapping.py` | `HistoryMapper` |
| DB side effects | `server/tests/integration/chat_service_contract/test_db_side_effects.py` | `ChatPersistence` |
| tool result response shape | `server/tests/integration/chat_service_contract/test_tool_results.py` | `ToolEventHandler` |
| security block cleanup | `server/tests/integration/chat_service_contract/test_security_cleanup.py` | `StreamGuard` |
| cancellation cleanup | `server/tests/integration/chat_service_contract/test_security_cleanup.py` | `StreamGuard` |
| workflow side effects | `server/tests/integration/chat_service_contract/test_workflow_side_effects.py` | `WorkflowChatHandler` |
| summary rollback | `server/tests/integration/chat_service_contract/test_summary_rollback.py` | summary integration contract 維持 |
| legacy dependency reintroduction | `server/tests/integration/chat_service_contract/test_no_legacy_dependency.py` | Phase 4 bootstrap behavioral proof |

## 必須移行先テストファイル（Phase 4 owner が作成/更新）

- `server/tests/unit/services/chat/test_conversation_state.py`
- `server/tests/unit/services/chat/test_history_mapper.py`
- `server/tests/unit/services/chat/test_turn_preparer.py`
- `server/tests/unit/services/chat/test_chat_persistence.py`
- `server/tests/unit/services/chat/test_llm_runner.py`
- `server/tests/unit/services/chat/test_stream_event_processor.py`
- `server/tests/unit/services/chat/test_tool_event_handler.py`
- `server/tests/unit/services/chat/test_stream_guard.py`
- `server/tests/unit/services/chat/test_workflow_chat_handler.py`

## 完了判定（本タスク）

- [x] `Legacy private method`, `Legacy test file`, `Migration target`, `Rationale`, `Owner task`, `Required marker` を migration map に含めた
- [x] Phase 4 extraction task が参照可能な owner task mapping を定義した
- [x] `gate_a_scenario_matrix.md` と整合する evidence 表現（`pass` / `fixture-schema-only` / `pending-phase-4`）に統一した
- [x] affected private tests を未分類のまま残さず、すべて migration target を割り当てた
