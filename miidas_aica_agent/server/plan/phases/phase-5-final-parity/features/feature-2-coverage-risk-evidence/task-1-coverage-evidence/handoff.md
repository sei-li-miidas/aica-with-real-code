# 引き継ぎ: task-1-coverage-evidence

## 概要

Phase 5 feature-2 task-1 として、coverage/risk evidence の文書化を完了した。

実施内容:
- legacy / refactored の branch coverage evidence を required command で再取得。
- `rollback_summary` を再実行して rollback subset の継続性を確認。
- performance baseline（同一 fixture, legacy vs real-refactored）を 15-run 比較で p50/p95/p99 記録。
- Phase 4 task-3 から持ち越した legacy 既知未到達分岐 3 件を再判定し、`verification.md` に明記。
- refactoring 導入・再構成ファイル inventory を gate 判定付きで更新。
- `gate_a_scenario_matrix.md` に Phase 5 feature-2 task-1 evidence section を追加。

## 変更ファイル

| ファイル | 概要 |
| --- | --- |
| `server/plan/phases/phase-5-final-parity/features/feature-2-coverage-risk-evidence/task-1-coverage-evidence/verification.md` | required commands 実行結果、分岐分類、inventory、performance baseline を記録。 |
| `server/plan/phases/phase-5-final-parity/features/feature-2-coverage-risk-evidence/task-1-coverage-evidence/handoff.md` | 本引き継ぎ内容へ更新。 |
| `server/plan/phases/gate_a_scenario_matrix.md` | Phase 5 feature-2 task-1 coverage/risk evidence セクションを追記。 |
| `server/plan/phases/status.md` | phase-5 feature-2 task-1 を `done` へ更新。 |

## 新しいAPI / ヘルパー / フィクスチャ

なし（code 変更なし、計画文書更新のみ）。

## 設計判断

| 判断 | 理由 | 検討した代替案 |
| --- | --- | --- |
| inventory の target gate は `chat_service_refactored.py` を integration、component modules を unit で固定 | Phase 4 で component ごとの unit branch 100% を達成済み。Phase 5 では integration parity 継続性を主証跡にするため。 | 全ファイルを integration branch 100% 目標に統一。抽出済み component の責務境界が不明瞭になるため不採用。 |
| `chat_service.py:991-1000` を `external dependency branch` へ再ラベル | finalize 検知の発火が chunk/token 境界条件に依存し deterministic 再現が難しいため。 | `defensive branch` 維持。再現特性が誤って伝わるため不採用。 |
| performance baseline は同一 fixture の lightweight subset で採取 | 反復計測で p50/p95/p99 を低コストに取得でき、legacy/refactored 差分を比較しやすいため。 | full pre_extraction_parity 全体を多重実行。時間コストが大きく task 範囲を超えるため不採用。 |

## 互換性メモ

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/ --cov=services.chat_service --cov-branch --cov-report=term-missing` は `1183 passed, 299 deselected`。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/ --cov=services.chat_service_refactored --cov-branch --cov-report=term-missing` は `1183 passed, 299 deselected`。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/` は `14 passed, 1468 deselected`。
- parity / rollback の required subset で回帰は検出されていない。

## 次タスクへのフォローアップ

- phase-5 feature-3 task-1（final matrix gate）で次を再確認すること:
	- `chat_service_refactored.py` 残分岐（`67->69`, `71->73`, `758->801`, `824-826`, `833`）に targeted test を追加するか、最終 waiver へ整理するか。
	- `chat_service.py:667->976` の zero-yield branch を residual risk として最終 evidence に明記すること。
	- performance baseline は lightweight subset のため、必要なら representative workload（長文/再試行多発）で補完すること。

## Phase 4 からの引き継ぎ入力

- 既知の legacy coverage 例外は次を起点にする:
	- `server/src/aica_agent/services/chat_service.py:480-481`
	- `server/src/aica_agent/services/chat_service.py:991-1000`
	- `server/src/aica_agent/services/chat_service.py:1031-1032`
- 上記 3 分岐は `server/plan/phases/phase-4-refactored-extraction/features/feature-5-summary-guard-backfill/task-3-summarization-consolidation/verification.md` に初期 waiver 根拠がある。
- Phase 5 owner は各分岐について `解消` / `waiver 継続` / `再ラベル` の最終判定を `verification.md` に反映する。
- parity contract fixture の `db.url` は `sqlite://` から `not-used://db` へ置換済み。DB repository がモック境界であるシナリオでは DB URL を判定根拠に使わないこと。
- unit repository tests では sqlite 実接続を継続する。`engine.dispose()` 追加により `ResourceWarning: unclosed database` は解消済み（`pytest -q server/tests/unit -ra -W default` warning summary なし）。

## 未解決の質問

なし。

## 前提にしてはいけないこと

- `verification.md` が pass になるまで、この task の成果を後続 task の前提にしない。
