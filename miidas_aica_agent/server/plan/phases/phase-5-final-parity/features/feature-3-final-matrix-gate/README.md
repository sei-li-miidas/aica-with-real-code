# フィーチャー: final matrix gate

## 目的

`gate_a_scenario_matrix.md` の final evidence を release-ready にし、Phase 6 が参照できる状態にする。

## 親フェーズ

- フェーズ: phase-5-final-parity

## スコープ

スコープ内:
- final evidence 更新
- critical pass 確認
- legacy dependency reintroduction check

スコープ外:
- release notes
- operational rollback procedure

## 依存関係

- feature-2-coverage-risk-evidence

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-final-matrix-gate | final evidence と release gate を固定する。 | coverage/risk evidence | matrix final evidence | not-started |

## 完了条件

- required scenario すべての final evidence が揃っている。
- critical scenario が `pass` でない場合、Phase 5 を `blocked` にする。
