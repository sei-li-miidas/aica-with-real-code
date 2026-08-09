# ChatService Refactoring Plan

## 目的

- `server/src/aica_agent/services/chat_service.py` の外部公開インターフェースと挙動を維持する。
- リファクタ版 `server/src/aica_agent/services/chat_service_refactored.py` を現行版と並行存在させ、設定で切り替えられるようにする。
- `chat_service_refactored.py` / `ChatService` は全体 orchestration に集中させ、現行 `chat_service.py` のように細かい処理を 1 クラスへ集約しない。
- OpenAI Agent SDK 利用を前提にする。
- Gate A では Responses style のまま構造リファクタ、DI 切替、endpoint 境界、contract test、rollback を完成させる。
- Gate B では Gate A 完了後に Completions style とチャット用 Agent モデル切替を追加する。
- Completions style はリファクタではなく新しい runtime behavior として扱い、Gate A の release candidate には含めない。

## Gate A フェーズ概要

| フェーズ | 役割 | 何を証明するか |
| --- | --- | --- |
| [Phase 1](server/plan/phases/phase-1-endpoint-config-boundary/README.md) | endpoint/config 境界を固定し、最小 scaffold を作る。 | invalid config が startup で失敗し、endpoint が concrete chat service に依存しないこと。 |
| [Phase 2](server/plan/phases/phase-2-service-variant-switch/README.md) | service variant 切替と delegating adapter を入れる。 | `legacy` と `refactored` を切り替えられ、refactored 側はまだ wiring-only であること。 |
| [Phase 3](server/plan/phases/phase-3-runner-contract-pre-extraction/README.md) | extraction 前の runner contract を characterization する。 | legacy / delegating behavior を matrix で固定し、real-refactored evidence はまだ `pending-phase-4` であること。 |
| [Phase 4](server/plan/phases/phase-4-refactored-extraction/README.md) | real refactored shell を作り、部品を順に抽出する。 | `chat_service_refactored.ChatService.chat()` が実 runner を呼び、delegating adapter を戻すと behavioral proof が失敗すること。 |
| [Phase 4.5](server/plan/phases/phase-4.5-e2e-workflow-compatibility/README.md) | e2e client を workflow 対応に更新し、refactored 実体との契約齟齬を解消する。 | `response_type="workflow"` と workflow submit/cancel request を e2e が受理・送信でき、workflow 発火シナリオでも e2e run が落ちないこと。 |
| [Phase 5](server/plan/phases/phase-5-final-parity/README.md) | 最終 parity と coverage / risk evidence を固める。 | 必須シナリオが legacy と refactored で一致し、critical scenario はすべて `pass` であること。 |
| [Phase 6](server/plan/phases/phase-6-release-readiness/README.md) | rollback 手順と release readiness を文書化する。 | config-only rollback 手順と release candidate checklist が揃っていること。 |

## 想定する主な変更領域

- ここに挙げるのは、現時点で主に変更が発生すると見込む領域であり、修正可能なファイルを限定するものではない。
- 実装中に必要と分かった関連ファイル、テスト、設定、ドキュメントは、この計画の目的と外部挙動維持に沿う範囲で追加・修正してよい。
- 主な変更候補:
  - `server/src/aica_agent/services/chat_service.py`
  - `server/src/aica_agent/services/chat_service_refactored.py`
  - `server/src/aica_agent/services/llm_service.py`
  - `server/src/aica_agent/containers.py`
  - `server/src/aica_agent/endpoints.py`
  - `server/src/aica_agent/config.yml`
  - `server/tests/`
- 外部公開インターフェース:
  - `init_session(model_name: str) -> tuple[ChatSessionStatus, bool]`
  - `chat(input: ChatRequestModel, client_ip: str) -> AsyncGenerator[ChatStreamResponseModel, None]`
  - `summarize_position_detail_chat(chat_request: ChatRequestModel) -> ChatSessionStatus`
  - `job_type_decided(input: ChatRequestModel, client_ip: str) -> AsyncGenerator[ChatStreamResponseModel, None]`
  - `clear_jobtype(input: ChatRequestModel, client_ip: str) -> AsyncGenerator[ChatStreamResponseModel, None]`
  - `workflow_submitted(input: ChatRequestModel, client_ip: str) -> AsyncGenerator[ChatStreamResponseModel, None]`
  - `workflow_cancelled(input: ChatRequestModel, client_ip: str) -> AsyncGenerator[ChatStreamResponseModel, None]`
  - `check_if_previous_chat_histories_exist(encrypted_position_id: str) -> bool`
  - `load_previous_chat_histories(limit: int, encrypted_position_id: str | None, before_id: str | None) -> tuple[list, bool]`
- 公開メソッドの side effect expectations:
  - `chat()`: stream response 生成、chat/session history 保存、tool output 更新、security block、workflow/tool side effect を発生させうる。
  - `summarize_position_detail_chat()`: position detail chat summary を保存し、summary model 設定を使う。chat runtime switching の対象外。
  - `job_type_decided()` / `clear_jobtype()` / `workflow_submitted()` / `workflow_cancelled()`: workflow/jobtype state を更新し、その後 `chat()` と同じ stream 契約で response を返す。
  - `check_if_previous_chat_histories_exist()` / `load_previous_chat_histories()`: REST history path の read-only 操作として扱い、初期化済み `ConversationState` に依存しない。
- 非対象:
  - フロントエンドの仕様変更
  - MCP ツール仕様の変更
  - DB スキーマ変更。ただしテスト上必要な fixture / fake は追加する。

Note:
- `init_session()` の引数名は `model_name` に寄せる。現行名 `provider` は実態とずれており、Phase 1 以降はチャット用 Agent model name として扱うため。
- 外部挙動維持のため、`endpoints.py` からの呼び出しは positional call のまま維持する。keyword call が残っていないことを検索または unit test で確認したうえで、`ChatServiceProtocol` / `chat_service_refactored.ChatService` / 必要に応じて legacy `chat_service.ChatService` の引数名を `model_name` に揃える。

## 現行 `chat_service.py` への想定修正点

現行 `chat_service.py` は移行完了まで変更最小限にし、既存バグ修正以外の構造変更は `chat_service_refactored.py` 側へ寄せる。計画上、現行 `chat_service.py` へ直接入る想定の修正は下記に限定する。

1. `init_session()` 引数名の整理
   - `provider` という引数名を `model_name` に寄せる可能性がある。
   - `endpoints.py` からの呼び出しは positional call のまま維持し、keyword call がないことを検索または unit test で確認する。
   - default config では現行 `"openai/gpt-4.1"` と同じ値が渡ることを固定し、外部挙動を変えない。

2. legacy runner seam の追加
   - Phase 3 で、テスト差し込み用の最小 seam を追加する。
   - 例: private method `_run_streamed(...)` または optional internal runner attribute を追加し、通常実行時は現行通り `Runner.run_streamed(...)` が返す SDK-shaped stream を処理し続ける。
   - constructor に新しい必須引数は追加しない。

3. test / coverage のための最小補助
   - legacy characterization test や coverage 計測に必要な範囲で、テスト差し込み口・型注釈・docstring などの小修正が発生する可能性がある。
   - private method の構造変更や責務分割は行わない。

明示的に行わないこと:
- 現行 `chat_service.py` を `ConversationState`, `HistoryMapper`, `ChatPersistence`, `StreamEventProcessor`, `ToolEventHandler`, `StreamGuard` へ分割しない。
- 現行 `chat_service.py` から `chat_service_refactored.py` へ依存させない。
- 現行 `chat_service.py` の production stream event consumption を normalized `LLMRunStream` ベースへ置き換えない。
- 現行 `chat_service.py` の constructor shape を refactored 実装に合わせて変更しない。

## 前提と注意

- この計画は 2 つの gate に分ける。
  - Gate A: legacy/refactored structural refactor only。Responses style only。導入する config は `service_variant` と現行チャットモデル値の明示化に限定する。
  - Gate B: Completions style runtime switching。Gate A 完了後に別 release candidate として扱う。
- Gate A の Phase はリリース単位ではなく、Gate A 用ミドルブランチ上で進める作業順序を表す。
- Gate A は、構造リファクタ、契約テスト、カバレッジ確認、rollback 確認が揃ってから `develop` へリリースする。
- Gate B は、Completions style の focused prototype が stream, handoff, retry, tool replay, rollback semantics を証明してから開始する。
- ブランチ運用は Gate ごとに `develop` からミドルブランチを作る。Gate A 完了後にミドルブランチから `develop` へ統合 PR を作る。Gate B は Gate A 統合後の別ミドルブランチで扱う。
- Gate A は単一 release candidate だが、ミドルブランチへの作業は計画 FIX 後に `server/plan/phases/phase-x/features/feature-y/task-z` へ分割する。各 task は原則として 1 PR 単位とする。
- この計画段階では phase/feature/task の確定分割は行わない。本文中の作業 slice は後続の phase/feature/task 分割候補であり、PR 数や PR 番号を固定しない。
- `endpoints.py` は現状 `ChatService` の具体クラスに依存しているため、切替は DI コンテナで完結させる。
- OpenAI Agent SDK は維持する。低レベル API へ全面置換しない。
- Gate A では Responses style の現行 semantics を維持し、Completions style は実装しない。
- Responses style は `previous_response_id` を使う。Completions style では同じ概念を直接使えない可能性があるため、Gate B の prototype で差分を検証してから runner adapter に閉じ込める。
- 現行 `chat_service.py` は移行完了まで変更最小限にし、既存バグ修正以外の構造変更は `chat_service_refactored.py` 側へ寄せる。

## Phase/feature/task 分割後の Agent 間コミュニケーション

タスク実装セッション間ではメモリ共有しない前提にする。そのため、Agent 間のコミュニケーションはチャット履歴ではなく、repository 内の markdown file を source of truth として行う。

想定ディレクトリ:

```text
server/plan/
  refactoring_plan.md
  architecture.md
  templates/
    status.md
    phase_README.md
    feature_README.md
    task.md
    handoff.md
    verification.md
  phases/
    status.md
    phase-1-endpoint-config-boundary/
      README.md
      features/
        feature-1/
          README.md
          task-1/
            task.md
            handoff.md
            verification.md
          task-2/
            task.md
            handoff.md
            verification.md
```

各 file の役割:
- `phases/status.md`
  - phase/feature/task 全体の進捗一覧。
  - phase, feature, task status, branch/PR, handoff link, blocked reason, verification summary を記録する。
  - template: `templates/status.md`
- `phases/phase-x/README.md`
  - phase の目的、対象範囲、phase exit criteria、含まれる feature 一覧を記録する。
  - template: `templates/phase_README.md`
- `phases/phase-x/features/feature-y/README.md`
  - feature の目的、対象範囲、依存 task、完了条件を記録する。
  - template: `templates/feature_README.md`
- `phases/phase-x/features/feature-y/task-z/task.md`
  - task の目的、変更してよい範囲、変更してはいけない範囲、依存前提、完了条件、必須 test command を記録する。
  - template: `templates/task.md`
- `phases/phase-x/features/feature-y/task-z/handoff.md`
  - 実装後に次 task へ渡す情報を記録する。
  - 変更した file、新規 API/helper/fixture、設計判断、注意点、未解決事項、後続 task が前提にしてよいことを含める。
  - template: `templates/handoff.md`
- `phases/phase-x/features/feature-y/task-z/verification.md`
  - 実行した test command、結果、失敗理由、未実行 test と理由を記録する。
  - template: `templates/verification.md`

フォーマットルール:
- `task.md`, `handoff.md`, `verification.md`, `phases/status.md` は task 間コミュニケーションの source of truth なので、原則 template に従う。
- phase / feature の `README.md` も template を使う。ただし phase / feature 固有の説明が必要な場合は、見出しを追加してよい。
- ADR、調査メモ、補足設計メモなど、後続 task の必須 input ではない文書は自由フォーマットでよい。
- template にない重要情報を追加した場合は、後続 task が見落とさないように `handoff.md` から link する。
- task を `done` にするには、`verification.md` の required command がすべて `pass`、または owner/reason/date/follow-up 付きで `waived`、または理由付きで `not-applicable` になっている必要がある。
- required command が `fail` または `not-run` のままの task は `done` にしてはいけない。
- 実装フェーズでは、`phases/status.md` と各 task の `verification.md` の整合性を確認する軽い lint script または static check を追加する。
  - `status.md` が `done` の task は、対応する `verification.md` の required command が `pass` / `waived` / `not-applicable` のみであることを検査する。
  - `waived` には owner, reason, date, follow-up があることを検査する。
  - `not-applicable` には reason があることを検査する。

実装 Agent の作業ルール:
- 作業開始時に必ず `refactoring_plan.md`, `architecture.md`, 自分の `task.md`, 依存 task の `handoff.md` を読む。
- 実装中に plan と違う判断をした場合は、code だけでなく `handoff.md` に理由を書く。
- shared boundary を変更した task は、該当 rollback subset の command と結果を `verification.md` に残す。
- task 完了時に `handoff.md` と `verification.md` を更新し、`phases/status.md` の status を更新する。
- 次 task の Agent は、前 task のチャット履歴ではなく `handoff.md` と `verification.md` を source of truth とする。

禁止事項:
- セッション内の記憶だけを前提に後続 task を進めない。
- `handoff.md` に書かれていない暗黙の実装判断を後続 task の前提にしない。
- test 未実行のまま完了扱いにする場合、未実行理由を `verification.md` に残さないまま進めない。

## 推奨アーキテクチャ

### 1. 公開ファサード

`chat_service_refactored.py` でもクラス名は現行版と同じ `ChatService` にする。ファイル名で実装を分け、`containers.py` では module alias で区別する。

例:

```python
from services import chat_service as legacy_chat_service
from services import chat_service_refactored as refactored_chat_service
```

両方の `ChatService` は同じ公開メソッド、同じ戻り値、同じ observable behavior を持つ。

Constructor について:
- constructor shape は公開契約に含めない。
- legacy/refactored の constructor は `containers.py` が吸収する。
- `chat_service_refactored.ChatService` は内部コンポーネント分割に必要な依存を constructor で受け取ってよい。
- `endpoints.py` と contract tests は constructor ではなく `ChatServiceProtocol` の public methods だけを見る。

責務:
- エンドポイントから受けたリクエストの入口
- セッション単位の状態保持
- 内部コンポーネントの orchestration

### 2. 内部コンポーネント

`services/chat/` 配下に分割する。

- `config_validator.py`
  - `agent_runtime` と `model_list` の整合性を検証する。
  - validation owner はこの module とし、`application.py` startup hook から呼ぶ。CLI/unit test では同じ関数を直接呼べるようにする。
  - invalid config は app startup で fail fast させる。module import 時には fail させない。
- `agent_runtime_config.py`
  - `agent_runtime` の読み取り helper を提供する。
  - default model resolver はこの module に置く。`config_validator.py` は resolver を呼んで検証するが、読み取り責務を持たない。
  - 例: `get_service_variant(config)`, `get_agent_model(config)`, `resolve_default_agent_model(config)`。
- `conversation_state.py`
  - `_model_name`, `_active_agent_name`, `_chat_key`, `_position_id`, `_previous_response_ids`, `_conversation`, `_chat_histories`, `_should_save`, `_session_created` を集約する。
  - WebSocket chat flow では 1 `ChatService` instance = 1 WebSocket/session を前提にする。`containers.py` の `providers.Factory` により接続ごとに生成され、`endpoints.py` の `finally` と stream guard の cleanup で session-id 紐づきの一時状態を破棄する。
  - REST の履歴取得・存在確認では `ChatService` instance は短命で stateless に扱う。REST path は `init_session()` 済みの `ConversationState` に依存してはいけない。
- `history_mapper.py`
  - DB の `ChatHistory` と Agent SDK input / フロント返却 payload の相互変換。
- `turn_preparer.py`
  - `PageName.CHAT` / `PageName.POSITION_DETAIL` / position detail 初期 developer message の組み立て。
- `chat_persistence.py`
  - セッション作成、ユーザー/開発者/LLM/ツール履歴保存、遅延保存キュー。
- `tool_event_handler.py`
  - tool call / tool output / handoff / stop_at_tool の処理。
- `stream_guard.py`
  - `InjectionDetector` を使ったストリーミング中・終了時の安全チェック。
- `workflow_chat_handler.py`
  - `job_type_decided`, `clear_jobtype`, `workflow_submitted`, `workflow_cancelled` の前処理。
- `llm_runner.py`
  - Agent SDK の `Runner.run_streamed` 呼び出し、retry、usage、API backend 差分を隠蔽。

### 3. Gate A 設定

Gate A では service variant と現行チャットモデル値の明示化だけを設定する。`api_style` は導入せず、runtime backend switching / model provider switching も行わない。

```yaml
agent_runtime:
  service_variant: legacy # legacy | refactored
  agent_model: openai/gpt-4.1
```

実装方針:
- `agent_runtime.agent_model` はチャット用 Agent モデルを指す。Gate A ではモデル切替機能ではなく、現行ハードコード値を config に明示化するための設定として扱う。
- `agent_runtime.agent_model` にポジション詳細チャットサマリ用モデルは含まない。
- ポジション詳細チャットサマリはチャット runtime switching の対象外とする。既存 summary 実装と `model_list.use_for: summary` の設定は Gate A で変更しない。
- `model_list` は利用可能な Agent model 定義の source of truth として残す。
- `agent_runtime.agent_model` は `init_session()` に渡すチャット用 Agent model の選択値とする。
- `agent_runtime.agent_model` が `model_list.use_for: agent` に存在しない場合は startup/config validation で fail fast し、silent fallback しない。
- `agent_runtime.agent_model` と `model_list.use_for: agent` が不整合な場合は `agent_runtime.agent_model` を優先して選択しつつ、存在しないモデルなら起動失敗にする。
- validation owner は `services/chat/config_validator.py` とする。`application.py` startup hook から `validate_agent_runtime_config(container.config)` を呼び、invalid config は app startup failure として扱う。
- `chat_service_refactored.ChatService` と service variant switch が実装登録される task までは `service_variant: legacy` のみ valid とする。`service_variant: refactored` が指定された場合は、refactored implementation が未登録であることを明示する config validation error で startup fail する。
- `chat_service_refactored.ChatService` と service variant switch が追加された task で、`service_variant: refactored` を valid にする。
- default config では現行 `init_session("openai/gpt-4.1")` と同じ model が渡ることを unit test で固定する。
- `LLMService._init_agents()` は `model_list` の model 定義から Agent を構築し、`init_session()` は `agent_runtime.agent_model` で既存 Agent 群を選ぶ。
- Gate A では Responses style の現行実行方式だけを使う。
- `chat_service_refactored.py` は Gate A 時点で Responses semantics を維持する。Responses 固有の `previous_response_id`, `last_response_id`, `last_agent`, `to_input_list()` は runner adapter 内で `continuation_state`, `agent_state`, `tool_replay_items` に map し、外部挙動は現行から変えない。

### 4. Gate B 設定

Gate B で初めて `api_style` を追加する。

```yaml
agent_runtime:
  service_variant: refactored
  api_style: completions # responses | completions
  agent_model: <provider/model>
```

実装方針:
- `api_style` は Agent SDK にどの実行方式を使わせるかを表す。
- 現状 Responses style は OpenAI モデル前提で、Completions style の場合のみ OpenAI 以外の provider も利用できる。
- Gate B では Responses style 用と Completions style 用の model 解決を `AgentModelFactory` に切り出す。
- チャットで Completions style を利用する場合のモデル変更は `agent_runtime.agent_model` の変更だけで完結させる。
- `chat_service_refactored.py` は `llm_runner.py` の stable interface だけを見る。Responses style の `previous_response_id` や Completions style の local conversation retention などの input 形式差分は runner 側で吸収する。

## 結合テスト計画

Goal: legacy `chat_service.py` と refactored `chat_service_refactored.py` の外部公開インターフェース挙動を、同じ scenario fixture で継続比較する。結合テストは Phase 5 から始めるものではなく、Phase 2 から開始して段階的に拡張し、Phase 5 で最終 parity suite として完成させる。

Test location:
- `tests/integration/chat_service_contract/` を基本置き場にする。
- legacy/refactored の両方へ同じ input fixture、fake repository、fake runner、fake service dependencies を流す。
- 比較対象は endpoint から見える response shape、stream event、DB side effect、error behavior、workflow/tool side effect とする。

段階的な拡張:
- Phase 1:
  - legacy のみで最小 contract harness を作る。
  - endpoint import decoupling、default model、WebSocket new-session START、existing-session RESTART_CHAT END を固定する。
- Phase 2:
  - delegating adapter を `refactored` として同じ fixture に乗せる。
  - この時点の refactored は legacy 委譲なので、wiring / endpoint boundary / response shape / service_variant switch の互換性確認に限定する。
  - 独立した refactored 実装の parity 証明とはみなさない。
- Pre-extraction parity gate:
  - streaming state machine の高リスク invariant を抽出前に固定する。
  - stream ordering, continuation state, agent state, stop-at-tool replay, tool result response shape, security block, DB write/update side effects, cancellation cleanup を含める。
- Phase 4:
  - 最初の bootstrap task で main `chat()` path の legacy 委譲を外し、runner boundary を使う薄い real `chat_service_refactored.ChatService` shell に置き換える。
  - bootstrap 後に `pre_extraction_parity` subset を refactored 実体で通す。
  - 各 extraction task PR で同じ scenario fixture を継続実行する。
  - refactored の実体に対してテストを流し、責務移植による挙動差分を検知する。
- Phase 4.5:
  - e2e headless client を `WORKFLOW` response と `WORKFLOW_ANSWERS_SUBMITTED` / `WORKFLOW_CANCELLED` request に対応させる。
  - workflow payload の contract validation と pending action dispatch を追加し、workflow 発火時に e2e run が中断しないことを確認する。
  - refactored 実体で workflow を含む scenario を e2e で実行し、Phase 5 parity suite 前の互換性ギャップを解消する。
- Phase 5:
  - 残りの scenario を追加し、legacy 委譲を削除済みの refactored 実体に対する最終 parity suite として完成させる。
  - coverage evidence と named behavioral invariants を揃える。

最終 parity suite に含める scenario:
- 新規セッション初期化成功
- 既存セッション再開
- blocked session
- REGISTERING / APPLYING 中の START
- 通常チャットの message delta / end response
- LLM エラー retry / 最終 error response
- forbidden word / context danger 検知
- position detail chat 初期化
- position search tool result
- job type search tool result
- start workflow tool result
- registration / application tool side effect
- summarize position detail chat
- job type selected / clear
- workflow submitted / cancelled
- previous history pagination

Named behavioral invariants:
- stream event ordering
- response JSON shape
- retry behavior and final error response
- `continuation_state` continuity。Gate A では Responses `previous_response_id` / `last_response_id` chain から map する。
- `agent_state` continuity。Gate A では Responses `last_agent` から map する。
- stop-at-tool replay via `tool_replay_items`。Gate A では Responses `to_input_list()` から map する。
- tool result frontend response shape
- DB write/update side effects
- block-session behavior
- workflow submit/cancel side effects
- summary remains outside chat runtime switching

Coverage policy:
- coverage は結合テストの代替ではなく、named behavioral invariants が十分にテストされているかを見る補助 evidence として扱う。
- `pytest-cov` で `services/chat_service.py` と `services/chat_service_refactored.py` の branch coverage を計測する。
- 現行 `chat_service.py` の未到達行は棚卸しし、到達不能・外部依存過大・例外防御などの理由と残リスクを plan またはテストコメントに記録する。

## Gate A 実行計画

### Phase 1: endpoint/config 境界の固定

Goal: リファクタ前に最小限の endpoint/config 境界を固定し、endpoint が現行 `chat_service.py` の具象実装へ直接依存しない状態を作る。

Actions:
- `agent_runtime.service_variant` と `agent_runtime.agent_model` を config に追加する。これは `handle_chat_session()` の model lookup より先に行う。
- `services/chat/config_validator.py` を追加し、`application.py` startup hook から呼ぶ。module import 時には validation しない。
- config validation を追加し、`agent_runtime.agent_model` が `model_list.use_for: agent` に存在することを app startup で検証する。
- Phase 1 と Phase 2 の DI lifecycle task までは `service_variant: legacy` のみ valid とし、`refactored` は clear startup error で拒否する。Phase 2 の Delegating adapter / service variant switch task で service variant switch と実装登録が入った時点で `refactored` を valid にする。
- `services/chat/service_protocol.py` を追加し、`ChatService` の公開メソッド一覧と戻り値を `ChatServiceProtocol` として定義する。
- `endpoints.py` の型注釈を具体 `ChatService` から `ChatServiceProtocol` に寄せる。
- `endpoints.py` の `ChatStreamResponse` / `ChatStreamResponseModel` / `ChatResponseType` 参照は `services.chat_service` 経由ではなく、既存の `utils.chat_response` から直接 import する。
- `endpoints.py` から `from services.chat_service import ...` をなくす。
- `handle_chat_session()` の `init_session("openai/gpt-4.1")` ハードコードをやめ、`agent_runtime.agent_model` から解決したチャット用 Agent モデルを渡す。
- `init_session()` の引数名を `model_name` に寄せる。`endpoints.py` からは positional call を維持し、keyword call がないことを確認して挙動を変えない。
- default config で `handle_chat_session()` から `init_session()` に渡る値が現行 `"openai/gpt-4.1"` と同一であることを unit test で固定する。
- 最小 contract harness を追加する。Phase 1 では legacy のみを実行対象にし、refactored は Phase 2 以降に同じ fixture へ乗せる。
- Phase 1 の contract scenario は小さく保つ。
  - endpoint import decoupling: `endpoints.py` が `services.chat_service` を import しない。
  - hardcoded model behavior: default config で `init_session()` に現行 `"openai/gpt-4.1"` が渡る。
  - WebSocket new-session START response shape。
  - WebSocket existing-session RESTART_CHAT END response shape。

Validation:
  - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q server/tests/unit/test_restful_api_endpoints.py server/tests/unit/test_websocket_endpoint.py`
  - config validation unit test:
    - default config resolves `"openai/gpt-4.1"` for chat Agent.
    - `agent_runtime.agent_model` absent from `model_list.use_for: agent` fails fast.
    - Phase 1 と DI lifecycle task まで、`agent_runtime.service_variant: refactored` は "refactored implementation is not registered yet" 相当の明確な startup/config validation error になる。
  - Phase 1 最小 contract harness が legacy `ChatService` で通る。
  - Minimum rollback suite の endpoint/config subset が `service_variant: legacy` で通る。

Exit criteria:
- `endpoints.py` が `services.chat_service` を import しない。
- response model construction/types が `chat_service.py` から切り離されている。
- `agent_runtime` が存在し、default config で現行 model と同じ値が解決される。
- config validation owner と fail timing が `services/chat/config_validator.py` + `application.py` startup hook に固定されている。
- Phase 1 と DI lifecycle task まで、`service_variant: refactored` が誤って silent fallback しない。
- Phase 1 最小 contract harness が legacy で通り、Phase 2 以降に refactored を同じ fixture へ追加できる形になっている。

### Phase 2: 切替口の追加

Goal: 現行版とリファクタ版が並行存在し、設定だけで切り替えられるようにする。

Actions:
- `chat_service_refactored.py` を追加し、最初は現行 `ChatService` と同じ公開メソッドだけを持つ一時的な delegating adapter として実装する。クラス名は `ChatService` に揃える。
- Phase 2 では `chat_service_refactored.ChatService` が `chat_service.ChatService` へ委譲する依存を許可する。これは切替口と contract harness を先に通すための一時ルールであり、Phase 4 の最後の extraction PR で削除する。
- この時点から legacy/refactored 共通の挙動維持テストを実行する。ただし Phase 2 の refactored は delegating adapter なので、テスト結果は endpoint/DI/response shape の切替互換性を確認するものであり、独立した refactored 実装の parity 証明とはみなさない。
- legacy `chat_service.py` から refactored 版への依存は禁止する。
- 既存の `Container.chat_svc` factory を variant-aware に変更する。
  - `agent_runtime.service_variant == "legacy"` なら `legacy_chat_service.ChatService`
  - `agent_runtime.service_variant == "refactored"` なら `refactored_chat_service.ChatService`
- config boundary task で追加済みの `agent_runtime` config は変更せず、Phase 2 の Delegating adapter / service variant switch task では service variant switch と `refactored` variant の実装登録だけを行う。
- Delegating adapter / service variant switch task で config validation を更新し、`service_variant: refactored` を valid にする。DI lifecycle task までは `refactored` を valid にしない。
- service variant 切替の unit test を追加する。
- DI lifecycle の unit test を追加し、`Container.chat_svc()` を複数回解決したときに別 `ChatService` instance が返ることを legacy/refactored 両設定で確認する。
- WebSocket/session ごとに別 instance が使われることを `handle_chat_session()` または dependency override のテストで固定する。

Validation:
- legacy 設定で既存テストが全て通る。
- refactored 設定で legacy/refactored 共通の挙動維持テストが通る。Phase 2 では delegating adapter 経由のため、これは切替口・endpoint 境界・response shape の互換性テストとして扱う。

Exit criteria:
- `chat_service.py` と `chat_service_refactored.py` が同時に import できる。
- `agent_runtime.service_variant` により DI で legacy/refactored を切り替えられる。
- DI が `ChatService` を singleton として共有せず、WebSocket/session ごとに別 instance を解決することがテストで保証されている。
- Phase 2 時点では refactored から legacy への一方向委譲を許可する。ただしこの依存は Phase 4 の最後の extraction PR で必ず削除する。
- delegating adapter に対する contract test は wiring と endpoint boundary の確認に限定して扱う。delegating adapter が通ることを refactored implementation の parity 証明とはみなさない。
- Phase 2 から開始した挙動維持テストは、Phase 4 の各 extraction PR で同じ fixture のまま refactored 実体に対して継続実行する。

### Phase 3: Responses runner 境界の固定

Goal: Gate A では Responses style の現行挙動だけを対象にし、streaming state machine を fakeable な runner 境界で固定する。責務移植より先に、SDK-shaped events を service が見る contract として固定する。

Actions:
- `LLMRunner` Protocol を作る。
  - `run_streamed(starting_agent, input, chat_key, continuation_state) -> LLMRunStream`
  - `LLMRunStream` は `stream_events()`, `continuation_state`, `agent_state`, `tool_replay_items`, `usage` を service-facing contract として提供する。
  - Gate A の `ResponsesAgentRunner` は `previous_response_id` を `continuation_state` に、`last_agent` を `agent_state` に、`to_input_list()` の stop-at-tool replay 対象を `tool_replay_items` に map する。
  - `previous_response_id`, `last_response_id`, `last_agent`, `to_input_list()` は Responses compatibility field として Gate A adapter 内に閉じ込める。`chat_service_refactored.ChatService` の安定 contract 名にはしない。
  - `stream_events()` は current `chat()` が扱う `raw_response_event` と `run_item_stream_event` 相当の fakeable event を返す。
  - `raw_response_event` は text delta, item_id, response ordering を表現する。
  - `run_item_stream_event` は message output, tool call, tool output, handoff, reasoning を表現する。
- stable service-facing concept と Responses compatibility field を分ける。
  - stable: `continuation_state`, `agent_state`, `tool_replay_items`, `usage`, normalized stream event。
  - Responses compatibility: `previous_response_id`, `last_response_id`, `last_agent`, `to_input_list()`。
  - Gate B の Completions style は stable concept に合わせて実装し、Responses naming を core contract として継承しない。
- SDK-shaped legacy event fixtures を先に作り、Responses style の現行 event contract を characterization test で固定する。
  - fixture は現行 `Runner.run_streamed(...)` が返す SDK-shaped event の shape を元に作る。
  - stream ordering, duplicate response/item filtering, handoff item shape, `to_input_list()` replay behavior を含める。
  - normalized `LLMRunStream` fixtures は、この SDK-shaped fixture から adapter を通して導出する。新しい抽象から先に期待値を作らない。
- legacy `chat_service.ChatService` に最小 runner seam を導入する。
  - 例: private method `_run_streamed(...)` または optional internal runner attribute を追加し、通常実行時は現行通り `Runner.run_streamed(...)` が返す SDK-shaped stream を処理し続ける。
  - constructor shape を公開契約にしないため、legacy constructor に新しい必須引数は追加しない。
  - legacy seam は SDK-shaped stream を返す現行 path を維持し、test seam だけが SDK-shaped legacy event fixture を差し込む。
  - normalized `LLMRunStream` を production path で消費するのは refactored 実装だけに限定する。
  - tests はこの seam を差し替えて SDK-shaped legacy event fixture を流す。
- `ResponsesAgentRunner` を実装する。
  - 現行 `Runner.run_streamed(..., previous_response_id=...)` を包む。
- Gate A では `CompletionsAgentRunner`, `api_style`, Completions model provider switching を実装しない。
- summary 用 `LLMService.summarize_position_detail_chat()` はチャット runtime switching の対象外として別系統のまま残す。Gate A では既存 summary 実装と `model_list.use_for: summary` の設定を変更しない。

Validation:
- minimal legacy runner seam 経由で SDK-shaped legacy event fixtures を流し、legacy characterization tests を作る。
- `ResponsesAgentRunner` adapter test で、SDK-shaped legacy event fixtures から `LLMRunStream` の `stream_events()`, `continuation_state`, `agent_state`, `tool_replay_items`, `usage` へ正しく normalize されることを検証する。
- runner 単体テストで `Runner.run_streamed` に渡る引数を検証する。
- Responses style 設定では `previous_response_id` が渡ることを確認する。
- `last_response_id`, `last_agent`, `to_input_list()` 由来の値がそれぞれ `continuation_state`, `agent_state`, `tool_replay_items` に正しく map されることを確認する。

Exit criteria:
- SDK-shaped legacy event fixtures があり、Responses style の runner adapter が現行 event contract を normalized `LLMRunStream` contract へ崩さず map することをテストで保証している。
- legacy `chat_service.ChatService` は default behavior と production event-shape consumption を変えずに fake runner を差し込める seam を持つ。
- Phase 3 では `chat_service_refactored.ChatService.chat()` の独立実装 parity は要求しない。refactored が delegating adapter の間は wiring parity と runner adapter contract だけを確認する。
- Gate A に Completions style runtime switching が含まれていない。

### Pre-extraction parity gate

Goal: Phase 4 の責務移植を始める前に、stateful streaming refactor の高リスク挙動を最小 contract として固定する。ここを通るまでは `ConversationState`, `HistoryMapper`, `ChatPersistence`, `StreamEventProcessor`, `ToolEventHandler`, `StreamGuard` の抽出を始めない。

Positioning:
- この gate は Phase 3 と Phase 4 の間に置く。
- Phase 2 の delegating adapter が通す contract test は wiring 確認であり、refactored implementation parity の証明ではない。
- Phase 4 以降の各 extraction PR は、この gate の invariant subset を legacy/refactored の両方で維持する。

Required pre-extraction invariants:
- stream ordering: 複数 `raw_response_event` の item_id ordering と chunk ordering が現行と一致する。
- continuation state: Responses style の `previous_response_id` / `last_response_id` chain が `continuation_state` として保持され、次 turn の runner input に渡る。
- agent state: `last_agent` 相当の値が `agent_state` として保持され、handoff 後の次 turn に反映される。
- stop-at-tool replay: `to_input_list()` 由来の function_call_output が `tool_replay_items` として次 turn に replay される。
- tool result response shape: position search / job type search / workflow start の frontend response JSON shape が現行と一致する。
- security block: forbidden word / context danger で block-session side effect, cleanup, error response shape が現行と一致する。
- DB write/update side effects: session 作成、user/developer/LLM/tool history 保存、tool output update、retry final error 保存が現行と一致する。
- cancellation cleanup: `chat()` async generator を stream 途中で `aclose()` しても `StreamGuard` / `InjectionDetector` / stream-local buffer cleanup が実行される。`ConversationState` 全体は `providers.Factory` による 1 WebSocket/session 1 instance lifecycle で session 間共有しないことを別 invariant として固定する。

Test migration map:
- Phase 4 で移植する private method ごとに、既存 legacy private test を次のどれに移すかを extraction PR の先頭で明記する。
  - `refactored component test`: private method の純粋ロジックを `HistoryMapper`, `TurnPreparer`, `ToolEventHandler`, `StreamGuard`, `ChatPersistence` などの unit test へ移す。
  - `contract invariant`: public API / stream / DB side effect として観測すべき挙動を legacy/refactored 共通 contract test へ移す。
  - `legacy-only characterization`: 現行 private implementation detail であり、refactored に同型テストを作らない。残す理由と残リスクを test comment または PR description に書く。
- mapping がない private method を含む extraction PR は開始しない。

Validation:
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di`

Exit criteria:
- 上記 invariant が legacy と delegating refactored adapter の両方で full behavioral runtime assertions として通る。`fixture-schema only` は exit criteria を満たさない。ただし legacy dependency reintroduction のみ Phase 4 bootstrap が前提のため `fixture-schema only` のまま許容する。
- delegating adapter 依存が残っているため、この時点の refactored pass は wiring parity としてだけ扱うことが明記されている。
- Phase 4 の bootstrap task で delegating adapter の main `chat()` path を薄い real refactored shell に置き換え、同じ `pre_extraction_parity` suite を refactored 実体に対して通せる。
- test migration map が作成され、Phase 4 の各 extraction PR が affected private tests の移行先を示せる。

### Phase 4: リファクタ版への責務移植

Goal: `chat_service_refactored.py` の public behavior を維持したまま、内部責務を小さなクラスへ分割する。

Actions:
- Bootstrap task を最初に実施する。
  - main `chat()` path では legacy `services.chat_service.ChatService` を import / instantiate / delegate しない状態にし、`chat_service_refactored.ChatService` が `LLMRunner` / `LLMRunStream` boundary を使う薄い real shell として動作する状態にする。
  - この bootstrap では大きな責務分割をまだ行わず、既存処理の一部を最小限に移して `pre_extraction_parity` subset を通すことを目的にする。
  - static check または unit test で、main `chat()` path が legacy `ChatService` を import / instantiate / delegate していないことを保証する。
  - bootstrap 後に `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity` を必ず refactored 実体で通す。
- `ConversationState` を導入し、状態変数を移す。
  - WebSocket chat flow では `ChatService` instance は 1 WebSocket/session 専用とし、セッション間で `ConversationState` を共有しない。
  - REST の `check_if_previous_chat_histories_exist()` / `load_previous_chat_histories()` は stateless path とし、`init_session()` 済みの `ConversationState` に依存しない。
  - `session_id` は `init_session()` 開始時点で確定済みの `get_session_id()` に紐づけ、ログ・履歴保存・security detector cleanup のキーにする。
  - cleanup は idempotent にする。`InjectionDetector.remove_session(session_id)` と stream-local buffer cleanup は複数回呼ばれても no-op として扱い、副作用が増えないことを cancellation test で固定する。
  - cleanup ownership:
    - `endpoints.py` の `finally`: request/session context の clear を担う。
    - `chat()` async generator の `finally`: `StreamGuard` / `InjectionDetector` / stream-local buffer cleanup の最終保証を担う。
    - `StreamGuard`: `InjectionDetector.remove_session(session_id)` による detector state cleanup を担う。すでに解放済みなら no-op にする。
  - WebSocket 切断時は `endpoints.py` の `finally` が request/session context を clear し、stream 途中の cancellation / disconnect では `chat()` async generator 自身の `try/finally` が `StreamGuard` と stream-local buffer cleanup を保証する。
  - `ConversationState` 全体は cleanup で逐一空にする前提ではなく、`Container.chat_svc` の factory lifecycle により WebSocket/session ごとに別 instance として破棄・分離されることを主防衛線にする。
  - rollback 時も legacy/refactored の state は DI 切替により instance 単位で分離され、同じプロセス内で state を共有しない。
- `HistoryMapper` を導入し、以下を移す。
  - `_convert_to_llm_messages`
  - `_parse_tool_output`
  - `_process_jobtype_search_result`
  - `load_previous_chat_histories` の整形ロジック
- `ChatPersistence` を導入し、以下を移す。
  - `_save_chat_history`
  - `_create_session`
  - `_save_user_or_developer_message`
  - `_save_llm_error`
  - `_save_chat_histories`
- `StreamEventProcessor` を導入し、以下を移す。
  - `LLMRunStream.stream_events()` の async iteration
  - `event.type == "raw_response_event"` / `event.type == "run_item_stream_event"` の分岐
  - `ResponseTextDeltaEvent` の item_id ordering / duplicate response filtering
  - `ToolCallItem`, `ToolCallOutputItem`, `HandoffOutputItem` など item 種別ごとの dispatch
  - stream から発生する frontend response の yield と turn outcome の集約
- `TurnPreparer` を導入し、以下を移す。
  - `_prepare_for_chat_turn`
  - `_get_position_detail`
  - `_get_message_role`
- `ToolEventHandler` を導入し、以下を移す。
  - `_handle_tool_call_item`
  - `_ensure_tool_execution_available`
  - `_append_stop_at_tool_outputs`
  - `_is_stop_at_tool`
  - `_generate_position_search_fake_result`
  - APPLICATION / REGISTRATION side effects（`chat_repository.update_session_status` / `user_repository.update_*`）は段階的移植では一旦 open gap として残してよいが、Phase 4 の exit criteria を満たすまでに tool output side effect として既存挙動（routing 境界）を実装し、parity で固定する。
- `StreamGuard` を導入し、以下を移す。
  - `InjectionDetector` の reset/process/finalize/remove
  - `_handle_security_detection`
- 各移植は 1 コンポーネントずつ行い、移植ごとに legacy/refactored 共通契約テストを実行する。

Validation:
- 各コンポーネントに focused unit test を追加する。
- affected private tests について test migration map を更新し、component test / contract invariant / legacy-only characterization のどれに移したかを示す。
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`
- refactored 設定で endpoint 契約テストが通る。
- legacy 設定でも既存テストが通る。

Exit criteria:
- Bootstrap task 後、main `chat()` path は legacy delegating adapter 経由ではなく refactored 実体で `pre_extraction_parity` subset を通している。
- `chat_service_refactored.ChatService.chat()` は高水準の orchestration だけになり、ストリーミングイベント処理、履歴保存、ツール処理が別モジュールに分離されている。
- `chat_service_refactored.ChatService` から legacy `chat_service.ChatService` への委譲が、Phase 4 の最後の extraction PR で削除されている。
- static check または unit test で、`chat_service_refactored.py` が legacy `services.chat_service.ChatService` を import / instantiate していないことを保証する。
- APPLICATION / REGISTRATION の side effect は、legacy の「POSITION_DETAIL page + CHATTING/APPLYING/REGISTERING は APPLYING へ集約する」ルーティング境界を保ったまま、tool output side effect として parity で固定する。これは未実装の open gap ではなく、final parity suite で保全する既存挙動である。

### Phase 4.5: e2e 互換性ギャップ解消（workflow path）

Goal: Phase 4 で独立実装化した refactored 実体が発火する workflow 系イベントについて、`e2e/` クライアント側の contract を先に追随させ、Phase 5 の最終 parity/e2e 実行が途中で落ちない土台を作る。

Actions:
- `e2e/src/aica_client/models.py` の enum/state を拡張する。
  - `ChatResponseType.WORKFLOW`
  - `ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED` / `WORKFLOW_CANCELLED`
  - `HeadlessState.pending_workflow`
- `e2e/src/aica_client/client/e2e_client.py` で workflow event の受信・検証・dispatch を追加する。
  - `_update_state_from_exchange()` で `WORKFLOW` を parse/store
  - `_handle_pending_actions()` で `pending_workflow` を優先処理
  - `_handle_workflow()` で workflow answers submit を送信
  - `_validate_ws_event_contract()` と history validation の許容型を更新
- workflow 発火シナリオを含む e2e run で crash が再現しないことを確認する。

Validation:
- `response_type: "workflow"` を含む stream response を e2e model が受理できる。
- workflow 発火シナリオで e2e が `workflow_answers_submitted` を送信し、run が継続する。
- workflow 非発火シナリオで既存挙動が退行しない。

Exit criteria:
- workflow response/request の enum 不整合による Pydantic validation error で e2e run が停止しない。
- `e2e_client` が workflow payload を contract として検証し、pending action として処理できる。
- Phase 5 parity/e2e 実行に進む前提として、workflow path の互換性ギャップが解消されている。

### Phase 5: 結合テストと behavioral invariants の完成

Goal: 「結合テスト計画」で定義した parity suite を完成させ、独立実装になった `chat_service_refactored.py` と legacy `chat_service.py` の外部挙動同等性を最終確認する。coverage は補助指標として扱い、単独の gate にしない。

Actions:
- `tests/integration/chat_service_contract/` の scenario fixture を「結合テスト計画」の最終 parity suite まで拡張する。
- Phase 4 で legacy 委譲を削除済みの refactored 実体に対して、legacy/refactored 同一 fixture を通す。
- named behavioral invariants が legacy/refactored の両方で通ることを確認する。
- `pytest-cov` で `services/chat_service.py` と `services/chat_service_refactored.py` の branch coverage を計測する。
- 現行 `chat_service.py` の未到達行を棚卸しし、到達不能・外部依存過大・例外防御などの理由をコメント付きで除外する。

Validation:
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q --cov=server/src/aica_agent/services/chat_service.py --cov-branch server/tests/`
- `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q --cov=server/src/aica_agent/services/chat_service_refactored.py --cov-branch server/tests/`
- legacy/refactored の契約テストが同一 fixture で通る。
- named behavioral invariants が legacy/refactored の両方で通る。

Exit criteria:
- 現行版とリファクタ版の外部公開インターフェース挙動が自動テストで比較されている。
- named behavioral invariants がテストで固定されている。
- coverage の未達箇所は、到達不能・外部依存過大・例外防御などの理由と残リスクが plan またはテストコメントに記録されている。

### Phase 6: 統合・リリース準備

Goal: Gate A のゴールが満たされた状態で、ミドルブランチから `develop` へ安全に統合できる状態にする。

Positioning:
- Phase 6 は新しい機能や大きなリファクタを実装するフェーズではない。
- 主要な実装は Phase 1〜5 で完了している前提とする。
- Phase 6 で発生しうる修正は、設定例、ログ出力、ドキュメント、テスト実行手順、rollback 手順など、統合・リリース準備に必要な小修正に限定する。

Actions:
- Gate A ミドルブランチ上で `legacy + responses`, `refactored + responses` の契約テストをすべて通す。
- `develop` へ統合する前に、リファクタ版を有効化する設定差分と rollback 設定を明文化する。
- `develop` への統合 PR では、リファクタ版の実装、切替設定、契約テスト、カバレッジ確認をまとめてレビュー対象にする。
- リリース後に refactored 実装で問題があれば、shared boundary の backward compatibility が rollback suite で保証されている前提で、`agent_runtime.service_variant: legacy` に戻す runtime rollback が成立する状態にする。

Validation:
- 起動時ログに `service_variant`, `agent_model`, `summary_model` を出す。
- chat turn のログに variant と backend を含める。
- token usage / tool call / security block / retry の既存ログが欠落しないことを確認する。
- ミドルブランチ上で全テスト、named behavioral invariants、coverage evidence が揃っている。

Exit criteria:
- `develop` へ統合する PR が、Gate A 完了後の単一リリース候補として成立している。
- legacy/refactored を設定で切り替えられる。
- Responses style の現行 runtime semantics が維持されている。
- refactored 実装から legacy 実装への runtime rollback 手順が config 変更のみで完了する。shared files の互換性は各 shared-file PR の rollback suite で事前に保証されていること。

## Gate A rollback test matrix

Gate A では shared files が変わるため、`service_variant: legacy` で新しい shared boundary が backward-compatible であることを各 task PR で確認する。

Rollback rule:
- `service_variant: legacy` は `ChatService` 実装を legacy に戻すための runtime rollback であり、shared files の変更自体を巻き戻すものではない。
- そのため、shared files を変更するすべての task PR は merge 前に Minimum rollback suite の該当 subset を通す。
- shared-file PR が legacy startup / endpoint response / config validation を壊す場合、その PR は Gate A ミドルブランチへ入れない。

| Shared change | Legacy rollback assertion |
| --- | --- |
| `endpoints.py` response import 変更 | REST / WebSocket response JSON shape が現行と一致する。 |
| `endpoints.py` `init_session()` model config 化 | default config で legacy `ChatService.init_session()` に `"openai/gpt-4.1"` が渡る。 |
| `containers.py` DI switch | `service_variant: legacy` で legacy `ChatService` が解決され、session ごとに別 instance になる。 |
| `config.yml` `agent_runtime` 追加 | default config で legacy 起動が成功し、`agent_runtime.agent_model` が `model_list.use_for: agent` に存在する。 |
| `llm_service.py` model resolution 変更 | legacy `clone_agents()` が現行と同じ model key で呼ばれる。 |
| `utils.chat_response` import 移動 | error / end / message / tool result response shape が変わらない。 |
| streaming runner boundary 追加 | legacy/refactored とも Responses style の event ordering, retry, stop-at-tool replay が contract harness で一致する。 |
| security cleanup 変更 | blocked session と stream cancellation で cleanup / block_session side effect が維持される。 |
| summary path | `summarize_position_detail_chat()` が chat runtime switching の影響を受けず、既存 summary model 設定を使う。 |

Minimum rollback suite:
- startup
- websocket init: new session / existing session
- REST history
- blocked session
- normal streaming message
- stop-at-tool replay
- retry final error
- position detail summary

Named rollback subsets:
- `rollback_endpoint_config`
  - startup
  - default config resolves `"openai/gpt-4.1"`
  - endpoint import decoupling
  - websocket init: new session / existing session
- `rollback_di`
  - startup
  - `service_variant: legacy` resolves legacy `ChatService`
  - WebSocket/session instance lifecycle
  - REST history stateless path
- `rollback_runner`
  - normal streaming message
  - stop-at-tool replay
  - retry final error
  - `continuation_state` continuity。Gate A では `previous_response_id` / `last_response_id` chain から map されること。
- `rollback_security`
  - blocked session
  - stream cancellation cleanup
  - security detection block_session side effect
- `rollback_summary`
  - position detail summary
  - summary model still comes from `model_list.use_for: summary`
  - summary path is not affected by chat runtime switching

Rollback subset commands:
- shared files を変更する task PR は、該当 subset の command を PR description と CI/local verification に必ず載せる。
- marker が未作成の段階では、その task PR で marker または同等の test file command を追加してから merge する。
- shared-file task PR が該当 command を持たない場合、その PR は Gate A ミドルブランチへ入れない。

```bash
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config server/tests/
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di server/tests/
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner server/tests/
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security server/tests/
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary server/tests/
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_bootstrap server/tests/
PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity server/tests/
```

## Gate A phase/feature/task split candidates

Gate A は単一 release candidate だが、計画 FIX 後に `server/plan/phases/phase-x/features/feature-y/task-z` へ分割する。下記はそのときの phase/feature/task 分割候補であり、この時点では PR 数や PR 番号を固定しない。各 task は原則として 1 PR 単位とする。

1. Config + endpoint boundary task candidate
   - `agent_runtime.service_variant` と `agent_runtime.agent_model` を追加する。
   - `services/chat/agent_runtime_config.py` に読み取り helper と default model resolver を追加する。
   - `services/chat/config_validator.py` と `application.py` startup hook の config validation を追加する。
   - `service_variant: legacy` のみ valid とし、`refactored` は clear startup/config validation error にする。
   - response model import を `utils.chat_response` へ移す。
   - `ChatServiceProtocol` を追加する。
   - `init_session()` の model ハードコードを config 解決へ移す。
   - Phase 1 最小 contract harness を追加する。
  - Required command: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_endpoint_config`
2. DI lifecycle task candidate
   - `service_variant: legacy` の既存 provider 解決と instance lifecycle test を追加する。
   - この task では `refactored` variant はまだ有効化しない。`chat_service_refactored.ChatService` が存在しないため、service variant switch は Delegating adapter / service variant switch task で追加する。
  - Required command: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di`
3. Delegating adapter / service variant switch task candidate
   - `chat_service_refactored.ChatService` を一時 delegating adapter として追加する。
   - `service_variant: refactored` の service variant switch を追加する。
   - config validation で `service_variant: refactored` を valid にする。
   - legacy/refactored contract harness を同じ fixture で通す。この時点の refactored は delegating adapter なので、wiring / endpoint boundary / response shape の挙動維持テストとして扱う。
  - Required command: `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di`
4. Runner contract task candidate
   - legacy `chat_service.ChatService` に minimal runner seam を追加する。
   - SDK-shaped legacy event fixtures, Responses adapter normalization tests, `LLMRunner` Protocol を追加する。
   - streaming / retry / stop-at-tool replay の legacy characterization tests を追加する。
   - pre-extraction parity gate の最小 invariant を追加する。
   - Required commands:
    - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner`
    - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`
5. Refactored bootstrap task candidate
   - main `chat()` path では legacy `services.chat_service.ChatService` を import / instantiate / delegate しない状態にし、`LLMRunner` / `LLMRunStream` boundary を使う薄い real refactored shell を作る。
   - 大きな責務分割はまだ行わず、refactored 実体で `pre_extraction_parity` subset を通す。
   - static check または unit test で legacy `ChatService` への import / instantiate / delegate が main `chat()` path にないことを保証する。
   - affected private tests の test migration map を更新する。
   - Required commands:
    - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`
    - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner`
6. State/history extraction task candidate
   - `ConversationState` と `HistoryMapper` を移植する。
   - affected private tests の test migration map を更新する。
   - Required commands:
    - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`
    - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_di`
7. Persistence/turn preparation task candidate
   - `ChatPersistence` と `TurnPreparer` を移植する。
   - DB side effects と position detail initialization invariants を通す。
   - affected private tests の test migration map を更新する。
   - Required commands:
    - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`
    - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_runner`
8. Tool/stream guard/workflow task candidate
   - `StreamEventProcessor`, `ToolEventHandler`, `StreamGuard`, `WorkflowChatHandler` を移植する。
   - security cleanup, tool result, workflow side effects の invariants を通す。
   - affected private tests の test migration map を更新する。
   - Required commands:
    - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`
    - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_security`
9. E2E compatibility update (between Phase 4 and 5) task candidate
   - `e2e` headless client を `WORKFLOW` response / workflow submit-cancel request に対応させる。
   - workflow payload validation と pending workflow dispatch を追加し、workflow 発火シナリオの e2e crash を除去する。
   - Verification: static lint check（`ruff check`）と、workflow 発火シナリオおよび非発火シナリオでの e2e 実行確認（unit test ではなく実行確認）。
10. Final parity task candidate
   - Phase 4 の最後の extraction PR で削除済みの delegating adapter 依存が再導入されていないことを確認する。
   - static check または unit test で `chat_service_refactored.py` が legacy `services.chat_service.ChatService` を import / instantiate していないことを再確認する。
   - named behavioral invariants と coverage evidence を揃える。
   - Required commands:
    - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m pre_extraction_parity`
    - `PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_summary`
   - rollback 手順と release notes を更新する。

## Gate A 作業順序

以下は Gate A ミドルブランチ上での作業順序であり、上記 phase/feature/task split candidates と対応する。実際の phase/feature/task ファイル分割と PR 数は、計画 FIX 後に決める。

1. `agent_runtime` config、config validation、default model resolver を追加する。
2. response model import と `init_session()` model ハードコードを endpoint から切り離し、`ChatServiceProtocol` と Phase 1 最小 contract harness を追加する。
3. `chat_service_refactored.py` の一時 delegating adapter と DI 切替を追加する。
4. legacy minimal runner seam、SDK-shaped legacy event fixtures、Responses adapter normalization tests、`LLMRunner` を追加する。
5. Pre-extraction parity gate を通し、Responses style の高リスク invariant と test migration map を抽出前に固定する。
6. Refactored bootstrap task で main `chat()` path の legacy 委譲を外し、薄い real refactored shell で `pre_extraction_parity` を通す。
7. `ConversationState` と `HistoryMapper` を移植する。
8. `ChatPersistence` と `TurnPreparer` を移植する。
9. `StreamEventProcessor`, `ToolEventHandler`, `StreamGuard` を移植する。
10. e2e workflow compatibility task を実施し、Phase 4 実装で発火する workflow path でも e2e が継続実行できる状態にする。
11. delegating adapter 依存の static check と named behavioral invariants、coverage evidence を揃える。
12. Gate A ミドルブランチ上で全ゴール完了を確認し、`develop` への統合 PR を準備する。

## Gate B 後続計画

Goal: Gate A の structural refactor が `develop` に統合された後、Completions style runtime switching を別 release candidate として追加する。

Entry criteria:
- Gate A が `develop` に統合済みで、legacy/refactored rollback が config-only で成立している。
- Gate A の contract harness、SDK-shaped legacy event fixtures、Responses adapter normalization tests が利用可能である。

Prototype:
- Completions style spike を作り、次の semantics が Responses style と同等に表現できるか検証する。
  - streaming event ordering
  - handoff state
  - retry input
  - stop_at_tool / tool output replay
  - local conversation retention
  - rollback from refactored completions to legacy responses
- spike では production path へ組み込まず、runner adapter と fake fixtures の feasibility を確認する。

Actions:
- `agent_runtime.api_style` を追加する。
- `AgentModelFactory` を追加し、Responses style / Completions style の model 解決を分離する。
- `CompletionsAgentRunner` を追加する。
- Completions style は `LLMRunStream.continuation_state`, `agent_state`, `tool_replay_items`, `usage` に adapter-local state を map する。`previous_response_id` / `last_response_id` / `to_input_list()` を Gate B の core contract 名として追加しない。
- Gate A の contract harness を `refactored + completions` にも適用する。ただし parity 対象は frontend/API から観測できる response shape, stream chunk ordering, tool result, error/end behavior に限定する。
- `previous_response_id`, adapter-local continuation token, local conversation retention などの内部 continuation invariants は runner-internal tests で別に固定する。

Exit criteria:
- `refactored + responses` と `refactored + completions` が observable frontend/API contract harness を通る。
- Completions style の local conversation retention / tool output replay / handoff state / retry input がテストで固定されている。
- Gate B rollback は `agent_runtime.api_style: responses` または `agent_runtime.service_variant: legacy` の config 変更で成立する。

## Gate B 運用準備

Gate B の canonical matrix / rollout / rollback / observability / threshold は [architecture.md](architecture.md#canonicality) を正とする。

### Gate B verification commands

既存 rollback subset に加えて、Gate B 専用 marker を追加する。ここでは venv 経由 + `PYTHONPATH=server/src/aica_agent` を Gate B の標準実行形式として統一する。

```bash
OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_runner_internal server/tests/
OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m completions_contract server/tests/
OPENAI_API_KEY=sk-test PYTHONPATH=server/src/aica_agent .venv-server/bin/python -m pytest -q -m rollback_api_style server/tests/
```

Required checks:
- `completions_runner_internal`
  - `continuation_state` round-trip
  - `tool_replay_items` の completions 形式
  - handoff/retry state の保持
- `completions_contract`
  - `refactored + responses` と `refactored + completions` の observable parity
- `rollback_api_style`
  - `api_style: completions -> responses`
  - `service_variant: refactored -> legacy`

### Gate B release candidate DoD

- `agent_runtime.api_style` が導入され、default は `responses`。
- `legacy + completions` が startup/config validation で拒否される。
- `refactored + completions` で observable parity suite が pass。
- completions runner internal invariants が pass。
- rollback (`api_style` または `service_variant`) が config-only で成立し、smoke で確認済み。
- summary path が runtime switching の影響を受けないことを確認済み。
- provider onboarding checklist（credentials, IAM, region/network）が verification に記録済み。

## 主なリスク

- Responses style の `previous_response_id` と Completions style の会話継続方式が異なる。
  - 対策: Gate A には含めない。Gate B の prototype で `LLMRunStream` fake contract を拡張し、local conversation retention / tool output replay / handoff state / retry input を runner adapter 側の責務としてテストする。
- Agent SDK の model 指定方法が `api_style` ごとに異なる。
  - 対策: `AgentModelFactory` を作り、`LLMService` 以外へ SDK model 構築詳細を漏らさない。
- `endpoints.py` が `services.chat_service` の具象 import やモデル名ハードコードを持ち続ける。
  - 対策: Phase 1 の exit criteria に concrete import 排除、response model import 移動、config 由来 model 解決を含める。
- shared files の変更により config-only rollback が壊れる。
  - 対策: Gate A の各 phase で legacy 設定の contract harness を必ず通し、`service_variant: legacy` で shared boundary が backward-compatible であることを確認する。
- Phase 2 の delegating adapter が長く残り、現行版と独立したリファクタ版実装にならない。
  - 対策: Phase 2 だけ一時許可し、Phase 4 の最後の extraction PR で legacy への委譲削除を必須にする。Final parity PR では static check / unit test で再導入されていないことを確認する。
- `chat_service.py` の private method に既存 unit test が強く依存している。
  - 対策: private test は legacy 用として残し、refactored は公開契約 + 分割コンポーネント単位で検証する。
- coverage 目標が brittle tests を誘発する。
  - 対策: named behavioral invariants を Gate A の主 gate とし、coverage は補助 evidence として扱う。到達不能行は明示的に除外理由を書く。
- 並行存在中に import 経路が混ざる。
  - 対策: `endpoints.py` は Protocol のみを参照し、具体実装選択は `containers.py` に閉じ込める。

## Gate A Done

- `chat_service.py` と `chat_service_refactored.py` が同時に存在し、設定で切り替えられる。
- `endpoints.py` から見える公開メソッドと JSON / stream response の挙動が legacy/refactored 共通の自動結合テストで保証されている。
- Gate A では OpenAI Agent SDK + Responses style のまま structural refactor が完了している。
- リファクタ版の `ChatService` / `chat()` は短い orchestration 層になっており、turn preparation, LLM execution, stream guard, tool handling, persistence, history mapping, workflow handling は責務ごとの内部コンポーネントへ分割されている。
- Gate A ミドルブランチから `develop` へ、structural refactor 完了後の単一リリース候補として統合できる。
- shared boundary の rollback suite が通っており、refactored 実装の問題は `agent_runtime.service_variant: legacy` への config 変更で runtime rollback できる。

## Overall Program Done

- Gate A が `develop` に統合済みで、legacy/refactored structural switch と rollback が成立している。
- Gate B で OpenAI Agent SDK を使ったまま Responses style / Completions style を設定で切り替えられる。
- Gate B でチャットが Completions style を利用する場合、モデルを設定だけで切り替えられる。
- Gate B の observable frontend/API parity suite が `refactored + responses` と `refactored + completions` の両方で通る。
