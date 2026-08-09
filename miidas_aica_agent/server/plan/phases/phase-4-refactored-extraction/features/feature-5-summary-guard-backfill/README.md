# フィーチャー: summary / guard バックフィル

## 目的

PR #249（メインチャットのサマリー機能）で追加された summary 関連挙動を、legacy 委譲に戻さず `chat_service_refactored.py` の native 実装に反映する。`SummaryService` / `LLMOutputGuard` の DI 境界を整理し、`build_summary_context()` 相当の再構築処理と `check_should_start_summary()` 起動判定を refactored path で parity 回復する。

## 背景

フェーズ4の計画策定後に PR #249 が `chat_service.py` へ以下を追加した:
- `SummaryService` DI パラメーター（`summary_service: SummaryService | None = None`）
- `LLMOutputGuard` DI パラメーター（`llm_output_guard: LLMOutputGuard | None = None`）
- `build_summary_context(session_id)` メソッド（メインチャット文脈を要約境界で再構築）
- `_remove_tool_trace_message()` ヘルパー
- `_summary_context_cache` フィールド（差分再構築キャッシュ、legacy のみに存在）
- `init_session()` 内での `build_summary_context()` 呼び出し
- `chat()` の `_prepare_for_chat_turn()` 後での `build_summary_context()` 呼び出し（`MAIN_CHAT_KEY` かつ `previous_response_id` 未設定時）
- 正常ターン完了後の `check_should_start_summary(session_id)` 呼び出し（`MAIN_CHAT_KEY` かつ `summary_service` 設定時）

現時点の refactored path は以下が未整備:

| 問題 | 影響 |
| --- | --- |
| summary 依存の DI 境界が未定義 | `SummaryService` をどこで注入するかが不明確で、実装時に境界がぶれやすい |
| `chat()` ターン先頭で `build_summary_context()` を呼ばない | 要約文脈が LLM に渡らない（parity 欠落） |
| 正常ターン後に `check_should_start_summary()` を呼ばない | 要約ジョブが一切起動しない（**機能的リグレッション**） |

`containers.py` の現行 wiring は refactored `ChatService` に `summary_service` を渡していないため、TypeError は再現条件ではない。task-1 では DI 方針を明確化し、native refactored 前提で実装境界を固定する。

## 親フェーズ

- フェーズ: phase-4-refactored-extraction

## スコープ

スコープ内:
- `chat_service_refactored.py` の constructor / field で `SummaryService` と `LLMOutputGuard` の依存境界を整理（DI するか内部生成するかを明示）
- refactored `chat()` の `prepare_turn()` 後に summary context 再構築処理（`build_summary_context()` 相当）を追加
- 正常ターン後に `SummaryService.check_should_start_summary()` 呼び出しを追加（`_record_usage()` 後、`should_save = True` の前）
- `rollback_summary` マーカーテストの real-refactored evidence を更新し、`pre_extraction_parity` を維持

スコープ外:
- `build_summary_context()` の専用コンポーネントへの大規模抽出（Phase 5 以降）
- `SummaryService` 内部ロジックの変更
- legacy 委譲 (`LegacyChatService` 再導入) に戻す変更

> **注意**: 当初スコープ外としていた `ConversationSummaryService` の変更は、task-3 にてスコープ内に追加した。
> `LLMService` との重複コードを削除するためであり、`summarize_conversation()` の動作は変更しない。

## 依存関係

- feature-4-stream-tool-security-workflow task-1 以降（`StreamEventProcessor` が chat loop を担う段階）
- `SummaryService` は `chat_service.py` 経由で既実装済み（PR #249）

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-summary-service-constructor-wiring | `SummaryService` / `LLMOutputGuard` の依存境界と container wiring 方針を確定し、refactored 実装に反映する。 | feature-4 task-1以降 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | done |
| task-2-build-summary-context-turn-wiring | `build_summary_context()` 相当処理と `check_should_start_summary()` を refactored `chat()` に追加し、behavioral parity を証明する。 | task-1 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | not-started |
| task-3-summarization-consolidation | `summarize_position_detail_chat()` を `ConversationSummaryService` に移植し、`LLMService` の要約重複コードをすべて削除する。 | task-1 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, unit tests, test_summary_rollback.py | not-started |

## 完了条件

- `chat_service_refactored.py` の summary 依存境界（DI / default 生成）がドキュメントと実装で一致している。
- refactored `chat()` が `prepare_turn()` 後に summary context 再構築処理を実行している。
- 正常ターン後に `SummaryService.check_should_start_summary()` が呼ばれている。
- `ConversationSummaryService` が `summarize_position_detail_chat()` を持ち、`LLMService` の要約重複コードが削除されている。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary` の real-refactored evidence が `pass` である。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` が `pass` である。
