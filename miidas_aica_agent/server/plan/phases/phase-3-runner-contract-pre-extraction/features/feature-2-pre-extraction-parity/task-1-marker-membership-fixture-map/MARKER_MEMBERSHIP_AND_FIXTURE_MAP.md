# マーカー メンバーシップ テーブルと フィクスチャ マップ

## 目的

task-1 で生成される marker membership table と fixture/test file map。
`gate_a_scenario_matrix.md` で定義された各 marker が coverage すべき scenario、fixture、test file の対応関係を実体化する。

## 生成日

2026-05-12

## マーカー メンバーシップ テーブル

各 marker がカバーするシナリオ、テストファイル、フィクスチャの一覧。

### rollback_endpoint_config

**目的**: endpoint/config 境界の startup 検証と backward compatibility。

| シナリオ | テストファイル | フィクスチャパス | ステータス |
| --- | --- | --- | --- |
| startup config failure | `server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py` | `server/tests/integration/chat_service_contract/fixtures/config_invalid_agent_model.yml` | fixture exists |
| default config compatibility | `server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py` | `server/tests/integration/chat_service_contract/fixtures/default_config_compatibility.yml` | fixture exists |
| endpoint protocol boundary | `server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py` | `server/tests/integration/chat_service_contract/fixtures/endpoint_boundary.py` | fixture exists |

**必須コマンド**: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_endpoint_config server/tests/integration/chat_service_contract`

**マーカー登録**: `server/pyproject.toml` に `rollback_endpoint_config` が登録されていること。

---

### rollback_di

**目的**: DI lifecycle と history mapping の legacy/delegating characterization。

| シナリオ | テストファイル | フィクスチャパス | ステータス |
| --- | --- | --- | --- |
| DI lifecycle | `server/tests/integration/chat_service_contract/test_di_lifecycle.py` | `server/tests/integration/chat_service_contract/fixtures/di_lifecycle.py` | fixture exists |
| history mapping | `server/tests/integration/chat_service_contract/test_history_mapping.py` | `server/tests/integration/chat_service_contract/fixtures/history_mapping.json` | fixture exists |

**必須コマンド**: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_di server/tests/integration/chat_service_contract`

**マーカー登録**: `server/pyproject.toml` に `rollback_di` が登録されていること。

---

### rollback_runner

**目的**: Responses runner event normalization と tool replay、usage propagation の characterization。

| シナリオ | テストファイル | フィクスチャパス | ステータス |
| --- | --- | --- | --- |
| runner event normalization | `server/tests/integration/chat_service_contract/test_runner_contract.py` | `server/tests/integration/chat_service_contract/fixtures/sdk_stream_events.py` | fixture exists |
| stop-at-tool replay | `server/tests/integration/chat_service_contract/test_runner_contract.py` | `server/tests/integration/chat_service_contract/fixtures/stop_at_tool_replay.json` | fixture exists |
| usage propagation | `server/tests/integration/chat_service_contract/test_runner_contract.py` | `server/tests/integration/chat_service_contract/fixtures/usage_response.json` | fixture exists |
| DB side effects | `server/tests/integration/chat_service_contract/test_db_side_effects.py` | `server/tests/integration/chat_service_contract/fixtures/db_side_effects.json` | fixture exists |
| tool result response shape | `server/tests/integration/chat_service_contract/test_tool_results.py` | `server/tests/integration/chat_service_contract/fixtures/tool_results.json` | fixture exists |

**必須コマンド**: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_runner server/tests/integration/chat_service_contract`

**マーカー登録**: `server/pyproject.toml` に `rollback_runner` が登録されていること。

---

### rollback_security

**目的**: Security block cleanup、cancellation cleanup、workflow side effects の legacy/delegating characterization。

| シナリオ | テストファイル | フィクスチャパス | ステータス |
| --- | --- | --- | --- |
| security block cleanup | `server/tests/integration/chat_service_contract/test_security_cleanup.py` | `server/tests/integration/chat_service_contract/fixtures/security_block.json` | fixture exists |
| cancellation cleanup | `server/tests/integration/chat_service_contract/test_security_cleanup.py` | `server/tests/integration/chat_service_contract/fixtures/cancellation_cleanup.py` | fixture exists |
| workflow side effects | `server/tests/integration/chat_service_contract/test_workflow_side_effects.py` | `server/tests/integration/chat_service_contract/fixtures/workflow_side_effects.json` | fixture exists |

**必須コマンド**: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_security server/tests/integration/chat_service_contract`

**マーカー登録**: `server/pyproject.toml` に `rollback_security` が登録されていること。

---

### rollback_summary

**目的**: Summary rollback の legacy/delegating characterization。

| シナリオ | テストファイル | フィクスチャパス | ステータス |
| --- | --- | --- | --- |
| summary rollback | `server/tests/integration/chat_service_contract/test_summary_rollback.py` | `server/tests/integration/chat_service_contract/fixtures/summary_rollback.json` | fixture exists |

**必須コマンド**: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_summary server/tests/integration/chat_service_contract`

**マーカー登録**: `server/pyproject.toml` に `rollback_summary` が登録されていること。

---

### pre_extraction_bootstrap

**目的**: Phase 4 bootstrap で real-refactored execution を証明するシナリオ。

| シナリオ | テストファイル | フィクスチャパス | ステータス |
| --- | --- | --- | --- |
| runner event normalization | `server/tests/integration/chat_service_contract/test_runner_contract.py` | `server/tests/integration/chat_service_contract/fixtures/sdk_stream_events.py` | fixture exists |
| stop-at-tool replay | `server/tests/integration/chat_service_contract/test_runner_contract.py` | `server/tests/integration/chat_service_contract/fixtures/stop_at_tool_replay.json` | fixture exists |
| usage propagation | `server/tests/integration/chat_service_contract/test_runner_contract.py` | `server/tests/integration/chat_service_contract/fixtures/usage_response.json` | fixture exists |
| legacy dependency reintroduction | `server/tests/integration/chat_service_contract/test_no_legacy_dependency.py` | `server/tests/integration/chat_service_contract/fixtures/no_legacy_dependency.py` | fixture exists |

**必須コマンド**: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m pre_extraction_bootstrap server/tests/integration/chat_service_contract`

**マーカー登録**: `server/pyproject.toml` に `pre_extraction_bootstrap` が登録されていること。

---

### pre_extraction_parity

**目的**: Phase 3 完了時に legacy/delegating characterization がすべて埋まっていることを証明する全体マーカー。

**必須シナリオ** (gate_a_scenario_matrix.md の marker 対応表参照):
- startup config failure
- default config compatibility
- endpoint protocol boundary
- DI lifecycle
- runner event normalization
- stop-at-tool replay
- usage propagation
- history mapping
- DB side effects
- tool result response shape
- security block cleanup
- cancellation cleanup
- workflow side effects
- summary rollback
- legacy dependency reintroduction

| シナリオ | テストファイル | フィクスチャパス |
| --- | --- | --- |
| startup config failure | `server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py` | `server/tests/integration/chat_service_contract/fixtures/config_invalid_agent_model.yml` |
| default config compatibility | `server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py` | `server/tests/integration/chat_service_contract/fixtures/default_config_compatibility.yml` |
| endpoint protocol boundary | `server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py` | `server/tests/integration/chat_service_contract/fixtures/endpoint_boundary.py` |
| DI lifecycle | `server/tests/integration/chat_service_contract/test_di_lifecycle.py` | `server/tests/integration/chat_service_contract/fixtures/di_lifecycle.py` |
| runner event normalization | `server/tests/integration/chat_service_contract/test_runner_contract.py` | `server/tests/integration/chat_service_contract/fixtures/sdk_stream_events.py` |
| stop-at-tool replay | `server/tests/integration/chat_service_contract/test_runner_contract.py` | `server/tests/integration/chat_service_contract/fixtures/stop_at_tool_replay.json` |
| usage propagation | `server/tests/integration/chat_service_contract/test_runner_contract.py` | `server/tests/integration/chat_service_contract/fixtures/usage_response.json` |
| history mapping | `server/tests/integration/chat_service_contract/test_history_mapping.py` | `server/tests/integration/chat_service_contract/fixtures/history_mapping.json` |
| DB side effects | `server/tests/integration/chat_service_contract/test_db_side_effects.py` | `server/tests/integration/chat_service_contract/fixtures/db_side_effects.json` |
| tool result response shape | `server/tests/integration/chat_service_contract/test_tool_results.py` | `server/tests/integration/chat_service_contract/fixtures/tool_results.json` |
| security block cleanup | `server/tests/integration/chat_service_contract/test_security_cleanup.py` | `server/tests/integration/chat_service_contract/fixtures/security_block.json` |
| cancellation cleanup | `server/tests/integration/chat_service_contract/test_security_cleanup.py` | `server/tests/integration/chat_service_contract/fixtures/cancellation_cleanup.py` |
| workflow side effects | `server/tests/integration/chat_service_contract/test_workflow_side_effects.py` | `server/tests/integration/chat_service_contract/fixtures/workflow_side_effects.json` |
| summary rollback | `server/tests/integration/chat_service_contract/test_summary_rollback.py` | `server/tests/integration/chat_service_contract/fixtures/summary_rollback.json` |
| legacy dependency reintroduction | `server/tests/integration/chat_service_contract/test_no_legacy_dependency.py` | `server/tests/integration/chat_service_contract/fixtures/no_legacy_dependency.py` |

**必須コマンド**: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m pre_extraction_parity server/tests/integration/chat_service_contract`

**マーカー登録**: `server/pyproject.toml` に `pre_extraction_parity` が登録されていること。

---

## フィクスチャ / テストファイル マップ

以下が task-1 で検証・実体化する必須フィクスチャとテストファイルの全リスト。

### Phase 1-owned fixtures (already exist from Phase 1 completion)

| フィクスチャ | パス | 必須マーカー | 説明 |
| --- | --- | --- | --- |
| config_invalid_agent_model.yml | `server/tests/integration/chat_service_contract/fixtures/config_invalid_agent_model.yml` | rollback_endpoint_config, pre_extraction_parity | invalid agent model で startup が失敗することを証明 |
| default_config_compatibility.yml | `server/tests/integration/chat_service_contract/fixtures/default_config_compatibility.yml` | rollback_endpoint_config, pre_extraction_parity | default config が現行 production と互換であることを証明 |
| endpoint_boundary.py | `server/tests/integration/chat_service_contract/fixtures/endpoint_boundary.py` | rollback_endpoint_config, pre_extraction_parity | endpoint が concrete service を import しないことを証明 |
| test_endpoint_config_boundary.py | `server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py` | rollback_endpoint_config, pre_extraction_parity | endpoint config boundary tests |

### Phase 2-owned fixtures (already exist from Phase 2 completion)

| フィクスチャ | パス | 必須マーカー | 説明 |
| --- | --- | --- | --- |
| di_lifecycle.py | `server/tests/integration/chat_service_contract/fixtures/di_lifecycle.py` | rollback_di, pre_extraction_parity | Container.chat_svc factory が session ごとに fresh instance を返すことを証明 |
| test_di_lifecycle.py | `server/tests/integration/chat_service_contract/test_di_lifecycle.py` | rollback_di, pre_extraction_parity | DI lifecycle tests |

### Phase 3-owned fixtures (from Phase 1 task-2 of feature-1-responses-runner-contract)

| フィクスチャ | パス | 必須マーカー | 説明 |
| --- | --- | --- | --- |
| sdk_stream_events.py | `server/tests/integration/chat_service_contract/fixtures/sdk_stream_events.py` | rollback_runner, pre_extraction_bootstrap, pre_extraction_parity | SDK-shaped Responses events fixture |
| test_runner_contract.py | `server/tests/integration/chat_service_contract/test_runner_contract.py` | rollback_runner, pre_extraction_bootstrap, pre_extraction_parity | Responses runner contract tests |

### Phase 3 pre-extraction-parity (task-1-marker-membership-fixture-map scope)

| フィクスチャ | パス | 必須マーカー | 説明 |
| --- | --- | --- | --- |
| stop_at_tool_replay.json | `server/tests/integration/chat_service_contract/fixtures/stop_at_tool_replay.json` | rollback_runner, pre_extraction_bootstrap, pre_extraction_parity | Tool replay fixture (legacy characterization) |
| usage_response.json | `server/tests/integration/chat_service_contract/fixtures/usage_response.json` | rollback_runner, pre_extraction_bootstrap, pre_extraction_parity | Usage propagation fixture (legacy characterization) |
| history_mapping.json | `server/tests/integration/chat_service_contract/fixtures/history_mapping.json` | rollback_di, pre_extraction_parity | History mapping fixture (legacy characterization) |
| db_side_effects.json | `server/tests/integration/chat_service_contract/fixtures/db_side_effects.json` | rollback_runner, pre_extraction_parity | DB side effects fixture (legacy characterization) |
| tool_results.json | `server/tests/integration/chat_service_contract/fixtures/tool_results.json` | rollback_runner, pre_extraction_parity | Tool result response shape fixture (legacy characterization) |
| security_block.json | `server/tests/integration/chat_service_contract/fixtures/security_block.json` | rollback_security, pre_extraction_parity | Security block cleanup fixture (legacy characterization) |
| cancellation_cleanup.py | `server/tests/integration/chat_service_contract/fixtures/cancellation_cleanup.py` | rollback_security, pre_extraction_parity | Cancellation cleanup fixture (legacy characterization) |
| workflow_side_effects.json | `server/tests/integration/chat_service_contract/fixtures/workflow_side_effects.json` | rollback_security, pre_extraction_parity | Workflow side effects fixture (legacy characterization) |
| summary_rollback.json | `server/tests/integration/chat_service_contract/fixtures/summary_rollback.json` | rollback_summary, pre_extraction_parity | Summary rollback fixture (legacy characterization) |
| no_legacy_dependency.py | `server/tests/integration/chat_service_contract/fixtures/no_legacy_dependency.py` | pre_extraction_bootstrap, pre_extraction_parity | Real refactored execution proof (legacy dependency reintroduction) |
| test_history_mapping.py | `server/tests/integration/chat_service_contract/test_history_mapping.py` | rollback_di, pre_extraction_parity | History mapping tests |
| test_db_side_effects.py | `server/tests/integration/chat_service_contract/test_db_side_effects.py` | rollback_runner, pre_extraction_parity | DB side effects tests |
| test_tool_results.py | `server/tests/integration/chat_service_contract/test_tool_results.py` | rollback_runner, pre_extraction_parity | Tool result response shape tests |
| test_security_cleanup.py | `server/tests/integration/chat_service_contract/test_security_cleanup.py` | rollback_security, pre_extraction_parity | Security cleanup tests |
| test_workflow_side_effects.py | `server/tests/integration/chat_service_contract/test_workflow_side_effects.py` | rollback_security, pre_extraction_parity | Workflow side effects tests |
| test_summary_rollback.py | `server/tests/integration/chat_service_contract/test_summary_rollback.py` | rollback_summary, pre_extraction_parity | Summary rollback tests |
| test_no_legacy_dependency.py | `server/tests/integration/chat_service_contract/test_no_legacy_dependency.py` | pre_extraction_bootstrap, pre_extraction_parity | Real refactored execution tests (legacy dependency reintroduction) |

---

## 検証チェックリスト

Task-1 の完了条件:

- [x] すべてのマーカー (`rollback_endpoint_config`, `rollback_di`, `rollback_runner`, `rollback_security`, `rollback_summary`, `pre_extraction_bootstrap`, `pre_extraction_parity`) が `server/pyproject.toml` に登録されている。
- [x] すべての必須フィクスチャが存在し、正しいパスに配置されている。
- [x] すべての必須テストファイルが存在し、正しいマーカー デコレータを持っている。
- [x] `gate_a_scenario_matrix.md` の marker 対応表と fixture パス が、このファイル内の mapping と一致している。
- [x] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_endpoint_config server/tests/integration/chat_service_contract` が実行可能。
- [x] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_di server/tests/integration/chat_service_contract` が実行可能。
- [x] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_runner server/tests/integration/chat_service_contract` が実行可能。
- [x] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_security server/tests/integration/chat_service_contract` が実行可能。
- [x] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_summary server/tests/integration/chat_service_contract` が実行可能。
- [x] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m pre_extraction_bootstrap server/tests/integration/chat_service_contract` が実行可能。
- [x] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m pre_extraction_parity server/tests/integration/chat_service_contract` が実行可能（Phase 3 pre-extraction-parity 完了前は partial pass 許可）。

---

## 実装メモ

- task-1 は fixtures / test file の存在確認と marker membership を実体化するタスク。
- 実装内容（legacy characterization evidence）は task-2 (legacy-delegating-characterization) の責任。
- Phase 1 / Phase 2 の fixtures はすでに存在し、task-1 では検証のみ。
- Phase 3 feature-1 (responses-runner-contract) の fixtures / test files がすでに存在し、task-1 では検証のみ。
- task-1 が新規作成する fixtures / test files は、Phase 3 pre-extraction-parity owned scenario の最小 scaffold。
- 最小 scaffold は `pytest -q -m <marker>` で `not-run` から出られる程度のテストファイル / fixture が必須。
- Phase 3 task-2 (legacy-delegating-characterization) で該当 fixture / test の内容を具体化する。
