# タスク: task-2-build-summary-context-turn-wiring

## 目的

refactored `chat()` に以下の 2 つを native 実装で追加し、summary 系の behavioral parity を回復する:

1. **summary context 再構築**: `prepare_turn()` の後（legacy と同等の順序）に、`MAIN_CHAT_KEY` かつ `previous_response_id` 未設定時だけ実行する。
2. **summary 起動判定**: `_record_usage()` の後、`should_save = True` の前に、`MAIN_CHAT_KEY` かつ `summary_service` 設定時に `check_should_start_summary(session_id)` を呼ぶ。

## 最初に読むコンテキスト

- 親フィーチャー README: `server/plan/phases/phase-4-refactored-extraction/features/feature-5-summary-guard-backfill/README.md`
- task-1 の handoff: `server/plan/phases/phase-4-refactored-extraction/features/feature-5-summary-guard-backfill/task-1-summary-service-constructor-wiring/handoff.md`
- `server/src/aica_agent/services/chat_service.py`: `build_summary_context()` と `chat()` 内の summary 起動判定
- `server/src/aica_agent/services/chat_service_refactored.py`: `chat()` メソッド全体

## スコープ

許可する変更:
- `chat_service_refactored.py`: `chat()` への 2 つの呼び出し追加
- `server/tests/unit/services/test_chat_service_refactored.py`: behavioral parity テスト追加
- `server/tests/integration/chat_service_contract/`: real-refactored evidence テスト追加または更新（`rollback_summary` マーカー）
- `gate_a_scenario_matrix.md`: `summary_rollback` の real-refactored evidence 更新

許可しない変更:
- `SummaryService` 内部ロジックの変更
- legacy 委譲の再導入

## 実装メモ

### 1. summary context 再構築の追加（turn 準備ブロック）

legacy では `_prepare_for_chat_turn()` の直後に再構築しているため、refactored でも `prepare_turn()` 後に実行する。

```python
await self._turn_preparer.prepare_turn(chat_request)

if (
    self._conv_state.chat_key == MAIN_CHAT_KEY
    and not self._conv_state.previous_response_ids.get(self._conv_state.chat_key)
):
    self._build_summary_context(get_session_id())
```

`_build_summary_context()` は refactored 側の private helper として追加し、`chat_service.py` の既存ロジックを移植する（委譲ではなく native 実装）。

### 2. summary 起動判定の追加（ターン完了後）

`_record_usage()` の直後、`self._conv_state.should_save = True` の前に追加:

```python
if (
    self._conv_state.chat_key == MAIN_CHAT_KEY
    and self._summary_service is not None
):
    try:
        self._summary_service.check_should_start_summary(get_session_id())
    except Exception:
        self.logger.exception("会話要約起動判定に失敗")
```

### behavioral parity test

`rollback_summary` マーカーで以下を証明する:
- `summary_service` が設定されている場合、refactored `chat()` が summary context 再構築を実行する
- 正常ターン後に `check_should_start_summary()` が呼ばれる
- `summary_service` が None の場合:
  - `build_summary_context()` は呼ばれる（legacy と同様、内部で早期 return する）
  - `check_should_start_summary()` は呼ばれない（`_summary_service is not None` ガードで skip）

## 必須テスト

- `pytest -q -m rollback_summary server/tests/` — real-refactored evidence が `pass`
- `pytest -q -m pre_extraction_parity server/tests/` — 既存の `pass` を維持
- 単体テスト（`test_chat_service_refactored.py`）:
  - `summary_service` あり / なし の両方でターン先頭・ターン後の挙動をテスト

## ロールバック確認対象

- `rollback_summary`: `pytest -q -m rollback_summary server/tests/`
- `pre_extraction_parity`: `pytest -q -m pre_extraction_parity server/tests/`

## 完了条件

- `verification.md` の必須コマンドがすべて `pass` または文書化された免除がある。
- `gate_a_scenario_matrix.md` の `summary_rollback` の real-refactored evidence が `pass` に更新されている。
- `handoff.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
- `gate_a_scenario_matrix.md` の該当 evidence を更新する。
