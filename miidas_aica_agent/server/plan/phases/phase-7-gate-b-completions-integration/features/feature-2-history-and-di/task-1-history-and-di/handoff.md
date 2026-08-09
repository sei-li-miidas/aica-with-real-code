# 引き継ぎ: history and DI wiring

## 概要

DI container の runner wiring を `agent_runtime.api_style` 対応に拡張し、history / turn preparation / persistence が style 非依存で動くことを completions contract テストで固定した。

レビューで弾く条件:
- 変更ファイル、互換性メモ、次タスクへのフォローアップ、未解決の質問のいずれかが `未記入` のまま。
- 実行した tests の exact path / marker が保存されていない。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/containers.py` | `agent_runtime.api_style` に応じて `ResponsesAgentRunner` / `CompletionsAgentRunner` を生成する factory (`_build_refactored_llm_runner`) を追加した。 |
| `server/tests/unit/services/chat/test_completions_history_and_di.py` | runner 切替、completions tool output parse、persistence serialization の style 非依存性を unit test で固定した。 |
| `server/tests/integration/chat_service_contract/test_completions_history_and_di.py` | refactored container の runner 注入切替と、`HistoryMapper` / `TurnPreparer` / `ChatPersistence` の style 非依存性を integration test で固定した。 |
| `server/tests/__init__.py` | pytest 同名 test module collision 回避のため package marker を追加した。 |
| `server/tests/unit/__init__.py` | pytest 同名 test module collision 回避のため package marker を追加した。 |
| `server/tests/unit/services/__init__.py` | pytest 同名 test module collision 回避のため package marker を追加した。 |
| `server/tests/unit/services/chat/__init__.py` | pytest 同名 test module collision 回避のため package marker を追加した。 |
| `server/tests/integration/__init__.py` | pytest 同名 test module collision 回避のため package marker を追加した。 |
| `server/tests/integration/chat_service_contract/__init__.py` | pytest 同名 test module collision 回避のため package marker を追加した。 |
| `server/tests/integration/chat_service_contract/conftest.py` ほか helper import 利用ファイル | package 化に伴い `chat_service_contract_helpers` import を相対 import に更新した。 |

## 互換性メモ

- runner の style 差分は `containers.py` で `LLMRunner` 実装選択に閉じ込め、`HistoryMapper` / `TurnPreparer` / `ChatPersistence` 本体ロジックは style-aware 分岐を追加していない。
- `responses` は既存の `ResponsesAgentRunner` を継続利用し、既存 contract を維持する。
- `completions` は `CompletionsAgentRunner` が注入されるが、chat subcomponents は同一型を維持し、履歴/保存フォーマットの責務境界を維持する。

## 次タスクへのフォローアップ

- feature-3 parity/rollback task では `completions_contract` と `rollback_api_style` の双方で container wiring が回帰しないことを前提にしてよい。
- marker 実行時は workspace root 収集で `cli/tests` が混ざるため、server scope (`server/tests/`) を明示して実行する。
- history/persistence 形式差分の検証追加時も、style 固有差分は runner contract 側（`LLMRunner`）に寄せる。

## 未解決の質問

- なし。feature-2 scope の DI/history/persistence wiring は固定済み。