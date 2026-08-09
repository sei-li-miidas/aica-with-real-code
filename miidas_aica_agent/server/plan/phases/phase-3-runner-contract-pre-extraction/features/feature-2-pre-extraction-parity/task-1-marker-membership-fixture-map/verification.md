# 検証: task-1-marker-membership-fixture-map

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m pre_extraction_parity server/tests/integration/chat_service_contract` | pass | 60/71 tests collected, marker membership を確認。 |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_runner server/tests/integration/chat_service_contract` | pass | 27/74 tests collected。 |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m "rollback_endpoint_config or rollback_di or rollback_security or rollback_summary or pre_extraction_bootstrap" server/tests/integration/chat_service_contract` | pass | 47/74 tests collected。 |
| `ls server/tests/integration/chat_service_contract/fixtures` | pass | required fixture file existence を確認。 |
| JSON fixtures に `_description` と `_expected_keys` metadata を追加 | pass | task-2 のガイダンス強化。 |

結果値:
- `pass`
- `fail`
- `not-run`
- `waived`
- `not-applicable`

完了ルール:
- 必須コマンドに `fail` または `not-run` がある間は、タスクを `done` にできない。
- `waived` は、免除セクションにオーナー、理由、日付、フォローアップがある場合のみ許可する。
- `not-applicable` は、理由がある場合のみ許可する。

## 必須コマンド

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m pre_extraction_parity server/tests/integration/chat_service_contract`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_runner server/tests/integration/chat_service_contract`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m "rollback_endpoint_config or rollback_di or rollback_security or rollback_summary or pre_extraction_bootstrap" server/tests/integration/chat_service_contract`
- `ls server/tests/integration/chat_service_contract/fixtures`

補足:
- `.venv-server/bin/pytest` を直接呼ぶ場合は shebang が旧パスを指しており実行不能 (`bad interpreter`) になるため、`python -m pytest` 形式を使用する。
- task-1 は marker/fixture existence 検証タスクのため、`--collect-only` を正式証跡とする。

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| rollback_endpoint_config | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_endpoint_config server/tests/integration/chat_service_contract` | pass | collection 成功。 |
| rollback_di | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_di server/tests/integration/chat_service_contract` | pass | collection 成功。 |
| rollback_runner | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_runner server/tests/integration/chat_service_contract` | pass | collection 成功。 |
| rollback_security | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_security server/tests/integration/chat_service_contract` | pass | collection 成功。 |
| rollback_summary | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m rollback_summary server/tests/integration/chat_service_contract` | pass | collection 成功。 |
| pre_extraction_bootstrap | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m pre_extraction_bootstrap server/tests/integration/chat_service_contract` | pass | collection 成功。 |
| pre_extraction_parity | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest --collect-only -q -m pre_extraction_parity server/tests/integration/chat_service_contract` | pass | collection 成功。 |

## 失敗したテスト

| コマンド | 失敗概要 | 次の対応 |
| --- | --- | --- |
| 該当なし | - | - |

## 未実行

| コマンド | 理由 |
| --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/integration/chat_service_contract` | task-1 の必須検証は marker/fixture existence のため、collect-only で判定。実 assertion 実装は task-2 担当。 |

## 免除

| コマンド | オーナー | 理由 | 日付 | フォローアップ |
| --- | --- | --- | --- | --- |
| 該当なし | - | - | - | - |

## 手動確認

- `server/pyproject.toml` の marker 登録を確認 (`rollback_endpoint_config`, `rollback_di`, `rollback_runner`, `rollback_security`, `rollback_summary`, `pre_extraction_bootstrap`, `pre_extraction_parity`)。
- `server/tests/integration/chat_service_contract/fixtures/` に required fixtures が存在することを確認。
- `MARKER_MEMBERSHIP_AND_FIXTURE_MAP.md` と `server/plan/phases/gate_a_scenario_matrix.md` の対応をレビューで照合。
