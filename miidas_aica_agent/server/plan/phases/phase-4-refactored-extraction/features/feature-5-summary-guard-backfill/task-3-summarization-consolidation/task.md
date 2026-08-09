# タスク: task-3-summarization-consolidation

## 目的

LLM ベースの要約処理を `ConversationSummaryService` に一本化する。
現在 `LLMService` に重複している `summarize_position_detail_chat()` と 5 つのヘルパーメソッド
（`_build_summary_input_items`、`_build_text_message`、`_format_summary_tool_response`、
`_extract_position_count_from_tool_output`、`_generate_position_search_fake_result`）を
`LLMService` から削除し、`ConversationSummaryService` を要約ロジックの単一ホームにする。

## 背景

`LLMService.summarize_position_detail_chat()` と `ConversationSummaryService.summarize_conversation()` は
5 つのヘルパーメソッドを完全に重複して持っている（コードが同一）。
2 つのメソッドが異なる点は 1 つだけ：

- `summarize_conversation`: `SummaryGenerationError` を raise（呼び出し元がリトライを制御）
- `summarize_position_detail_chat`: 例外をすべてキャッチして `None` を返す（fire-and-forget）

両者とも `async def` だが、呼び出しパターンが異なる：
- `summarize_conversation` → `asyncio.create_task()` 経由でバックグラウンド実行
- `summarize_position_detail_chat` → `await` でリクエストをブロック

## 最初に読むコンテキスト

- `server/src/aica_agent/services/conversation_summary_service.py`
- `server/src/aica_agent/services/llm_service.py`（lines 20–36, 71, 432–590）
- `server/src/aica_agent/services/chat_service_refactored.py`（`summarize_position_detail_chat()`）
- `server/src/aica_agent/services/chat_service.py`（line 1341）
- `server/src/aica_agent/containers.py`（`conversation_summary_svc` Singleton）
- `server/tests/integration/chat_service_contract/test_summary_rollback.py`

## スコープ

許可する変更:
- `files/prompts/7_PositionDetailInquirySummary.txt`: 新規作成
- `conversation_summary_service.py`: プロンプトファイル読み込みと `summarize_position_detail_chat()` を追加
- `llm_service.py`: 要約関連コード（定数・属性・メソッド・import）をすべて削除
- `chat_service_refactored.py`: constructor に `conversation_summary_svc: ConversationSummaryService`（必須）を追加し、呼び出し元を切り替え
- `chat_service.py`: 同上（legacy）
- `containers.py`: `_build_optional_conversation_summary_service` / `_build_optional_summary_service` を削除し、`ConversationSummaryService` と `SummaryService` を直接 Singleton / Factory で登録。rollback DI テスト用の stub config に summary model を追加
- テスト: `test_llm_service.py`（削除）、`test_conversation_summary_service.py`（追加）、チャットサービス系（モック対象変更）、`test_summary_rollback.py`（import と mock 対象変更）、rollback DI テスト fixture 更新

許可しない変更:
- `SummaryService` 内部ロジックの変更
- `ConversationSummaryService.__init__` のシグネチャ変更
- `summarize_conversation()` の動作変更
- legacy 委譲の再導入

## 実装手順

### Step 1a — `files/prompts/7_PositionDetailInquirySummary.txt`（新規作成）

`llm_service.py` の `POSITION_DETAIL_INQUIRY_SUMMARY_PROMPT` 定数（lines 20–36）の内容をそのままファイルに書き出す。
他のプロンプトファイル（`6_ConversationSummary.txt` など）と同じ場所に置く。

### Step 1b — `conversation_summary_service.py`

1. `__init__` でプロンプトファイルを読み込む（`6_ConversationSummary.txt` と同じパターン）:
   ```python
   position_detail_prompt_path = (
       Path(__file__).resolve().parent.parent
       / "files" / "prompts" / "7_PositionDetailInquirySummary.txt"
   )
   self._position_detail_inquiry_summary_prompt = position_detail_prompt_path.read_text(encoding="utf-8")
   ```
2. `async def summarize_position_detail_chat(self, chat_histories: list[ChatHistory]) -> str | None` を追加:
   - `self._build_summary_input_items(chat_histories)` を呼び出す（既存ヘルパーを再利用）
   - 空なら `None` を返す
   - `self._position_detail_inquiry_summary_prompt` を developer メッセージとして末尾に追加
   - `self._openai_client.responses.create(model=..., input=..., **model_settings)` を呼び出す（`text=` json_schema kwarg は付けない）
   - 成功時は `response.output_text` を返す；例外はすべてキャッチして `self.logger.exception` でログし `None` を返す

### Step 2 — `llm_service.py`（削除対象）

| 対象 | 内容 |
| --- | --- |
| 定数 | `POSITION_DETAIL_INQUIRY_SUMMARY_PROMPT`（lines 20–36）、`POSITION_SEARCH_FAKE_RESULT`（line 71） |
| クラス属性 | `_openai_client: AsyncOpenAI \| None`（line 86）、`_summary_model: dict[str, Any] \| None`（line 89） |
| `__init__` | `self._openai_client = None`、`self._summary_model = None` |
| `init()` ブロック | `summary_models` フィルタ・バリデーション・代入ブロック（lines 175–188） |
| メソッド | `summarize_position_detail_chat`、`_get_openai_client`、`_build_summary_input_items`、`_format_summary_tool_response`、`_extract_position_count_from_tool_output`、`_generate_position_search_fake_result`、`_build_text_message` |
| import 削除 | `import json`、`from openai import AsyncOpenAI`、`from domain.entities.chat_history import ChatHistory`、`LLMMessageRole`（`ToolName` は他所で使用するため残す） |

### Step 3 — `chat_service_refactored.py`

1. `from services.conversation_summary_service import ConversationSummaryService` を追加
2. constructor に `conversation_summary_svc: ConversationSummaryService` パラメーターを追加（`None` なし — コンテナが起動時に保証する）し、`self._conversation_summary_svc = conversation_summary_svc` で保持
3. `summarize_position_detail_chat()` 内の `self._llm_svc.summarize_position_detail_chat(...)` を `await self._conversation_summary_svc.summarize_position_detail_chat(position_chat_histories)` に置き換え（None ガード不要）

### Step 4 — `chat_service.py`（legacy）

Step 3 と同じパターン。呼び出し元は line 1341。

### Step 5 — `containers.py`

**削除**:
- `_build_optional_conversation_summary_service` 関数（optional ラッパー）
- `_build_optional_summary_service` 関数（同上）

**変更後**:
```python
conversation_summary_svc = providers.Singleton(
    conversation_summary_service.ConversationSummaryService,
    model_list=config.model_list,
)

summary_svc = providers.Factory(
    summary_service.SummaryService,
    conversation_summary_service=conversation_summary_svc,
    summary_repository=summary_repository,
    chat_repository=chat_repository,
)
```

`chat_svc` に `conversation_summary_svc=conversation_summary_svc` を追加で渡す。summary モデルが未設定なら `ConversationSummaryService.__init__` が起動時に `ValueError` を raise する（fail-fast を維持）。

### Step 6 — テスト

| ファイル | 変更内容 |
| --- | --- |
| `test_llm_service.py` | `TestSummarizePositionDetailChat`、`TestBuildSummaryInputItems`、`TestBuildTextMessage`、`test_warns_when_multiple_summary_models_defined` を削除。`test_raises_exception_when_no_summary_models_defined` は `test_conversation_summary_service.py` へ移動 |
| `test_conversation_summary_service.py` | `TestSummarizePositionDetailChat` クラスを追加（成功、空履歴、API エラー、入力フォーマット、model settings の 5 テスト）；`test_raises_when_no_summary_models_defined` を追加（起動時 fail-fast の担保） |
| `test_chat_service.py` / `test_chat_service_refactored.py` | モック対象を `mock_llm_svc.summarize_position_detail_chat` → `mock_conversation_summary_svc.summarize_position_detail_chat` に変更（`conversation_summary_svc=None` ガードテストは追加しない） |
| rollback DI テスト | `model_list=None` の stub config に summary model エントリを追加（`ConversationSummaryService` が必須になるため） |
| `test_summary_rollback.py` | `POSITION_DETAIL_INQUIRY_SUMMARY_PROMPT` は Python 定数ではなくなるのでファイルから直接読み込む；`_make_summary_llm_service()` を `ConversationSummaryService` ベースに書き換え；`svc._llm_svc` → `svc._conversation_summary_svc` に置き換え |

## 挙動上の注意

- summary モデル未定義時の fail-fast は `ConversationSummaryService.__init__` の `ValueError` で継続して保証される（`LLMService.init()` から担当が移るだけ）。
- `_build_optional_conversation_summary_service` の optional ラッパーは生産環境では dead code だった（`LLMService` が先に失敗するため `None` が返ることがなかった）。task-1 でテスト互換のために導入されたが、このタスクで rollback DI テストの stub config を修正してクリーンに削除する。
- `ConversationSummaryService` のインスタンスは `providers.Singleton` のため、`summarize_position_detail_chat()` と `summarize_conversation()` が同一インスタンスを共有する。これは意図した動作。

## 必須テスト

```bash
# unit tests
OPENAI_API_KEY="sk-test" PYTHONPATH=server/src/aica_agent \
  .venv-server/bin/python -m pytest -q server/tests/unit/

# rollback_summary
PYTHONPATH=server/src/aica_agent \
  .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/

# pre_extraction_parity
PYTHONPATH=server/src/aica_agent \
  .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/

# integration (summary rollback contract)
OPENAI_API_KEY="sk-test" PYTHONPATH=server/src/aica_agent \
  .venv-server/bin/python -m pytest -v \
    server/tests/integration/chat_service_contract/test_summary_rollback.py
```

## ロールバック確認対象

- `rollback_summary`: `pytest -q -m rollback_summary server/tests/`
- `pre_extraction_parity`: `pytest -q -m pre_extraction_parity server/tests/`

## 完了条件

- `verification.md` の必須コマンドがすべて `pass` または文書化された免除がある。
- `handoff.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
