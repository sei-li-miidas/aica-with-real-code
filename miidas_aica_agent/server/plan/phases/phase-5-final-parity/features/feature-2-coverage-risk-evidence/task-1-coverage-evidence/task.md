# タスク: task-1-coverage-evidence

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

- coverage は hard threshold ではなく補助 evidence として記録する。
- 未到達 branch は `defensive branch`, `external dependency branch`, `unreachable by contract`, `follow-up required` のいずれかで分類する。
- performance baseline は同一 fixture で legacy/refactored を比較し、p50 / p95 / p99 またはそれに準じる latency 指標を `verification.md` に記録する。
- Phase 4 task-3 で記録済みの legacy 未到達分岐（`chat_service.py:480-481`, `991-1000`, `1031-1032`）は、この task で必ず再判定する。
- 再判定は各分岐ごとに次の 3 択で記録する: `テスト追加で解消` / `waiver 継続` / `別分類へ再ラベル`。
- `waiver 継続` の場合は、再現困難性ではなく「契約上なぜ必須でないか」を scenario evidence と紐づけて明記する。
- inventory には最低でも `services/chat_service_refactored.py` と、Phase 4 で新規導入した component modules（stream/tool/security/workflow/state/history/persistence/turn preparation）を含める。
- 各 inventory 行は `unit branch 100%` / `integration branch 100%` / `not-applicable` のいずれかを必ず選び、未選択を許可しない。

## 必須テスト

- 親 feature README の task table に記載された必須検証。
- `server/plan/phases/gate_a_scenario_matrix.md` の該当 evidence 更新。

## ロールバック確認対象

- 必須サブセット: 親 feature README と `gate_a_scenario_matrix.md` に記載された該当 subset。
- 必須コマンド: 親 feature README の task table に記載された検証コマンド。

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`、または `pass` 以外の各コマンドに文書化された免除がある。
- coverage 未到達 branch の分類と残リスクが `verification.md` または `handoff.md` に記録されている。
- performance baseline の比較結果と残リスクが記録されている。
- 各免除に、オーナー、理由、日付、フォローアップが含まれている。
- `chat_service.py:480-481`, `991-1000`, `1031-1032` の各分岐について、判定結果（解消 / waiver 継続 / 再ラベル）と根拠が `verification.md` に記録されている。
- refactoring 導入・再構成ファイル inventory が `verification.md` に存在し、各ファイルに gate 判定（unit/integration/not-applicable）と根拠が記録されている。
- `not-applicable` 判定の行には owner/date/follow-up が必ず記録されている。
- 必須ロールバック確認対象が `pass`、または理由付きで明示的に `not-applicable` と記録されている。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
