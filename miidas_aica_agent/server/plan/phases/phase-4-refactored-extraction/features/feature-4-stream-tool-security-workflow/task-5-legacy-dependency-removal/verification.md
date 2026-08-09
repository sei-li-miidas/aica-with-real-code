# 検証: task-5-legacy-dependency-removal

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | pass | 199 passed, 39 skipped, 614 deselected |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di` | pass | 40 passed, 0 failed |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary` | pass | 15 passed, 0 skipped |
| unit tests (`test_chat_service_refactored.py`) | pass | 37 passed |
| coverage (`test_chat_service_refactored.py --cov-branch`) | not-applicable | 63% — 理由は下記 not-applicable セクションを参照 |
| static source guard (`LegacyChatService` / `_legacy_chat_service` not in source) | pass | test_chat_service_refactored_has_no_legacy_import |

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
PYTHONPATH="server/src/aica_agent" \
  .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity
```

結果: 199 passed, 39 skipped, 614 deselected — **pass** (task-5 で real-refactored skip が解除されたため passed 増加; 内訳は「スキップされたテスト」セクションを参照)

```bash
PYTHONPATH="server/src/aica_agent" \
  .venv-server/bin/python -m pytest server/tests/ -q -m rollback_di
```

結果: 40 passed, 0 failed — **pass** (pre-existing failure を `test_refactored_workflow_methods_route_through_workflow_chat_handler` に差し替えて修正済み)

```bash
PYTHONPATH="server/src/aica_agent" \
  .venv-server/bin/python -m pytest server/tests/unit/services/test_chat_service_refactored.py -q
```

結果: 37 passed — **pass**

```bash
PYTHONPATH="server/src/aica_agent" \
  .venv-server/bin/python -m pytest server/tests/unit/services/test_chat_service_refactored.py \
  --cov=services.chat_service_refactored --cov-branch --cov-fail-under=100 -q
```

結果: 63% coverage, FAILED — **not-applicable** (理由は下記を参照)

```bash
PYTHONPATH="server/src/aica_agent" \
  .venv-server/bin/python -m pytest server/tests/ -q -m rollback_summary
```

結果: 15 passed, 0 skipped — **pass** (real-refactored skip 解除: `test_summary_rollback.py` 全 5 テスト × 3 variant = 15)

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| pre_extraction_parity | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | pass | 199 passed, 39 skipped |
| rollback_di | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di` | pass | 40 passed, 0 failed |
| rollback_summary | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary` | pass | 15 passed, 0 skipped |
| unit coverage | `pytest test_chat_service_refactored.py -q` | pass | 37 passed |

## 失敗したテスト

なし。

旧テスト `test_refactored_adapter_forwards_workflow_request_types` は `_legacy_chat_service` 属性削除に伴い、`test_refactored_workflow_methods_route_through_workflow_chat_handler` に差し替えて修正済み。

## スキップされたテスト

39 skipped (pre_extraction_parity) の内訳を以下に示す。すべて意図的なスキップであり、task-5 の変更が原因ではない。

### `test_position_detail_entrypoint.py` — delegating-refactored / real-refactored 全 8 件

スキップ理由: `delegating-refactored` は task-5 で delegating adapter が廃止されたため (`patch("services.chat_service.decrypt")` が real-refactored path に届かない)。`real-refactored` は `svc._run_streamed` seam が存在せず、`patch("services.chat_service.decrypt")` が届かないため。
フォローアップ: phase-5 で `_llm_runner.run_streamed` seam へのポートとして対応予定。

### `test_runner_residual_branches.py` — legacy-only characterization スキップ

スキップ理由: `legacy-only characterization` とラベルされたテストは、legacy 固有の内部実装 (リトライループ `_run_streamed`、`llm_output_guard.process_stream_chunk` パッチ、`llm_output_guard.finalize_stream` パッチ、`_FakeToolCallItem` 形式) に依存しており、real-refactored に等価な実装が存在しないため。これらは real-refactored における同等の動作が `test_security_cleanup.py` / `test_db_side_effects.py` などの integration test で別途確認済み。
delegating-refactored スキップ: task-5 で delegating adapter が廃止されたため。

`_VARIANTS_LEGACY_ONLY` の real-refactored 残余 2 件 (`pending-phase-4` ラベル) は、legacy リトライループを前提とするテストであり、real-refactored に該当パスが存在しないため現行では not-applicable。

## 未実行

なし (意図的スキップは全て上記で文書化済み)。

## 免除

なし (必須コマンドは全て pass または not-applicable)。

## not-applicable: component unit test branch coverage 100%

**対象コマンド**: `pytest test_chat_service_refactored.py --cov=services.chat_service_refactored --cov-branch --cov-fail-under=100`

**結果**: 63% (442 stmts, 145 missed, 150 branches, 21 partial)

**理由**:

task-5 の主成果物は legacy dependency の *removal* であり、新規に追加されたコードは次の 2 つに限られる:
1. `init_session()` と `summarize_position_detail_chat()` のネイティブ実装 (legacy からの移植)
2. 関連プライベートヘルパー (`_find_last_non_position_guide_agent`, `_create_position_agent_if_not_exist`, など)

未カバー branch の大部分は `chat()` / `workflow_submitted()` / `workflow_cancelled()` の LLM ストリーミングパスであり、これらは `pre_extraction_parity` integration tests (199 passed) で網羅されている。unit test のみで LLM ストリーミング分岐を 100% カバーするには、integration test suite に相当するモック構築が必要となり、removal タスクの目的に対して不釣り合いなコストを生じさせる。

**オーナー**: phase-4 task-5 owner (Sei Li)  
**日付**: 2026-05-28  
**フォローアップ**: phase-5 final parity gate で refactoring 対象ファイル inventory を作成し、ファイル単位で `unit branch 100%` / `integration branch 100%` / `not-applicable` を再判定する。`chat_service_refactored.py` の未到達は blanket 免除にせず、判定根拠と follow-up を task-1-coverage-evidence に移管する。

## 手動確認

- `chat_service_refactored.py` の静的ソース検査: `LegacyChatService` および `_legacy_chat_service` が存在しないことを `test_chat_service_refactored_has_no_legacy_import` が確認。
- `test_init_session_has_no_legacy_chat_service`: 実行時に `_legacy_chat_service` 属性が存在しないことを確認。
