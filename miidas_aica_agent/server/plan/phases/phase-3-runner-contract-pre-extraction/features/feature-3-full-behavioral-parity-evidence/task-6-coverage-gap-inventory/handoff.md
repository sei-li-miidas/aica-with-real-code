# 引き継ぎ: task-6-coverage-gap-inventory

## 概要

task-1〜5 完了時点の `pre_extraction_parity` coverage report を source of truth に、
legacy `chat_service.py` の未カバーブランチを method 単位で inventory 化した。
branch coverage は 54% (`787 stmts / 323 miss / 348 branch / 80 partial`) で、
未カバー領域の大半は public interface 経由で task-7 が閉じられる。

`ChatService.__init__()` の `workflow_dir` validation (`163`, `168`) については、
owner 判断により task-7 が constructor validation もカバーしてよいことになった。
したがって、この 2 行も parity test closure 対象として task-7 に含める。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/plan/phases/phase-3-runner-contract-pre-extraction/features/feature-3-full-behavioral-parity-evidence/task-6-coverage-gap-inventory/handoff.md` | coverage report を source of truth にした未カバーブランチ inventory、task-7 向け scenario 固定、plan amendment 要否を記録。 |
| `server/plan/phases/phase-3-runner-contract-pre-extraction/features/feature-3-full-behavioral-parity-evidence/task-6-coverage-gap-inventory/verification.md` | `pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing` の実行結果を記録。 |
| `server/plan/phases/status.md` | task-6 を `done` に更新し、owner 判断で constructor validation も task-7 scope に含めたため、task-7 は `not-started` に戻した。 |

## 未カバーブランチ inventory

| line / branch | 到達入口 | 分類 | 既存 scenario | 次対応 |
| --- | --- | --- | --- | --- |
| `63-71` (`_json_default`) | `chat()` の token usage serialize | `reachable by parity test` | `tests/integration/chat_service_contract/test_runner_contract.py` の usage propagation は dict usage のみ | task-7 で `test_runner_contract.py` か新規 `test_runner_residual_branches.py` に、`run_result.context_wrapper.usage` を dataclass / `model_dump()` / `dict()` / plain object に切り替える parametrized scenario を追加し、`json.dumps(..., default=_json_default)` の全分岐を通す。 |
| `163`, `168` (`__init__`) | constructor (`ChatService(...)`) の invalid `workflow_dir` | `reachable by parity test` | 既存 Phase 3 parity は public method contract 中心で constructor validation を未実装 | task-7 で新規 constructor validation scenario を追加し、存在しない `workflow_dir` と file-path `workflow_dir` の 2 ケースで `FileNotFoundError` / `NotADirectoryError` を固定する。 |
| `209` (`_run_streamed`) | `chat()` が legacy seam 経由で `Runner.run_streamed()` を呼ぶ | `reachable by parity test` | `test_runner_contract.py` は `_run_streamed` を差し替えるケースが中心 | task-7 で `Runner.run_streamed` 自体を patch し、`svc._run_streamed` は差し替えずに `chat()` を実行する scenario を追加して seam 本体を通す。 |
| `240`, `247-251`, `255->253`, `273->289`, `287` (`init_session`) | `init_session()` | `reachable by parity test` | `test_history_mapping.py` は既存 session happy path、`test_workflow_side_effects.py` は workflow happy path | task-7 で `test_history_mapping.py` か新規 `test_init_session_residuals.py` に、`current_search_filter` あり / load 失敗 fallback / `exists=True` で `chat_session is None` / histories 空の resume を追加し、`_extract_position_search_tool_name()` と `_extract_selected_jobtypes()` 連動を assertion する。 |
| `322-323`, `366-370`, `373-387`, `392-415`, `428-432` (`_convert_to_llm_messages`) | `init_session()` で DB histories を復元 | `reachable by parity test` | `test_history_mapping.py` は USER / ASSISTANT / generic TOOL のみ | task-7 で `fixtures/history_mapping.json` を拡張し、position-detail history key、空 tool output、position search persisted output、jobtype persisted output、REASONING / unsupported role を含む session fixture を追加する。 |
| `478-479`, `486`, `491-492` (`_handle_security_detection`) | `chat()` 中の security detection | `reachable by parity test` | `test_security_cleanup.py` は forbidden/context-danger の happy path のみ | task-7 で `test_security_cleanup.py` に、`_session_created=False` 時の create-session-before-block、`block_session()` 失敗時の error response 維持、unexpected detector exception re-raise を追加する。 |
| `522`, `529-537`, `546-551`, `558-562`, `595-605` (`chat` preflight / prepare) | `chat()` | `reachable by parity test` | 既存 parity は通常 chat path と workflow entrypoint happy path が中心 | task-7 で新規 `test_chat_entrypoint_guards.py` を追加し、`session_status is None` defaulting、blocked session early error、`START` + `REGISTERING/APPLYING` early end、decrypt / `_prepare_for_chat_turn` failure を固定する。 |
| `661->978`, `664->661`, `668-670`, `672->661`, `714->661`, `983-991`, `1030->1063`, `1040->1043`, `1045-1049`, `1067`, `1072`, `1083-1092` (`chat` stream / retry bookkeeping) | `chat()` | `reachable by parity test` | `test_runner_contract.py` と `test_security_cleanup.py` は single-message happy path / cancellation path のみ | task-7 で `test_runner_contract.py` か新規 `test_runner_residual_branches.py` に、duplicate `item_id` ignore、empty delta、`current_item_id is None` final chunk、rate-limit exception、`last_response_id` / `last_agent` capture、retry backoff success-on-second-attempt を追加する。 |
| `741->661`, `750-767`, `831->661`, `854->661`, `867-876`, `882-925`, `931-958`, `964` (`chat` tool output special cases) | `chat()` | `reachable by parity test` | `test_tool_results.py` は position / jobtype / workflow start success、`test_workflow_side_effects.py` は workflow public method happy path | task-7 で `test_tool_results.py` に、tool `"Message"` failure payload、jobtype empty result、workflow definition failure、APPLICATION / REGISTRATION / HandoffOutputItem branchesを emit する residual scenario を追加する。 |
| `1120` (`_is_stop_at_tool`) | `chat()` finally から direct-tool 判定 | `reachable by parity test` | `test_runner_contract.py` は stop-at-tool replay の一部のみ | task-7 で direct tool `tool_use_behavior={"stop_at_tool_names": [...]}` の truthy path を追加し、`item.raw_item.name in stop_at_tool_names` を通す。 |
| `1138-1189` (`_append_stop_at_tool_outputs`) | `chat()` finally の stop-at-tool replay | `reachable by parity test` | `test_runner_contract.py` の existing replay は limited shape | task-7 で `fixtures/stop_at_tool_replay.json` を拡張し、position search fake-result replay、jobtype replay、duplicate suppression、fallback `conversation.append(item)` の 4 ケースを追加する。 |
| `1204-1212`, `1216-1220`, `1235-1240` (`summarize_position_detail_chat`) | `summarize_position_detail_chat()` | `reachable by parity test` | `test_summary_rollback.py` は decrypt success + summary success のみ | task-7 で `test_summary_rollback.py` に、decrypt failure、`position_id=None`、position history missing、summary text empty を追加する。 |
| `1304-1355` (`_prepare_for_chat_turn`) | `chat()` | `reachable by parity test` | 現行 tests は `PageName.CHAT` の通常 path と summary path が中心 | task-7 で新規 `test_position_detail_entrypoint.py` を追加し、`POSITION_GUIDE` から main chat へ戻る path、position-detail 初回 bootstrap、detail/company/business missing、unknown page を固定する。 |
| `1363`, `1380->1390`, `1383-1388`, `1392-1409`, `1413-1426`, `1438`, `1458-1460`, `1468-1472`, `1489` (`tool output parsing / rate limit`) | `chat()` | `reachable by parity test` | `test_db_side_effects.py` / `test_tool_results.py` は parse success と tool result success のみ | task-7 で `test_tool_results.py` と `test_db_side_effects.py` に、invalid JSON / empty list / non-dict list element / non-str `text` / unsupported output type / unsupported tool name / invalid position-search arguments / rate-limit exceeded を追加する。 |
| `1510-1511`, `1533`, `1558-1570` (`_save_chat_history`) | `chat()` | `reachable by parity test` | `test_db_side_effects.py` は assistant/tool/tool-output retry-error のみ | task-7 で `test_db_side_effects.py` に、`_should_save=False` queueing、`transfer_to_*` ToolCall skip、ReasoningItem save、unsupported item logging を追加する。 |
| `1602-1607` (`_create_session`) | `chat()` 2nd-turn session creation | `reachable by parity test` | `test_db_session_creation` は create call ordering だけを見る | task-7 で `test_db_side_effects.py` に、`_conversation_to_save_when_session_created` へ `ChatRequestModel` / `ChatHistory` / `RunItem` を混在させた flush scenario を追加し、3 分岐すべてを通す。 |
| `1665` (`_save_user_or_developer_message`) | `chat()` 初回 turn | `reachable by parity test` | `test_db_side_effects.py` は `_should_save=True` のみ | task-7 で first-turn chat scenario を追加し、DB 保存せず queue へ積む分岐を assertion する。 |
| `1683` (`_save_llm_error`) | `chat()` retry path on first turn | `reachable by parity test` | `test_db_retry_error_save` は `_should_save=True` の既存 session のみ | task-7 で new-session first-turn retry failure scenario を追加し、developer error history が queue へ積まれることを固定する。 |
| `1699-1732` (`_get_position_detail`) | `chat()` position-detail page | `reachable by parity test` | 現行 parity では position detail bootstrap の negative path を未実装 | task-7 で `test_position_detail_entrypoint.py` に、position/company/business missing を 3 ケース追加する。 |
| `1750` (`_get_agent`) | `chat()` / `init_session()` | `reachable by parity test` | 既存 tests は always-default-agent fixture | task-7 で `init_session()` / `chat()` setup に default agent 不在または missing position agent を入れ、`Agent not found` が prepare error path へ流れることを確認する。 |
| `1769-1771` (`_create_position_agent_if_not_exist`) | `chat()` position-detail page / `init_session()` position history | `reachable by parity test` | `test_history_mapping.py` は position history を未使用 | task-7 で position-detail history bootstrap を追加し、`POSITION_GUIDE.clone()` 経由で per-position agent が作られることを確認する。 |
| `1801-1805` (`check_if_previous_chat_histories_exist`) | `check_if_previous_chat_histories_exist()` | `reachable by parity test` | Phase 3 parity では未実装 | task-7 で新規 `test_previous_history_contract.py` を追加し、decrypt された position id で `has_position_chat_histories()` が呼ばれることを固定する。 |
| `1827-1831`, `1839`, `1844->2032`, `1876-1986`, `1995->1872`, `1998`, `2011->2030`, `2015->2028`, `2035->2059`, `2039-2057` (`load_previous_chat_histories`) | `load_previous_chat_histories()` | `reachable by parity test` | `test_history_mapping.py` は main-chat simple payload のみ | task-7 で `fixtures/history_mapping.json` と新規 `test_previous_history_contract.py` に、position detail path、empty histories、position search link reconstruction、jobtype result + selected name、duplicate assistant skip、session greeting tail を追加する。 |
| `2067->2066`, `2069` (`_find_last_non_position_guide_agent`) | `init_session()` resume / `chat()` return from position detail | `reachable by parity test` | 既存 tests は MAIN history に non-position agent あり | task-7 で all-`POSITION_GUIDE` history を使う negative resume scenario を追加し、`init_session()` が `ChatSessionStatus.ERROR` を返す path まで固定する。 |
| `2089`, `2094` (`_process_jobtype_search_result`) | `chat()` tool result / `load_previous_chat_histories()` | `reachable by parity test` | `test_tool_results.py` は valid `職種` payload のみ | task-7 で null payload / `職種` key missing payload を追加し、response を出さず conversation だけ進むことを assertion する。 |
| `2130-2135`, `2144`, `2147-2151`, `2155-2162`, `2167-2170` (`job_type_decided`) | `job_type_decided()` | `reachable by parity test` | `test_workflow_side_effects.py` は valid list + update success のみ | task-7 で invalid JSON、non-list JSON、empty list、`update_jobtypes()` が空 tool name、`_update_agents_with_position_search_tool()` failure を追加する。 |
| `2204-2209`, `2212-2220`, `2230-2238`, `2241->2258` (`workflow_submitted`) | `workflow_submitted()` | `reachable by parity test` | `test_workflow_side_effects.py` は valid payload + history save happy path のみ | task-7 で invalid JSON、missing `workflow_id` / non-dict answers、`ValueError` / `FileNotFoundError`、`history_to_save=[]` の no-save path を追加する。 |
| `2278-2279`, `2283`, `2285` (`workflow_cancelled`) | `workflow_cancelled()` | `reachable by parity test` | `test_workflow_side_effects.py` は known workflow happy path のみ | task-7 で malformed JSON、missing workflow id、unknown workflow id を追加し、fallback message shape を固定する。 |
| `2315`, `2317-2323` (`_update_agents_with_position_search_tool`) | `job_type_decided()` / `clear_jobtype()` | `reachable by parity test` | `test_workflow_side_effects.py` は update success のみ | task-7 で `update_agent_by_tool_name()` が `updated_agents=[]` または mismatched configured tool を返すケースを追加する。 |
| `2333-2338` (`_extract_position_search_tool_name`) | `init_session()` | `reachable by parity test` | 現行 tests は `ToolName` happy path 未固定 | task-7 で `current_search_filter` に non-str / whitespace-only `ToolName` を入れ、clone_agents の fallback arg shape を確認する。 |
| `2346-2383` (`_extract_selected_jobtypes`) | `init_session()` | `reachable by parity test` | 現行 tests は `SearchFilters.Jobtypes` 正常 shape 未固定 | task-7 で `current_search_filter` に invalid `SearchFilters` / invalid `Jobtypes` / duplicate selected / blank value を追加し、selected jobtypes list が dedupe されることを固定する。 |

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| inventory は raw line number の羅列ではなく method 単位で cluster 化した | task-7 の次実装を fixture / test file / assertion レベルへ具体化するには、coverage token を public entrypoint と scenario file に結び付ける必要があるため | coverage report の `Missing` 欄をそのまま handoff に貼り付ける |
| constructor-only `workflow_dir` validation も task-7 closure 対象に含める | owner から task-7 で constructor validation もカバーしてよい判断が出たため、100% branch coverage の closure 対象として扱える | constructor-only branch を別 task に分離し、task-7 を引き続き blocked にする |
| 既存 scenario file を最大限再利用し、追加が大きいものだけ新規 test file を提案した | task-7 が residual branch closure であり、Phase 3 feature の scenario ownershipを変えずに拡張しやすいため | residual branch ごとに完全新規 fixture / file を細かく乱立させる |

## 互換性メモ

- production code は未変更。今回の差分は planning / verification docs のみ。
- `pre_extraction_parity` の source of truth は task-1〜5 完了時点で `47 passed, 25 skipped, 267 deselected` の coverage run。
- `real-refactored` skip (`pending-phase-4`) はそのまま維持されており、今回の inventory は legacy `chat_service.py` の residual branch closure 計画のみを扱う。
- task-7 は constructor validation (`163`, `168`) を含めて legacy `chat_service.py` residual branch を閉じる前提で進めてよい。

## カバレッジ状況

コマンド: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing`

| 計測対象 | Stmts | Miss | Branch | BrPart | Coverage |
| --- | --- | --- | --- | --- | --- |
| `pre_extraction_parity` スイート全体 | 787 | 323 | 348 | 80 | 54% |

実行結果:
- `47 passed`
- `25 skipped`
- `267 deselected`

残存ギャップ要約:
- `reachable by parity test`: 31 method cluster（現行 inventory table の全行数。pass-3 で `__init__()` constructor validation cluster を reachable に再分類した後の数）
- `requires plan amendment`: 0
- 主要な未到達領域は `init_session()` の current filter / resume 分岐、`chat()` の early-return・tool failure・workflow/application/registration 分岐、`load_previous_chat_histories()` の payload reconstruction、workflow/jobtype の negative path。

task-7 開始条件:
- `reachable by parity test` の未カバーブランチ inventory が task-7 の fixture / assertion レベルまで具体化されていること。
- constructor validation (`163`, `168`) を含む residual cluster を parity test only で閉じること。

## レビュー / 修正ログ

| pass | reviewer | 結果 | 指摘 | 対応 |
| --- | --- | --- | --- | --- |
| 1 | `code-reviewer` subagent | request-changes | `verification.md` に actual inventory がなく、reachable count が `29` になっており、review log が `pending` placeholder のままだった | `verification.md` に raw `Missing` list と condensed inventory を追記し、当時の分類（constructor validation を別扱い）に合わせて reachable count を `30` に修正。後続の pass-3 で constructor validation を task-7 scope に含めたため、現時点の reachable count は `31`。 |
| 2 | `code-reviewer` subagent | clean | blocking な追加指摘なし。前回の requirement gap は解消済み | 追加修正なし。現行 handoff / verification / status の組み合わせで task 要件を満たすことを確認した |
| 3 | human plan decision | scope-updated | task-7 で constructor validation もカバーしてよい、という owner 判断が入った | `__init__()` の `163`, `168` を `reachable by parity test` へ再分類し、task-7 blocker を解除した |

## 次タスクへのフォローアップ

- task-7 は下記の順で実装すると衝突が少ない:
  - constructor validation residual case（invalid path / not-a-directory）
  - `test_runner_contract.py` / `fixtures/stop_at_tool_replay.json` / usage fixture 拡張
  - `test_history_mapping.py` / 新規 `test_previous_history_contract.py`
  - `test_tool_results.py` / `test_db_side_effects.py`
  - `test_workflow_side_effects.py` / `test_summary_rollback.py`
  - 必要なら新規 `test_chat_entrypoint_guards.py` / `test_position_detail_entrypoint.py`
- task-7 完了時の必須確認は、同じ `pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing` で `chat_service.py` branch coverage が 100% になること。

## 未解決の質問

- なし。

## 前提にしてはいけないこと

- この inventory は legacy `chat_service.py` の residual branch closure 計画であり、`real-refactored evidence` の不足を補ったものではない。
