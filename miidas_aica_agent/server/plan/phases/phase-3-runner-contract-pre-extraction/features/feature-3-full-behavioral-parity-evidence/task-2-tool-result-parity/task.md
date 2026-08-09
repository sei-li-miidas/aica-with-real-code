# タスク: task-2-tool-result-parity

## 目的

親 feature README の task table で定義された成果を実装する。詳細 scope は親 feature README と親 phase README を source of truth とする。

`tool result response shape` シナリオに full behavioral runtime assertions を実装し、`legacy evidence` を `pass` にする。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズREADME: 親 phase の `README.md` を参照する。
- 親フィーチャーREADME: 親 feature の `README.md` を参照する。
- 依存タスクの引き継ぎ: `server/plan/phases/status.md` の先行 task と各 `handoff.md` を参照する。

## スコープ

許可する変更:
- 親 feature README に記載された scope 内の実装、テスト、計画文書更新。
- `tests/integration/chat_service_contract/test_tool_results.py` の `fixture-schema only` テストを full behavioral assertions に置き換える。
- `tests/integration/chat_service_contract/fixtures/tool_results.json` のフィクスチャ更新。

許可しない変更:
- 親 feature README のスコープ外項目。

## 依存関係

- task-1-db-and-history-parity（conftest のモック構成拡張が完了していること）

## 実装メモ

### モック構成

- `Runner.run_streamed` をモックして、tool call イベント（`function_call` → `function_call_output`）を含む `LLMRunStream` シーケンスを返す。
- `PositionService` はリアルインスタンスを使う。その依存リポジトリ（`position_repository`, `aica_api_repository` 等）をモックして、ツール呼び出し結果として期待する値を返すよう設定する。
- `RateLimitService` はリアルインスタンスを使う。`rate_limit_repository` をモックして、rate limit チェックが通るよう設定する。

### テスト対象シナリオ

1. **position search**: Runner が position search tool call を emit したとき、`chat()` が yield する `ChatStreamResponse` の JSON shape が `tool_results.json` の `position_search._expected_keys` と一致する。
2. **job type search**: 同様に job type search tool call の response shape を検証する。
3. **workflow start**: 同様に workflow start tool call の response shape を検証する。

### アサート方法

- `chat()` async generator を消費し、`ChatResponseType.TOOL_RESULT` 相当のイベントを収集する。
- 収集したイベントの JSON shape（キー構造）が `tool_results.json` の各 `_expected_keys` に一致することをアサートする。
- legacy / delegating-refactored の両 variant で同じアサートを通す。

### `real-refactored` variant

`real-refactored` は引き続き `pytest.skip("pending-phase-4: real-refactored evidence")` とする。

## 必須テスト

- 親 feature README の task table に記載された必須検証。
- `server/plan/phases/gate_a_scenario_matrix.md` の `tool result response shape` の `legacy evidence` / `delegating evidence` を更新する。

## ロールバック確認対象

- 必須サブセット: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner`

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`、または `pass` 以外の各コマンドに文書化された免除がある。
- 各免除に、オーナー、理由、日付、フォローアップが含まれている。
- 必須ロールバック確認対象が `pass`、または理由付きで明示的に `not-applicable` と記録されている。
- `gate_a_scenario_matrix.md` の `tool result response shape` の `legacy evidence` / `delegating evidence` が `pass` になっている。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
