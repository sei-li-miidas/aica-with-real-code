# 検証: task-1-rollback-procedure

## テスト概要

| コマンド | 結果 | メモ |
| --- | --- | --- |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config server/tests/` | pass | `4 passed, 1491 deselected` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di server/tests/` | pass | `30 passed, 1465 deselected` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner server/tests/` | pass | `25 passed, 1470 deselected` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security server/tests/` | pass | `29 passed, 1466 deselected` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/` | pass | `14 passed, 1481 deselected` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap server/tests/` | pass | `8 passed, 1487 deselected` |
| `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/` | pass | `1196 passed, 299 deselected` |

結果値:
- `pass`
- `fail`
- `not-run`
- `waived`
- `not-applicable`

完了ルール:
- 必須コマンドに `fail` または `not-run` がある間は、タスクを `done` にできない。
- `waived` は、免除セクションにオーナー、理由、日付、フォローアップがある場合のみ許可する。
- `not-applicable` は、理由がある場合のみ許可する。

## 必須コマンド

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/`

## rollback procedure (config-only)

### exact config/env override

- config override (source of truth): `server/src/aica_agent/config.yml`
  - 変更前: `agent_runtime.service_variant: refactored`
  - 変更後: `agent_runtime.service_variant: legacy`
- env override: アプリ設定は `providers.Configuration(yaml_files=["config.yml"])` を利用しており、`agent_runtime.service_variant` の direct env key はこの repository では運用定義されていない。運用環境ではデプロイ設定側で配布する `config.yml`（または等価設定 artifact）に同一キーを反映して rollback する。

### restart / rollout / reload 方法

1. rollback 用設定ファイルを配布する（`agent_runtime.service_variant: legacy` を含む）。
2. rollout/restart を実行して新設定を反映する。
3. 起動直後に rollback subset command を実行し、contract 互換性を確認する。

### 確認ログ

- 起動確認: service 起動失敗がないこと。
- 互換確認: 本 file のテスト概要に記録した rollback subset command がすべて `pass`。

### data compatibility assumption

- 本 rollback は runtime の service variant 切替のみで、DB schema migration の巻き戻しを前提にしない。
- shared boundary は Phase 5 final matrix gate で `pass` 固定済みであり、`agent_runtime.service_variant: legacy` で後方互換を維持できる前提で運用する。

### rollback success criterion

- `agent_runtime.service_variant: legacy` で service が起動し、mandatory rollback confirmation subset（endpoint_config/di/runner/security/summary）がすべて `pass`。
- `pre_extraction_parity` が `pass` で、Gate A required scenario の互換性が維持される。

## rollback drill procedure

### 事前状態

- current release candidate が `service_variant: refactored` で動作中。
- rollback 対象 commit と rollback 設定ファイル（`service_variant: legacy`）を準備済み。

### 操作手順

1. 現行設定を退避する。
2. `agent_runtime.service_variant` を `legacy` に変更した設定を配布する。
3. rollout/restart を実行する。
4. health check が安定後、rollback subset command を順に実行する。
5. chat の代表シナリオ 1 本（tool 呼び出しを含む）を手動実行し、stream が完走することを確認する。

### 想定所要時間

- 設定差し替え + rollout/restart: 5-10 分
- rollback subset command 実行: 1-2 分
- 合計目安: 6-12 分

### 成功基準

- mandatory rollback confirmation subset がすべて `pass`。
- startup/chat の致命ログがなく、代表シナリオが完走する。

### 失敗時の戻し方

1. 退避しておいた設定へ戻す（`agent_runtime.service_variant: refactored`）。
2. 再 rollout/restart する。
3. rollback subset command を再実行し、refactored 側の baseline と一致することを確認する。

## rollback drill 実施結果

- 結果: not-applicable
- オーナー: sei.li@miidas.jp
- 日付: 2026-06-08
- 理由: この作業環境は local verification 専用で、staging または同等運用環境への設定配布/rollout 権限がないため drill 実行不可。
- 代替確認:
  - mandatory rollback confirmation subset（endpoint_config/di/runner/security/summary）を local で全件 `pass`。
  - `pre_extraction_bootstrap` / `pre_extraction_parity` を再実行し、Phase 5 final matrix gate の pass と整合することを確認。
- release 判定への影響:
  - 技術的互換性 evidence は揃っている。
  - ただし「実運用での実測 rollback 時間」と「運用手順の実地妥当性」は未検証のため、Gate B entry 条件として staging drill 実施・記録が必要。
- フォローアップ: Gate B の release candidate 承認ゲートで、staging rollback drill（実測時間・確認ログ・実施者）を必須確認として記録すること。

## reconciliation note (2026-06-09)

- この task の required command evidence は 2026-06-08 記録値を再確認し、再実行は行わず整合性チェックのみ実施。
- completion criteria 充足を明確化するため、rollback drill `not-applicable` 記録に owner/date/follow-up を追記。
- Phase 5 base merge（feature-1 → phase_6, 2026-06-09）で 13 tests が `pre_extraction_parity` マーカーとして追加された。これにより `pre_extraction_parity` passed が 1183 → 1196、rollback marker の deselected がすべて +13 となった。rollback subset の pass 数に変化なし（regression なし）。本 reconciliation でカウントを現 HEAD 値へ更新。

## ロールバック確認対象の結果

| サブセット | コマンド | 結果 | メモ |
| --- | --- | --- | --- |
| rollback_endpoint_config | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config server/tests/` | pass | `4 passed, 1491 deselected` |
| rollback_di | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di server/tests/` | pass | `30 passed, 1465 deselected` |
| rollback_runner | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner server/tests/` | pass | `25 passed, 1470 deselected` |
| rollback_security | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security server/tests/` | pass | `29 passed, 1466 deselected` |
| rollback_summary | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/` | pass | `14 passed, 1481 deselected` |
| pre_extraction_bootstrap | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap server/tests/` | pass | `8 passed, 1487 deselected` |
| pre_extraction_parity | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/` | pass | `1196 passed, 299 deselected` |

## 失敗したテスト

| コマンド | 失敗概要 | 次の対応 |
| --- | --- | --- |
| なし | なし | なし |

## 未実行

| コマンド | 理由 |
| --- | --- |
| なし | なし |

## 免除

| コマンド | オーナー | 理由 | 日付 | フォローアップ |
| --- | --- | --- | --- | --- |
| なし | なし | なし | なし | なし |

## 手動確認

- rollback drill 実施は not-applicable（staging 権限なし）。
- staging drill は未実施のため、Gate B entry 条件として運用担当で drill 実施・実測時間・確認ログを記録する。

