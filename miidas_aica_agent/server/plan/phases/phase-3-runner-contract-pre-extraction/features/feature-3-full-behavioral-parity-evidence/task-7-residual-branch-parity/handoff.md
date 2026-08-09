# 引き継ぎ: task-7-residual-branch-parity

## 概要

task-6 inventory に記載された residual reachable branches を parity テストで閉じる作業を進めたが、user 指示で legacy production change を revert したため、最終結果は legacy `chat_service.py` branch coverage 99% で止める。残差は `661->978` の 1 branch だけで、legacy `async for` の zero-yield termination path に相当する。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat_service.py` | user 指示により legacy stream-loop change を revert した。現状の production code 差分はなし。 |
| `server/tests/integration/chat_service_contract/test_chat_entrypoint_guards.py` | `chat()` entrypoint guard の residual branch を public sequence ベースで追加した。 |
| `server/tests/integration/chat_service_contract/test_init_session_residuals.py` | constructor validation、`init_session()` resume/current-filter residuals を追加した。 |
| `server/tests/integration/chat_service_contract/test_position_detail_entrypoint.py` | position detail entrypoint の residual branch を追加した。 |
| `server/tests/integration/chat_service_contract/test_previous_history_contract.py` | previous history reconstruction の residual pagination/greeting/tool-result branches を追加した。 |
| `server/tests/integration/chat_service_contract/test_runner_residual_branches.py` | runner/tool/security/workflow residual branch を public `chat()` 中心に追加し、最後の helper-level residual 2 arc を最小補助テストで閉じた。 |
| `server/tests/integration/chat_service_contract/test_security_cleanup.py` | security cleanup の block-session write failure branch を追加した。 |
| `server/tests/integration/chat_service_contract/test_summary_rollback.py` | summary rollback residual branch を追加した。 |
| `server/tests/integration/chat_service_contract/test_workflow_side_effects.py` | workflow cancelled/jobtype/workflow submission fallback branch を追加した。 |
| `server/tests/integration/chat_service_contract/fixtures/history_mapping.json` | residual previous-history cases に合わせて fixture metadata を更新した。 |
| `server/plan/phases/phase-3-runner-contract-pre-extraction/features/feature-3-full-behavioral-parity-evidence/README.md` | feature task table の task-4〜7 status を実績に合わせて更新した。 |
| `server/plan/phases/status.md` | task-7 status を `done` に更新した。 |
| `server/plan/phases/phase-3-runner-contract-pre-extraction/features/feature-3-full-behavioral-parity-evidence/task-7-residual-branch-parity/verification.md` | 実行コマンドと pass 結果を反映した。 |

## 閉じたブランチ対応表

| line / branch | 追加した入口 | fixture / test | 備考 |
| --- | --- | --- | --- |
| `163`, `168` | `ChatService(...)` constructor | `test_init_session_residuals.py::test_chat_service_constructor_rejects_missing_or_non_directory_workflow_dir` | workflow dir validation。 |
| `266-302`, `382-413`, `2332-2388` | `init_session()` | `test_init_session_residuals.py` | current filter fallback / malformed restored history / invalid filter shape。 |
| `500-605`, `1286-1360` | `chat()` | `test_chat_entrypoint_guards.py`, `test_position_detail_entrypoint.py` | blocked session / start short-circuit / decrypt failure / empty conversation / position guide restore / missing active agent。 |
| `607-1194`, `1440-1577` | `chat()` | `test_runner_residual_branches.py` | runner stream event variants、tool output parse variants、stop-at replay、workflow/application/registration residuals、queued run-item flush。 |
| `465-492` | `chat()` security detection | `test_security_cleanup.py`, `test_runner_residual_branches.py::test_final_residual_helper_arcs_for_security_and_tool_output` | public cleanup/write-failure pathsに加えて、`_handle_security_detection()` の未作成 session helper arc を最小補助テストで closure。 |
| `1200-1278` | `summarize_position_detail_chat()` | `test_summary_rollback.py` | invalid token / missing position / recovery residuals。 |
| `1844-2059` | `load_previous_chat_histories()` | `test_previous_history_contract.py` | empty segment skip / jobtype follow-up scan / greeting tail / limit-zero branch。 |
| `2114-2292` | `job_type_decided()`, `workflow_submitted()`, `workflow_cancelled()` | `test_workflow_side_effects.py` | invalid payload / fallback / unknown workflow residuals。 |
| `1364-1368` | helper serialization | `test_runner_residual_branches.py::test_final_residual_helper_arcs_for_security_and_tool_output` | non-string tool-output serialization arc。public contract 上は副作用保存経由で通るが、最後の 1 line は helper 補助テストで固定。 |

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| legacy stream loop の production change は採用しない | user が legacy code 変更を望まないため、`async for event in run_result.stream_events()` のまま残す。 | explicit async iterator 化で 100% を取る案は一度成立したが、user 指示で revert。 |
| residual branch の大半は public entrypoint から閉じた | task-6 / task-7 の source of truth が public-interface parity を要求しているため。 | private helper の直接呼び出しで埋める案は reviewer 指摘により縮小した。 |
| helper-level 補助テストを 2 arc (`_handle_security_detection()` の session-create path、`_serialize_tool_output_for_storage()` の non-string path) に限定した | これ以上 public harness だけで閉じようとすると suite が不安定になり、branch 自体は純 helper 後処理の残差だったため。 | 初回実装のように複数 helper/private state を直接叩く案は取り下げた。 |

## 100% にできない理由

- 残っている未カバー branch は coverage report 上の `661->978` のみ。
- これは legacy 実装の `async for event in run_result.stream_events():` が **1 件も event を yield しないまま終了する** ときの暗黙の fallthrough に相当する。
- 振る舞い自体は parity tests で空 stream と単一 unhandled event のケースを通して確認済みだが、coverage は `async for` の暗黙の `StopAsyncIteration` 終端を branch として credit しない。
- この branch を 100% として観測させるには、legacy loop を explicit async iterator / `__anext__()` 形式へ書き換える必要がある。
- user 指示によりその legacy code change を revert したため、task の元々の完了条件である 100% は現状態では満たせない。

## 互換性メモ

- user 指示で legacy production change を revert 済み。現在の成果はテスト / fixture / task docs 更新のみ。
- `real-refactored` variant は引き続き `pending-phase-4` / skip のまま。今回の evidence は legacy / delegating characterization のみ。

## カバレッジ状況

コマンド: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/ --cov=services.chat_service --cov-branch --cov-report=term-missing`

| 計測対象 | Stmts | Miss | Branch | BrPart | Coverage |
| --- | --- | --- | --- | --- | --- |
| `pre_extraction_parity` スイート全体 | 787 | 0 | 348 | 1 | 99% |

完了時の期待値:
- legacy `chat_service.py` branch coverage 100%

現状:
- user 指示により legacy change を revert したため、task-7 は `done*` 扱いとし、99% coverage / residual `661->978` を明示した waiver-style exception として記録する。

## Review / Fix Log

| Pass | Reviewer | 結果 | 指摘 / 修正 |
| --- | --- | --- | --- |
| 1 | `code-reviewer` subagent | request-changes | task docs / status 未更新、private helper/state 依存の residual tests が多い。 |
| 1-fix | owner | fixed | docs/status を実値へ更新し、`test_chat_entrypoint_guards.py` と `test_runner_residual_branches.py` の private state/helper 依存を public sequence 中心へ置換。補助 helper test は final 2 arc のみに縮小。 |
| 2 | `code-reviewer` subagent | request-changes | docs はほぼ整合したが、`handoff.md` の review 状態文言だけが stale。 |
| 2-fix | owner | fixed | `handoff.md` の review pass 状態と helper arc 数の文言を実態へ合わせた。 |
| 3 | `code-reviewer` subagent | clean | remaining findings なし。task requirements / helper scope / docs 整合性ともに確認済み。 |
| 4 | user | change-request | legacy production change を revert し、100% 未達理由を明記するよう依頼。 |
| 4-fix | owner | fixed | `chat_service.py` の stream-loop refactor を revert し、`661->978` の residual branch が coverage tool の `async for` fallthrough 由来であることを docs に追記した。 |

## 次タスクへのフォローアップ

- Phase 4 完了後、`real-refactored` variant の skip を解除して同じ residual branch coverage を real implementation でも確認する。
- helper-level 補助テスト 2 arc も、Phase 4 で harness が改善したら public-interface evidence へ吸収できるか再確認する。
- もし将来 user / owner が legacy change を許容するなら、`async for` を explicit async iterator へ置換すると `661->978` を閉じて 100% に戻せる。

## 未解決の質問

- task original completion condition (`100%`) と user の「legacy change を入れない」制約は両立しない。現状態では後者を優先した。

## 前提にしてはいけないこと

- task-7 未完了を、依存関係に明記されていない後続 task まで一律に止める根拠として扱わない。
