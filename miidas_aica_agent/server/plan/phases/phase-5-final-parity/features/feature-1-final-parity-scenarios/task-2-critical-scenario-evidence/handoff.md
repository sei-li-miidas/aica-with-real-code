# 引き継ぎ: task-2-critical-scenario-evidence

## 概要

Phase 5 feature-1 task-2 として、critical scenario の最終 pass 固定と residual branch coverage の強化を実施した。

主な変更:
1. **RetryableToolOutputFailure 機構**: ツール実行失敗時に LLM へのフィードバック付き再試行を行う retry loop を `chat_service_refactored.py` に追加。`ToolEventHandler` が "Message" キーを含む出力を受け取った際、サイレントリターンの代わりに `RetryableToolOutputFailure` 例外を送出し、LLM がセッション ID / リクエスト ID を補完して再試行できるようにした。
2. **Integration residual tests**: `test_refactored_residual_coverage.py` (354 lines)、`test_runner_residual_branches.py` (大幅拡張)、`test_summary_rollback.py` (157 lines new) を追加し、refactored variant の residual branch を網羅。
3. **Unit residual tests**: `test_llm_runner.py`、`test_llm_output_guard_residual.py`、`test_user_service.py`、`test_position_service_extra.py`、`test_llm_service_residual.py`、`test_summary_service_residual.py`、`test_conversation_summary_service_residual.py`、`test_rate_limit_service_residual.py`、`test_workflow_handlers_residual.py`、`test_workflow_service_residual.py` を新規追加。

実行メタ情報:
- 実行者: `<owner>`
- 実行ブランチ: `feature/77996_chat_service_refactoring_phase_5_feature_1_task_1`

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat/tool_event_handler.py` | `RetryableToolOutputFailure` 例外追加、ツール失敗時の raise に変更 |
| `server/src/aica_agent/services/chat_service_refactored.py` | `MAX_LLM_RETRY_COUNT=5` retry loop 追加、`RetryableToolOutputFailure` ハンドリング追加 |
| `server/tests/integration/chat_service_contract/test_refactored_residual_coverage.py` | 新規: refactored residual branch coverage integration tests |
| `server/tests/integration/chat_service_contract/test_runner_residual_branches.py` | 大幅拡張: refactored variant の runner residual branch tests |
| `server/tests/integration/chat_service_contract/test_summary_rollback.py` | 大幅拡張: summary rollback の real-refactored tests |
| `server/tests/unit/services/chat/test_llm_runner.py` | 新規: LLMRunner unit tests |
| `server/tests/unit/security/test_llm_output_guard_residual.py` | 新規: LLMOutputGuard residual branch tests |
| `server/tests/unit/services/test_user_service.py` | 新規: UserService unit tests (1055 lines) |
| `server/tests/unit/services/test_position_service_extra.py` | 新規: PositionService additional tests |
| `server/tests/unit/services/test_llm_service_residual.py` | 新規: LLMService residual branch tests |
| `server/tests/unit/services/test_summary_service_residual.py` | 新規: SummaryService residual branch tests |
| `server/tests/unit/services/test_conversation_summary_service_residual.py` | 新規: ConversationSummaryService residual branch tests |
| `server/tests/unit/services/test_rate_limit_service_residual.py` | 新規: RateLimitService residual branch tests |
| `server/tests/unit/services/test_workflow_handlers_residual.py` | 新規: WorkflowHandlers residual branch tests |
| `server/tests/unit/services/test_workflow_service_residual.py` | 新規: WorkflowService residual branch tests |
| 各既存テストファイル (integration + unit) | `pre_extraction_parity` marker 追加、real-refactored fixture 拡張 |

## 新しいAPI / ヘルパー / フィクスチャ

- `RetryableToolOutputFailure(call_id, message_to_llm)` — `services/chat/tool_event_handler.py` に追加。LLM retry ループ用例外。
- `DEFAULT_LLM_FAIL_RESPONSE`, `MAX_LLM_RETRY_COUNT` — `chat_service_refactored.py` に追加。
- `_FakeRunStream` 等の既存 helpers は変更なし。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| ツール失敗を RetryableToolOutputFailure で伝搬させる | サイレントリターンでは LLM が失敗を認識できず、会話が止まる。例外で制御を引き渡すことで、retry loop が LLM に補足情報を送れる。 | 従来通りのサイレントリターン。ただし LLM 側が失敗を検知できない問題が解決しない。 |
| 最大 5 回 retry + exponential backoff (0.5s 起点、上限 8s) | 一時的なツール失敗や LLM 内部エラーを自動回復させつつ、無限ループを防ぐ。 | 固定 1 回 retry。回復機会が限られる。 |
| 一般例外も retry loop に取り込む | runner レベルの一時エラーも LLM に system message を送って継続させる。 | 一般例外は即エラー応答。安定性は低下する。 |

## 互換性メモ

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity` は `766 passed, 298 deselected`。task-1 の `153 passed` から大幅に拡大 (residual unit tests を marker に追加)。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m rollback_summary` は `14 passed, 1050 deselected`。task-1 の `12 passed` から微増。
- 全サーバーテストは exit code 0。

## 次タスクへのフォローアップ

- `feature-2-coverage-risk-evidence / task-1-coverage-evidence` では、本タスクで追加した unit/integration tests を基に coverage 数値と未到達理由を記録すること。
- retry logic の behavioral proof は本タスクの integration tests (`test_refactored_residual_coverage.py`) で固定済み。
- `gate_a_scenario_matrix.md` の task-2 evidence を追記すること（本タスク作業中に実施）。

## 未解決の質問

なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
