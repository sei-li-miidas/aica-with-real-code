# 引き継ぎ: delegating adapter service switch

## 概要

Phase 2 の `chat_service_refactored.ChatService` を一時 delegating adapter として追加し、`service_variant: legacy` / `refactored` を `Container.chat_svc` で切り替えられるようにした。

この task の `refactored` は独立実装ではなく、legacy `ChatService` へ委譲する wiring adapter である。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat_service_refactored.py` | legacy `ChatService` に委譲する temporary adapter を追加した。 |
| `server/src/aica_agent/containers.py` | `Container.chat_svc` を service variant selector に変更した。 |
| `server/src/aica_agent/services/chat/agent_runtime_config.py` | `refactored` を service variant として定義した。 |
| `server/src/aica_agent/services/chat/config_validator.py` | `service_variant: refactored` を startup validation で許可した。 |
| `server/tests/integration/chat_service_contract/test_di_lifecycle.py` | legacy/refactored 共通の DI lifecycle contract harness に拡張した。 |
| `server/tests/unit/services/chat/test_config_validator.py` | `refactored` の valid 化を追加した。 |
| `server/tests/unit/services/chat/test_agent_runtime_config.py` | `service_variant` 解決が `refactored` を返せることを追加確認した。 |
| `server/plan/phases/gate_a_scenario_matrix.md` | DI lifecycle の delegating evidence を wiring evidence として記録した。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `services.chat_service_refactored.ChatService`
- `Container.chat_svc` は `service_variant` に応じて legacy / refactored を選ぶ。
- `test_di_lifecycle.py` は variant パラメータ付きの共通 harness になった。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| refactored 版は legacy へ委譲する | Phase 2 では wiring / boundary の確認だけが目的で、独立 parity は求めないため | 早期に real refactored 実装へ置き換える |
| `Container.chat_svc` を selector 化する | config だけで variant 切替を行うため | endpoint 側で条件分岐する |
| adapter は explicit delegation にする | temporary adapter でも contract surface を明示し、private attribute への blanket passthrough を避けるため | `__getattr__` で legacy service を丸ごと forward する |

## 互換性メモ

- `service_variant: legacy` は従来どおり legacy `ChatService` を解決する。
- `service_variant: refactored` は temporary delegating adapter を解決する。
- どちらも `Container.chat_svc()` は factory lifecycle のままで、session ごとに fresh instance を返す。

## 次タスクへのフォローアップ

- Phase 4 の最後の extraction PR で delegating adapter を削除し、`chat_service_refactored.ChatService` を real implementation に置き換える。
- 削除条件は、`chat_service_refactored.ChatService.chat()` が `LLMRunner.run_streamed()` に到達し、legacy `ChatService` への依存を持たないこと。
- `gate_a_scenario_matrix.md` の DI lifecycle delegating evidence は wiring evidence として残し続け、final parity evidence には転用しない。

## 未解決の質問

- なし。

## 前提にしてはいけないこと

- この task の `refactored` pass は独立実装 parity の証明ではない。
