# タスク: task-5-summary-rollback-parity

## 目的

親 feature README の task table で定義された成果を実装する。詳細 scope は親 feature README と親 phase README を source of truth とする。

`summary rollback` シナリオに full behavioral runtime assertions を実装し、`legacy evidence` を `pass` にする。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズREADME: 親 phase の `README.md` を参照する。
- 親フィーチャーREADME: 親 feature の `README.md` を参照する。
- 依存タスクの引き継ぎ: `server/plan/phases/status.md` の先行 task と各 `handoff.md` を参照する。

## スコープ

許可する変更:
- 親 feature README に記載された scope 内の実装、テスト、計画文書更新。
- `tests/integration/chat_service_contract/test_summary_rollback.py` の `fixture-schema only` テストを full behavioral assertions に置き換える。
- `tests/integration/chat_service_contract/fixtures/summary_rollback.json` のフィクスチャ更新。

許可しない変更:
- 親 feature README のスコープ外項目。

## 依存関係

- task-1-db-and-history-parity（conftest のモック構成拡張が完了していること）

## 実装メモ

### モック構成

- `LLMService` はモックを許容する（MCP サーバー起動が必要なため）。`llm_svc.summarize()` の戻り値をスタブして summary テキストを返すよう設定する。
- `chat_repository` をモックして、summary 保存メソッドの `call_args` を検証できるようにする。

### テスト対象シナリオ

1. **summary model 使用の確認**: `summarize_position_detail_chat()` が `llm_svc.summarize()` を呼び、summary モデル config を使っていることをアサートする。`service_variant` が `legacy` でも `refactored` でも同じ summary モデルが使われること（chat runtime switching の外側にあること）を確認する。
2. **summary 保存の確認**: `summarize_position_detail_chat()` 実行後に `chat_repository` の summary 保存メソッドが正しい引数で呼ばれることをアサートする。
3. **variant 独立性**: `legacy` と `delegating-refactored` の両 variant で同じ summary 動作をすることをアサートし、summary path が service_variant 切替の影響を受けないことを確認する。

### `real-refactored` variant

`real-refactored` は引き続き `pytest.skip("pending-phase-4: real-refactored evidence")` とする。

## 必須テスト

- 親 feature README の task table に記載された必須検証。
- `server/plan/phases/gate_a_scenario_matrix.md` の `summary rollback` の `legacy evidence` / `delegating evidence` を更新する。

## ロールバック確認対象

- 必須サブセット: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary`

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`、または `pass` 以外の各コマンドに文書化された免除がある。
- 各免除に、オーナー、理由、日付、フォローアップが含まれている。
- 必須ロールバック確認対象が `pass`、または理由付きで明示的に `not-applicable` と記録されている。
- `gate_a_scenario_matrix.md` の `summary rollback` の `legacy evidence` / `delegating evidence` が `pass` になっている。
- task-6 / task-7 に引き渡す前提で、summary rollback scenario の behavioral evidence を確定させる。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
