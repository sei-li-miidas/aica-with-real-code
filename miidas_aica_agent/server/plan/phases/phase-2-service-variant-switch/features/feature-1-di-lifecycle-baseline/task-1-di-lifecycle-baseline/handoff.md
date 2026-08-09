# 引き継ぎ: DI lifecycle baseline

## 概要

この handoff は task 完了まで引き継ぎ資料として使わない。完了時に 未記入項目 を実値へ置き換え、未確定事項は「未解決の質問」へ移す。

legacy provider の lifecycle baseline を固定済み。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/tests/integration/chat_service_contract/test_di_lifecycle.py` | `Container.chat_svc()` が fresh instance を返すことと、websocket/session で service instance が分離されることを確認する rollback_di test を追加した。 |

## 新しいAPI / ヘルパー / フィクスチャ

- `Container.chat_svc` は factory のまま維持し、session ごとに fresh な `ChatService` instance を返す前提を固定した。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| `Container.chat_svc` を singleton にしない | DI lifecycle を session 単位で分離するため | `Container.chat_svc` を singleton 化する |

## 互換性メモ

- `service_variant: legacy` で legacy `ChatService` が解決されることを維持する。
- `service_variant: legacy` で legacy `ChatService` が解決され、WebSocket/session ごとに別 instance が返る前提を固定した。

## 次タスクへのフォローアップ

- delegating adapter task は、この lifecycle test を legacy/refactored 両設定へ拡張する。

## 未解決の質問

- なし。

## 前提にしてはいけないこと

- `chat_service_refactored.ChatService` が存在すること。
