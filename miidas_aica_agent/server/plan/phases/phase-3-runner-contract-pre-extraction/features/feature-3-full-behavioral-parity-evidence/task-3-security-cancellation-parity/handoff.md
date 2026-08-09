# 引き継ぎ: task-3-security-cancellation-parity

## 概要

`test_security_cleanup.py` の `fixture-schema only` テストを完全な behavioral runtime assertions に置き換えた。
Forbidden word 検知時の session block / detector cleanup と、`chat()` generator `aclose()` 時の
idempotent cleanup を legacy / delegating-refactored 両 variant で検証する。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat_service.py` | `chat()` stream 中に async generator が close された場合、`GeneratorExit` で `InjectionDetector` の session state を削除する。 |
| `server/src/aica_agent/services/chat_service_refactored.py` | delegating adapter の `chat()` forwarding で、外側 generator close 時に内側 legacy stream を `aclose()` する。 |
| `server/tests/integration/chat_service_contract/chat_service_contract_helpers.py` | `conftest.py` から通常 import していた shared helper を専用 helper module に移動。 |
| `server/tests/integration/chat_service_contract/conftest.py` | fixture 定義に集中させるため、shared helper 定義を削除。 |
| `server/tests/integration/chat_service_contract/test_security_cleanup.py` | fixture-schema-only テスト 2 本を full behavioral テストに置換。security block と cancellation cleanup を runtime で検証する。 |
| `server/tests/integration/chat_service_contract/fixtures/security_block.json` | forbidden word / expected response / expected result を追加。 |
| `server/tests/integration/chat_service_contract/fixtures/cancellation_cleanup.py` | cancellation scenario の delta と expected final state を返す fixture に更新。 |
| `server/plan/phases/gate_a_scenario_matrix.md` | `security block cleanup` と `cancellation cleanup` の `legacy evidence` を `pass` に更新。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `_make_text_delta(item_id, delta)`: `ResponseTextDeltaEvent` を持つ `raw_response_event` を作る test helper。
- `chat_service_contract_helpers.py`: `_FakeRunResult` / `_inner` / `_setup_existing_session` / `_make_run_item_event` を提供する通常の test helper module。`conftest.py` から import しない。
- `security_session_id` fixture: test ごとに UUID 付き session id を発行し、teardown で `clear_session_id()` する。
- `_RecordingInjectionDetector`: real detector に委譲しつつ、test-facing な active session set だけを記録する test-local wrapper。production security module には test-only API を追加しない。
- `security_block.json`: `forbidden_detection.forbidden_input` に `searchjobpostings` を追加。
- `cancellation_cleanup.py`: `cancellation_cleanup_fixture()` が `first_delta` / `second_delta` / `expected_final_state` を返す。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| `GeneratorExit` で detector state を削除 | `chat()` async generator を `aclose()` すると通常の `finalize_stream()` に到達しないため、stream-local state が残る | `finally` で通常 path も含めて常に remove する（正常 stream の既存 cleanup と重複しやすい） |
| delegating adapter の `chat()` で inner stream を明示的に `aclose()` | 外側 adapter の async generator close だけでは legacy inner generator の `GeneratorExit` cleanup が実行されなかった | adapter 側では何もしない（delegating evidence が false-green になる） |
| detector cleanup は test-local recording wrapper で観測 | cleanup invariant は session-local state が消えることなので、production code に test-only API を追加せず、real detector に委譲する wrapper の active set で確認する | `remove_session` call count のみを assert（正常/異常 path の実装詳細に寄りすぎる） |

## 互換性メモ

- `real-refactored` variant は引き続き `pending-phase-4` skip。
- delegating adapter は legacy stream を buffer せず forward する既存 contract を維持しつつ、close propagation だけを追加した。
- `block_session()` は forbidden / context-danger detection path で 1 回呼ばれる。cancellation path では呼ばれない。

## カバレッジ状況

コマンド: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing`

| 計測対象 | Stmts | Miss | Branch | BrPart | Coverage |
| --- | --- | --- | --- | --- | --- |
| このタスクのテストのみ | 787 | 541 | 348 | 39 | 26% |
| `pre_extraction_parity` スイート全体 | 787 | 386 | 348 | 68 | 46% |

このタスクで新たにカバーされた主要パス:
- `_handle_security_detection()` forbidden word / context danger path: error response、`block_session()`、detector cleanup。
- `chat()` streaming raw delta path: `process_stream_chunk()` → message response。
- `chat()` cancellation path: `GeneratorExit` → detector cleanup。
- delegating adapter `chat()` cancellation propagation: outer `aclose()` → inner stream `aclose()`。

未カバーのパス:
- workflow side effects は task-4 scope。
- summary rollback は task-5 scope。

`chat_service.py` branch coverage: task-3 完了時点で 46%。残りは task-4〜5 がカバーする。

## 次タスクへのフォローアップ

- task-4 は `rollback_security` を共有するため、今回追加した cancellation cleanup と workflow side effects が同じ marker で実行される前提で進めてよい。
- Phase 4 完了後、`real-refactored` variant の skip を解除して同じ security/cancellation assertions を real implementation に適用する。

## 未解決の質問

- なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
