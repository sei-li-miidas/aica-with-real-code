# 引き継ぎ: task-1-real-refactored-shell

## 概要

`chat_service_refactored.ChatService` を Phase 2 の全面委譲アダプタから、Phase 4 bootstrap 用の thin real shell へ置き換えた。main `chat()` path は `services.chat.llm_runner.ResponsesAgentRunner` を通るようになり、runner event normalization / stop-at-tool replay / usage propagation の real-refactored evidence を `pre_extraction_bootstrap` で更新した。

同時に、Phase 3 の delegating characterization を壊さないため、contract test fixture 側でのみ `_delegate_chat=True` を使って旧 delegating path を維持するようにした。production code の default は real shell であり、task-2 はこの shell に対して「delegating adapter を戻すと fail する」behavioral proof を追加する。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/containers.py` | refactored shell 用の `ResponsesAgentRunner` を container で生成し、`ChatService` へ明示 inject するようにした。legacy variant ではこの dependency を破棄する。 |
| `server/src/aica_agent/services/chat/llm_runner.py` | `LLMRunStream.aclose()` contract を追加し、Responses runner の close path を公開した。 |
| `server/src/aica_agent/services/chat_service_refactored.py` | main `chat()` path を normalized runner contract に接続する thin real shell へ変更した。legacy persistence helper と usage/token-usage behavior は bootstrap 中も維持する。 |
| `server/tests/integration/chat_service_contract/conftest.py` | `delegating-refactored` の characterization 用に `_delegate_chat=True` を差し込む fixture 調整と、明示的な `real_refactored_chat_service_container` を追加した。 |
| `server/tests/integration/chat_service_contract/test_refactored_bootstrap_shell.py` | real-refactored shell が runner event / stop-at-tool replay / usage propagation / current-turn persistence を保つことを証明する bootstrap integration test を追加した。 |
| `server/tests/unit/services/test_chat_service_refactored.py` | bootstrap shell の branch coverage 100% を満たす unit test を追加した。 |
| `server/plan/phases/phase-4-refactored-extraction/README.md` | phase feature status を `in-progress` に更新した。 |
| `server/plan/phases/phase-4-refactored-extraction/features/feature-1-refactored-bootstrap/README.md` | task-1 status を `done`、feature status を `in-progress` に更新した。 |
| `server/plan/phases/phase-4-refactored-extraction/features/feature-1-refactored-bootstrap/task-1-real-refactored-shell/verification.md` | 実行コマンド、coverage 結果、bootstrap/parity marker 結果を反映した。 |
| `server/plan/phases/status.md` | phase-4 task-1 row を `done` に更新し、概要の最終更新日/現在フェーズを更新した。 |
| `server/plan/phases/gate_a_scenario_matrix.md` | `runner event normalization` / `stop-at-tool replay` / `usage propagation` の real-refactored evidence を task-1 の結果で `pass` に更新した。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `ChatService(..., llm_runner: LLMRunner)`
  - refactored shell は runner を必須 dependency とし、composition root（container / test fixture）から明示 inject する。
- `ChatService._delegate_chat`
  - Phase 3 の `delegating-refactored` characterization を test fixture だけで維持する private test hook。production default は `False`。
- `real_refactored_chat_service_container`
  - bootstrap evidence 専用に real refactored shell を明示的に解決する integration fixture。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| bootstrap shell は non-chat public methods を legacy へ委譲したまま、main `chat()` だけ real runner path に切り替える | task-1 の scope は thin shell と runner boundary 接続に限定されており、state/history/persistence/tool/security/workflow の本格抽出は後続 task の責務だから。 | `chat_service_refactored.py` 全体から即座に legacy 依存を消す。 |
| real shell でも legacy persistence helper (`_create_session`, `_save_user_or_developer_message`, `_save_chat_history`) を使い続ける | DB side effects の behavior drift を task-1 で発生させないため。抽出そのものは feature-2 / feature-3 で行う。 | task-1 の時点で persistence path も refactored 側へ仮移植する。 |
| `delegating-refactored` の characterization は test fixture の `_delegate_chat=True` で維持する | `pre_extraction_parity` の Phase 2/3 wiring evidence を保持しつつ、task-1 では explicit `real_refactored` evidence を追加したかったため。 | production default を delegating のまま残し、task-1 では別の class 名で real shell を導入する。 |
| `ResponsesAgentRunner` は service constructor の implicit default にせず、container で composition する | runner 初期化の責務を DI に集約し、test/production の wiring strategy を一本化するため。 | `ChatService.__init__()` 内で `llm_runner is None` のときに `ResponsesAgentRunner()` を new する。 |
| usage logging failure は error response に丸める | legacy は usage/accounting path も guarded flow の中にあり、partial stream 後に insert 失敗がそのまま generator exception になる public drift を避ける必要があるため。 | usage logging の失敗を握り潰して END を返す。 |
| delegated legacy stream と refactored runner stream の cleanup は `Exception` のみ close し、`CancelledError` / `GeneratorExit` は即 re-raise する | cancellation を cleanup await で遅延させず、正常な async cancellation semantics を維持するため。 | `BaseException` を catch して常に `aclose()` を試みる。 |

## 互換性メモ

- `service_variant: refactored` の default path は main `chat()` で `LLMRunner.run_streamed()` を使う real shell になった。
- bootstrap shell でも、session creation・current-turn user/developer save・run item save・tool output update・token usage action log は legacy helper を通して維持する。
- local/dev 環境では legacy と同様に token usage message chunk を stream する。
- `delegating-refactored` characterization は production behaviorではなく test fixture 上の compatibility mode として維持される。
- stop-at-tool replay の duplicate check は mixed conversation item（dict 以外の OpenAI Message object など）が混在しても落ちないように guard している。

## 次タスクへのフォローアップ

- `task-2-bootstrap-behavioral-proof` は `test_no_legacy_dependency.py` の pending tests を実装し、real shell が `LLMRunner.run_streamed()` に到達すること、そして `_delegate_chat=True` 相当の rollback を戻すと fail することを証明する。
- `task-2` 完了までは `legacy dependency reintroduction` の matrix evidence は `pending-phase-4` のまま。
- state/history extraction task は `chat_service_refactored.py` がまだ legacy helper/state を保持している前提で作業し、bootstrap shell の public behavior を壊さずに component 分離を進める。

## 未解決の質問

- なし。

## Review / Fix Log

| Pass | Reviewer | 結果 | 指摘 / 修正 |
| --- | --- | --- | --- |
| 1 | `code-reviewer` subagent | request-changes | real shell が legacy persistence/session side effects と local/dev token usage chunk を落としていた。usage logging failure が guarded flow 外にあり、task docs/evidence 更新も未実施だった。 |
| 1-fix | owner | fixed | `chat_service_refactored.ChatService.chat()` で `_create_session`, `_save_user_or_developer_message`, `_save_chat_history` を再利用するように修正し、usage logging を guarded error path に戻し、local/dev token usage chunk を復元した。bootstrap integration/unit tests に persistence と local/dev usage の assertion を追加した。 |
| 2 | owner | fixed | `ResponsesAgentRunner` の implicit default construction をやめ、container から explicit inject に変更した。 |
| 3 | owner | fixed | bootstrap integration test の logging context setup を autouse fixture 化し、`clear_session_id()` で cleanup するようにした。 |
| 4 | owner | fixed | stop-at-tool replay duplicate check が non-dict conversation item に対して `.get()` しないよう guard を追加した。 |
| 5 | owner | fixed | `LLMRunStream.aclose()` contract を追加し、refactored runner path の stream cleanup を明示化した。 |
| 6 | owner | fixed | public streaming wrapper の `BaseException` catch を廃止し、通常例外だけ close、cancellation は即 re-raise するようにした。 |

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
