# AICA Workspace

このワークスペースは、AI転職アドバイザーを構成する複数プロジェクトをまとめて開発するためのルートです。

利用者向けの主要な実行経路は次のとおりです。

1. `miidas_aica_frontend`
   Next.js フロントエンド。ユーザーのチャット UI とポジション詳細画面を提供します。
2. `miidas_aica_agent/server`
   FastAPI ベースの Agent サーバー。WebSocket `/chat` と REST API を提供し、LLM と MCP を仲介します。
3. `miidas_aica_mcp`
   Go 製 MCP サーバー。Agent からのツール呼び出しを受け、AICA API に委譲します。
4. `miidas_aica_api`
   Go 製 API サーバー。ポジション検索、詳細取得、職種/業種/勤務地関連 API を提供します。

補助プロジェクト:

- `miidas_aica_agent/cli`
  バッチ、マイグレーション、メンテナンス系処理。
- `miidas_aica_agent/e2e`
  Agent サーバーとの E2E 検証クライアント。

## Project Map

| Project | Role | Main Tech | Main Entry | Default Port |
| --- | --- | --- | --- | --- |
| `miidas_aica_frontend` | チャット UI、ポジション詳細 UI | Next.js / React / TypeScript | `start_frontend.sh` | `80` |
| `miidas_aica_agent/server` | WebSocket と REST API、LLM 実行 | FastAPI / Python | `start_server.sh` | `8000` |
| `miidas_aica_mcp` | MCP ツール公開、API への橋渡し | Go / `mcp-go` | `start_server.sh` | `8080` |
| `miidas_aica_api` | 業務 API、検索/詳細/マスター取得 | Go | `start_server.sh` | `10001` |
| `miidas_aica_agent/cli` | バッチ、DB メンテ | Python | `cli` 配下スクリプト | - |
| `miidas_aica_agent/e2e` | E2E テストクライアント | Python | `start_test.sh` | - |

## Runtime Relation

- Frontend は `NEXT_PUBLIC_AGENT_ENDPOINT` で Agent の WebSocket `/aica/agent/chat` に接続します。
- Frontend は `NEXT_PUBLIC_API_ENDPOINT` で Agent の REST API `/aica/agent/...` を利用します。
- Agent は `AICA_AGENT_MCP_ENDPOINT` で MCP の `/sse` に接続します。
- Agent は `AICA_AGENT_API_ENDPOINT` で AICA API の `/aica/mcptool/...` を直接利用します。
- MCP は `AICA_MCP_API_SERVER` を使って AICA API を呼び出します。
- API/Agent/MCP はいずれも DB や周辺基盤に依存します。

## Startup Order

ルートの `start.sh` は次の順で起動します。

1. `miidas_aica_api`
2. `miidas_aica_mcp`
3. `miidas_aica_agent/server`
4. `miidas_aica_frontend`

この順序になっているのは、Agent が MCP と API を利用し、Frontend が Agent を利用するためです。

## Sequence Diagram

このワークスペースでは、UI から見た主要フローは 1 つではありません。  
特に `miidas_aica_frontend` は WebSocket と REST API を使い分けており、画面操作ごとに経路が変わります。

### 1. セッション初期化

既存セッションの再開時に走る過去会話復元は、[2. 画面初期化時の過去会話復元](#2-画面初期化時の過去会話復元) を参照してください。  
また、フロントエンドはチャット画面初期化時に現在の求人検索フィルターを取得し、条件が揃っていれば `FilterChipBar` を表示します。`JobSearchFilterDialog` のモーダル本体は、そのバーをクリックしたときに開きます。

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend<br/>miidas_aica_frontend
    participant AG as Agent Server<br/>miidas_aica_agent/server
    participant Pos as PositionService
    participant API as AICA API<br/>miidas_aica_api
    participant LLM as LLMService

    User->>FE: チャット画面を開く
    FE->>AG: WebSocket /aica/agent/chat 接続
    AG->>AG: accept and initial maintenance check
    AG->>AG: session initialization start
    AG->>Pos: current search filter を取得
    Pos->>API: GET /aica/mcptool/positions/search_filter/current
    API-->>Pos: current filter and ToolName
    Pos-->>AG: current filter
    AG->>LLM: session-local agents を clone
    LLM-->>AG: initialized agents
    alt new session
        AG-->>FE: initial greeting
    else existing session
        AG-->>FE: restart response
    end
    FE->>AG: GET /aica/agent/positions/search_filter/current
    AG->>Pos: current search filter を取得
    Pos->>API: GET /aica/mcptool/positions/search_filter/current
    API-->>Pos: current filter and ToolName
    Pos-->>AG: current filter
    AG-->>FE: SearchFilters
    FE->>FE: filter state を hydrate
    opt jobtypes, location, salary are ready
        FE-->>User: FilterChipBar を表示
    end
    FE-->>User: 会話開始 or 再開
```

### 2. 画面初期化時の過去会話復元

チャット画面やポジション詳細画面では、画面表示時に過去会話の有無確認と履歴取得が走ります。

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant AG as Agent Server
    participant Repo as Chat Repository

    User->>FE: チャット画面または詳細画面を開く
    alt position detail page
        FE->>AG: GET /aica/agent/chat/{position_id}/exist
        AG->>Repo: 対象ポジションの履歴有無確認
        Repo-->>AG: exist / not exist
        AG-->>FE: 200 or 404
    end
    FE->>AG: GET /aica/agent/chat/previous[/ {position_id}]?before_id=...&limit=...
    AG->>Repo: 過去チャット履歴取得
    Repo-->>AG: PreviousChatHistories
    AG-->>FE: 履歴 + NoMoreUserMessageLeft
    FE-->>User: 過去会話を復元表示
```

### 3. チャット経由のポジション検索

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend<br/>miidas_aica_frontend
    participant AG as Agent Server<br/>miidas_aica_agent/server
    participant LLM as LLM Runtime
    participant MCP as MCP Server<br/>miidas_aica_mcp
    participant API as AICA API<br/>miidas_aica_api
    participant DB as DB / Search Backend

    User->>FE: チャットで条件を送信
    FE->>AG: WebSocket /aica/agent/chat
    AG->>LLM: 会話入力を渡す
    LLM->>MCP: MCP tool call
    MCP->>API: POST /aica/mcptool/positions/search
    API->>DB: 検索条件解決、DB/MV2 検索
    DB-->>API: 検索結果
    API-->>MCP: JSON response
    MCP-->>LLM: tool result
    LLM-->>AG: 応答文 + 検索結果
    AG-->>FE: WebSocket stream response
    FE-->>User: メッセージと求人一覧を表示
```

### 4. フィルターモーダルからの職種別再検索

`JobSearchFilterModal` では、チャットで一度得た検索条件を UI 上で再編集し、`jobtype_specific` REST API を直接叩いて再検索する経路があります。

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend<br/>Filter Modal
    participant AG as Agent Server
    participant API as AICA API
    participant DB as DB / Search Backend

    User->>FE: 職種・年収・勤務地・詳細条件を変更
    FE->>AG: POST /aica/agent/positions/search/jobtype_specific
    AG->>API: POST /aica/mcptool/positions/search/jobtype_specific
    API->>DB: 職種別条件で検索
    DB-->>API: 検索結果
    API-->>AG: JSON response
    AG-->>FE: SearchResult
    FE-->>User: チャット一覧へ再検索結果を追加表示
```

### 5. 職種切り替え時の詳細フィルター取得

職種グループを切り替えると、その職種専用の `OtherFilters` を取得して UI を組み替えます。

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend<br/>Filter Modal
    participant AG as Agent Server
    participant Repo as Agent Repository / Cache

    User->>FE: 別の職種グループを選択
    FE->>AG: GET /aica/agent/positions/search_filter/jobtype?JobtypeName=...
    AG->>Repo: 職種別フィルター取得
    Repo-->>AG: OtherFilters / SelectedFilterOptions
    AG-->>FE: SearchFilters
    FE-->>User: 職種専用の詳細条件 UI を表示
```

### 6. ポジション詳細画面の取得

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend<br/>miidas_aica_frontend
    participant AG as Agent Server<br/>miidas_aica_agent/server
    participant API as AICA API<br/>miidas_aica_api
    participant Cache as Agent Cache / Repository
    participant DB as DB

    User->>FE: ポジション詳細画面を開く
    FE->>AG: GET /aica/agent/positions/detail/{encrypted_position_id}
    AG->>AG: position_id を復号
    AG->>Cache: キャッシュ確認
    alt cache hit
        Cache-->>AG: 詳細データ
    else cache miss
        AG->>API: POST /aica/mcptool/positions/detail/{position_id}
        API->>DB: 詳細取得
        DB-->>API: ポジション詳細
        API-->>AG: JSON response
        AG->>Cache: キャッシュ保存
    end
    AG-->>FE: 詳細データを返却
    FE-->>User: ポジション詳細を表示
```

### 7. おすすめポジションの取得

検索結果カード配下の recommendation UI は、Agent REST API を経由しておすすめ一覧を取得します。

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend<br/>Recommendation UI
    participant AG as Agent Server
    participant API as AICA API
    participant DB as DB

    User->>FE: おすすめテーマを開く
    FE->>AG: GET /aica/agent/positions/recommendations/{search_key}/{encrypted_theme}
    AG->>API: GET /aica/mcptool/positions/recommendations/{theme}
    API->>DB: テーマに基づく求人取得
    DB-->>API: おすすめ求人
    API-->>AG: Positions
    AG-->>FE: SearchKey + Positions
    FE-->>User: おすすめカード一覧を表示
```

### 8. 検索結果の「もっと見る」

初回検索結果の続きを取得するときは、Frontend が Agent の REST API を呼び、Agent が保存済み検索結果を元にページングします。

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant AG as Agent Server
    participant Cache as Agent Position Cache

    User->>FE: 「もっと見る」を押す
    FE->>AG: GET /aica/agent/positions/search/{search_key}/{offset}?limit=...
    AG->>Cache: 既存検索結果から続き取得
    Cache-->>AG: TotalPositionCount + next Positions
    AG-->>FE: 追加求人一覧
    FE-->>User: 現在の検索結果に追記表示
```

### 9. 応募開始から応募確定まで

応募・登録導線には少なくとも 2 つのトリガーがあります。

- チャット上でユーザーが「登録したい」「応募したい」と伝え、LLM が MCP の `form_registration` / `form_application` ツールを呼ぶ
- ポジション詳細画面でユーザーが応募ボタンを押す

下記は、その 2 つのトリガーと、その後の応募確定フローをまとめたものです。

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant AG as Agent Server
    participant LLM as LLM Runtime
    participant MCP as MCP Server
    participant UserSvc as User Service
    participant Ext as MIIDAS / External API

    alt Trigger 1: chat message
        User->>FE: 応募や登録の意図を含むメッセージを送信
        FE->>AG: WebSocket /aica/agent/chat
        AG->>LLM: 会話入力を渡す
        LLM->>LLM: ユーザー意図から登録/応募導線が必要と判断
        LLM->>MCP: form_registration or form_application
        MCP-->>LLM: フォーム案内メッセージ
        LLM-->>AG: 登録/応募導線の応答
        AG-->>FE: チャット上で案内
    else Trigger 2: position detail button
        User->>FE: ポジション詳細画面で応募ボタンを押す
        FE->>AG: POST /aica/agent/apply/{position_id}/start
        AG->>UserSvc: start_apply()
        UserSvc-->>AG: session_status
        AG-->>FE: 応募セッション開始
    end

    User->>FE: 必要に応じてプロフィール入力・確認
    FE->>AG: POST /aica/agent/profile/basic<br/>/profile/education<br/>/profile/experience<br/>/profile/preferences
    AG->>UserSvc: プロフィール保存
    UserSvc-->>AG: 保存結果
    AG-->>FE: Success/Validation result

    User->>FE: 応募確定
    FE->>AG: POST /aica/agent/apply/finish
    AG->>UserSvc: finish_apply()
    UserSvc->>Ext: 登録/応募処理
    Ext-->>UserSvc: 結果
    UserSvc-->>AG: ApplyResult + cookies
    AG-->>FE: 応募結果

    User->>FE: 個別ポジションへ応募
    FE->>AG: POST /aica/agent/apply/position/{position_id}
    AG->>UserSvc: apply_position()
    UserSvc->>Ext: 面談応募 API
    Ext-->>UserSvc: 結果
    UserSvc-->>AG: PositionID / status
    AG-->>FE: 最終応募結果
```

### 10. Workflow の提示・回答・中断

`workflow.md` のフローを、Frontend から Agent までのメッセージ往復に寄せてシーケンス化したものです。

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant WS as WebSocketProvider
    participant EP as Endpoint<br/>process_chat_messages
    participant CS as ChatService
    participant WFS as WorkflowService
    participant LLM as LLMService
    participant API as REST API

    EP-->>WS: response_type: workflow
    WS->>FE: createWorkflowItem + display_type 判定
    alt inline workflow
      FE->>FE: setInlineWorkflow
      alt 初期メニューワークフロー (id: initial_menu)
        FE->>FE: フッターを非表示 (HideFooterReason: initialMenuWorkflow)
      end
      FE-->>User: チャット内に設問を表示
    else modal workflow
      FE->>FE: setModalWorkflow
      FE-->>User: WorkflowModal を表示
    end

    alt ユーザーが回答して決定
      User->>FE: 選択肢/自由入力を編集して送信
      opt position_change_analyze ワークフロー
        Note over FE,API: ステップ4回答完了時にサマリー生成APIを呼ぶ
        FE->>API: POST /workflow/position_change_analyze/generate_summary
        API-->>FE: summary テキスト
        FE-->>User: 最終ステップにサマリーを表示
        Note over FE: 全ステップ回答完了後、各ステップのQ&Aをチャットメッセージとして追加
        FE->>FE: addOrUpdateMainChatMessageItem (ステップ数分)
      end
      FE->>WS: request_type: workflow_answers_submitted
      WS->>EP: workflow_id + answers
      EP->>CS: workflow_submitted
      CS->>WFS: process_workflow_submission
      WFS->>WFS: 定義読込/回答バリデーション/保存
      WFS-->>CS: 回答要約を返却
      CS->>CS: chat 入力へ要約を注入
    else ユーザーが中断
      User->>FE: 中断ボタンを押下
      FE->>WS: request_type: workflow_cancelled
      WS->>EP: workflow_id
      EP->>CS: workflow_cancelled
      CS->>CS: キャンセル文脈メッセージ作成
    end

    CS->>LLM: chat
    LLM-->>EP: 応答ストリーム
    EP-->>WS: チャット応答
    WS-->>FE: 応答反映
    FE-->>User: 会話を継続表示
```

## Project-Level Processing Docs

各プロジェクト内部の詳細フローは、それぞれの README に移しました。  
ルート README では全体構造とプロジェクト間シーケンスを見て、個別処理は以下を参照してください。

- [miidas_aica_frontend/README.md](https://github.com/MIIDAS-Company/miidas_aica_frontend/blob/develop/README.md)
  チャット画面初期化、WebSocket ストリーム、検索フィルター復元、REST ベース画面処理のフローをまとめています。
- [miidas_aica_agent/server/README.md](https://github.com/MIIDAS-Company/miidas_aica_agent/blob/master/server/README.md)
  WebSocket セッション初期化、メッセージ処理ループ、職種選択時の動的ツール差し替え、REST API 委譲をまとめています。
- [miidas_aica_mcp/README.md](https://github.com/MIIDAS-Company/miidas_aica_mcp/blob/develop/README.md)
  MCP サーバー起動、ツール定義ロードと登録、各 tool handler から AICA API へ委譲する流れをまとめています。
- [miidas_aica_api/README.md](https://github.com/MIIDAS-Company/miidas_aica_api/blob/develop/README.md)
  既存の `ポジションAPI エンドポイントフロー` を中心に、handler から usecase までの詳細処理をまとめています。

### Supporting Projects

- `miidas_aica_agent/cli`
  Flyway マイグレーション、会話データ整理、レート制限集計などの運用処理を担当します。
- `miidas_aica_agent/e2e`
  WebSocket ベースで Agent サーバーの会話フローを検証するクライアントです。

## Repository Notes

- `miidas_aica_frontend`
  UI 層。会話とフィルター状態は Redux で管理します。
- `miidas_aica_agent/server`
  WebSocket 会話、REST API、MCP 接続、OpenAI Agents 初期化を担当します。
- `miidas_aica_mcp`
  各ツール実装は `src/sdk/tools` 配下にあり、AICA API に HTTP リクエストします。
- `miidas_aica_api`
  `src/api/mcptool/http` 配下で各 API ルートを公開し、usecase/repository 層へつなぎます。
- `miidas_aica_agent/cli`
  マイグレーションや会話データ整理などの運用系コマンドを持ちます。
- `miidas_aica_agent/e2e`
  WebSocket ベースで Agent サーバーを検証します。

## Local Start

個別起動:

```bash
cd miidas_aica_api && ./start_server.sh
cd miidas_aica_mcp && ./start_server.sh
cd miidas_aica_agent/server && ./start_server.sh
cd miidas_aica_frontend && ./start_frontend.sh
```

まとめて起動:

```bash
./start.sh
```

## GOバージョンアップツール

upgrade-go-version.sh

### 使い方

`~/aica/`配下にコピーしてから
```bash
cd ~/aica
chmod +x upgrade-go-version.sh
./upgrade-go-version.sh x.x.x
```
