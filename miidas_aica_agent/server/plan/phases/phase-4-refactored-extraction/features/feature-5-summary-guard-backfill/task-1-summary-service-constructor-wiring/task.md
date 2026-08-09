# タスク: task-1-summary-service-constructor-wiring

## 目的

`chat_service_refactored.ChatService.__init__` の summary 依存境界を native refactored 前提で確定する。`SummaryService` と `LLMOutputGuard` を DI するか内部生成するかを明示し、実装と container wiring を一致させる。

## 現行ギャップの確認

`containers.py` の現行 `chat_svc` wiring は refactored `ChatService` に `summary_service` を渡していない。そのため「unexpected keyword argument 'summary_service'」は現行構成の再現バグではない。

一方で、summary 関連処理を refactored path に追加するための依存境界が未定義であり、task-2 実装の前提が揺れる。task-1 はこの境界を固定するタスクとする。

## 最初に読むコンテキスト

- 親フィーチャー README: `server/plan/phases/phase-4-refactored-extraction/features/feature-5-summary-guard-backfill/README.md`
- `server/src/aica_agent/services/chat_service.py`（summary 関連ロジックの参照実装）
- `server/src/aica_agent/services/chat_service_refactored.py`（現行 constructor / field 構成）
- `server/src/aica_agent/containers.py`（`_build_chat_service` と `chat_svc` プロバイダー定義）

## スコープ

許可する変更:
- `chat_service_refactored.py`: constructor に `summary_service` / `llm_output_guard` の受け口を追加し、native refactored path で利用可能にする
- `containers.py`: task-1 で決めた DI 方針に合わせて provider wiring を更新する（必要な場合のみ）
- `server/tests/unit/services/test_chat_service_refactored.py`: constructor 変更に追従するテスト更新

許可しない変更:
- `build_summary_context()` 相当処理や `check_should_start_summary()` の呼び出し追加（task-2 で実施）
- `ConversationState` への `summary_context_cache` フィールド追加（phase-4 では不要）
- `SummaryService` 内部ロジックの変更
- legacy 委譲 (`LegacyChatService` 再導入) を前提にした変更

## 実装メモ

### 依存境界の候補

```python
from security.llm_output_guard import LLMOutputGuard
from services.summary_service import SummaryService

class ChatService(BaseService):
    def __init__(
        self,
        ...,
        llm_runner: LLMRunner,
        llm_output_guard: LLMOutputGuard | None = None,
        summary_service: SummaryService | None = None,
    ) -> None:
        self.llm_output_guard = llm_output_guard or LLMOutputGuard()
        self._summary_service = summary_service
```

### container 側の整合

`containers.py` の `chat_svc` provider は、task-1 で確定した依存境界と一致させる。DI を採用する場合は `summary_service` / `llm_output_guard` の注入を追加し、非DI運用とする場合は README / task.md に理由を明記する。

### `init_session()` への影響

task-1 は依存注入境界の確定まで。summary context 再構築および summary 起動判定の実行タイミング追加は task-2 で扱う。

## 必須テスト

- `pytest -q -m rollback_summary server/tests/` — `pass` を維持
- `pytest -q -m pre_extraction_parity server/tests/` — `pass` を維持
- 単体テスト:
  - `summary_service` を注入する構成 / しない構成の両方で constructor が成立すること
  - `llm_output_guard` を注入する構成 / しない構成の両方で既存ガード挙動を壊さないこと

## ロールバック確認対象

- `rollback_summary`: `pytest -q -m rollback_summary server/tests/`
- `pre_extraction_parity`: `pytest -q -m pre_extraction_parity server/tests/`

## 完了条件

- `verification.md` の必須コマンドがすべて `pass` または文書化された免除がある。
- `handoff.md` が更新されている。
- `server/plan/phases/status.md` が更新されている。

## 引き継ぎ要件

- `handoff.md` を更新する。
- `verification.md` を更新する。
- `server/plan/phases/status.md` を更新する。
