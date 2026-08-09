# フェーズ: 統合・リリース準備

## 目的

Gate A の構造リファクタを単一 release candidate として `develop` へ統合できる状態にする。

## スコープ

スコープ内:
- release notes
- rollback 手順
- 起動時ログと chat turn ログの確認
- release candidate verification checklist の取りまとめ
- develop 統合 PR の準備

スコープ外:
- 新しい大規模リファクタ
- Gate B の runtime behavior 追加
- Phase 1-5 gate の再設計

## 開始条件

- Phase 5 が完了している。
- `gate_a_scenario_matrix.md` で定義した Gate A の named behavioral invariants と rollback suite が揃っている。

## 終了条件

- config 変更だけで `service_variant: legacy` へ rollback できる手順が文書化されている。
- rollback 手順に exact config/env override、反映方法、確認ログ、data compatibility assumption、success criterion が含まれている。
- `develop` 統合 PR が Gate A 完了後の単一 release candidate として成立している。
- shared boundary の backward compatibility が rollback suite で確認済みである。
- Phase 1-5 の gate command 再実行は release candidate verification checklist に記録されており、Phase 6 の新規成果物とは分離されている。

## フィーチャー

| フィーチャー | 目的 | 依存関係 | ステータス |
| --- | --- | --- | --- |
| feature-1-operational-rollback | config-only rollback の運用手順を完成させる。 | Phase 5 | done |
| feature-2-release-evidence | release logging evidence と RC verification checklist を揃える。 | feature-1 | done |
| feature-3-develop-integration | develop 統合 PR readiness を固定する。 | feature-2 | done |

## タスク分割

| フィーチャー | タスク | 目的 | 必須検証 |
| --- | --- | --- | --- |
| feature-1-operational-rollback | task-1-rollback-procedure | exact config/env override、反映方法、確認ログ、success criterion を文書化する。 | operational rollback procedure 確認 |
| feature-2-release-evidence | task-1-release-logging-and-verification | startup/chat turn logging evidence と RC verification checklist を揃える。 | logging evidence / RC verification checklist |
| feature-3-develop-integration | task-1-integration-pr-readiness | develop 統合 PR の evidence checklist と release notes を完成させる。 | matrix / verification / release notes |

## Phase 6 必須成果物

- operational rollback procedure 確認
- startup log evidence
- chat turn log evidence
- release notes
- develop 統合 PR checklist
- release candidate verification checklist
- `server/plan/phases/gate_a_scenario_matrix.md` の rollback subset matrix 完了確認

## release candidate verification checklist

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/`

これらは Phase 1-5 gate の再確認であり、Phase 6 の新規 implementation scope ではない。収集範囲は Gate A refactoring scope に合わせて `server/tests/` に限定し、`cli/tests` など非対象スイートは含めない。未実行または失敗がある場合、release candidate は作らず Phase 6 を `blocked` にする。

## メモ

- Phase 6 は実装追加ではなく release readiness の確認に限定する。
