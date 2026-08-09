# 引き継ぎ: boundary foundation

## 概要

Phase 1 boundary foundation を完了。`agent_runtime` config を追加し、startup validation と endpoint の model 解決を config boundary に寄せた。`tests/integration/chat_service_contract/` に最小 scaffolding を追加し、default config compatibility を fixture-backed assertion で固定した。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/application.py` | startup 時に `validate_agent_runtime_config()` を呼ぶようにした。 |
| `server/src/aica_agent/endpoints.py` | concrete chat service import を削除し、protocol + injected config から agent model を解決するようにした。 |
| `server/src/aica_agent/config.yml` | `agent_runtime.service_variant` と `agent_runtime.agent_model` を追加した。 |
| `server/src/aica_agent/services/chat/agent_runtime_config.py` | agent runtime config の読み取り helper を追加した。 |
| `server/src/aica_agent/services/chat/config_validator.py` | startup validation を追加した。 |
| `server/src/aica_agent/services/chat/service_protocol.py` | endpoint が依存する public contract を Protocol として固定した。 |
| `server/src/aica_agent/services/chat_service.py` | `init_session(provider)` を `init_session(agent_model)` に整理した。 |
| `server/pyproject.toml` | Gate A pytest markers を登録した。 |
| `server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py` | Phase 1 contract harness を追加し、fixture-backed assertion を入れた。 |
| `server/tests/integration/chat_service_contract/fixtures/config_invalid_agent_model.yml` | startup config failure 用 fixture。 |
| `server/tests/integration/chat_service_contract/fixtures/default_config_compatibility.yml` | default config compatibility 用 fixture。 |
| `server/tests/integration/chat_service_contract/fixtures/endpoint_boundary.py` | endpoint protocol boundary 用 fixture。 |
| `server/plan/phases/gate_a_scenario_matrix.md` | startup config failure / default config compatibility / endpoint protocol boundary evidence を更新した。 |
| `server/plan/phases/status.md` | task status を完了状態へ更新した。 |
| `server/plan/phases/phase-1-endpoint-config-boundary/features/feature-1-agent-runtime-config-endpoint-contract/task-1-boundary-foundation/verification.md` | 実行結果を記録した。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `services.chat.agent_runtime_config.AgentRuntimeConfig`
- `services.chat.agent_runtime_config.get_service_variant()`
- `services.chat.agent_runtime_config.get_agent_model()`
- `services.chat.agent_runtime_config.resolve_default_agent_model()`
- `services.chat.config_validator.validate_agent_runtime_config()`
- `services.chat.service_protocol.ChatServiceProtocol`
- `tests/integration/chat_service_contract/fixtures/config_invalid_agent_model.yml`
- `tests/integration/chat_service_contract/fixtures/default_config_compatibility.yml`
- `tests/integration/chat_service_contract/fixtures/endpoint_boundary.py`

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| startup validation は module import ではなく `application.lifespan()` で実行する | invalid config を import time で落とさず、app startup で fail fast させるため。 | import 時に validate する案もあったが、起動不能時の診断が悪くなるので採用しなかった。 |
| endpoint は concrete service ではなく `ChatServiceProtocol` に依存する | Phase 1 で public contract を固定し、後続 phase の service switching を安全にするため。 | concrete `ChatService` を残したまま型だけ抽象化する案もあったが、boundary が弱かった。 |
| default config compatibility は fixture-backed assertion で固定する | 現行 production chat behavior contract と互換であることを、plan と test の両方で明示するため。 | inline assertion だけで済ませる案もあったが、fixture 由来の契約が見えなくなる。 |

## 互換性メモ

- default config では `agent_runtime.agent_model: openai/gpt-4.1` が解決される。
- `service_variant` は Phase 1 では `legacy` のみ有効。`refactored` は未実装エラーとして落ちる。
- `endpoints.py` は `services.chat_service` へ依存しない。

## 次タスクへのフォローアップ

- Phase 2 の DI lifecycle baseline は、`agent_runtime` config と startup validation を前提にしてよい。
- `service_variant: refactored` の valid 化はまだ行っていないので、次段階で `containers.py` 側の切替口を追加する必要がある。

## 未解決の質問

- なし

## 前提にしてはいけないこと

- `service_variant: refactored` が valid であること。
