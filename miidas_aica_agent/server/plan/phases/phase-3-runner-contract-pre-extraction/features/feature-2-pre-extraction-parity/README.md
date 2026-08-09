# フィーチャー: pre-extraction parity

## 目的

Phase 4 の責務抽出前に、legacy/delegating evidence、marker membership、test migration map を characterization として固定する。

この feature の pass は final refactored parity を意味しない。`real-refactored evidence` は Phase 4/5 の owner が埋める。

## 親フェーズ

- フェーズ: phase-3-runner-contract-pre-extraction

## スコープ

スコープ内:
- marker membership table
- required fixture / test file existence
- legacy/delegating characterization
- affected private test migration map

スコープ外:
- real-refactored evidence の作成
- component extraction
- release confidence の判定

## 依存関係

- feature-1-responses-runner-contract

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-marker-membership-fixture-map | marker membership と fixture map を実体化する。 | runner contract | marker / fixture existence | done |
| task-2-legacy-delegating-characterization | legacy/delegating evidence を required scenario へ記録する。 | task-1 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | done |
| task-3-test-migration-map | private tests の移行先を固定する。 | task-2 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | done |

## 完了条件

- `gate_a_scenario_matrix.md` の legacy/delegating evidence が Phase 3 owner 分すべて埋まっている。
- `real-refactored evidence` は `pending-phase-4` と明記されている。
