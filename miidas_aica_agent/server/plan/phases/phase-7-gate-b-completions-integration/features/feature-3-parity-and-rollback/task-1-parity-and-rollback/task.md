# タスク: parity and rollback verification

## 目的

`completions_contract` と `rollback_api_style` の integration suite を整備する。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズ README: `server/plan/phases/phase-7-gate-b-completions-integration/README.md`
- 親フィーチャー README: `server/plan/phases/phase-7-gate-b-completions-integration/features/feature-3-parity-and-rollback/README.md`

## スコープ

許可する変更:
- `server/tests/integration/` 配下の completions / rollback tests
- matrix / evidence の更新

許可しない変更:
- completions runner の core logic
- container / persistence の追加実装

## 依存関係

- feature-2-history-and-di

## 実装メモ

- observable parity と rollback safety を別々のテスト群として固定する。
- rollback は `api_style` と `service_variant` の config-only return path を確認する。