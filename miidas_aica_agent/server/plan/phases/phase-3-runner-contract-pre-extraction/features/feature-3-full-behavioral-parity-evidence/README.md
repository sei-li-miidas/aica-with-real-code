# フィーチャー: full behavioral parity evidence

## 目的

`fixture-schema only` の required scenarios に full behavioral runtime assertions を追加し、`legacy evidence` を `pass` にする。

Phase 4 の各 extraction task が開始時点から完全な regression net を持てる状態にする。

## 親フェーズ

- フェーズ: phase-3-runner-contract-pre-extraction

## スコープ

スコープ内:
- required scenarios の full behavioral legacy/delegating runtime assertions
- `chat()` を起動して観測可能な出力をアサートするテスト実装
- 未到達コードパスの発見（legacy の unused code 特定）
- `chat_service.py` の未カバーブランチ inventory 作成と、100% 到達までの residual parity テスト追加

スコープ外:
- real-refactored evidence の作成
- component extraction
- legacy dependency reintroduction の runtime behavioral 証明（Phase 4 bootstrap が前提のため除外）

## 依存関係

- feature-2-pre-extraction-parity

## モック方針

パリティテストは外部システム境界だけをモックする。ビジネスロジックを持つインプロセスサービスはモックしない。

**モックする（外部システム境界）:**
- `ChatRepository`、`PositionRepository`、`UserRepository`、`ActionLogRepository` — DB 操作
- `AICAAPIRepository` — 外部 API
- `BaseRateLimitRepository` — Redis/DB 操作
- `WorkflowRepository`、`WorkflowDefinitionRepository` — DB 操作
- `Runner.run_streamed` および `openai.AsyncOpenAI` クライアント — OpenAI SDK インターフェース

**モックしない（リアルインスタンスを使う）:**
- `PositionService` — モックリポジトリをバックに持つリアルインスタンス
- `RateLimitService` — モック `BaseRateLimitRepository` をバックに持つリアルインスタンス
- `WorkflowService` — モックリポジトリをバックに持つリアルインスタンス

**`LLMService` — 特殊ケース:**
`LLMService` は OpenAI クライアント初期化と MCP サーバー接続の両方を管理する重量インフラコンポーネントである。MCP サーバー起動はテストインフラ範囲外のため、`LLMService` についてはリアルインスタンスではなくモックを許容する。主な利用箇所は `init_session()` でのエージェントクローンが中心のため、`LLMService.clone_agents()` の戻り値をスタブすれば内部実装のモックは不要。

## タスク

| タスク | 目的 | 依存関係 | 必須検証 | ステータス |
| --- | --- | --- | --- | --- |
| task-1-db-and-history-parity | `history mapping` と `DB side effects` の full behavioral assertions を実装する。`init_session()` から Agent SDK input への mapping と、`chat()` の DB 書き込み（session/history/tool output/retry error）をリポジトリモックでアサートする。 | feature-2 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` | done |
| task-2-tool-result-parity | `tool result response shape` の full behavioral assertions を実装する。Runner が tool call イベントを emit したとき、position search / job type search / workflow start の frontend response shape が legacy の JSON shape と一致することをアサートする。 | task-1 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` | done |
| task-3-security-cancellation-parity | `security block cleanup` と `cancellation cleanup` の full behavioral assertions を実装する。forbidden/context-danger 検知で session が block され detector state が cleanup されること、および `chat()` generator を `aclose()` したとき `StreamGuard` / `InjectionDetector` / stream-local buffer の idempotent cleanup が実行されることをアサートする。 | task-1 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security` | done |
| task-4-workflow-parity | `workflow side effects` の full behavioral assertions を実装する。jobtype selected/clear と workflow submitted/cancelled が state を更新し、chat stream contract を返すことをリアル `WorkflowService`（モックリポジトリバック）でアサートする。 | task-1 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security` | done |
| task-5-summary-rollback-parity | `summary rollback` の full behavioral assertions を実装する。`summarize_position_detail_chat()` が chat runtime switching の外側にあり summary model config を使い続けることをアサートする。 | task-1 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary` | done |
| task-6-coverage-gap-inventory | task-1〜5 完了時点の `pre_extraction_parity` coverage report を source of truth に、`chat_service.py` の未カバーブランチを 1 件ずつ inventory 化する。各ブランチに対して task-7 で追加すべき parity scenario / fixture / assertion を固定する。 | task-5 | `pytest -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing` | done |
| task-7-residual-branch-parity | task-6 の inventory を source of truth に、required scenario だけでは埋まらなかった residual reachable branches を public interface 経由の parity テストで閉じ、legacy `chat_service.py` branch coverage を 100% にする。 | task-6 | `pytest -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing` | done* |

`*` task-7 は user 指示で legacy stream-loop change を revert したため、最終 coverage は `99%` (`661->978`) で記録している。`async for event in run_result.stream_events()` の zero-yield 終端は parity tests で挙動確認済みだが、coverage は暗黙の `StopAsyncIteration` fallthrough を credit しない。`100%` にするには legacy loop の explicit async iterator 化が必要だが、この変更は採用していない。

## カバレッジ方針

この feature のゴールは、パリティテストのみで legacy `chat_service.py` の branch coverage 100% を達成することである。

既存の task-1〜5 は required scenario を behavioral runtime assertions に置き換えるための scenario-driven task であり、それだけで 100% 到達を保証するものではない。100% 到達のために、feature 後半で residual branch closure を明示的に扱う。

進め方は以下のとおり:

1. task-1〜5 で required scenario の legacy / delegating evidence をすべて `pass` にする。
2. task-6 で `pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing` を実行し、未カバーブランチを inventory 化する。
3. task-6 で全未カバーブランチを `reachable by parity test` / `requires plan amendment` に分類する。
4. `reachable by parity test` と判定されたブランチは task-7 で public interface 経由の parity テストで閉じる。
5. `requires plan amendment` と判定されたブランチがある場合は、feature owner が task-6 handoff を source of truth に feature / phase plan を更新し、追加 task または dead code removal task を明示してから継続する。

この feature では、coverage 未達を dead code / explicit waiver で暗黙に閉じることは完了条件にしない。task-6 で public interface から到達できないブランチが見つかった場合は plan defect として記録し、plan amendment を経ないまま feature を `done` にしてはいけない。

task-7 については、user 指示で legacy stream-loop change を revert したため、最終 coverage は `99%` (`661->978`) のまま残っている。これは legacy `async for event in run_result.stream_events()` の zero-yield 終端で発生する暗黙の `StopAsyncIteration` fallthrough であり、coverage 上で `100%` にするには legacy loop 自体を explicit async iterator 形式へ書き換える必要がある。Gate A matrix と task handoff/verification に未達理由を明記したうえで、本 feature では user 判断により task-7 を `done` 扱いにした。

## 完了条件

- `gate_a_scenario_matrix.md` の legacy/delegating evidence が Phase 3 owner 分すべて `pass` で埋まっている。`fixture-schema only` は完了条件を満たさない。
- legacy dependency reintroduction の `legacy evidence` のみ `fixture-schema only` のままでよい（Phase 4 bootstrap が前提のため）。
- feature-3 の task-1〜6 がすべて `done`、task-7 が `done*` である。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest server/tests/ -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing` で、legacy `chat_service.py` の branch coverage が 100% である。ただし task-7 の `done*` では、user 指示で legacy stream-loop change を採用しないため `99%` / residual `661->978` を Gate A matrix、handoff、verification に記録した状態を完了扱いとする。
- task-6 で `requires plan amendment` に分類されたブランチがあった場合、その対応 task / plan 更新が phase / feature plan に反映され、完了済みである。
- `real-refactored evidence` は `pending-phase-4` と明記されている。
