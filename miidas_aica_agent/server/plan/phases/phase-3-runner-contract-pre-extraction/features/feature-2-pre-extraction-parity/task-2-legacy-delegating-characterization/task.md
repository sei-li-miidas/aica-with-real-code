# タスク: task-2-legacy-delegating-characterization

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

- task-1 で作成した scaffold test の module-level skip を解除し、`pre_extraction_parity` で実行可能な characterization suite に更新する。
- `server/tests/integration/chat_service_contract/conftest.py` に variant-aware な fixture を追加し、`legacy` と `delegating-refactored` の service 解決を固定する。
- `real-refactored` は本 task では `pending-phase-4` 扱いとし、テストでは明示的に skip して matrix の `real-refactored evidence` と整合させる。
- fixture (`_description`, `_expected_keys`) を source of truth に、Phase 3 範囲の contract characterization assertion を実装する。
- `gate_a_scenario_matrix.md` の Phase 3 owner 分シナリオについて、legacy/delegating evidence を更新する。

## 必須テスト

- 親 feature README の task table に記載された必須検証。
- `server/plan/phases/gate_a_scenario_matrix.md` の該当 evidence 更新。

## ロールバック確認対象

- 必須サブセット: 親 feature README と `gate_a_scenario_matrix.md` に記載された該当 subset。
- 必須コマンド: 親 feature README の task table に記載された検証コマンド。

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`、または `pass` 以外の各コマンドに文書化された免除がある。
- 各免除に、オーナー、理由、日付、フォローアップが含まれている。
- 必須ロールバック確認対象が `pass`、または理由付きで明示的に `not-applicable` と記録されている。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
