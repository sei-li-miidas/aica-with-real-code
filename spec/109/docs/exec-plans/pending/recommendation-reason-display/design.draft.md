# Design: 推薦理由表示機能 (recommendation-reason-display)

Issue #109: ユーザーがポジション詳細チャットを開いたら、推薦理由文が表示されるように機能追加

---

## 概要

ポジション詳細ページを開いた際に、そのユーザー専用の推薦理由を LLM で生成して表示する機能を追加する。AB テストはせず一律表示し、効果を検証する。

推薦理由は REST API 経由で取得し（WebSocket とは独立）、`session_id × position_id` キーでDBにキャッシュする。キャッシュはハッシュベースで無効化し、ポジションデータまたは転職軸が変わった場合は再生成する。

---

## 既存コードベースの調査結果

### ポジション詳細チャットフロー
1. フロントエンドが `position_id` と `current_page = PageName.POSITION_DETAIL` を付けた WebSocket メッセージを送信
2. `chat_service._prepare_for_chat_turn` が `POSITION_DETAIL` ページを検知し、POSITION_GUIDE エージェントのクローンを作成
3. 初回メッセージ時: API から position_detail / company_detail / business_detail を取得
4. `POSITION_DETAIL_INQUIRY_START_PROMPT` に求人データを埋め込んで `DEVELOPER` ロールのメッセージとして会話コンテキストにセット

### 転職軸データ
- `workflow_answers` テーブル: `session_id`, `workflow_id="position_change_analyze"`, `answers (JSON)` で保存
- `WorkflowRepository` には `save_workflow_answer` のみ実装（`get` は未実装 → 今回追加）
- 未診断の場合: 一般的な転職理由（定型文）を代替として使用

### チャットエントリポイント（現行）
- `app/positions/page.tsx` に Fab ボタン（MIIBOアイコン）と吹き出し（初回のみ）が存在
- タップでチャットモーダルを開く
- 今回はこの Fab + 吹き出しを新しい推薦理由チップ UI に置き換える

### LLMサービスパターン
- `position_change_analyze_summary_service.py` が同様のパターン（`AsyncOpenAI` 直接利用、プロンプトは `files/prompts/*.txt`）
- 今回も同じパターンで `recommendation_reason_service.py` を作成する

### フロントエンド構造
- `app/positions/page.tsx`: ポジション詳細ページ
- チャットモーダルは `isChatOpen` state で制御
- `ChatResponseType` に `Recommendation = "recommendation"` が既にフロントエンド側に定義済み

---

## アーキテクチャ

```
フロント                     Agent                        DB
  │                           │                           │
  │ GET /positions/detail/... │                           │
  │──────────────────────→    │                           │
  │ ←── ポジション詳細 ──────  │                           │
  │                           │                           │
  │ GET /positions/           │                           │
  │  recommendation-reason/   │                           │
  │  {encrypted_position_id}  │                           │
  │──────────────────────→    │                           │
  │                           │ SELECT FROM               │
  │                           │  recommendation_reasons   │
  │                           │──────────────────────→    │
  │                           │ ←── hit / miss ─────────  │
  │                           │                           │
  │                           │ [miss or hash mismatch]   │
  │                           │  fetch position data      │
  │                           │  fetch workflow_answers   │
  │                           │  call LLM (OpenAI)        │
  │                           │  INSERT/UPDATE DB         │
  │                           │──────────────────────→    │
  │                           │ ←── saved ──────────────  │
  │ ←── {recommendation_reason} ─────────────────────────  │
```

---

## バックエンド設計

### 新設エンドポイント

```
GET /aica/agent/positions/recommendation-reason/{encrypted_position_id}
```

- セッション認証必須
- `encrypted_position_id` を復号して `position_id` を得る（既存の detail エンドポイントと同じ復号ロジック）
- レスポンス:
  ```json
  {
    "recommendation_reason": {
      "summary": "...",
      "sections": [
        {"title": "やりたいこととのマッチ", "body": "..."},
        {"title": "今の経験がどう使えるか", "body": "..."},
        {"title": "条件のズレについて", "body": "..."},
        {"title": "未来の自分の価値", "body": "..."}
      ]
    }
  }
  ```

### 新規ファイル

| ファイル | 役割 |
|---|---|
| `src/aica_agent/services/recommendation_reason_service.py` | キャッシュ確認・ハッシュ比較・LLM生成・DB保存のオーケストレーション |
| `src/aica_agent/repositories/recommendation_reason_repository.py` | `recommendation_reasons` テーブルの読み書き（UPSERT） |
| `src/aica_agent/files/prompts/9_RecommendationReason.txt` | LLMへの入力プロンプト（JSON出力指示を含む） |

### 既存ファイルの変更

| ファイル | 変更内容 |
|---|---|
| `src/aica_agent/endpoints.py` | `@router.get("/positions/recommendation-reason/{encrypted_position_id}")` を追記 |
| `src/aica_agent/repositories/workflow_repository.py` | `get_workflow_answer(session_id, workflow_id) -> dict \| None` を追加 |

### DBスキーマ（新規マイグレーション）

```sql
CREATE TABLE recommendation_reasons (
  id          BIGSERIAL    PRIMARY KEY,
  session_id  VARCHAR      NOT NULL,
  position_id BIGINT       NOT NULL,
  reason_text TEXT         NOT NULL,  -- JSON文字列
  input_hash  VARCHAR(64)  NOT NULL,  -- SHA-256 hex
  created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
  UNIQUE (session_id, position_id)
);
```

### ハッシュ計算対象

推薦理由生成に使う全入力フィールドの SHA-256:

**求人側**（position_detail / company_detail / business_detail から取得）:
- 年収（想定年収下限・上限）
- 残業時間
- 労働環境の特徴
- アピールポイント
- 実績のある福利厚生
- 福利厚生（休日休暇）

**求職者側**:
- `workflow_answers` の `position_change_analyze` 回答 JSON（未診断時は固定文字列 `"__no_diagnosis__"`）

ハッシュはこれらを辞書ソートした JSON 文字列から計算する。フィールドが `None` の場合は空文字列として扱う。

### キャッシュロジック

```python
cached = repo.get(session_id, position_id)
current_hash = compute_hash(position_data, workflow_answers)

if cached and cached.input_hash == current_hash:
    return parse_json(cached.reason_text)

reason = await llm.generate(position_data, workflow_answers)
repo.upsert(session_id, position_id, reason_json, current_hash)
return reason
```

### LLMプロンプト概要（`9_RecommendationReason.txt`）

- 求人データ（年収・残業・労働環境・アピールポイント・福利厚生）と転職軸を入力
- 出力は以下のJSONスキーマに従うよう指示:
  ```json
  {
    "summary": "string",
    "sections": [
      {"title": "string", "body": "string"}
    ]
  }
  ```
- セクションタイトルは固定（やりたいこととのマッチ / 今の経験がどう使えるか / 条件のズレについて / 未来の自分の価値）
- 転職軸未診断の場合は一般的な転職理由（「より良い環境・待遇・成長機会を求めている」旨）を使用
- モデル設定: `position_change_analyze_summary` と同様に `config.yml` の `model_list` から `recommendation_reason` 用エントリで指定

### エラー処理（バックエンド）

| ケース | 挙動 |
|---|---|
| LLM生成失敗（タイムアウト・APIエラー） | 503 を返す、DB には保存しない |
| position_id 復号失敗 | 400 を返す |
| ポジション情報取得失敗 | 503 を返す |
| DB 書き込み失敗 | ログを記録し、生成済みテキストをそのまま返す（次回アクセス時に再生成） |

---

## フロントエンド設計

### UIの状態遷移

```
[ローディング]               [準備完了・初回]              [通常]
「あなただけの               「ここに注目！ ＞」             「ここに注目！ ＞」
 注目ポイントを準備中」        + スパークルアニメーション       (アニメーションなし)
 (MIIBOアイコン付きチップ)     (ローディング→成功の遷移時に
                               1回だけ再生。キャッシュヒット
                               でも遷移があれば再生する)
```

チップをタップするとチャットモーダルが開く。

### チャットモーダル内の推薦理由表示

```
┌──────────────────────────────────┐
│ 💡 ここに注目！             ∧   │  ← タップで折り畳み
│                                   │
│ [summary 段落]                    │
│                                   │
│ ┌──────────────────────────────┐ │
│ │ やりたいこととのマッチ         │ │
│ │ [body]                        │ │
│ └──────────────────────────────┘ │
│ ┌──────────────────────────────┐ │
│ │ 今の経験がどう使えるか         │ │
│ │ [body]                        │ │
│ └──────────────────────────────┘ │
│ ┌──────────────────────────────┐ │
│ │ 条件のズレについて             │ │
│ │ [body]                        │ │
│ └──────────────────────────────┘ │
│ ┌──────────────────────────────┐ │
│ │ 未来の自分の価値               │ │
│ │ [body]                        │ │
│ └──────────────────────────────┘ │
│                                   │
│ ※これはAIが求人情報を基に作成した │
│ ものです。内容の正確性を保証する   │
│ ものではありません。最新の求人情報 │
│ を必ずご確認ください。            │
│                                   │
│ 🤖 この求人について、気になる点や  │  ← 通常チャット開始メッセージ
│    ご質問はありますか？            │
│    お気軽にお尋ねください。        │
└──────────────────────────────────┘
```

折り畳み状態では「ここに注目！」ヘッダーのみ表示。

### エラー処理（フロントエンド・B+C方式）

1. API呼び出し時: ローディング状態のチップを表示
2. 失敗時: 「推薦理由を読み込み中...」プレースホルダーを表示して1回リトライ
3. リトライも失敗時: 「推薦理由を取得できませんでした」エラーメッセージを表示

### 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `app/positions/page.tsx` | Fab + 吹き出し を削除し、推薦理由チップ UI を追加。マウント時に `fetchRecommendationReason()` を呼び出す |
| `components/RecommendationReasonChip.tsx` | 新規: ローディング / スパークル / 通常 の3状態チップ。クリックでチャットモーダルを開く |
| `components/RecommendationReasonModal.tsx` | 新規: 展開/折り畳み対応の推薦理由セクション一覧。免責文を固定テキストとして末尾に表示 |
| `app/positions/apiRequest.ts` | `fetchRecommendationReason(encryptedPositionId: string)` を追加（既存の `getPositionData` 等と同じパターン） |

---

## テスト方針

### バックエンド（unit）

- `recommendation_reason_service.py`
  - キャッシュヒット（ハッシュ一致）→ LLM を呼ばずキャッシュを返す
  - キャッシュヒット（ハッシュ不一致）→ LLM を呼んでキャッシュを上書き
  - キャッシュミス → LLM を呼んで新規保存
  - LLM 失敗 → 503 を返す、DB に保存しない
- `workflow_repository.py`
  - `get_workflow_answer`: レコードあり / なし の両ケース

### フロントエンド（unit）

- `RecommendationReasonChip`: ローディング / 成功（通常・スパークル）/ エラー 各状態のレンダリング
- `RecommendationReasonModal`: 展開 / 折り畳み の切り替え、セクション一覧の表示

### E2E

- ポジション詳細ページを開いてローディングチップが表示されること
- 推薦理由取得成功後に「ここに注目！」チップが表示されること
- チップをタップして推薦理由モーダルが開くこと
- 推薦理由モーダルを開いた後、通常のチャット入力・送信・返答受信が正常に行われること（既存のポジション詳細チャット機能が引き続き動作すること）
- 推薦理由 API がエラーを返した場合（503 等）、エラーメッセージが表示され、チャットモーダルへのアクセスは引き続き可能であること
