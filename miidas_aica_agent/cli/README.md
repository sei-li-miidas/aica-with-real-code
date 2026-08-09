# AICA Batch CLI

[typer](https://github.com/fastapi/typer)を使ってバッチコマンドを提供します。

## コマンド一覧

### `clean_session`

非会員の場合、下記の処理を行います。

- 論理削除：2日（会員になったら復元できる）
  - また以下は物理削除する：
    - 氏名の削除（カナ氏名も削除）
    - 電話番号の削除
    - メールアドレスの削除
    - パスワードの削除
    - 企業名
- 物理削除：1ヶ月（会員になっても復元できない）

### `aggregate_and_delete_rate_limits`

日次（夜間バッチ）で、前日分のレート制限データ（DB.rate_limits）を集計し削除します。

※参考資料は[こちら](https://docs.google.com/spreadsheets/d/1YMXT1o1ua2yyzRfb1U6EtX6ioftJs9I3t1yOx6qokWg/edit?gid=2049097385#gid=2049097385)

# ローカルでの起動

## 事前準備

### Python バージョン

- 必須: Python 3.14 (>=3.14,<3.15)
- 推奨: 仮想環境 `.venv-cli`

セットアップ例：

```
python3.14 -m venv .venv-cli
source .venv-cli/bin/activate
pip install ./cli
```

### DB構築

[aica_db_migrationsリポジトリ](https://github.com/MIIDAS-Company/aica_db_migrations)のREADMEを参照

### 環境変数

- `.env.example`を`.env.local`にコピーし、値を入れてください。
  - `AICA_PYTHON_FERNET_AES_128_CBC_KEY_LV5`も追加してください。値は`server/.env.local`と同じにしてください。
- `127.0.0.1	pgvector`を事前に`/etc/hosts`にいれるとVSCodeとコンテナ内と同じエンドポイントが利用できます。

### イメージ作成・実行

```bash
cd cli
docker compose -f docker/compose-agent-cli.yaml run --rm agent-cli-server [コマンド名]

# 例）clean_session
docker compose -f docker/compose-agent-cli.yaml run --rm agent-cli-server clean_session
```

# 開発者向け

## プロジェクト構造

- src/aica_batch/commands
  - 具体的なコマンド実装
- docker
  - イメージ作成・起動用

## 主に利用しているライブラリ

- typer
  - Python CLI作成
- psycopg、SQLAlchemy
  - DBアクセス
- dependency-injector
  - 依存性注入（Dependency Injection: DI）

## デバッグ

### 準備

全体`README`参照

### 起動方法

VSCodeで`launch.json`の`[Batch]Local Debug`を実行してください。

## 単体テスト

### 概要
単体テストにはpytestを使用しており、テストコードは`tests/unit/`に配置しています。

### 実行方法

以下コマンドで実行
```
docker compose -f docker/compose-agent-cli.yaml run --rm agent-cli-test
```

特定のファイルを実行したい場合
```
docker compose -f docker/compose-agent-cli.yaml run --rm agent-cli-test [ファイルパス]

# 例
docker compose -f docker/compose-agent-cli.yaml run --rm agent-cli-test tests/unit/commands/test_aggregate_and_delete_rate_limits.py
```

※その他のオプションについては[serverのREADME](https://github.com/MIIDAS-Company/miidas_aica_agent/tree/develop/server#pytest%E3%82%AA%E3%83%97%E3%82%B7%E3%83%A7%E3%83%B3)を参照
