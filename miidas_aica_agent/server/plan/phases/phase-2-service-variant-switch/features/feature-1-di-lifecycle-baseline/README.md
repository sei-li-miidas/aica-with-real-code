# フィーチャー: DI lifecycle baseline

## 目的

legacy 設定で `Container.chat_svc` が session ごとに別 instance を返すことを固定する。

## 親フェーズ

- フェーズ: phase-2-service-variant-switch

## スコープ

スコープ内:
- `service_variant: legacy` の provider 解決テスト
- WebSocket/session 単位の factory lifecycle テスト
- REST history path の stateless 確認

スコープ外:
- `chat_service_refactored.py` の追加
- `service_variant: refactored` の valid 化

## 依存関係

- phase-1-endpoint-config-boundary

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-di-lifecycle-baseline | legacy DI lifecycle を固定する。 | Phase 1 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di` | done |

## 完了条件

- `service_variant: legacy` で legacy `ChatService` が解決される。
- `Container.chat_svc()` が singleton ではないことがテストで保証される。

## メモ

- この feature では `refactored` variant はまだ有効化しない。
