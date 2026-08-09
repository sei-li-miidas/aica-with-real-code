<!-- template: refactoring-feature (feature → phase PR) -->

## フィーチャー参照

<!-- 対応する feature README へのパスを記載してください -->

- Phase:
- Feature: `server/plan/phases/phase-x/features/feature-y/README.md`

## 概要

<!-- このフィーチャーで何を達成したかを記載してください -->

## チケット

<!-- 関連するRedmineチケット番号を記載してください -->

- Closes #

## 含まれるタスク PR

| タスク | PR | ステータス |
| --- | --- | --- |
| task-1 | #xxx | merged |

## フィーチャー終了条件

<!-- feature README の終了条件を満たしているか確認してください -->

- [ ]
- [ ]

## Shared boundary チェック（集約）

<!-- 各タスク PR の shared boundary 変更を集約してください。なければ「なし」 -->

| 変更した shared file | 影響する rollback subset | 対応タスク PR |
| --- | --- | --- |
|  |  |  |

## Rollback subset 結果（集約）

<!-- 各タスクで実行された subset の集約結果を記載してください。対象外は N/A -->

- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config` — pass / N/A
- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di` — pass / N/A
- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` — pass / N/A
- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security` — pass / N/A
- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary` — pass / N/A
- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` — pass / N/A

## plan ドキュメント更新

- [ ] `server/plan/phases/status.md` のステータスを更新した
- [ ] feature README の終了条件を満たした

## チェックリスト

- [ ] セルフレビュー済み
- [ ] CI が通過している
- [ ] `service_variant: legacy` で既存テストが全て通る
- [ ] 各タスク PR がすべて merged 済み

## レビュアーへのメモ

<!-- フィーチャー全体として確認してほしい点・タスク間の整合性・未解決事項があれば記載してください -->
