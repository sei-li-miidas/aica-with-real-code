# タスク: task-1-db-and-history-parity

## 目的

親 feature README の task table で定義された成果を実装する。詳細 scope は親 feature README と親 phase README を source of truth とする。

`history mapping` と `DB side effects` シナリオに full behavioral runtime assertions を実装し、`legacy evidence` を `pass` にする。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズREADME: 親 phase の `README.md` を参照する。
- 親フィーチャーREADME: 親 feature の `README.md` を参照する。
- 依存タスクの引き継ぎ: `server/plan/phases/status.md` の先行 task と各 `handoff.md` を参照する。

## スコープ

許可する変更:
- 親 feature README に記載された scope 内の実装、テスト、計画文書更新。
- `tests/integration/chat_service_contract/conftest.py` のモック構成拡張（リポジトリを `Mock(spec=...)` に置き換える）。
- `tests/integration/chat_service_contract/test_history_mapping.py` の `fixture-schema only` テストを full behavioral assertions に置き換える。
- `tests/integration/chat_service_contract/test_db_side_effects.py` の `fixture-schema only` テストを full behavioral assertions に置き換える。
- `tests/integration/chat_service_contract/fixtures/history_mapping.json` / `fixtures/db_side_effects.json` のフィクスチャ更新。

許可しない変更:
- 親 feature README のスコープ外項目。

## 依存関係

- feature-2-pre-extraction-parity（完了済み）

## 実装メモ

### conftest 拡張

`tests/integration/chat_service_contract/conftest.py` の `_build_variant_container` を更新し、リポジトリを `SimpleNamespace()` ではなく `Mock(spec=ChatRepository)` 等に置き換える。他のタスクも同じ conftest を使うため、各タスクで必要なモック設定を test 側で上書きできる形にする。

### history mapping テスト

- `chat_svc.init_session()` を呼ぶ前に `chat_repository.get_session` / `get_previous_chat_histories` が特定の `ChatHistory` リストを返すよう設定する。
- `Runner.run_streamed` をモックして、渡された `input` 引数を記録する。
- `init_session()` 実行後、キャプチャした `input` が `history_mapping.json` の `_expected_keys` で定義した Agent SDK input shape と一致することをアサートする。
- legacy / delegating-refactored の両 variant で同じアサートを通す。

### DB side effects テスト

- `Runner.run_streamed` をモックして、通常チャット / tool call / retry error の各シナリオ用の `LLMRunStream` イベントシーケンスを返す。
- `chat_svc.chat()` の async generator を完全に消費する。
- `chat_repository` の各書き込みメソッド（`create_session`, `save_user_history`, `save_developer_history`, `save_llm_history`, `save_tool_history`, `update_tool_output`, `save_retry_error_history` 等）の `call_args` を検証し、`db_side_effects.json` の `_expected_keys` で定義したキーが含まれることをアサートする。
- legacy / delegating-refactored の両 variant で同じアサートを通す。

### `real-refactored` variant

`real-refactored` は引き続き `pytest.skip("pending-phase-4: real-refactored evidence")` とする。

## 必須テスト

- 親 feature README の task table に記載された必須検証。
- `server/plan/phases/gate_a_scenario_matrix.md` の `history mapping` と `DB side effects` の `legacy evidence` / `delegating evidence` を更新する。

## ロールバック確認対象

- 必須サブセット: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner`

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`、または `pass` 以外の各コマンドに文書化された免除がある。
- 各免除に、オーナー、理由、日付、フォローアップが含まれている。
- 必須ロールバック確認対象が `pass`、または理由付きで明示的に `not-applicable` と記録されている。
- `gate_a_scenario_matrix.md` の `history mapping` と `DB side effects` の `legacy evidence` / `delegating evidence` が `pass` になっている。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
