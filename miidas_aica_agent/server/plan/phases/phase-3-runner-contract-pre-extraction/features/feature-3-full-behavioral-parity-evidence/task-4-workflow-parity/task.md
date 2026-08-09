# タスク: task-4-workflow-parity

## 目的

親 feature README の task table で定義された成果を実装する。詳細 scope は親 feature README と親 phase README を source of truth とする。

`workflow side effects` シナリオに full behavioral runtime assertions を実装し、`legacy evidence` を `pass` にする。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズREADME: 親 phase の `README.md` を参照する。
- 親フィーチャーREADME: 親 feature の `README.md` を参照する。
- 依存タスクの引き継ぎ: `server/plan/phases/status.md` の先行 task と各 `handoff.md` を参照する。

## スコープ

許可する変更:
- 親 feature README に記載された scope 内の実装、テスト、計画文書更新。
- `tests/integration/chat_service_contract/test_workflow_side_effects.py` の `fixture-schema only` テストを full behavioral assertions に置き換える。
- `tests/integration/chat_service_contract/fixtures/workflow_side_effects.json` のフィクスチャ更新。

許可しない変更:
- 親 feature README のスコープ外項目。

## 依存関係

- task-1-db-and-history-parity（conftest のモック構成拡張が完了していること）

## 実装メモ

### モック構成

- `WorkflowService` はリアルインスタンスを使う。`WorkflowRepository` と `WorkflowDefinitionRepository` をモックして、テスト用のワークフロー定義と状態を返すよう設定する。

### テスト対象シナリオ

1. **jobtype selected**: jobtype selection リクエストを `chat()` に渡し、state が更新され、適切な chat stream contract が返ることをアサートする。
2. **jobtype clear**: jobtype clear リクエストを `chat()` に渡し、state がクリアされることをアサートする。
3. **workflow submitted**: workflow submit リクエストを `chat()` に渡し、`WorkflowService` の submit メソッドが呼ばれ、chat stream contract が返ることをアサートする。
4. **workflow cancelled**: workflow cancel リクエストを `chat()` に渡し、`WorkflowService` の cancel メソッドが呼ばれることをアサートする。

### アサート方法

- `chat()` async generator を消費し、返された `ChatStreamResponse` イベントの shape が `workflow_side_effects.json` の各 `_expected_keys` と一致することをアサートする。
- `WorkflowService` を通じた state 変更が `workflow_repository` の call_args に反映されていることをアサートする。
- legacy / delegating-refactored の両 variant で同じアサートを通す。

### `real-refactored` variant

`real-refactored` は引き続き `pytest.skip("pending-phase-4: real-refactored evidence")` とする。

## 必須テスト

- 親 feature README の task table に記載された必須検証。
- `server/plan/phases/gate_a_scenario_matrix.md` の `workflow side effects` の `legacy evidence` / `delegating evidence` を更新する。

## ロールバック確認対象

- 必須サブセット: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security`

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`、または `pass` 以外の各コマンドに文書化された免除がある。
- 各免除に、オーナー、理由、日付、フォローアップが含まれている。
- 必須ロールバック確認対象が `pass`、または理由付きで明示的に `not-applicable` と記録されている。
- `gate_a_scenario_matrix.md` の `workflow side effects` の `legacy evidence` / `delegating evidence` が `pass` になっている。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
