# 引き継ぎ: task-2-tool-result-parity

## 概要

`test_tool_results.py` の `fixture-schema only` テストを完全な behavioral runtime assertions に置き換えた。
Runner が tool call イベント（ToolCallItem → ToolCallOutputItem）を emit したとき、
`chat()` が yield する `ChatStreamResponseModel` の JSON shape が `tool_results.json` の
`_expected_keys` と一致することを legacy/delegating-refactored 両 variant で検証する。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/tests/integration/chat_service_contract/test_tool_results.py` | fixture-schema-only テストを完全な behavioral テスト 3 本に置き換え。position search / job type search / workflow start の tool call イベント → ChatStreamResponseModel shape を runtime で検証する。 |
| `server/tests/integration/chat_service_contract/fixtures/tool_results.json` | `_expected_keys` を実際の `ChatStreamResponseModel.model_dump()` キーに更新。`response_type` フィールドを追加。 |
| `server/plan/phases/gate_a_scenario_matrix.md` | `tool result response shape` の `legacy evidence` を `fixture-schema only` → `pass: pytest -q -m pre_extraction_parity` に更新。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `_inner(chat_svc)`: task-1 と同パターン。delegating adapter をアンラップして private attrs にアクセス。
- `_FakeRunResult(events)`: task-1 の同名クラスと同構造。指定イベントリストを replay する async generator。
- `_make_run_item_event(item)`: task-1 と同パターン。`SimpleNamespace(type="run_item_stream_event", item=item)` ファクトリー。
- `_setup_existing_session(chat_svc, agent_mock, session_id)`: task-1 の `_setup_existing_session` と同パターン。`_should_save=True` かつ `_session_created=True` にするヘルパー。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| `response.model_copy(deep=True)` でスナップショットを取得する | `ChatStreamResponse.create_response()` は `self._model` を in-place で mutate して同じオブジェクトを返す。`async for` ループの外でアサートすると最終 mutation（END response）が反映されて失敗する | ループ内で即時アサート（可読性低下）|
| `RateLimitService` を conftest でリアルインスタンス化（空 config） | mock policy に準拠するため（in-process サービスは real instance + mocked repo が要件）。空の `ActionLimits` config を渡すと `_build_ordered_checks` がチェックを生成しないため全メソッドが即 `True` を返す。per-test オーバーライドが不要になる | テスト内で `MagicMock` を直接注入（mock policy 違反） |
| `WorkflowService` を conftest でリアルインスタンス化（mocked repo） | mock policy に準拠するため。workflow test は `svc._workflow_service._workflow_definition_repository.get_definition.return_value` を設定して repo 層のみスタブする | `SimpleNamespace()` スタブ（`model_dump()` が呼べない） |
| `PositionService` を conftest でリアルインスタンス化（mocked repos） | mock policy に準拠するため。`aica_api_repository.get = AsyncMock(return_value=(None, None))` により `current_search_filter()` が `None` を返し、`init_session()` の正常パスを通る | `MagicMock` で直接スタブ（mock policy 違反） |
| `WorkflowDefinition` リアルインスタンスをスタブとして使用 | `definition.model_dump(by_alias=True)` が chat_service.py 内で呼ばれるため、Pydantic モデルの real instance が必要 | MagicMock（`model_dump` の戻り値設定が複雑） |

## 互換性メモ

- `delegating-refactored` variant は `init_session()` と `chat()` を外側 wrapper で呼び、private attrs を `_inner()` 経由でアクセスする。task-1 と同じパターン。
- `real-refactored` variant は conftest の `chat_service_container` fixture が `pytest.skip` するため、テスト関数内での明示的スキップは不要。
- `ChatStreamResponse` の mutable model 設計（in-place mutation）は既存仕様であり変更しない。テスト側で `model_copy(deep=True)` を使うことで対処する。

## カバレッジ状況

コマンド: `pytest server/tests/integration/chat_service_contract/ -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing`

| 計測対象 | Stmts | Miss | Branch | BrPart | Coverage |
| --- | --- | --- | --- | --- | --- |
| `tool_results.py` テストのみ | 779 | 485 | 346 | 56 | 33% |
| `pre_extraction_parity` スイート全体 | 779 | 420 | 346 | 64 | 42% |

task-2 で新たにカバーされた主要パス:
- `chat()` 内の `ToolCallItem` ハンドリング（`_handle_tool_call_item` 呼び出し）
- `ToolCallOutputItem` ハンドリングの成功パス（`GENERIC_POSITION_SEARCH`, `JOBTYPE_SEARCH_BY_KEYWORDS`, `START_WORKFLOW` の各 `case`）
- `_ensure_tool_execution_available` の通過パス（rate limit 許可）
- `_process_jobtype_search_result` の正常パス（`職種` キーあり）
- `WorkflowService.get_definition` 呼び出しパス

未カバーのパス（`pre_extraction_parity` 全体で 42% 止まり）:
- `chat()` 内のエラー系ブランチ（LLM failure 系は task-1 でカバー済み、残りは他 task スコープ）
- 多数の helper メソッド（`job_type_decided`, `summarize_position_detail_chat` 等）は task-4/task-5 スコープ
- `APPLICATION`, `REGISTRATION` ツール case — 現在 dead code 候補（Phase 4 前に除去検討）
- セキュリティ系ブランチ — task-3 スコープ
- `_rate_limit_service` の超過パス（`PositionSearchRateLimitExceeded`）— task-3/4 スコープ

`chat_service.py` branch coverage 100% 目標に対し、task-1〜2 完了時点で 42%。残りは task-3〜5 がカバーする。

## 次タスクへのフォローアップ

- Phase 4 完了後、`real-refactored` variant の skip を解除して全 3 variant を通す。
- 将来 `ChatStreamResponseModel` のフィールドが追加・削除された場合、`tool_results.json` の `_expected_keys` を更新する必要がある。
- `APPLICATION` / `REGISTRATION` ツール case は未カバーかつ incomplete な TODO 実装（`pass` のみ）。refactored version でも TODO として残す。

## 未解決の質問

- なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
