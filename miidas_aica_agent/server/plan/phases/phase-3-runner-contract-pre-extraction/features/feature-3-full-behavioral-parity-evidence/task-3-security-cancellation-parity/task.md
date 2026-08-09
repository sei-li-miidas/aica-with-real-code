# タスク: task-3-security-cancellation-parity

## 目的

親 feature README の task table で定義された成果を実装する。詳細 scope は親 feature README と親 phase README を source of truth とする。

`security block cleanup` と `cancellation cleanup` シナリオに full behavioral runtime assertions を実装し、`legacy evidence` を `pass` にする。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズREADME: 親 phase の `README.md` を参照する。
- 親フィーチャーREADME: 親 feature の `README.md` を参照する。
- 依存タスクの引き継ぎ: `server/plan/phases/status.md` の先行 task と各 `handoff.md` を参照する。

## スコープ

許可する変更:
- 親 feature README に記載された scope 内の実装、テスト、計画文書更新。
- `tests/integration/chat_service_contract/test_security_cleanup.py` の `fixture-schema only` テストを full behavioral assertions に置き換える。
- `tests/integration/chat_service_contract/fixtures/security_block.json` / `fixtures/cancellation_cleanup.py` のフィクスチャ更新。

許可しない変更:
- 親 feature README のスコープ外項目。

## 依存関係

- task-1-db-and-history-parity（conftest のモック構成拡張が完了していること）

## 実装メモ

### security block cleanup テスト

- forbidden word または context danger を含むメッセージを `chat()` に渡す。
- `chat()` async generator を消費し、session block レスポンスが返ることをアサートする。
- `chat_repository` の session block 書き込みメソッドが呼ばれたことをアサートする。
- `InjectionDetector` の session state が cleanup されていることをアサートする（`remove_session` が呼ばれたか、または detector 状態が空であること）。
- legacy / delegating-refactored の両 variant で同じアサートを通す。

### cancellation cleanup テスト

- `Runner.run_streamed` をモックして、消費に時間がかかるかのように複数イベントを返す `LLMRunStream` を返す。
- `chat()` async generator を開始し、最初のイベントを取得した後 `await gen.aclose()` を呼ぶ。
- `aclose()` 後に `StreamGuard` / `InjectionDetector` / stream-local buffer の cleanup が実行されていることをアサートする。
- `aclose()` を複数回呼んでも副作用が増えないこと（idempotent）をアサートする。
- legacy / delegating-refactored の両 variant で同じアサートを通す。

### `real-refactored` variant

`real-refactored` は引き続き `pytest.skip("pending-phase-4: real-refactored evidence")` とする。

## 必須テスト

- 親 feature README の task table に記載された必須検証。
- `server/plan/phases/gate_a_scenario_matrix.md` の `security block cleanup` と `cancellation cleanup` の `legacy evidence` / `delegating evidence` を更新する。

## ロールバック確認対象

- 必須サブセット: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security`

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`、または `pass` 以外の各コマンドに文書化された免除がある。
- 各免除に、オーナー、理由、日付、フォローアップが含まれている。
- 必須ロールバック確認対象が `pass`、または理由付きで明示的に `not-applicable` と記録されている。
- `gate_a_scenario_matrix.md` の `security block cleanup` と `cancellation cleanup` の `legacy evidence` / `delegating evidence` が `pass` になっている。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
