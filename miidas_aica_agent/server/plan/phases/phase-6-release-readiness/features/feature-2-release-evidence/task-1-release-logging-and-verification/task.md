# タスク: task-1-release-logging-and-verification

## 目的

startup/chat turn logging evidence と release candidate verification checklist を作成する。Phase 1-5 gate command の再実行結果は checklist として記録し、Phase 6 の新規 implementation scope と混ぜない。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズREADME: 親 phase の `README.md` を参照する。
- 親フィーチャーREADME: 親 feature の `README.md` を参照する。
- 依存タスクの引き継ぎ: `server/plan/phases/status.md` の先行 task と各 `handoff.md` を参照する。

## スコープ

許可する変更:
- release logging evidence の記録。
- release candidate verification checklist の作成。
- `server/plan/phases/gate_a_scenario_matrix.md` の release readiness 関連メモ更新。
- `handoff.md` / `verification.md` / `server/plan/phases/status.md` の更新。

許可しない変更:
- Phase 1-5 gate の再設計。
- runtime behavior の変更。
- Gate B の runtime behavior 追加。

## 依存関係

- 親 feature README の依存関係を参照する。

## 実装メモ

- Phase 1-5 の marker command は RC verification checklist として再実行結果を記録する。
- checklist に `fail` または `not-run` がある場合、release candidate は作らず Phase 6 を `blocked` にする。
- startup log evidence には、実アプリ startup path が出力する `service_variant` / `agent_model` / `summary_model` / `backend` の log line を含める。
- chat turn log evidence には、実 endpoint path が出力する `service_variant` / `agent_model` / `backend` / `chat_service` / `request_type` の log line を含める。

## 必須テスト

- startup log evidence 確認。
- chat turn log evidence 確認。
- release candidate verification checklist 作成。
- `server/plan/phases/gate_a_scenario_matrix.md` の rollback subset matrix 完了確認。

## ロールバック確認対象

- 必須サブセット: rollback_endpoint_config, rollback_di, rollback_runner, rollback_security, rollback_summary, pre_extraction_bootstrap, pre_extraction_parity
- 必須コマンド: Phase 6 README の release candidate verification checklist に列挙された marker command。

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
