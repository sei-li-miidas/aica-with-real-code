# フィーチャー: completions foundation

## 目的

`agent_runtime.api_style` の導入、モデル解決、Completions runner の土台を追加する。

## スコープ

スコープ内:
- config schema と validity matrix の追加
- model string boundary の明示
- `CompletionsRunStream` / `CompletionsAgentRunner` の追加
- OpenAI Agents SDK の `LiteLLM` adapter 依存関係の明示

スコープ外:
- DI コンテナの全面的な wiring / factory 差し替え
- history/persistence の completions 対応
- parity / rollback suite

補足:
- `DI wiring` はスコープ外とするが、既存の依存解決ポイントに対する最小限の登録・参照追加は許可する。ここでいう最小限の登録とは、`llm_runner.py` が必要とする adapter を既存 factory / provider 経由で受け渡せるようにする範囲に限る。
- レビュー時は、DI コンテナの構造変更、他の provider への波及、endpoint / history / persistence への責務追加があればスコープ逸脱と判定する。

## 開始条件

- Gate A が完了している。
- `service_variant` の legacy/refactored 切替が利用可能である。

## 終了条件

- `legacy + completions` が startup/config validation で拒否される。
- completions モードのモデル解決が config / env から安全に行える。
- 少なくとも 1 つの provider backend（Claude または Bedrock のいずれか）が `LiteLLM` adapter 経由で verified である。検証に失敗した backend は対象外とする。
- runner internal invariants の検証方針が固定される。

## 検証方針

- 失敗した provider backend は対象外とし、設定 validation で拒否する。自動フォールバックは行わない。
- `verified` は、Claude / Bedrock 向け provider backend について、(1) adapter 経由での疎通、(2) tool calling、(3) structured outputs、(4) usage reporting が必要条件を満たした状態を指す。
- CI では `completions_runner_internal` を中心とした統合寄りテストで、adapter 経由の疎通と runner 内部契約を確認する。
- staging / canary では runtime smoke と healthcheck で実際の provider backend に対する動作確認を行い、tool calling / structured outputs / usage reporting の実動作を確認する。
- manual verification は新しい backend を採用する最終承認時のみ使い、通常の回帰判定には使わない。

## フィーチャー内タスク

| タスク | 目的 | 依存関係 | ステータス |
| --- | --- | --- | --- |
| task-1-schema-and-matrix | config schema と validity matrix を固定する。 | なし | not-started |
| task-3-llm-runner | completions runner / stream を追加する。 | task-1-schema-and-matrix | not-started |

## 必須検証

- `OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_runner_internal server/tests/`
- `server/pyproject.toml` の marker 登録確認
- `server/src/aica_agent/config.yml` の `api_style` validity matrix 確認

## メモ

- Secret はコードや config に平文で置かず、環境変数または secret manager から注入する。