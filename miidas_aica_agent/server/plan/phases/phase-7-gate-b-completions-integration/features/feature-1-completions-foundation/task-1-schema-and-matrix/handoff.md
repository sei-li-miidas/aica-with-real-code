# 引き継ぎ: schema and validity matrix

## 概要

task 実装完了後の引き継ぎ。

Gate B の入口として、`api_style` の default と validation matrix を固定した。`legacy + completions` は startup/config validation で fail fast し、`refactored + completions` は accepted される。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/config.yml` | `agent_runtime.api_style: responses` を明示して default を固定した。 |
| `server/src/aica_agent/services/chat/agent_runtime_config.py` | `api_style` 定数、getter、resolver、`AgentRuntimeConfig` 拡張を追加した。 |
| `server/src/aica_agent/services/chat/config_validator.py` | `service_variant` / `api_style` validity matrix を追加し、legacy + completions を拒否するようにした。 |
| `server/pyproject.toml` | `completions_runner_internal` / `completions_contract` / `rollback_api_style` marker を登録した。 |
| `server/tests/unit/services/chat/test_agent_runtime_config.py` | `api_style` default/resolution の unit test を追加した。 |
| `server/tests/unit/services/chat/test_config_validator.py` | matrix の accept/reject test を追加した。 |
| `server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py` | fixture と checked-in `config.yml` の両方で default / fail-fast を確認した。 |
| `server/tests/integration/chat_service_contract/fixtures/default_config_compatibility.yml` | `expected_default_api_style` を追加した。 |
| `server/tests/integration/chat_service_contract/fixtures/config_invalid_legacy_completions.yml` | invalid matrix fixture を追加した。 |

## 互換性メモ

- `responses` を default に固定し、`agent_runtime.api_style` を未指定でも既存の chat runtime contract と同じ結果になることを確認した。
- `legacy + completions` は `InvalidAgentRuntimeConfigError` で fail fast し、silent fallback しない。
- `refactored + completions` は Gate B matrix 上で accepted される。
- 影響した marker / contract test: `completions_contract`, `rollback_api_style`, `rollback_endpoint_config`。

## 次タスクへのフォローアップ

- 次 task は `api_style` を `responses | completions` の runtime choice として前提にできる。
- 次 task は `get_api_style()` / `resolve_default_api_style()` と `VALID_AGENT_RUNTIME_MATRIX` を再利用できる。
- 追加 fixture は不要。次 task では model resolver / secret injection の検証に進める。
- 次 task が参照できる marker は `completions_contract` と `rollback_api_style`。

## 未解決の質問

- なし。`api_style` の default と matrix はこの task で固定した。