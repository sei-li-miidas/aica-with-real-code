<!-- template: refactoring-task (task → feature PR) -->

## タスク参照

<!-- 対応する task.md へのパスを記載してください -->

- Phase:
- Feature:
- Task: `server/plan/phases/phase-x/features/feature-y/task-z/task.md`

## 概要

<!-- このタスクで何を実装したか・なぜこの判断をしたかを記載してください -->

## チケット

<!-- 関連するRedmineチケット番号を記載してください -->

- Closes #

## 主な変更ファイル

| ファイル | 変更内容 |
| --- | --- |
|  |  |

## タスク種別

<!-- 該当するものに [x] を入れてください -->

- [ ] Shared boundary 変更（`endpoints.py`, `containers.py`, `config.yml`, `llm_service.py`, `utils.chat_response` など）
- [ ] 新コンポーネント追加（`services/chat/` 配下）
- [ ] Delegating adapter 変更
- [ ] Runner / Stream contract 変更
- [ ] Extraction（責務移植）
- [ ] テスト追加・修正のみ
- [ ] ドキュメント・plan 更新のみ

## Shared boundary チェック

<!-- Shared boundary を変更した場合のみ記入してください。変更がなければ「なし」と記載してください -->

| 変更した shared file | 影響する rollback subset |
| --- | --- |
|  |  |

## 必須 verification コマンド

<!-- task.md に記載された required command の実行結果を貼り付けてください -->

<details>
<summary>実行結果</summary>

```
# コマンドと出力を貼り付けてください
```

</details>

## Rollback subset 結果

<!-- 該当する subset に [x] を入れ、結果を記載してください。対象外は N/A -->

- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config` — pass / N/A
- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di` — pass / N/A
- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` — pass / N/A
- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security` — pass / N/A
- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary` — pass / N/A
- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` — pass / N/A

## Test migration map（Extraction タスクのみ）

<!-- Extraction タスク以外は「N/A」と記載してください -->
<!-- 移植した private method ごとに移行先を記載してください -->

| 移植した private method | 移行先 | 種別 |
| --- | --- | --- |
| `_xxx` | `component/contract_test/legacy-only` | refactored component test / contract invariant / legacy-only characterization |

## Static check（該当する場合）

<!-- 以下に該当する場合、確認結果を記載してください -->

- [ ] `endpoints.py` が `services.chat_service` を import していない（Phase 1 以降）
- [ ] `chat_service_refactored.py` が legacy `services.chat_service.ChatService` を import / instantiate していない（Phase 4 bootstrap 以降）
- [ ] main `chat()` path が delegating adapter 経由でない（Phase 4 bootstrap 以降）

## plan ドキュメント更新

- [ ] `server/plan/phases/status.md` のステータスを更新した
- [ ] `handoff.md` を更新した（実装判断・注意点・未解決事項を含む）
- [ ] `verification.md` を更新した（required command が pass / waived / not-applicable のみ）
- [ ] plan と異なる実装判断をした場合、`handoff.md` に理由を記載した

## チェックリスト

- [ ] セルフレビュー済み
- [ ] CI が通過している
- [ ] `service_variant: legacy` で既存テストが全て通る
- [ ] Protocol / インターフェースの変更がある場合、全実装クラスを更新した
- [ ] shared boundary を変更した場合、該当 rollback subset を通した

## レビュアーへのメモ

<!-- レビュー時に特に確認してほしい点・設計判断の背景・未解決事項があれば記載してください -->
