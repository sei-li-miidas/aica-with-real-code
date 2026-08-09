# 検証: task-1-coverage-evidence

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/ --cov=services.chat_service --cov-branch --cov-report=term-missing` | pass | `1183 passed, 299 deselected`。`chat_service.py` branch coverage `99%`（未到達 `667->976`）。 |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/ --cov=services.chat_service_refactored --cov-branch --cov-report=term-missing` | pass | `1183 passed, 299 deselected`。`chat_service_refactored.py` branch coverage `98%`（未到達 `67->69`, `71->73`, `758->801`, `824-826`, `833`）。 |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python tmp/perf_baseline.py` 相当（同一 fixture 比較） | pass | 同一 fixture: `server/tests/integration/chat_service_contract/test_tool_results.py` を legacy/real-refactored で各 15 回計測し p50/p95/p99 を算出。 |

結果値:
- `pass`
- `fail`
- `not-run`
- `waived`
- `not-applicable`

完了ルール:
- 必須コマンドに `fail` または `not-run` がある間は、タスクを `done` にできない。
- `waived` は、免除セクションにオーナー、理由、日付、フォローアップがある場合のみ許可する。
- `not-applicable` は、理由がある場合のみ許可する。

## 必須コマンド

```bash
# legacy coverage evidence
PYTHONPATH=server/src/aica_agent \
	.venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/ \
	--cov=services.chat_service --cov-branch --cov-report=term-missing

# refactored coverage evidence
PYTHONPATH=server/src/aica_agent \
	.venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/ \
	--cov=services.chat_service_refactored --cov-branch --cov-report=term-missing

# performance baseline (owner が具体 command を追記)
# legacy / refactored 同一 fixture 比較
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity \
	server/tests/integration/chat_service_contract/test_tool_results.py -k legacy
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity \
	server/tests/integration/chat_service_contract/test_tool_results.py -k "real and refactored"

# rollback subset continuity
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/
```

補足:
- branch 分類は `defensive branch` / `external dependency branch` / `unreachable by contract` / `follow-up required` のいずれかを使う。
- `follow-up required` には issue / PR / task を必須で記録する。

## Refactoring 対象ファイル Inventory（必須）

| file | coverage owner | target gate (unit/integration/not-applicable) | coverage result | 判定 | 根拠 | follow-up |
| --- | --- | --- | --- | --- | --- | --- |
| `server/src/aica_agent/services/chat_service_refactored.py` | sei.li@miidas.jp | integration branch 100% | `98%`（`--cov=services.chat_service_refactored --cov-branch`） | follow-up required | Phase 5 task-2 で residual tests は追加済みだが、retry/finalize 周辺の例外防御分岐が未到達。挙動同等性は `pre_extraction_parity` と critical scenario `pass` で担保。 | phase-5 feature-3 task-1 で final matrix gate 時に再評価（必要なら targeted test 追加）。 |
| `server/src/aica_agent/services/chat/stream_event_processor.py` | sei.li@miidas.jp | unit branch 100% | `100%`（Phase 4 feature-4 task-1 verification） | pass | 抽出時に unit branch 100% を達成済み。Phase 5 parity suite で回帰なし。 | なし |
| `server/src/aica_agent/services/chat/tool_event_handler.py` | sei.li@miidas.jp | unit branch 100% | `100%`（Phase 4 feature-4 task-2 verification） | pass | 抽出時 unit 100% を維持。Phase 5 task-2 で retry 連携の integration evidence を追加済み。 | なし |
| `server/src/aica_agent/services/chat/stream_guard.py` | sei.li@miidas.jp | unit branch 100% | `100%`（Phase 4 feature-4 task-3 verification） | pass | security/cancellation scenario の real-refactored evidence が `pass`。 | なし |
| `server/src/aica_agent/services/chat/workflow_chat_handler.py` | sei.li@miidas.jp | unit branch 100% | `100%`（Phase 4 feature-4 task-4 verification） | pass | workflow side effects の real-refactored evidence `pass`。 | なし |
| `server/src/aica_agent/services/chat/history_mapper.py` | sei.li@miidas.jp | unit branch 100% | `100%`（Phase 4 feature-2 task-2 verification） | pass | history mapping scenario を parity で維持。 | なし |
| `server/src/aica_agent/services/chat/conversation_state.py` | sei.li@miidas.jp | unit branch 100% | `100%`（Phase 4 feature-2 task-1 verification） | pass | state コンポーネントは抽出時 unit 100%。 | なし |
| `server/src/aica_agent/services/chat/chat_persistence.py` | sei.li@miidas.jp | unit branch 100% | `100%`（Phase 4 feature-3 task-1 verification） | pass | DB side effects scenario の parity evidence `pass`。 | なし |
| `server/src/aica_agent/services/chat/turn_preparer.py` | sei.li@miidas.jp | unit branch 100% | `100%`（Phase 4 feature-3 task-2 verification） | pass | turn preparation の抽出時 unit 100% を維持。 | なし |

ルール:
- `target gate` が `not-applicable` の行には、`根拠` と `follow-up` を必須で記入する。
- task 単位の一括 `not-applicable` は不可。必ずファイル単位で判定する。

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| pre_extraction_parity（coverage evidence） | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/ --cov=services.chat_service --cov-branch --cov-report=term-missing` | pass | legacy coverage evidence と required scenario 継続確認。 |
| pre_extraction_parity（coverage evidence） | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/ --cov=services.chat_service_refactored --cov-branch --cov-report=term-missing` | pass | refactored coverage evidence と required scenario 継続確認。 |
| rollback_summary | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/` | pass | `14 passed, 1468 deselected`。summary rollback subset 回帰なし。 |

## 失敗したテスト

| コマンド | 失敗概要 | 次の対応 |
| --- | --- | --- |
| なし | なし | なし |

## 未実行

| コマンド | 理由 |
| --- | --- |
| なし | なし |

## 免除

| コマンド | オーナー | 理由 | 日付 | フォローアップ |
| --- | --- | --- | --- | --- |
| なし | なし | なし | なし | なし |

## 既知分岐の再判定（Phase 4 task-3 からの引き継ぎ）

| branch | 現在分類 | 判定（解消 / waiver 継続 / 再ラベル） | 根拠 | owner | date | follow-up |
| --- | --- | --- | --- | --- | --- | --- |
| `server/src/aica_agent/services/chat_service.py:480-481` | defensive branch | waiver 継続 | `ForbiddenWordDetectedException` 以外の想定外 security 例外時のみ通る防御分岐。required scenario は forbidden-word 契約を `pass` しており、契約外異常系を release gate 必須にしない方針を維持。 | sei.li@miidas.jp | 2026-06-08 | phase-5 feature-3 task-1 で最終 matrix gate 時に再確認。 |
| `server/src/aica_agent/services/chat_service.py:991-1000` | defensive branch | 別分類へ再ラベル | `external dependency branch` へ再ラベル。最終 forbidden 検知は `LLMOutputGuard.finalize_stream()` の chunk 境界依存で発火し、外部依存（token/chunk 境界）条件が強い。security cleanup required scenario は `pass` のため契約上の必須条件は満たす。 | sei.li@miidas.jp | 2026-06-08 | finalize 境界条件の deterministic fixture 化を phase-5 feature-3 task-1 で検討。 |
| `server/src/aica_agent/services/chat_service.py:1031-1032` | defensive branch | waiver 継続 | 会話要約起動判定の post-turn side effect 失敗を握りつぶして対話継続する防御分岐。summary rollback scenario は `rollback_summary` で `pass`。契約上は END 応答継続が必須であり、例外ログ分岐到達は必須ではない。 | sei.li@miidas.jp | 2026-06-08 | phase-6 release readiness で observability（error budget/alert）観点の follow-up を記録。 |

## 未到達 branch 分類（今回コマンド結果）

| file/branch | 分類 | 残リスク | 対応 |
| --- | --- | --- | --- |
| `chat_service.py:667->976` | unreachable by contract | `async for` zero-yield 終端（暗黙 `StopAsyncIteration`）で coverage credit が付かない可能性。挙動回帰リスクは低い。 | 既知 residual として維持。final matrix gate で再確認。 |
| `chat_service_refactored.py:67->69`, `71->73` | defensive branch | `_json_default` の戻り値型が dict 以外になる型でのみ通る。通常 payload では発火しない。 | follow-up required（targeted unit 追加要否を feature-3 で判定）。 |
| `chat_service_refactored.py:758->801` | defensive branch | stream iteration がゼロ回で finally のみ実行される経路。運用影響は低い。 | follow-up required。stream fixture 追加余地を feature-3 で評価。 |
| `chat_service_refactored.py:824-826`, `833` | defensive branch | finalize 時 ERROR chunk 到達時の早期 return 分岐。security scenario は pass だが、この局所分岐は未到達。 | follow-up required。security finalize 専用 fixture 追加を検討。 |

## Performance baseline（同一 fixture）

- fixture: `server/tests/integration/chat_service_contract/test_tool_results.py`
- legacy command: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/integration/chat_service_contract/test_tool_results.py -k legacy`
- real-refactored command: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/integration/chat_service_contract/test_tool_results.py -k "real and refactored"`
- runs: 各 variant 15 回

| variant | avg | p50 | p95 | p99 |
| --- | --- | --- | --- | --- |
| legacy | 1.8594s | 1.8438s | 1.9512s | 2.0770s |
| real-refactored | 1.8379s | 1.8316s | 1.8730s | 1.8754s |

所見:
- 同一 fixture では real-refactored が legacy 比でわずかに低レイテンシ。
- 本計測は tool result contract subset のみで、全 chat path の負荷特性を代表しない。
- residual risk: 長文 streaming / retry 多発時の tail latency は別途計測が必要（phase-5 feature-3 で matrix gate と合わせて扱う）。

## 手動確認

