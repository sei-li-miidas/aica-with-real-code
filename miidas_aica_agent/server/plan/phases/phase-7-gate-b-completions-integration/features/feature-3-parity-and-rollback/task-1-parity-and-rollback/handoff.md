# 引き継ぎ: parity and rollback verification

## 概要

Gate B の observable parity suite と rollback safety suite を integration tests として確立した。
`completions_contract` と `rollback_api_style` の 2 マーカーを別々のテストファイルとして固定し、
feature-2 の DI/history/persistence wiring が前提として機能することを確認した。

実行コマンドおよびすべての `TODO` の解消を `verification.md` に記録した。

レビューで弾く条件:
- 変更ファイル、互換性メモ、次タスクへのフォローアップ、未解決の質問のいずれかが `未記入` のまま。
- evidence の保存場所が明記されていない。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/tests/integration/chat_service_contract/test_completions_observable_parity.py` | 新規追加。`completions_contract` marker の observable parity suite。共通 `build_parity_container` helper（`chat_service_contract_helpers.py`）を使い、同一の `_FakeRunStream` イベントを responses/completions 両 api_style に注入して chat() 出力の同一性を 4 テストケースで検証する。 |
| `server/tests/integration/chat_service_contract/test_completions_rollback.py` | 新規追加。`rollback_api_style` marker の rollback safety suite。`_build_lightweight_container` (local, wiring 確認用) と共通 `build_parity_container` (behavior parity 確認用) の 2 ヘルパーを使用し、runner wiring rollback / behavior parity rollback / service_variant rollback の 3 テストケースを固定する。 |

## 互換性メモ

- 比較対象: `refactored + responses` vs `refactored + completions` の observable parity (frontend 観測可能挙動)。`replay_items` 契約変更 (feature-2 task-2 handoff 参照) 後の parity を明示的に比較し、responses/completions 間で同一の chat() 出力が得られることを確認済み。
- Rollback primary `api_style: completions -> responses`: config key フリップのみで `CompletionsAgentRunner` から `ResponsesAgentRunner` への切り替えが成立することを `containers.refactored_llm_runner()` の型確認と behavior parity で確認した。
- Rollback secondary `service_variant: refactored -> legacy`: config key フリップのみで legacy `ChatService` (module: `services.chat_service`) への切り替えが成立することを確認した。
- production source (`server/src/aica_agent/**`) は一切変更していない。変更はすべて `server/tests/` と `server/plan/` に限定される。
- 既存の `completions_runner_internal` (29 passed) に regression なしを確認した。

## 次タスクへのフォローアップ

- Gate B RC 判定前に `server/plan/architecture.md` の 4 threshold (error rate / latency p95 delta / tool success rate / conversation completion rate) を埋めること。本タスクではアクセス不能 (production dashboard 未整備) のため `verification.md` に explicit なフォローアップとして記録した。オーナー: sei.li@miidas.jp。
- feature-3 が Gate B の integration test 固定を完了したため、Gate B の次 step は staging smoke / canary 実行と RC threshold の実測値記録になる。
- `build_parity_container` は `chat_service_contract_helpers.py` に共通化されている。追加の parity/rollback テストを書く場合はこのヘルパーをインポートして使用すること。

## 未解決の質問

- Gate B RC threshold (error rate / latency p95 delta / tool success rate / conversation completion rate) の target value と dashboard link は production environment での計測が必要。RC 判定前に sei.li@miidas.jp がオーナーとして記録すること (`server/plan/architecture.md#gate-b-rc-checklist` 参照)。
- それ以外の feature-3 scope の parity/rollback 整理は完了。
