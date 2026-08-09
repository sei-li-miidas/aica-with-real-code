# フィーチャー: Responses runner contract

## 目的

Responses style の Agent SDK stream を、legacy characterization と `LLMRunStream` contract で固定する。

## 親フェーズ

- フェーズ: phase-3-runner-contract-pre-extraction

## スコープ

スコープ内:
- legacy runner seam
- SDK-shaped event fixtures
- OpenAI Agent SDK version / pinning policy の記録
- `LLMRunner` / `LLMRunStream`
- `ResponsesAgentRunner`

スコープ外:
- Completions style
- refactored の独立 `chat()` 実装

## 依存関係

- Phase 2 service variant switch

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-legacy-runner-seam-and-fixtures | legacy seam と SDK-shaped fixtures を作る。 | Phase 2 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` | done |
| task-2-responses-runner-adapter | Responses adapter と normalized contract を固定する。 | task-1 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` | done |

## 完了条件

- SDK-shaped fixture から `LLMRunStream` への mapping がテストで固定されている。
- Responses compatibility field は adapter 内に閉じている。
- OpenAI Agent SDK の利用 version と pinning policy が handoff または `server/plan/architecture.md` に記録されている。
