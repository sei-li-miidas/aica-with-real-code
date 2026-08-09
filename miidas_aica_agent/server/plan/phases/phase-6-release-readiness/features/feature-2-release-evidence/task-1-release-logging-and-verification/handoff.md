# 引き継ぎ: task-1-release-logging-and-verification

## 概要

Phase 6 feature-2 task-1 として、startup/chat turn logging evidence と RC verification checklist を更新した。

実施内容:
- startup evidence を実アプリの `application.lifespan()` logger 出力に変更し、`service_variant` / `agent_model` / `summary_model` / `backend` を記録する runtime log を追加・検証。
- chat turn evidence を実 endpoint logger 出力に変更し、START turn と通常メッセージ turn の `service_variant` / `agent_model` / `backend` / `chat_service` / `request_type` を追加・検証。
- Phase 6 README の refactoring scope を `server/tests/` に固定し、7 marker command を workspace root で `.venv-server/bin/python` により再実行して全件 pass を確認。
- `gate_a_scenario_matrix.md` の Phase 6 release evidence memo を pass 結果に更新。
- `status.md` の当該 task を `done` に更新。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat/agent_runtime_config.py` | runtime logging helper と summary model 解決 helper を追加。 |
| `server/src/aica_agent/application.py` | startup 時に runtime config log を実 logger から出力。 |
| `server/src/aica_agent/endpoints.py` | START turn / 通常 message turn で runtime chat turn log を実 logger から出力。 |
| `server/tests/unit/services/chat/test_agent_runtime_config.py` | runtime logging helper と summary model 解決の unit test を追加。 |
| `server/tests/unit/test_application_runtime_logging.py` | FastAPI lifespan が startup runtime log を出すことを検証。 |
| `server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py` | endpoint が START / 通常 message turn の runtime log を出すことを検証。 |
| `server/tests/integration/chat_service_contract/test_di_lifecycle.py` | `process_chat_messages()` の runtime config 引数追加に追随。 |
| `server/plan/phases/phase-6-release-readiness/README.md` | RC verification checklist command を `server/tests/` スコープへ更新し、非対象スイート除外を明記。 |
| `server/plan/phases/phase-6-release-readiness/features/feature-2-release-evidence/task-1-release-logging-and-verification/verification.md` | startup/chat evidence、RC checklist 実行結果、rollback subset 判定、RC done 判定を更新。 |
| `server/plan/phases/phase-6-release-readiness/features/feature-2-release-evidence/task-1-release-logging-and-verification/handoff.md` | 本引き継ぎ内容を実値へ更新。 |
| `server/plan/phases/gate_a_scenario_matrix.md` | Phase 6 release evidence memo（feature-2 task-1）を pass 結果へ更新。 |
| `server/plan/phases/status.md` | phase-6 feature-2 task-1 のステータスを `done` に更新。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `get_summary_model(config)`: `model_list.use_for: summary` の model 名を startup log 用に解決する。
- `log_startup_runtime_config(logger, config)`: startup runtime config log を出力する。
- `log_chat_turn_runtime(logger, config, chat_svc, request_type=...)`: chat turn runtime log を出力する。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| synthetic `python -c print(...)` evidence を廃止し、runtime logger 出力を test で固定する | Phase 6 plan は app-emitted logs を要求しており、print evidence では production path のログ出力を証明できないため。 | verification.md の synthetic evidence のままにする。plan/code mismatch が残るため不採用。 |
| Gate A marker 再確認は `server/tests/` を明示し、refactoring 対象外スイートを除外する | Gate A refactoring scope と required scenario/rollback subset は server package に限定されるため。 | workspace 全体収集で実行する。非対象 `cli/tests` collection error の影響を受けるため不採用。 |
| required 7 command は上記 scope で再実行し、結果を RC checklist に反映する | Phase 6 README ルールに沿って RC 判定を実測値で固定するため。 | 過去 run の参照のみで更新する。最新の再確認証跡が不足するため不採用。 |
| task ステータスは `done` にする | startup/chat evidence と required checklist が全件 pass で完了条件を満たしたため。 | `blocked` 継続。現行 evidence と矛盾するため不採用。 |

## 互換性メモ

- startup evidence: `startup runtime config: service_variant=refactored agent_model=openai/gpt-4.1 summary_model=<summary model> backend=responses` 相当の logger call を `application.lifespan()` で検証。
- chat turn evidence: `chat turn runtime: service_variant=<legacy|refactored> agent_model=<model> backend=responses chat_service=<module.class> request_type=<type>` 相当の logger call を `handle_chat_session()` / `process_chat_messages()` で検証。
- focused runtime logging command: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/unit/services/chat/test_agent_runtime_config.py server/tests/unit/test_application_runtime_logging.py server/tests/integration/chat_service_contract/test_endpoint_config_boundary.py server/tests/integration/chat_service_contract/test_di_lifecycle.py` -> `34 passed in 0.24s`。
- required 7 marker command（`server/tests/` scope）は全件 pass。

## 次タスクへのフォローアップ

- feature-3 task-1（integration-pr-readiness）は、本 task の RC checklist pass evidence を前提に統合 PR checklist を更新すること。
- feature-1 handoff の依存事項どおり、staging rollback drill（実測時間・実ログ・実施者）を運用環境で追記すること。

## 未解決の質問

- staging rollback drill の実施責任者と実施日をどの release check point で固定するか。

## 前提にしてはいけないこと

- `verification.md` は pass 済み。feature-3 task-1 は本 task の RC checklist pass evidence を前提にできる。
