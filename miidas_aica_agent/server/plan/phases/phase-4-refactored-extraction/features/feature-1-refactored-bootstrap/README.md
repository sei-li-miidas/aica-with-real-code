# フィーチャー: refactored bootstrap

## 目的

main `chat()` path で legacy 委譲しない薄い real refactored shell を作り、real runner path 到達を behavioral proof で示す。

## 親フェーズ

- フェーズ: phase-4-refactored-extraction

## スコープ

スコープ内:
- thin real shell
- `pre_extraction_bootstrap`
- behavioral real-refactored execution proof
- runner contract レベルで `stop-at-tool replay` / usage propagation が通る最低限の real implementation
- `gate_a_scenario_matrix.md` の bootstrap 対象 real evidence

スコープ外:
- DB side effects 移植
- full tool handling / tool result response shape 移植
- security/workflow 移植

## 依存関係

- Phase 3 pre-extraction parity

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-real-refactored-shell | thin shell と runner boundary 接続を作る。 | Phase 3 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap` | done |
| task-2-bootstrap-behavioral-proof | delegating adapter 復元時に fail する behavioral proof を追加する。 | task-1 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap` | done |

## 完了条件

- bootstrap 対象 scenario の real-refactored evidence が `pass` である。
- static check だけではなく behavioral proof がある。
