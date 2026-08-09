# フェーズ: refactored 実装への責務移植

## 目的

`chat_service_refactored.ChatService` の public behavior を維持したまま、内部責務を小さな component へ移植する。

## スコープ

スコープ内:
- main `chat()` path の legacy 委譲削除
- `ConversationState`
- `HistoryMapper`
- `ChatPersistence`
- `TurnPreparer`
- `StreamEventProcessor`
- `ToolEventHandler`
- `StreamGuard`
- `WorkflowChatHandler`
- `SummaryService` / `LLMOutputGuard` のコンストラクタ wiring と `build_summary_context()` 呼び出し（PR #249 バックフィル）

スコープ外:
- Gate B の `api_style`
- summary path の runtime switching
- legacy `chat_service.py` の大規模分割
- `build_summary_context()` の専用コンポーネントへの抽出（Phase 5 以降）

## 開始条件

- Phase 3 の pre-extraction parity gate が pass している。
- affected private tests の移行方針を task ごとに記録できる。

## 終了条件

- `chat_service_refactored.ChatService.chat()` が orchestration に集中している。
- Phase 4 の最後で legacy `ChatService` への委譲が削除されている。
- behavioral real-refactored execution proof により、`chat_service_refactored.ChatService.chat()` が real runner path に到達し、delegating adapter 復元時に失敗することが確認されている。
- static check は追加防御として使ってよいが、static check だけでは Phase 4 完了条件を満たさない。
- Phase 4 bootstrap 後、`server/plan/phases/gate_a_scenario_matrix.md` の `real-refactored evidence` が対象 scenario で更新されている。
- Phase 4 の各 extraction task は、変更対象 scenario の `real-refactored evidence` を更新してから完了する。

## フィーチャー

| フィーチャー | 目的 | 依存関係 | ステータス |
| --- | --- | --- | --- |
| feature-1-refactored-bootstrap | real refactored shell を作る。 | Phase 3 | done |
| feature-2-state-history-extraction | state と history mapping を分離する。 | feature-1 | done |
| feature-3-persistence-turn-preparation | persistence と turn preparation を分離する。 | feature-2 | done |
| feature-4-stream-tool-security-workflow | stream/tool/security/workflow を分離する。 | feature-3 | done |
| feature-5-summary-guard-backfill | SummaryService / LLMOutputGuard を refactored path に wiring する（PR #249 バックフィル）。 | feature-4 task-1以降 | not-started |

## タスク分割

| フィーチャー | タスク | 目的 | 必須検証 |
| --- | --- | --- | --- |
| feature-1-refactored-bootstrap | task-1-real-refactored-shell | main `chat()` path の legacy 委譲を外した薄い shell を作る。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap` |
| feature-1-refactored-bootstrap | task-2-bootstrap-behavioral-proof | real runner path 到達と delegating adapter 復元時 fail を証明する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap` |
| feature-2-state-history-extraction | task-1-conversation-state | WebSocket/session state を `ConversationState` へ移す。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di` |
| feature-2-state-history-extraction | task-2-history-mapper | DB history / Agent input / previous history payload mapping を分離する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di` |
| feature-3-persistence-turn-preparation | task-1-chat-persistence | session/history/tool output write side effects を `ChatPersistence` へ移す。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` |
| feature-3-persistence-turn-preparation | task-2-turn-preparer | LLM turn input preparation を `TurnPreparer` へ移す。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` |
| feature-4-stream-tool-security-workflow | task-1-stream-event-processor | stream event loop と frontend response yield を分離する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` |
| feature-4-stream-tool-security-workflow | task-2-tool-event-handler | tool call/output と tool result response shape を分離する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` |
| feature-4-stream-tool-security-workflow | task-3-stream-guard-security | security detection と cancellation cleanup を分離する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security` |
| feature-4-stream-tool-security-workflow | task-4-workflow-chat-handler | workflow/jobtype public method preprocessing を分離する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security` |
| feature-4-stream-tool-security-workflow | task-5-legacy-dependency-removal | legacy dependency removal と final real-refactored evidence を固定する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` |
| feature-5-summary-guard-backfill | task-1-summary-service-constructor-wiring | `summary_service` / `llm_output_guard` をコンストラクタ wiring する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` |
| feature-5-summary-guard-backfill | task-2-build-summary-context-turn-wiring | refactored `chat()` に `build_summary_context()` 呼び出しを追加する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` |

## 必須検証

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security`
- `server/plan/phases/gate_a_scenario_matrix.md` の `real-refactored evidence` 更新

## Coverage Policy（Phase 4 全タスク共通）

`test_migration_map.md` は migration の最低限（floor）を定義するが、coverage の完全性は保証しない。  
各 extraction task の component unit test は以下をすべて満たす必要がある。

### 必須要件

1. **Branch coverage 100%** per component:  
   対象 component モジュールに対して branch coverage 100% を達成する。  
   ```
   pytest --cov=<component_module> --cov-branch --cov-fail-under=100 <component_test_file>
   ```
   結果サマリーを `verification.md` に記録する。

   **100% を達成できない場合の手順:**
   - `verification.md` に **explicit waiver** セクションを作成する。
   - 各 uncovered branch について以下を記録する:
     - **branch**: ファイル:行:条件の説明
     - **reason**: 未テスト化の根拠（e.g., "dead code（legacy 削除待ち）"、"runtime error path（fault injection test 未対応）"、"環境依存（CI で実行不可）"）
     - **owner**: 免除責任者
     - **date**: 免除日
     - **follow-up**: Phase 5 以降のフォローアップ（必須）

2. **Interface/boundary enumeration**:  
   着手前に component の入力・出力・副作用の boundary を列挙し、legacy test が不足しているケースを補完テストとして追加する。

3. **対象外タスク**:  
   `task-2-bootstrap-behavioral-proof`（behavioral proof 主体）および `task-5-legacy-dependency-removal`（removal 主体）は component unit test が主ではないため coverage gate を `not-applicable` としてよい。  
   `verification.md` に `not-applicable` と理由を明記すること。

## メモ

- 各 extraction は 1 component group ずつ進める。
