# フィーチャー: e2e search filter contract compatibility

## 目的

workflow verification に入る前の REST 初期化経路で発生している search filter payload の contract drift を吸収し、`e2e/` headless client が `positions/search_filter/current` の応答で停止せず workflow path まで到達できる状態にする。

## 親フェーズ

- フェーズ: phase-4.5-e2e-workflow-compatibility

## スコープ

スコープ内:
- `e2e/src/aica_client/client/e2e_client.py` の search filter 正規化ロジック
- `OtherFilters[].Type` の許容値拡張または正規化
- workflow verification 前提となる REST 初期化経路の実行確認
- `e2e/tests/client/` 配下の focused compatibility test 追加
	- contract drift を再現する payload fixture
	- receive -> pending -> dispatch -> send の主要互換経路

スコープ外:
- workflow response/request enum や dispatch の変更（feature-1 / feature-2 の責務）
- サーバー側レスポンスの変更
- search filter 以外の REST contract drift 対応

## 依存関係

- feature-2-e2e-client-workflow-handling / task-2 で blocker が記録されていること

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-other-filter-type-compatibility | `positions/search_filter/current` の `OtherFilters[].Type` drift を e2e が受理できるようにする。 | feature-2 task-2 blocker 記録済み | static lint check; search filter current refresh の手動確認; workflow task の再実行 | not-started |
| task-2-contract-regression-tests | search filter drift と workflow compatibility の回帰を固定する focused test を追加する。 | task-1 | `pytest` 追加テスト pass; static lint check | not-started |

## 完了条件

- `positions/search_filter/current` の `OtherFilters[].Type` が既知差分を含んでも `rest_format_invalid` で停止しない。
- workflow verification 前の初期化経路が完走する。
- feature-2 task-2 の workflow 発火/非発火確認を再実行できる状態になる。
- drift と workflow compatibility の回帰がテストで検知できる。