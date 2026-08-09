
# E2E AICA クライアント

AI転職アドバイザーのサーバー/API を、UI を介さず headless に検証するクライアントです。

このクライアントは `miidas_aica_frontend` の画面操作そのものを再現するものではなく、フロントエンド相当の WebSocket / REST アクションを headless に送って、会話フローと応募フローを確認します。

## 概要

- 複数のクライアントを同時に実行
- markdown + YAML sidecar からのペルソナ駆動
- 設定可能な LLM モデル（OpenAI、Bedrock）
- 会話ターン数の制限設定
- デバッグモードおよびテストモード
- パフォーマンス計測と統計収集
- 自動要約レポート生成

## このクライアントでテストできること

- メインチャットの開始 / 再開
  - WebSocket 接続直後の初回応答受信
  - テスト中のランダム切断 / 再接続
  - 再接続時の `restart_chat` とメインチャット履歴復元
  - 再接続後に復元履歴へ `position_search_link` があれば、ランダムに 1 件ポジションを選び、詳細会話に再入場
  - 再接続後に復元履歴へ `jobtype_search_result` があれば、30% の確率で複数職種をランダム再選択、70% は未再選択のまま継続
- 通常会話
  - アドバイザーの最新メッセージを受け、求職者 LLM が次の発話を返す流れ
  - 会話ターン上限や終了条件に応じた停止
- 職種提案と職種選択
  - `jobtype_search_result` の受信
  - 候補から 1 件以上をランダム選択して `job_types_selected` を送信
  - 未選択時の `job_types_clear`
  - 最新検索条件 (`positions/search_filter/current`) の追従
- 求人検索から求人詳細会話への遷移
  - `position_search_result` の受信
  - `position_search_link` を受けたときの `positions/re-search/{ToolCallId}` 実行
  - 検索結果 / おすすめ求人から 1 件選択
  - 求人詳細 API 取得とポジション詳細チャット実行
- ポジション詳細会話の復元と終了
  - `chat/{position_id}/exist` による履歴存在確認
  - `chat/previous/{position_id}` による履歴復元
  - 詳細画面終了時の `summarize_position`
- プロフィール保存と応募フロー
  - 基本情報 / 学歴 / 職歴 / 希望条件の保存
  - `apply/start` / `apply/{position_id}/start`
  - `apply/{position_id}/add`
  - `apply/finish`
  - `apply/position/{position_id}`
- セッション状態と性能の観測
  - `session_status` の変化
  - 初回応答時間 / 総応答時間 / 求職者 LLM 応答時間の集計

## テストしないこと

- フロントエンドの描画や DOM 挙動
- スクロール、モーダル、Redux state 更新そのもの
- ブラウザ固有のイベントや見た目

つまり、この e2e は「画面 E2E」ではなく「headless 会話フロー E2E」です。

## どうやってテストするか

1. ペルソナ markdown と sidecar YAML を読み込みます。
2. sidecar YAML の固定データを、プロフィール保存・応募用の決定済み入力として使います。
3. WebSocket で AI転職アドバイザーサーバーに接続します。
4. サーバーからの応答を受けて、必要に応じて REST API を呼びます。
   - 例: `chat/previous`, `chat/previous/{position_id}`, `positions/re-search/{ToolCallId}`, `positions/detail/{position_id}`
5. アドバイザーの最新メッセージを元に、求職者 LLM が次の発話を生成します。
6. `TEST` 実行時は、一定確率で WebSocket をランダム切断し、同じ `session_id` で再接続します。
7. 再接続後、サーバーが `restart_chat` を返した場合は履歴を復元します。
8. 復元履歴に `position_search_link` があれば、それを優先して `positions/re-search/{ToolCallId}` を再実行し、ランダムに 1 件選んで詳細会話へ入ります。
9. `position_search_link` がなく `jobtype_search_result` があれば、30% の確率で複数職種をランダムに再選択して継続し、70% はそのまま継続します。
10. 求人検索・職種選択・応募などの pending action を headless で自動処理します。
11. `finish_policy` または `max_rounds` に達するまでこの流れを繰り返します。

## 実装上の前提

- WebSocket の request type は、サーバーが受け付けるものだけを送ります。
  - `chat`
  - `restart_chat`
  - `summarize_position`
  - `job_types_selected`
  - `job_types_clear`
- フロントエンドにだけ存在する古い / 未使用の action を headless 側で新規実装しません。
- headless client は、現在の server / API 契約を source of truth として追従します。

## 設定

`config.yml` で設定可能：

- `run_mode`: "DEBUG"（手動入力の単一クライアント）または "TEST"（自動化された複数クライアント）
- `client_number`: クライアント数（0 = すべてのペルソナを使用）
- `max_rounds`: 会話のグローバルターン制限（0 = 無制限）
- `persona_included`: 使用する特定のペルソナ（オプションで max_rounds を指定可）
- `persona_excluded`: 使用対象外のペルソナ
- `model_list`: 使用可能な LLM モデルとその設定
- `runtime.finish_policy`: `MAX_ROUNDS` / `APPLY_FINISHED` / `EITHER`
- `runtime.auto_follow_position_search_link`: `position_search_link` を自動で再検索するか
- `runtime.auto_run_profile_apply`: プロフィール保存と応募完了まで自動実行するか
- `runtime.restore_history_on_restart`: `restart_chat` とポジション詳細再入場時の履歴復元を行うか
- `runtime.random_disconnect_probability`: `TEST` 実行中に各ループでランダム再接続を発生させる確率（`0.0`-`1.0`）
- `runtime.resume_session_id`: 既存セッションを再開するときのセッションID

### 環境変数

必須環境変数：
- `AICA_WS_ENDPOINT`: AI転職アドバイザーサーバーのWebsocketエンドポイント
  - 例: `ws://agent-server:8000/aica/agent/chat`
- `AICA_API_ENDPOINT`: AI転職アドバイザーサーバーのAPIエンドポイント
- `AICA_RESUME_SESSION_ID`: 再接続時に利用する既存セッションID（任意）
- `RUN_MODE`: DEBUG または TEST
  - `DEBUG`: 1クライアントで実行し、各ターンの進行を Enter で手動制御できる
  - `TEST`: 設定どおり複数クライアントを自動実行する
- `CLIENT_NUMBER`: クライアント数
  - 推薦値: 9 ([参照](https://github.com/MIIDAS-Company/miidas_aica_agent/pull/16#discussion_r2191266523))
- `MAX_ROUNDS`
  - 会話上限
  - 推薦値: 21 ([参照](https://github.com/MIIDAS-Company/miidas_aica_agent/pull/16#discussion_r2191266523))
- `FINISH_POLICY`: `MAX_ROUNDS` / `APPLY_FINISHED` / `EITHER`
- `AUTO_FOLLOW_POSITION_SEARCH_LINK`: `true` / `false`
- `AUTO_RUN_PROFILE_APPLY`: `true` / `false`
- `RESTORE_HISTORY_ON_RESTART`: `true` / `false`
- `RANDOM_DISCONNECT_PROBABILITY`: `0.0`-`1.0`
- `OPENAI_API_KEY`: OpenAI モデル用
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_REGION_NAME`: Bedrock モデル（AWS 認証情報）用

## ペルソナ

`files/persona/` ディレクトリにペルソナ markdown と headless sidecar YAML を作成：

- `e2e/files/persona/persona_definition_01.md`
- `e2e/files/persona/persona_definition_01.yml`
- `e2e/files/persona/persona_definition_02.md`
- `e2e/files/persona/persona_definition_02.yml`
- `e2e/files/persona/persona_definition_03.md`
- `e2e/files/persona/persona_definition_03.yml`
- `e2e/files/persona/persona_definition_04.md`
- `e2e/files/persona/persona_definition_04.yml`
- `e2e/files/persona/persona_definition_05.md`
- `e2e/files/persona/persona_definition_05.yml`
- `e2e/files/persona/persona_definition_06.md`
- `e2e/files/persona/persona_definition_06.yml`
- `e2e/files/persona/persona_definition_07.md`
- `e2e/files/persona/persona_definition_07.yml`
- `e2e/files/persona/persona_definition_08.md`
- `e2e/files/persona/persona_definition_08.yml`
- `e2e/files/persona/persona_definition_09.md`
- `e2e/files/persona/persona_definition_09.yml`
- `e2e/files/persona/persona_definition_10.md`
- `e2e/files/persona/persona_definition_10.yml`

YAML sidecar には headless 実行用の決定済みデータを入れます：
- 基本情報
- 学歴
- 職歴
- 希望条件
- `run_hints`
  - `apply_mode`
  - `position_selection`
  - `position_detail_turns`
  - `auto_apply_position`

## パフォーマンスモニタリング

クライアントは自動で以下を記録します：
- サーバーからの初回メッセージまでの時間
- ストリーミング応答の総応答時間
- ペルソナごとの会話統計
- 全体的なパフォーマンスの平均値

テスト完了後、自動で `summary_yyyyMMddHHmmss.md` レポートを生成：
- すべての会話に関する全体統計
- ペルソナごとのパフォーマンス平均

# ローカルでの起動

## 事前準備

### Python バージョン

- 必須: Python 3.14 (>=3.14,<3.15)
- 推奨: 仮想環境 `.venv-e2e`

セットアップ例：

```bash
python3.14 -m venv .venv-e2e
source .venv-e2e/bin/activate
pip install ./e2e
```

### 環境変数

- `.env.example`を`.env.local`にコピーし、値を入れてください。
- `127.0.0.1	agent-server`を事前に`/etc/hosts`にいれるとVSCodeとコンテナ内と同じエンドポイントが利用できます。

### イメージ作成

```bash
cd e2e
docker build -f docker/Dockerfile . -t agent-e2e:latest
```

## 実行コマンド

```bash
cd e2e
docker run -it --rm --env-file .env.local --network ai-ca_default agent-e2e:latest
```

## Summary Output

実行後は `summary_yyyyMMddHHmmss.md` を生成し、以下を集計します。

- 初回レスポンス時間
- 総レスポンス時間
- 求職者 LLM 応答時間
- client ごとの統計
- ランダム再接続回数
- 終了理由 (`max_rounds` / `apply_finished` / `completed` / `maintenance` など)
- 最終 session status

# 開発者向け

## プロジェクト構造

- src/aica_client/client
  - AI転職アドバイザーサーバーのWebsocketクライアント
  - 求職者AIクライアント
- src/aica_client/repositories
  - レポジトリ（LLMクライアント作成）
- src/aica_client/utils
  - 定数、ヘルパークラス、メソッド
- persona
  - ペルソナマークダウン

## 主に利用しているライブラリ

- `openai`
  - OpenAI ベースの求職者 LLM クライアント
- `boto3`
  - Bedrock ベースの求職者 LLM クライアント
- `websockets`
  - Websocket クライアント
- `aiohttp`
  - REST API クライアント

## デバッグ

### 準備

全体`README`参照

### 起動方法

VSCodeで`launch.json`の`[E2E]Local Debug`を実行してください。

## コード上の主なテストフロー

- `E2EClient.run()`
  - WebSocket 接続、初回応答処理、停止条件までのメインループ
- `_handle_pending_actions()`
  - 職種候補、求人検索リンク、求人検索結果の処理
- `_run_position_detail_chat()`
  - 求人詳細への遷移、履歴復元、詳細会話、要約してメインチャットへ戻る処理
- `_handle_profile_and_apply_actions()`
  - 登録中 / 応募中セッションでのプロフィール保存と応募完了処理
- `generate_summary()`
  - 実行結果の集計と markdown レポート生成

# 残課題

求職者LLMに利用しているモデルに関して、

## Bedrock

下記2種類のエラーが発生する可能性があります

1. `An error occurred (ThrottlingException) when calling the Converse operation (reached max retries: 4): Too many requests, please wait before trying again.`

[ここ](https://ap-northeast-1.console.aws.amazon.com/servicequotas/home/services/bedrock/quotas)から見ると、`Not adjustable`なので、backoff（現在10回リトライ）対応していますが、完全防止はできない。

2. `An error occurred (ThrottlingException) when calling the Converse operation (reached max retries: 4): Too many tokens, please wait before trying again.`

[ここ](https://ap-northeast-1.console.aws.amazon.com/servicequotas/home/services/bedrock/quotas)から見ると、デフォルトのon demandモデルは、Quotaの調整できなさそうなので、たぶん発生するたびに、古い会話履歴からけすしかない。まだやってない。

3. 原因不明だが、会話回数が増えるたびに、実行時間が長くなります。
