# 引き継ぎ: task-1-summary-service-constructor-wiring

## 概要

`chat_service_refactored.ChatService` の constructor に `llm_output_guard` と
`summary_service` の DI 受け口を追加し、container 側の wiring を整合させた。
`model_list` が未設定のテスト/最小構成では `SummaryService` を生成しない
optional wiring にして、既存 rollback DI 契約を維持した。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/src/aica_agent/services/chat_service_refactored.py` | constructor に `llm_output_guard: LLMOutputGuard \| None` と `summary_service: SummaryService \| None` を追加し、`self.llm_output_guard` を DI 優先初期化、`self._summary_service` を保持するよう更新。 |
| `server/src/aica_agent/containers.py` | `SummaryRepository` / optional `SummaryService` builder / `LLMOutputGuard` provider を追加。`chat_svc` provider から `llm_output_guard` と `summary_service` を渡す wiring に更新。 |
| `server/tests/unit/services/test_chat_service_refactored.py` | constructor の DI 有無（`llm_output_guard`/`summary_service`）を検証する単体テストを追加。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `containers._build_optional_summary_service(model_list, summary_repository, chat_repository)`
  - `model_list` に summary 用モデルがある場合のみ `SummaryService` を生成。
  - 無い場合は `None` を返し、既存 rollback/最小構成テストを壊さない。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| `ChatService` の guard/summary を optional DI 受け口にした | task-2 で summary 呼び出しを追加する前提として依存境界を固定しつつ、未注入時の後方互換を維持するため | constructor 内で常に内部生成（DIなし） |
| container で `summary_service` を常時生成せず optional 化した | rollback DI テストの stub config で `model_list=None` があり、summary service 必須化すると回帰するため | `ConversationSummaryService` を常時生成し、テスト側だけ config を増やす |
| `LLMOutputGuard` は provider から注入し、未注入 fallback を残した | DI 方針を明確化しつつ既存単体テスト・直接生成コードの互換を保つため | 完全 DI 必須化して constructor 引数を必須化 |
| `summary_svc` を `providers.Callable` にした（`providers.Singleton` ではなく） | rollback DI テストで `container.summary_svc.override(providers.Object(None))` によるオーバーライドを簡潔に行えるため。DB セッション安全性は `SummaryRepository` が `session_factory` callable を保持するため `Singleton` でも問題ないが、DI オーバーライド互換性の観点から `Callable` を選択した。task-3 で optional ガードを外して必須化する際は `providers.Singleton` に変更可。 | `providers.Singleton`（DB セッション lifecycle は問題ないが DI テストオーバーライドが複雑化） |
| `ConversationSummaryService.__init__` で `AsyncOpenAI()` を eager 生成 | このサービスは `providers.Singleton` のため constructor は 1 回のみ実行される。lazy init の `_get_openai_client()` パターンは不要であり、プロンプト/スキーマのファイル読み込みと同様に起動時 1 回で完結させる方が明確。PR review `#discussion_r3338502876` でリクエストごとのファイル I/O 排除を目的に intentional に変更した（コミット ba8f8a7）。`AsyncOpenAI()` は `OPENAI_API_KEY` 不在でもコンストラクタは成功し、API 呼び出し時に初めてエラーになる。`_build_optional_conversation_summary_service` ガードにより summary model 未設定の環境では constructor 自体が呼ばれない。 | `self._openai_client = None` + lazy `_get_openai_client()`（`LLMService` のパターン、Singleton化前は正しかった） |

## 互換性メモ

- `summary_service` が `None` の場合でも `ChatService` は正常に初期化される。
- `llm_output_guard` 未注入時は従来どおり `LLMOutputGuard()` をローカル生成する。
- rollback marker の既存契約（特に `rollback_di`）は維持。

## レビュー/修正ログ

1. Iteration 1
	- Reviewed: constructor DI 追加と container wiring の整合。
	- Fixed: `containers.py` の import 重複（`chat_repo` 二重 import）を解消。
	- Why: 可読性低下と将来の lint エラー予防。
2. Iteration 2
	- Reviewed: rollback DI 契約（stubbed config での `container.chat_svc()` 解決）。
	- Fixed: `model_list=None` で `ConversationSummaryService` 生成が失敗する回帰を修正し、optional summary builder を導入。
	- Why: task-1 の目的は依存境界固定であり、既存 rollback 契約を壊さないことが必須のため。

## 次タスクへのフォローアップ

- task-2-build-summary-context-turn-wiring は task-1 が完了し `rollback_summary` が pass になってから着手する。

## 未解決の質問

なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
