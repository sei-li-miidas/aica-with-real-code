# フィーチャー: final parity scenarios

## 目的

marker membership table の全 scenario を legacy/refactored 同一 fixture で最終確認する。

## 親フェーズ

- フェーズ: phase-5-final-parity

## スコープ

スコープ内:
- final contract suite
- critical scenario evidence
- summary rollback evidence

スコープ外:
- coverage 棚卸し

## 依存関係

- Phase 4 完了

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-final-contract-suite | 全 scenario の final contract suite を通す。 | Phase 4 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary` | done |
| task-2-critical-scenario-evidence | critical scenario がすべて `pass` であることを固定する。 | task-1 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | done |

## 完了条件

- critical scenario がすべて `pass` である。
- delegating evidence を final parity evidence として数えない。
