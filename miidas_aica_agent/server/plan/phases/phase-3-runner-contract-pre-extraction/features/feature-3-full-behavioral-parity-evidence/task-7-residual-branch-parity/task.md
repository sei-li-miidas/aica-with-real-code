# タスク: task-7-residual-branch-parity

## 目的

親 feature README の task table で定義された成果を実装する。詳細 scope は親 feature README と親 phase README を source of truth とする。

task-6 の inventory を source of truth に、required scenario だけでは埋まらなかった residual reachable branches を public interface 経由の parity テストで閉じ、legacy `chat_service.py` branch coverage を 100% にする。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズREADME: 親 phase の `README.md` を参照する。
- 親フィーチャーREADME: 親 feature の `README.md` を参照する。
- task-6 の `handoff.md` / `verification.md`

## スコープ

許可する変更:
- 親 feature README に記載された scope 内の実装、テスト、計画文書更新。
- task-6 inventory に記載された residual reachable branches を閉じる parity テストの追加。
- 追加 fixture / helper の更新。

許可しない変更:
- 親 feature README のスコープ外項目。
- real-refactored evidence の追加。

## 依存関係

- task-6-coverage-gap-inventory

## 実装メモ

### テスト方針

- `chat()`、`init_session()`、`summarize_position_detail_chat()` など public interface から到達できる入力だけを使う。
- task-6 inventory の各 line / branch に対して、どの fixture と assertion で閉じたかを handoff に対応づける。
- task-7 完了時は `pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing` が 100% を示すことを原則とする。
- ただし user 指示で legacy stream-loop change を採用しない場合に限り、`verification.md` と `handoff.md` に `661->978` の residual branch waiver が明記されていれば `done*` 扱いを許可する。

## 必須テスト

- 親 feature README の task table に記載された必須検証。

## ロールバック確認対象

- 必須サブセット: `pytest -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing`

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`、または `pass` 以外の各コマンドに文書化された免除がある。
- task-6 inventory に記載された residual reachable branches がすべて parity テストで閉じられている。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing` で legacy `chat_service.py` branch coverage が 100% である。
- 例外として、user 指示で legacy stream-loop change を採用しない場合は、`verification.md` と `handoff.md` に同じ `661->978` waiver が記録されていることを条件に 99% / `done*` を許可する。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
