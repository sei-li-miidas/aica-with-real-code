# 引き継ぎ: task-1-marker-membership-fixture-map

## 概要

task-1 では marker membership と fixture/test file map を実体化し、Phase 3 feature-2 の required scaffold を作成した。task-2 はこの scaffold に実 assertion を実装し、legacy/delegating evidence を matrix に記録する。
## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/plan/phases/phase-3-runner-contract-pre-extraction/features/feature-2-pre-extraction-parity/task-1-marker-membership-fixture-map/task.md` | task-1 scope と必須検証を具体化。 |
| `server/tests/integration/chat_service_contract/fixtures/history_mapping.json` | history mapping fixture scaffold。 |
| `server/tests/integration/chat_service_contract/fixtures/db_side_effects.json` | DB side effects fixture scaffold。 |
| `server/tests/integration/chat_service_contract/fixtures/tool_results.json` | tool result shape fixture scaffold。 |
| `server/tests/integration/chat_service_contract/fixtures/security_block.json` | security block fixture scaffold。 |
| `server/tests/integration/chat_service_contract/fixtures/workflow_side_effects.json` | workflow side effects fixture scaffold。 |
| `server/tests/integration/chat_service_contract/fixtures/summary_rollback.json` | summary rollback fixture scaffold。 |
| `server/tests/integration/chat_service_contract/fixtures/cancellation_cleanup.py` | cancellation cleanup fixture scaffold。 |
| `server/tests/integration/chat_service_contract/fixtures/no_legacy_dependency.py` | legacy dependency fixture scaffold。 |
| `server/tests/integration/chat_service_contract/fixtures/di_lifecycle.py` | DI lifecycle fixture scaffold (matrix整合用)。 |
| `server/tests/integration/chat_service_contract/test_history_mapping.py` | history mapping test scaffold (task-2 まで skip)。 |
| `server/tests/integration/chat_service_contract/test_db_side_effects.py` | DB side effects test scaffold (task-2 まで skip)。 |
| `server/tests/integration/chat_service_contract/test_tool_results.py` | tool results test scaffold (task-2 まで skip)。 |
| `server/tests/integration/chat_service_contract/test_security_cleanup.py` | security cleanup test scaffold (task-2 まで skip)。 |
| `server/tests/integration/chat_service_contract/test_workflow_side_effects.py` | workflow side effects test scaffold (task-2 まで skip)。 |
| `server/tests/integration/chat_service_contract/test_summary_rollback.py` | summary rollback test scaffold (task-2 まで skip)。 |
| `server/tests/integration/chat_service_contract/test_no_legacy_dependency.py` | real refactored proof scaffold (task-2/phase-4 まで skip)。 |
| `server/tests/integration/chat_service_contract/test_runner_contract.py` | pre_extraction_bootstrap / pre_extraction_parity marker 整合を調整。 |

## 補助資料（task spec 外）

- `MARKER_MEMBERSHIP_AND_FIXTURE_MAP.md` (新規作成): marker/scenario/fixture/test file の対応表。task spec には含まれないが、task-2 の実装ガイダンスとして作成。

## 新しいAPI / ヘルパー / フィクスチャ

- 新規 fixture scaffold: `history_mapping.json`, `db_side_effects.json`, `tool_results.json`, `security_block.json`, `workflow_side_effects.json`, `summary_rollback.json`, `cancellation_cleanup.py`, `no_legacy_dependency.py`, `di_lifecycle.py`。
- 新規 test scaffold: `test_history_mapping.py`, `test_db_side_effects.py`, `test_tool_results.py`, `test_security_cleanup.py`, `test_workflow_side_effects.py`, `test_summary_rollback.py`, `test_no_legacy_dependency.py`。
- いずれも task-2/phase-4 実装前提のため、module-level skip で false-green を防止。
- JSON fixtures に `_description` と `_expected_keys` メタデータを追加し、task-2 実装のガイダンスを強化。
## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| task-1 の検証を collect-only ベースにした | task-1 の目的は marker membership / fixture existence の確定であり、assertion 実装は task-2 scope。 | すべての scaffold test を実行 (`pytest -m ...`) する案。false-green になりやすいため不採用。 |
| scaffold tests に module-level skip を入れた | `pass` だけのテストを green にしないため。 | `xfail(strict=True)` 案。現時点の placeholder 実装では xpass/fail になり運用ノイズが大きいため不採用。 |
| `test_runner_contract.py` の bootstrap marker を実質証跡テストへ限定 | fixture 内容確認だけのテストを bootstrap evidence に数えないため。 | fixture-doc test へ bootstrap marker を残す案。不正確な証跡になるため不採用。 |

## 互換性メモ

- 既存 API/本番コードは未変更。変更は test/doc/scaffold のみ。
- pytest 実行ファイルを直接呼ぶ運用は shebang 依存になるため利用不可。task-2 以降は workspace root から `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest` を利用すること。

## 次タスクへのフォローアップ

- task-2 で skip 解除し、legacy/delegating characterization assertion を実装する。
- 各 JSON fixture の `_expected_keys` を参考に、fixture データ構造を設計・実装する。
- `verification.md` の collect-only 証跡を実行証跡 (`PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`) に置き換える。
- `server/plan/phases/gate_a_scenario_matrix.md` の legacy/delegating evidence を task-2 で更新する。

## 未解決の質問

- なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
