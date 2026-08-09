# 引き継ぎ: task-2-contract-regression-tests

## 概要

search filter contract drift と workflow receive->dispatch->send 互換性を固定する focused regression tests を `e2e/tests/client/` に追加し、指定の必須検証コマンドをすべて pass させた。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `e2e/tests/__init__.py` | 未追加（リポジトリに存在しない）。 |
| `e2e/tests/client/__init__.py` | 未追加（リポジトリに存在しない）。 |
| `e2e/tests/conftest.py` | 未追加（リポジトリに存在しない）。 |
| `e2e/tests/client/test_workflow_contract_validation.py` | 未追加（リポジトリに存在しない）。内容: `OtherFilters[].Type` alias 正規化、未知 type の contract error、`Jobtypes` / `OtherFilters` / `JobtypeNamesWithSameSearchFilters` の list drift 正規化を直接メソッド呼び出しで固定。 |
| `e2e/tests/client/test_workflow_receive_dispatch_send_compatibility.py` | 未追加（リポジトリに存在しない）。内容: workflow event 受信時の `pending_workflow` 設定、pending action 優先順、`WORKFLOW_ANSWERS_SUBMITTED` 送信 payload、workflow action log 順序を固定。 |

## 新しいAPI / ヘルパー / フィクスチャ

- 新規 API 追加なし。
- テスト専用 helper として各テストファイル内に `_build_client()` を追加し、最小 `HeadlessPersonaSeed` で `E2EClient` を生成する形に統一した。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| runtime 本体ではなく private メソッドへの direct call を中心に固定 | 本 task のスコープは「互換回帰の検知」であり、依存 task-1 で修正済み contract 正規化の再発防止を最短経路で担保するため。 | E2E フル実行で固定する案は、外部依存/非決定性が高く failure reason の局所化が難しいため採用しなかった。 |
| `e2e/tests/conftest.py` で import path を最小補助 | `e2e/src/aica_client/client/e2e_client.py` が `from client...` / `from models...` を使うため、テスト実行時に import 解決を安定させる必要があるため。 | 各 test file ごとに `sys.path` を操作する案は重複が増えるため採用しなかった。 |

## 互換性メモ

- 既存 runtime behavior は未変更。回帰検知のみを追加。
- `OtherFilters.Type` は `multi_select -> multiple`, `single_select -> single` を pass ケースで固定し、`unknown_type` は `rest_format_invalid` を必須 failure として固定。
- workflow pending 中は jobtype/position pending dispatch より先に workflow を処理する優先順を固定。

## 次タスクへのフォローアップ

- phase-4.5 workflow verification で contract drift 再発時、まず本 task の focused tests 失敗メッセージで drift 箇所（Type alias / grouped payload / workflow submit payload）を特定してから runtime 側調査へ進む。

## 未解決の質問

- なし

## Review / Fix Log

| Pass | Reviewer | 結果 | 指摘 / 修正 |
| --- | --- | --- | --- |
| 1 | task owner | pass | 初版実装で `pytest -q` 11 件 pass。追加修正なし。 |

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。