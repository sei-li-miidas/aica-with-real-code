# 検証: parity and rollback verification

## テスト概要

Gate B の observable parity suite と rollback safety suite を integration tests として確立した。
`completions_contract` (15 passed) および `rollback_api_style` (5 passed) の必須コマンドを実行し、
`completions_runner_internal` (29 passed) で regression なしを確認した。

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_contract server/tests/` | pass: 15 passed, 1572 deselected | feature-2 からの 11 件 + 新規 4 件 (observable parity: response shape, stream ordering, tool result, empty stream END) |
| `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_api_style server/tests/` | pass: 5 passed, 1582 deselected | feature-2 からの 2 件 + 新規 3 件 (runner wiring rollback, behavior parity rollback, service_variant rollback) |
| `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_runner_internal server/tests/` | pass: 29 passed, 1558 deselected | regression guard: 変更なし、全件 pass |

実行日: 2026-06-19
ブランチ: feature/80254_completionapi_phase_7_feature_3_task_1

## 必須コマンド

- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_contract server/tests/`
- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_api_style server/tests/`

## evidence 保存場所

- 本ファイル (`verification.md`) に実行ログと pass 件数を記録した。
- 比較対象テストの実装: `server/tests/integration/chat_service_contract/test_completions_observable_parity.py` (parity) および `server/tests/integration/chat_service_contract/test_completions_rollback.py` (rollback)

## 比較対象

- **observable parity**: `refactored + responses` vs `refactored + completions` — 同一の `_FakeRunStream` イベントを注入し、`chat()` の frontend 観測可能な出力 (response_type / message / stream ordering) が一致することを確認。
- **rollback primary**: `api_style: completions -> responses` — config key フリップで `CompletionsAgentRunner` → `ResponsesAgentRunner` に戻ること、かつ `chat()` の observable 出力が一致することを確認。
- **rollback secondary**: `service_variant: refactored -> legacy` — config key フリップで legacy `ChatService` モジュールに戻ることを確認。

## rollback 参照

- `server/plan/architecture.md#rollout-and-rollback-architecture` — Rollback order (primary: api_style completions->responses, secondary: service_variant refactored->legacy) の canonical source。
- `server/plan/architecture.md#gate-b-verification-layers` — Layer 1 (observable parity), Layer 3 (rollback safety) の定義。

## Gate B RC threshold 記録

architecture.md "Rollout and rollback architecture" / "Gate B RC checklist" の 4 threshold (error rate / latency p95 delta / tool success rate / conversation completion rate) は本タスク時点で `TODO` のままである。

これらは本タスクで埋めることができない理由:
- threshold の target value 設定には production dashboard と baseline metrics が必要であり、本タスクの scope (integration test 固定) ではアクセスできない。
- evidence location には staging / canary environment の dashboard link または runbook path が必要。

フォローアップ:
- オーナー: sei.li@miidas.jp
- 内容: Gate B RC 判定前に architecture.md の 4 threshold すべてに target / owner / due date / evidence location を埋め、RC checklist を `pass` にすること。
- 期限: RC 判定前 (Gate B promote の staging canary 完了後)
- 本タスクは integration test 固定 scope を完了しており、RC threshold 記録不足は feature-3 task-1 の `done` 判定を block しない（threshold 記録は RC 判定前の独立フォローアップ）。

## 未実行

なし。必須コマンドはすべて実行済みであり、`completions_runner_internal` regression guard も pass した。
