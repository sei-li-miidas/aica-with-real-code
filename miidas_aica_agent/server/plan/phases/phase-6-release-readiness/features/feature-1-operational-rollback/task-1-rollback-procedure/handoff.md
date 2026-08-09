# 引き継ぎ: task-1-rollback-procedure

## 概要

Phase 6 feature-1 task-1 として、config-only rollback の運用手順を `verification.md` に文書化し、rollback subset command の再実行証跡を更新した。

実施内容:
- rollback procedure（exact config override、反映方法、確認ログ、data compatibility assumption、success criterion）を記録。
- rollback drill procedure（事前状態、操作手順、想定所要時間、成功基準、失敗時の戻し方）を記録。
- mandatory rollback confirmation subset と parity markers を再実行して all pass を確認。
- staging drill 実施不能理由、代替確認、release 影響を `verification.md` へ記録。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/plan/phases/phase-6-release-readiness/features/feature-1-operational-rollback/task-1-rollback-procedure/verification.md` | rollback 手順/rollback drill 手順、実行コマンド結果、実施不能理由と release 影響を記録。 |
| `server/plan/phases/phase-6-release-readiness/features/feature-1-operational-rollback/task-1-rollback-procedure/handoff.md` | 本タスクの引き継ぎを実値へ更新。 |
| `server/plan/phases/phase-6-release-readiness/features/feature-1-operational-rollback/README.md` | task table の `task-1-rollback-procedure` ステータスを `done` へ更新。 |
| `server/plan/phases/gate_a_scenario_matrix.md` | Phase 6 operational rollback evidence（command replay と drill 実施可否）を追記。 |
| `server/plan/phases/status.md` | phase-6 feature-1 task-1 を `done` へ更新し、概要リスクを現況へ更新。 |

## 新しいAPI / ヘルパー / フィクスチャ

なし（ドキュメント証跡更新のみ）。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| mandatory rollback confirmation subset は marker command 再実行で固定する | feature/phase/task の完了条件が rollback subset の pass 証跡を要求するため。 | Phase 5 証跡の参照のみ。最新作業時点の再現性が弱いため不採用。 |
| rollback drill は not-applicable とし、代替確認と release 影響を明記する | 実運用環境への設定配布/rollout 権限が local 環境にないため。 | 実施結果未記載のまま task 完了。完了条件を満たせないため不採用。 |
| env override は「repository 内 direct key 未定義」として扱う | 設定ロードが `config.yml` 中心であり、`service_variant` direct env key の運用規約が repository 内で定義されていないため。 | 未確認の env key 名を手順書へ固定。誤運用リスクがあるため不採用。 |

## 互換性メモ

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config server/tests/` は `4 passed, 1491 deselected`。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di server/tests/` は `30 passed, 1465 deselected`。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner server/tests/` は `25 passed, 1470 deselected`。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security server/tests/` は `29 passed, 1466 deselected`。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/` は `14 passed, 1481 deselected`。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap server/tests/` は `8 passed, 1487 deselected`。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/` は `1196 passed, 299 deselected`。
- 2026-06-09 reconciliation で Phase 5 base merge 分 (+13 pre_extraction_parity tests) を反映してカウントを更新。rollback subset pass 数に変化なし。

## 次タスクへのフォローアップ

- feature-2 task-1（release evidence）で、staging rollback drill の実測時間・実ログを運用環境から追記すること。
- release candidate 承認時には、本 task の「drill 実施不能理由」と「release 影響」を前提に、staging drill 完了を gate 条件として扱うこと。

## reconciliation update (2026-06-09)

- phase-6 親 README の feature table で `feature-1-operational-rollback` が `not-started` のまま残っていた不整合を `done` に修正。
- `verification.md` の rollback drill `not-applicable` 記録へ owner/date/follow-up を追記し、免除記録要件との対応を明示。
- 本 reconciliation では実装/テスト追加は行わず、既存 evidence の整合性確認と文書同期のみ実施。

## 未解決の質問

- staging または同等環境での rollback drill 実施者（運用 owner）と実施日をどの task で固定するか → feature-2 task-1 で記録することとしている（次タスクへのフォローアップ参照）。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
