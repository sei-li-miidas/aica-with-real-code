# 引き継ぎ: task-2-build-summary-context-turn-wiring

## 概要

refactored `chat()` に summary parity 用の 2 つの呼び出しを追加した。

1. `prepare_turn()` 後、`MAIN_CHAT_KEY` かつ continuation 未設定時に
	 `_build_summary_context(get_session_id())` を実行。
2. `_record_usage()` 後、`MAIN_CHAT_KEY` かつ `_summary_service` 設定時に
	 `check_should_start_summary(get_session_id())` を実行。

あわせて、refactored 側に native `_build_summary_context()` / `_remove_tool_trace_message()`
を追加し、legacy 委譲なしで summary 文脈再構築を行うようにした。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat_service_refactored.py` | `chat()` へ summary context 再構築呼び出しと summary 起動判定呼び出しを追加。native `_build_summary_context()` / `_remove_tool_trace_message()` を実装。 |
| `server/tests/unit/services/test_chat_service_refactored.py` | summary_service あり/なし、continuation ありの分岐を検証する unit tests を追加。 |
| `server/tests/integration/chat_service_contract/test_summary_rollback.py` | `rollback_summary` marker に real-refactored の chat() summary wiring evidence（2 tests）を追加。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `ChatService._build_summary_context(session_id: str) -> None`
	- `SummaryService.get_latest_completed()` / `get_histories_after()` と
		`HistoryMapper.convert_to_llm_messages()` を使って MAIN 会話文脈を再構築。
- `ChatService._remove_tool_trace_message(messages)`
	- 再構築時に tool trace developer message の重複混入を除外。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| summary context 呼び出し条件を `chat_key == MAIN_CHAT_KEY && previous_response_id 未設定` に限定 | task.md と legacy 順序に合わせ、初回 MAIN ターンだけ再構築するため | 常時再構築（無駄な DB/read と文脈再構築コストが増える） |
| summary 起動判定を `_record_usage()` 後・`should_save=True` 前へ配置 | task.md の順序要件を満たし、legacy 呼び出し位置と揃えるため | END 応答後に非同期で呼ぶ（失敗時のログ整合が崩れる） |
| `_build_summary_context()` を refactored に native 実装 | legacy 委譲再導入禁止の制約を守るため | legacy `build_summary_context()` を呼ぶ（スコープ外かつ禁止） |

## 互換性メモ

- `SummaryService` が `None` の構成でも、summary context 再構築呼び出し自体は維持される（内部早期 return）。
- `check_should_start_summary()` は `_summary_service is not None` ガードでのみ実行される。
- `rollback_summary` / `pre_extraction_parity` の marker は green を維持。

## 次タスクへのフォローアップ

- Phase 5 以降で `build_summary_context()` を専用コンポーネントに抽出する際は、この task で追加した呼び出し箇所が変更対象になる。
- native refactored 実装で追加した summary context helper を source of truth とし、legacy 委譲再導入は行わない。

## 既知のパフォーマンス差異（Phase 5 フォローアップ）

legacy の `build_summary_context()` は `_summary_context_cache` を使用して増分フェッチを行う：
同一セッション・同一サマリ境界の連続ターンでは、前回取得済みの `last_history_id` 以降のみ DB から取得し、
それ以前の履歴はキャッシュから再利用する。

refactored の `_build_summary_context()` はこのキャッシュを持たない：
completed summary がある場合は毎ターン `get_histories_after(boundary_id)` を呼ぶため、
境界から現在ターンまでの全履歴が毎回フェッチされる。

これは正確性に影響しないが（結果は同等）、ターン数が多いセッションでは N 回の冗長 DB 読み取りが発生する。
Gate A の contract tests は呼び出し回数をアサートしないため、この差異はテストで検出されない。

**Phase 5 フォローアップ**: `_summary_context_cache` を refactored 実装にも追加するか、
専用コンポーネントへの抽出時にキャッシュ戦略を統一すること。

## 未解決の質問

なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。

## 検証サマリ

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/services/test_chat_service_refactored.py`
	- `46 passed`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/`
	- `17 passed, 905 deselected`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/`
	- `213 passed, 27 skipped, 682 deselected`
