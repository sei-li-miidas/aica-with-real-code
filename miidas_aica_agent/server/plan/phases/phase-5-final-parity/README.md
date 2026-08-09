# フェーズ: 最終 parity suite の完成

## 目的

legacy と独立 refactored 実装の外部挙動同等性を、同一 fixture の contract suite と `gate_a_scenario_matrix.md` で定義した named behavioral invariants で確認する。

## スコープ

スコープ内:
- 最終 parity scenario suite
- `gate_a_scenario_matrix.md` で定義した named behavioral invariants
- branch coverage evidence
- legacy 未到達行の棚卸し
- legacy dependency 再導入の static check / unit test

スコープ外:
- coverage 数値だけを gate にすること
- Gate B の Completions style

## 開始条件

- Phase 4 の責務移植が完了している。
- refactored 実装が main chat path で legacy へ委譲していない。

## 終了条件

- legacy/refactored の contract tests が同一 fixture で pass している。
- `gate_a_scenario_matrix.md` で定義した named behavioral invariants がテストで固定されている。
- coverage 未達箇所に理由と残リスクが記録されている。
- `server/plan/phases/gate_a_scenario_matrix.md` の required scenario すべてで final evidence が揃っている。
- critical scenario はすべて `pass` である。critical scenario が `waived` / `not-applicable` / `not-run` / `fail` の場合、Phase 5 は `blocked` のままにする。
- final parity evidence は `legacy` と `real-refactored` の 2 系統で判定する。
- refactoring で導入・再構成したファイルを inventory 化し、各ファイルごとに coverage 判定責務（unit 100% / integration 100% / not-applicable）を owner が明示する。
- `not-applicable` は blanket で許可しない。ファイル単位で理由、owner、日付、follow-up を必須とする。

## フィーチャー

| フィーチャー | 目的 | 依存関係 | ステータス |
| --- | --- | --- | --- |
| feature-1-final-parity-scenarios | final contract scenario suite を完成させる。 | Phase 4 | not-started |
| feature-2-coverage-risk-evidence | coverage evidence と未到達リスク棚卸しを揃える。 | feature-1 | not-started |
| feature-3-final-matrix-gate | matrix final evidence と release gate を固定する。 | feature-2 | not-started |

## タスク分割

| フィーチャー | タスク | 目的 | 必須検証 |
| --- | --- | --- | --- |
| feature-1-final-parity-scenarios | task-1-final-contract-suite | marker membership table の全 scenario を final contract suite として通す。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary` |
| feature-1-final-parity-scenarios | task-2-critical-scenario-evidence | critical scenario がすべて `pass` であることを固定する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` |
| feature-2-coverage-risk-evidence | task-1-coverage-evidence | legacy/refactored の branch coverage と未到達理由を記録する。 | coverage commands |
| feature-3-final-matrix-gate | task-1-final-matrix-gate | `gate_a_scenario_matrix.md` の final evidence を release-ready にする。 | matrix final evidence |

## 必須検証

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q --cov=server/src/aica_agent/services/chat_service.py --cov-branch server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q --cov=server/src/aica_agent/services/chat_service_refactored.py --cov-branch server/tests/`
- `server/plan/phases/gate_a_scenario_matrix.md` の required scenario final evidence 更新

## メモ

- coverage は補助 evidence として扱う。
- ただし「補助 evidence」であっても、refactoring で導入・再構成したファイルの coverage 責務を未定義のまま残してはいけない。
