# タスク: task-2-bootstrap-behavioral-proof

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

- contract harness は `implementation_mode` を明示的に parametrization する。最低限 `legacy`, `delegating-refactored`, `real-refactored` を区別できるようにする。
- `real-refactored` mode では `chat_service_refactored.ChatService.chat()` が `LLMRunner.run_streamed()` に到達したことを spy / mock / test double で検証する。
- 同じ fixture を `delegating-refactored` mode で実行した場合は、behavioral proof 用の assertion が fail する negative test を追加する。
- contract harness は test output または evidence に implementation identity を記録し、`delegating-refactored` を `real-refactored` と誤記録しない。
- static import check は追加防御として許可するが、`LLMRunner.run_streamed()` 到達 proof の代替にしてはいけない。

## 必須テスト

- 親 feature README の task table に記載された必須検証。
- `server/plan/phases/gate_a_scenario_matrix.md` の該当 evidence 更新。
- component 単体テストの branch coverage 100%（`pytest --cov --cov-branch --cov-fail-under=100`）。100% を達成できない場合、`verification.md` に explicit waiver を記録：各 uncovered branch について branch / reason / owner / date / follow-up 。対象外タスクは `not-applicable` と理由を記録。
- component interface/boundary を列挙し、legacy test gap を補完テストとして追加する。

## ロールバック確認対象

- 必須サブセット: 親 feature README と `gate_a_scenario_matrix.md` に記載された該当 subset。
- 必須コマンド: 親 feature README の task table に記載された検証コマンド。

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`、または `pass` 以外の各コマンドに文書化された免除がある。
- `real-refactored` mode で `LLMRunner.run_streamed()` 到達 proof が `pass` している。
- `delegating-refactored` mode に戻した negative test が期待どおり fail することを `verification.md` に記録している。
- `gate_a_scenario_matrix.md` の bootstrap 対象 scenario に `real-refactored evidence` が記録されている。
- 各免除に、オーナー、理由、日付、フォローアップが含まれている。
- 必須ロールバック確認対象が `pass`、または理由付きで明示的に `not-applicable` と記録されている。
- component unit test の branch coverage 100% が達成されているか、または `verification.md` に explicit waiver が記録されている（各 uncovered branch について branch / reason / owner / date / follow-up を含む）。
- 対象外タスクは `verification.md` に `not-applicable` と理由が記録されている。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
