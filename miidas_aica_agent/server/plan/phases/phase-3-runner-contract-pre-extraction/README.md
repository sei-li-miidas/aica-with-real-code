# フェーズ: runner contract と抽出前 parity gate

## 目的

Responses style の現行 streaming semantics を fakeable な runner 境界で固定し、責務抽出前に高リスク invariant を characterization contract として押さえる。

Phase 3 の parity は独立 refactored 実装の regression protection ではない。`legacy` と Phase 2 の `delegating-refactored` を同じ fixture で特徴づけ、Phase 4 以降の real-refactored evidence が比較できる土台を作る。

## スコープ

スコープ内:
- legacy minimal runner seam
- SDK-shaped legacy event fixtures
- OpenAI Agent SDK version / pinning policy の記録
- `LLMRunner` / `LLMRunStream` contract
- `ResponsesAgentRunner`
- pre-extraction characterization invariant

スコープ外:
- `CompletionsAgentRunner`
- production path で legacy が normalized `LLMRunStream` を consume する変更
- refactored 独立実装の完成
- final refactored parity / release confidence の判定

## 開始条件

- Phase 2 が完了している。
- delegating adapter 経由で legacy/refactored fixture が実行できる。

## 終了条件

- Responses compatibility field が adapter 内に閉じている。
- `gate_a_scenario_matrix.md` の marker membership table で、`pre_extraction_parity` と `pre_extraction_bootstrap` の membership が定義されている。
- Phase 4 の各 extraction PR が参照する test migration map の型が明確になっている。
- `server/plan/phases/gate_a_scenario_matrix.md` の required scenario matrix で、Phase 3 が owner の scenario と Phase 3 gate に必要な scenario の `legacy evidence` / `delegating evidence` が `pass` で埋まっている。`fixture-schema only` は完了条件を満たさない。ただし legacy dependency reintroduction の `legacy evidence` のみ `fixture-schema only` のまま許容する（Phase 4 bootstrap が前提のため）。
- `real-refactored evidence` は `pending-phase-4` と明記され、Phase 3 の pass を final refactored parity と誤認しない。
- `pre_extraction_parity` の Phase 3 pass は legacy/delegating full behavioral characterization の完了を意味し、real-refactored regression protection とは扱わない。

## フィーチャー

| フィーチャー | 目的 | 依存関係 | ステータス |
| --- | --- | --- | --- |
| feature-1-responses-runner-contract | Responses runner 境界を固定する。 | Phase 2 | done |
| feature-2-pre-extraction-parity | 抽出前の高リスク invariant を characterization として固定する。 | feature-1 | done |
| feature-3-full-behavioral-parity-evidence | required scenarios の full behavioral runtime assertions を実装し、`legacy evidence` を `pass` にする。 | feature-2 | done |

## タスク分割

| フィーチャー | タスク | 目的 | 必須検証 |
| --- | --- | --- | --- |
| feature-1-responses-runner-contract | task-1-legacy-runner-seam-and-fixtures | legacy runner seam と SDK-shaped fixtures を追加する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` |
| feature-1-responses-runner-contract | task-2-responses-runner-adapter | `LLMRunner` / `LLMRunStream` / `ResponsesAgentRunner` を固定する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` |
| feature-2-pre-extraction-parity | task-1-marker-membership-fixture-map | marker membership table と required fixture map を実体化する。 | marker registration 確認 / fixture existence |
| feature-2-pre-extraction-parity | task-2-legacy-delegating-characterization | required scenario の legacy/delegating evidence を埋める。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` |
| feature-2-pre-extraction-parity | task-3-test-migration-map | affected private tests の移行先を固定する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` |
| feature-3-full-behavioral-parity-evidence | task-1-db-and-history-parity | `history mapping` と `DB side effects` の full behavioral assertions を実装する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` |
| feature-3-full-behavioral-parity-evidence | task-2-tool-result-parity | `tool result response shape` の full behavioral assertions を実装する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner` |
| feature-3-full-behavioral-parity-evidence | task-3-security-cancellation-parity | `security block cleanup` と `cancellation cleanup` の full behavioral assertions を実装する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security` |
| feature-3-full-behavioral-parity-evidence | task-4-workflow-parity | `workflow side effects` の full behavioral assertions を実装する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security` |
| feature-3-full-behavioral-parity-evidence | task-5-summary-rollback-parity | `summary rollback` の full behavioral assertions を実装する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`, `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary` |
| feature-3-full-behavioral-parity-evidence | task-6-coverage-gap-inventory | `pre_extraction_parity` coverage report を source of truth に、legacy `chat_service.py` の未カバーブランチ inventory を作成し residual parity 実装対象を固定する。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing server/tests/` |
| feature-3-full-behavioral-parity-evidence | task-7-residual-branch-parity | task-6 inventory に残った residual reachable branches を parity テストで閉じ、legacy `chat_service.py` branch coverage を 100% にする。 | `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity --cov=services.chat_service --cov-branch --cov-report=term-missing server/tests/` |

## 必須検証

- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`
- `server/plan/phases/gate_a_scenario_matrix.md` の required scenario matrix 更新
- `server/plan/phases/gate_a_scenario_matrix.md` の marker membership table 完成
- required scenario fixture / test file の存在確認
- `server/pyproject.toml` の Gate A marker 登録確認
- OpenAI Agent SDK の利用 version と pinning policy が `server/plan/architecture.md` または該当 handoff に記録されていること

## メモ

- Gate A に Completions style runtime switching は含めない。
