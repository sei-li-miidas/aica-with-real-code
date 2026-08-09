# 検証: task-6-coverage-gap-inventory

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing` | pass | `chat_service.py` coverage inventory の source of truth。`47 passed, 25 skipped, 267 deselected`。branch coverage は `54%`。 |

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

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing`

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| `pre_extraction_parity` coverage inventory | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing` | pass | coverage summary: `787 stmts / 323 miss / 348 branch / 80 partial / 54% cover` |

Missing (raw source of truth):
```text
63-71
163, 168
209
240, 247-251, 255->253, 273->289, 287
322-323, 366-370, 373-387, 392-415, 428-432
478-479, 486, 491-492
522, 529-537, 546-551, 558-562, 595-605
661->978, 664->661, 668-670, 672->661, 714->661, 741->661, 750-767, 831->661, 854->661, 867-876, 882-925, 931-958, 964, 983-991, 1030->1063, 1040->1043, 1045-1049, 1067, 1072, 1083-1092
1120
1138-1189
1204-1212, 1216-1220, 1235-1240
1304-1355
1363, 1380->1390, 1383-1388, 1392-1409, 1413-1426, 1438, 1458-1460, 1468-1472, 1489
1510-1511, 1533, 1558-1570
1602-1607
1665
1683
1699-1732
1750
1769-1771
1801-1805
1827-1831, 1839, 1844->2032, 1876-1986, 1995->1872, 1998, 2011->2030, 2015->2028, 2035->2059, 2039-2057
2067->2066, 2069
2089, 2094
2130-2135, 2144, 2147-2151, 2155-2162, 2167-2170
2204-2209, 2212-2220, 2230-2238, 2241->2258
2278-2279, 2283, 2285
2315, 2317-2323
2333-2338
2346-2383
```

## 未カバーブランチ inventory

| line / branch | 分類 | task-7 target |
| --- | --- | --- |
| `63-71` (`_json_default`) | `reachable by parity test` | `test_runner_contract.py` または新規 `test_runner_residual_branches.py` に usage object shape parametrization を追加する。 |
| `163`, `168` (`__init__`) | `reachable by parity test` | constructor validation scenario を追加し、存在しない `workflow_dir` と file-path `workflow_dir` を固定する。 |
| `209` (`_run_streamed`) | `reachable by parity test` | `Runner.run_streamed` patch で seam 本体を通す scenario を追加する。 |
| `240`, `247-251`, `255->253`, `273->289`, `287` (`init_session`) | `reachable by parity test` | `test_history_mapping.py` か新規 `test_init_session_residuals.py` に current filter / fallback / empty resume を追加する。 |
| `322-323`, `366-370`, `373-387`, `392-415`, `428-432` (`_convert_to_llm_messages`) | `reachable by parity test` | `fixtures/history_mapping.json` と `test_history_mapping.py` に position / empty tool / jobtype / reasoning / unsupported role を追加する。 |
| `478-479`, `486`, `491-492` (`_handle_security_detection`) | `reachable by parity test` | `test_security_cleanup.py` に create-session-before-block / block_session failure / unexpected detector error を追加する。 |
| `522`, `529-537`, `546-551`, `558-562`, `595-605` (`chat` preflight / prepare) | `reachable by parity test` | 新規 `test_chat_entrypoint_guards.py` で blocked session / START short-circuit / decrypt failure を固定する。 |
| `661->978`, `664->661`, `668-670`, `672->661`, `714->661`, `983-991`, `1030->1063`, `1040->1043`, `1045-1049`, `1067`, `1072`, `1083-1092` (`chat` stream / retry bookkeeping) | `reachable by parity test` | `test_runner_contract.py` か新規 residual runner test に duplicate item / empty delta / final chunk / rate limit / retry bookkeeping を追加する。 |
| `741->661`, `750-767`, `831->661`, `854->661`, `867-876`, `882-925`, `931-958`, `964` (`chat` tool output special cases) | `reachable by parity test` | `test_tool_results.py` に tool failure / empty jobtype / workflow error / application / registration / handoff branchesを追加する。 |
| `1120` (`_is_stop_at_tool`) | `reachable by parity test` | `test_runner_contract.py` に truthy direct-tool replay 判定を追加する。 |
| `1138-1189` (`_append_stop_at_tool_outputs`) | `reachable by parity test` | `fixtures/stop_at_tool_replay.json` と `test_runner_contract.py` に position/jobtype/duplicate/fallback replay を追加する。 |
| `1204-1212`, `1216-1220`, `1235-1240` (`summarize_position_detail_chat`) | `reachable by parity test` | `test_summary_rollback.py` に decrypt failure / no position / no histories / empty summary を追加する。 |
| `1304-1355` (`_prepare_for_chat_turn`) | `reachable by parity test` | 新規 `test_position_detail_entrypoint.py` に return-from-position-detail / bootstrap / unknown page を追加する。 |
| `1363`, `1380->1390`, `1383-1388`, `1392-1409`, `1413-1426`, `1438`, `1458-1460`, `1468-1472`, `1489` (`tool output parsing / rate limit`) | `reachable by parity test` | `test_tool_results.py` / `test_db_side_effects.py` に invalid parse shapes、unsupported tool、invalid args、rate-limit exceeded を追加する。 |
| `1510-1511`, `1533`, `1558-1570` (`_save_chat_history`) | `reachable by parity test` | `test_db_side_effects.py` に queueing / `transfer_to_*` skip / reasoning / unsupported item を追加する。 |
| `1602-1607` (`_create_session`) | `reachable by parity test` | `test_db_side_effects.py` に queued `ChatRequestModel` / `ChatHistory` / `RunItem` flush を追加する。 |
| `1665` (`_save_user_or_developer_message`) | `reachable by parity test` | `test_db_side_effects.py` に first-turn queueing を追加する。 |
| `1683` (`_save_llm_error`) | `reachable by parity test` | `test_db_side_effects.py` に new-session first-turn retry failure を追加する。 |
| `1699-1732` (`_get_position_detail`) | `reachable by parity test` | `test_position_detail_entrypoint.py` に position/company/business missing を追加する。 |
| `1750` (`_get_agent`) | `reachable by parity test` | default agent 不在 setup で `chat()` / `init_session()` failure path を追加する。 |
| `1769-1771` (`_create_position_agent_if_not_exist`) | `reachable by parity test` | position-detail history bootstrap で `POSITION_GUIDE.clone()` path を追加する。 |
| `1801-1805` (`check_if_previous_chat_histories_exist`) | `reachable by parity test` | 新規 `test_previous_history_contract.py` を追加する。 |
| `1827-1831`, `1839`, `1844->2032`, `1876-1986`, `1995->1872`, `1998`, `2011->2030`, `2015->2028`, `2035->2059`, `2039-2057` (`load_previous_chat_histories`) | `reachable by parity test` | `fixtures/history_mapping.json` と新規 `test_previous_history_contract.py` に previous-history residual cases を追加する。 |
| `2067->2066`, `2069` (`_find_last_non_position_guide_agent`) | `reachable by parity test` | all-`POSITION_GUIDE` resume fixture を追加し、`init_session()` error return を固定する。 |
| `2089`, `2094` (`_process_jobtype_search_result`) | `reachable by parity test` | `test_tool_results.py` に null / missing `職種` payload を追加する。 |
| `2130-2135`, `2144`, `2147-2151`, `2155-2162`, `2167-2170` (`job_type_decided`) | `reachable by parity test` | `test_workflow_side_effects.py` に invalid JSON / empty list / tool update failure を追加する。 |
| `2204-2209`, `2212-2220`, `2230-2238`, `2241->2258` (`workflow_submitted`) | `reachable by parity test` | `test_workflow_side_effects.py` に invalid payload / workflow error / no-save path を追加する。 |
| `2278-2279`, `2283`, `2285` (`workflow_cancelled`) | `reachable by parity test` | `test_workflow_side_effects.py` に malformed / missing / unknown workflow cancellation を追加する。 |
| `2315`, `2317-2323` (`_update_agents_with_position_search_tool`) | `reachable by parity test` | `test_workflow_side_effects.py` に empty updated_agents / mismatched configured tool を追加する。 |
| `2333-2338` (`_extract_position_search_tool_name`) | `reachable by parity test` | `test_init_session_residuals.py` か `test_history_mapping.py` に invalid `ToolName` shape を追加する。 |
| `2346-2383` (`_extract_selected_jobtypes`) | `reachable by parity test` | `test_init_session_residuals.py` か `test_history_mapping.py` に invalid `SearchFilters.Jobtypes` / dedupe case を追加する。 |

## 失敗したテスト

| コマンド | 失敗概要 | 次の対応 |
| --- | --- | --- |
| なし | なし | なし |

## 未実行

| コマンド | 理由 |
| --- | --- |
| なし | なし |

## 免除

| コマンド | オーナー | 理由 | 日付 | フォローアップ |
| --- | --- | --- | --- | --- |
| なし | なし | なし | なし | なし |

## 手動確認

- coverage report の `Missing` 欄を `handoff.md` の inventory へ method 単位で転記し、public interface からの到達入口を付与した。
- owner 判断により `ChatService.__init__()` の invalid `workflow_dir` branch (`163`, `168`) も task-7 の parity closure 対象に含めるよう、handoff と status を更新した。
