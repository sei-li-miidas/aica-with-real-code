<!-- template: refactoring-phase (phase → feature/77996_chat_service_refactoring PR) -->

## フェーズ参照

<!-- 対応する phase README へのパスを記載してください -->

- Phase: `server/plan/phases/phase-x/README.md`

## 概要

<!-- このフェーズで何を達成したかを記載してください -->

## チケット

<!-- 関連するRedmineチケット番号を記載してください -->

- Closes #

## 含まれるフィーチャー PR

| フィーチャー | PR | ステータス |
| --- | --- | --- |
| feature-1 | #xxx | merged |
| feature-2 | #xxx | merged |

## フェーズ終了条件

<!-- phase README の終了条件を満たしているか確認してください -->

- [ ]
- [ ]

## Rollback suite 結果（フル）

<!-- このフェーズで影響を受けた全 subset を通してください -->

- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config` — pass / N/A
- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di` — pass / N/A
- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` — pass / N/A
- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security` — pass / N/A
- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary` — pass / N/A
- [ ] `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` — pass / N/A

## plan ドキュメント更新

- [ ] `server/plan/phases/status.md` のステータスを更新した
- [ ] phase README の終了条件を満たした

## チェックリスト

- [ ] セルフレビュー済み
- [ ] CI が通過している
- [ ] `service_variant: legacy` で既存テストが全て通る
- [ ] 各フィーチャー PR がすべて merged 済み
- [ ] phase README に記載された必須検証コマンドが全て pass している

## レビュアーへのメモ

<!-- フェーズ全体として確認してほしい点・フィーチャー間の整合性・未解決事項があれば記載してください -->
