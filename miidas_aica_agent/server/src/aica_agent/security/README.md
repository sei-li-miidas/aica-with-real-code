# セキュリティモジュール - プロンプトインジェクション対策

## 概要

本モジュールは、LLM出力をストリーミング中に監視し、
**禁止ワード（システム内部情報やツール名など）の漏洩を防止**します。

現在の防御は **Trie木ベースの禁止ワード検知のみ** です。

```
┌─────────────┐     ┌────────────────┐     ┌──────────────────────────────────┐
│   ユーザー   │ --> │  LLM (OpenAI)  │ --> │ LLMOutputGuard (ストリーミング)   │ --> ユーザーへ
│   入力      │     │                │     │ • Trie木（禁止ワード検知）       │
└─────────────┘     └────────────────┘     └──────────────────────────────────┘
```

---

## モジュール構成

```
security/
├── README.md
├── __init__.py
├── llm_output_guard.py        # Trie木ベースのLLM出力検知
└── output_forbidden_words.csv # 禁止ワードリスト
```

---

## 1. LLMOutputGuard（禁止ワード検知本体）

### ファイル
- `llm_output_guard.py`

### 役割
- Trie木で禁止ワードを文字単位に検知
- セッション単位でストリーミング状態を管理

### 主なAPI

#### `process_stream_chunk(session_id, chunk) -> list[str]`
- ストリーミングチャンクを検知
- 禁止ワードに完全一致した場合は `ForbiddenWordDetectedException` を送出
- 安全な文字列のみ返却

#### `finalize_stream(session_id) -> list[str]`
- 応答終了時の最終処理
- Trieの途中一致で保留していた文字列を安全確定として解放

#### `reset_session_for_new_response(session_id)`
- 新しい応答ターン開始時にセッション内状態をリセット

#### `remove_session(session_id)`
- セッション状態をメモリから削除（DBセッションは保持）

---
### 検知時の挙動
- `ForbiddenWordDetectedException` を送出
- `chat_service` 側でセッションブロック処理を実行

### 検知フロー

1. 受信文字を正規化（小文字化・記号除去）
2. Trie木を1文字ずつ探索
3. 前方一致中は `pending_buffer` に保留
4. 完全一致したら `ForbiddenWordDetectedException` を送出
5. 不一致なら `pending_buffer` を解放して安全文字として返却

### 禁止ワードデータ

- ファイル: `output_forbidden_words.csv`
- 例:
  - ツール名
  - システムプロンプト断片
  - エージェント識別子

### 計算量

- 文字列長を `m` とすると概ね `O(m)`
- 各文字の遷移は辞書アクセスで高速

---

## 2. chat_service.py での統合

### ファイル
- `services/chat_service.py`

### 実行タイミング
- LLMの `ResponseTextDeltaEvent` を受けるたびに `process_stream_chunk()`
- ストリーミング終了時に `finalize_stream()`

### 検知時の挙動
- `ForbiddenWordDetectedException` を捕捉
- セッション状態をクリーンアップ
- DBセッションをブロック
- ユーザーへ定型エラーメッセージを返却

---

## 3. セッション管理ポリシー

### メモリで保持する状態
- Trie探索位置
- 途中一致の保留バッファ
- 処理文字数などの統計

### ブロック時の扱い
- メモリ状態は削除
- DB上の会話履歴は保持
- フロントリロード後の運用はアプリ仕様に従う
