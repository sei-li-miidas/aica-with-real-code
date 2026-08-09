# フィーチャー: coverage/risk evidence

## 目的

coverage を補助 evidence として記録し、未到達行の理由と残リスクを棚卸しする。

## 親フェーズ

- フェーズ: phase-5-final-parity

## スコープ

スコープ内:
- legacy branch coverage
- refactored branch coverage
- 未到達行の理由と残リスク

スコープ外:
- coverage 数値だけを gate にすること
- hard threshold を単独 release gate にすること

## 依存関係

- feature-1-final-parity-scenarios

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-coverage-evidence | coverage evidence と未到達理由を記録する。 | final parity scenarios | coverage commands | not-started |

## 完了条件

- 未到達行に到達不能、外部依存過大、例外防御などの理由が記録されている。
- hard coverage threshold は設けない。coverage は behavior evidence の補助として扱う。
- critical scenario に関係する branch は、coverage 不足を waiver で隠さず、scenario evidence が `pass` していることを優先する。
- 未到達 branch は `defensive branch`, `external dependency branch`, `unreachable by contract`, `follow-up required` のいずれかに分類する。
- `follow-up required` がある場合は、follow-up issue / PR / task を記録する。
- legacy/refactored の performance baseline を補助 evidence として記録する。最低限、同一 fixture で p50 / p95 / p99 またはそれに準じる latency 指標を比較し、差分と残リスクを書く。
- refactoring 導入・再構成ファイル inventory を作成し、各ファイルに以下を記録する。
	- coverage owner
	- target gate (`unit branch 100%` / `integration branch 100%` / `not-applicable`)
	- 判定根拠
	- follow-up（必要時）
- `not-applicable` はファイル単位でのみ許可し、task 単位の一括 `not-applicable` は不可とする。
