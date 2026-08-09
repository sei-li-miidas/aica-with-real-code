# タスク: task-6-coverage-gap-inventory

## 目的

親 feature README の task table で定義された成果を実装する。詳細 scope は親 feature README と親 phase README を source of truth とする。

task-1〜5 完了時点の `pre_extraction_parity` coverage report を source of truth に、legacy `chat_service.py` の未カバーブランチを inventory 化し、100% 到達に必要な residual parity 実装対象を固定する。

## 最初に読むコンテキスト

- `server/plan/refactoring_plan.md`
- `server/plan/architecture.md`
- 親フェーズREADME: 親 phase の `README.md` を参照する。
- 親フィーチャーREADME: 親 feature の `README.md` を参照する。
- 依存タスクの引き継ぎ: `server/plan/phases/status.md` の先行 task と各 `handoff.md` を参照する。

## スコープ

許可する変更:
- 親 feature README に記載された scope 内の計画文書更新。
- `pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing` を source of truth に、`chat_service.py` の未カバーブランチ inventory を handoff / verification に記録する。
- 各未カバーブランチについて、到達入口、既存 scenario との対応、`reachable by parity test` / `requires plan amendment` の分類、および task-7 または後続追加 task で必要な対応を明記する。

許可しない変更:
- 親 feature README のスコープ外項目。
- task-7 に属する residual parity テストの実装着手。

## 依存関係

- task-5-summary-rollback-parity

## 実装メモ

### inventory ルール

- coverage report の未達 line / branch を 1 件ずつ列挙し、`chat_service.py` の public interface からどの入力で到達するかを記録する。
- 「既存 task-1〜5 の scenario で自然に閉じるはず」では済ませず、task-7 で追加する fixture / test file / assertion まで具体化する。
- public interface 経由での到達経路が説明できないブランチは、`requires plan amendment` として handoff に記録し、feature / phase plan に追加 task を起票するまで task-7 を開始してはいけない。

## 必須テスト

- 親 feature README の task table に記載された必須検証。

## ロールバック確認対象

- 必須サブセット: `pytest -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing`

## 完了条件

- `verification.md` の必須コマンドがすべて `pass`、または `pass` 以外の各コマンドに文書化された免除がある。
- `chat_service.py` の未カバーブランチ inventory が handoff / verification に実値で記録されている。
- `reachable by parity test` と判定されたブランチについて、task-7 が実装すべき residual parity scenario 一覧が具体化されている。
- `requires plan amendment` と判定されたブランチがある場合、feature / phase plan を更新すべきことが handoff に明記されている。
- `handoff.md` が更新されている。
- `verification.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
