# フィーチャー: delegating adapter と service variant switch

## 目的

一時 delegating adapter を追加し、config による legacy/refactored 切替口を作る。

## 親フェーズ

- フェーズ: phase-2-service-variant-switch

## スコープ

スコープ内:
- `chat_service_refactored.ChatService` の一時 delegating adapter
- variant-aware `Container.chat_svc`
- `service_variant: refactored` の valid 化
- legacy/refactored 共通 fixture での wiring parity

スコープ外:
- 独立した refactored 実装の parity 証明
- main `chat()` path の legacy 委譲削除

## 依存関係

- feature-1-di-lifecycle-baseline

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-delegating-adapter-service-switch | delegating adapter と variant switch を追加する。 | DI lifecycle baseline | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di` | done |

## 完了条件

- `service_variant: legacy` / `refactored` の両方で container 解決ができる。
- `refactored` 設定の contract pass は wiring parity として記録されている。

## メモ

- この依存は Phase 4 の最後の extraction PR で必ず削除する。
