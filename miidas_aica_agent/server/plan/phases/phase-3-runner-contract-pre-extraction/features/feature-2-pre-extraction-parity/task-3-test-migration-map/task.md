# タスク: task-3-test-migration-map

## 目的

親 feature README の task table で定義された成果を実装する。詳細 scope は親 feature README と親 phase README を source of truth とする。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズREADME: 親 phase の `README.md` を参照する。
- 親フィーチャーREADME: 親 feature の `README.md` を参照する。
- 依存タスクの引き継ぎ: `server/plan/phases/status.md` の先行 task と各 `handoff.md` を参照する。

## スコープ

許可する変更:
- 親 feature README に記載された scope 内の実装、テスト、計画文書更新。

許可しない変更:
- 親 feature README のスコープ外項目。

## 依存関係

- 親 feature README の依存関係を参照する。

## 実装メモ

- `server/plan/phases/phase-3-runner-contract-pre-extraction/features/feature-2-pre-extraction-parity/task-3-test-migration-map/test_migration_map.md` を作成する。
- migration map は Phase 4 extraction task が legacy private test をどこへ移すかを判断する source of truth とする。
- map には少なくとも `Legacy private method`, `Legacy test file`, `Migration target`, `Rationale`, `Owner task`, `Required marker` を含める。
- 既存 private test を contract test へ移す場合は、対応する `gate_a_scenario_matrix.md` の scenario 名も記録する。

## 必須テスト

- 親 feature README の task table に記載された必須検証。
- migration map を作成して Phase 4 owner task mapping を固定する。

## ロールバック確認対象

- 必須サブセット: 親 feature README と `gate_a_scenario_matrix.md` に記載された該当 subset。
- 必須コマンド: 親 feature README の task table に記載された検証コマンド。

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`、または `pass` 以外の各コマンドに文書化された免除がある。
- `test_migration_map.md` が作成され、Phase 4 の各 extraction task が参照できる。
- migration map に未分類の affected private test が残っていない。
- 各免除に、オーナー、理由、日付、フォローアップが含まれている。
- 必須ロールバック確認対象が `pass`、または理由付きで明示的に `not-applicable` と記録されている。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
