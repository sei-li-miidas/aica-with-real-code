# test migration map

## 目的

Phase 4 の責務抽出で、legacy `ChatService` の private method / private test をどの component test または contract test へ移すかを固定する。

## 記入ルール

- Phase 3 task-3 完了時点で、affected private test をすべて分類する。
- Phase 4 の各 extraction task は、着手時にこの表を読み、自 task の行を `in-progress` に更新する。
- 移行先が contract test の場合、`gate_a_scenario_matrix.md` の scenario 名を `Scenario` に記録する。
- 移行しない場合は `Migration target` に `not-migrated` と書き、`Rationale` に理由を記録する。

## migration map

| Legacy private method | Legacy test file | Migration target | Scenario | Owner task | Required marker | Rationale | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `_convert_to_llm_messages` | `tests/unit/services/test_chat_service.py` | `tests/integration/chat_service_contract/test_history_mapping.py` | history mapping | phase-4 state/history / task-2-history-mapper | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` | Agent input / previous-history payload shape は public contract で固定する。 | planned |
| `_handle_security_detection` | `tests/unit/services/test_chat_service.py` | `tests/integration/chat_service_contract/test_security_cleanup.py` | security block cleanup | phase-4 stream/security / task-3-stream-guard-security | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security` | block session と cleanup side effect は observable behavior として固定する。 | planned |

## 完了条件

- `planned` 行は Phase 3 task-3 owner が実 repo の private tests に合わせて精査し、必要に応じて更新する。
- `Status` は `planned`, `in-progress`, `migrated`, `not-migrated` のいずれかにする。
