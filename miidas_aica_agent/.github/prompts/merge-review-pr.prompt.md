---
agent: agent
description: Merge a branch into current, resolve conflicts, run review/fix loop, then create a PR against that branch
---

Merge from branch: ${input:mergeFromBranch:Branch to merge into current branch (e.g. feature/77996_chat_service_refactoring)}
Redmine ticket URL: ${input:redmineTicketUrl:Redmine ticket URL (e.g. https://redmine.miidas.dev/issues/12345)}

## Workflow

Perform the following steps in order. Do not skip any step.

### Step 1 — Merge and resolve conflicts

1. Run `git fetch origin ${input:mergeFromBranch}`.
2. Run `git merge origin/${input:mergeFromBranch} --no-edit`.
3. If `git fetch` or `git merge` fails with an error other than conflicts, stop and report the error to the user without proceeding.
4. If conflicts exist:
   - Read all conflicting files.
   - Understand the intent of both sides before resolving.
   - Resolve each conflict semantically (not just accepting one side). Prefer keeping both sides when they are non-overlapping (e.g. different tests). Prefer the side with docstrings when the only difference is documentation.
   - Verify no conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) remain.
   - Stage resolved files and complete the merge commit.
5. If no conflicts, the merge completes automatically.

### Step 2 — Review

Invoke the `code-reviewer` subagent to review the full diff introduced by this merge (`git diff origin/${input:mergeFromBranch}..HEAD`). Provide the agent with:
- All changed files and their diffs.
- The conflict resolution decisions made in Step 1.
- Context derived from `${input:mergeFromBranch}` and the changed files. If this is a ChatService refactoring branch (Gate A), focus on Protocol conformance, rollback subset integrity, `service_variant: legacy` backward compatibility, and test coverage of new paths. Otherwise, review using the relevant project/domain concerns from the diff without applying Gate A-specific criteria.

### Step 3 — Fix

For each issue the reviewer reports:
- Fix **critical** and **important** issues immediately.
- Fix **minor** issues (e.g. missing docstrings, style) immediately.
- Commit all fixes in a single commit with a descriptive message.

### Step 4 — Re-review

Re-invoke the `code-reviewer` subagent on the fixed state. Repeat Steps 3–4 up to 3 times. If the reviewer has not returned **LGTM** after 3 iterations, stop and report the remaining issues to the user.

### Step 5 — Create PR

Determine the PR level from the current branch name:
- `*_phase_x_feature_y_task_z` → **task PR** (task → feature): use `.github/PULL_REQUEST_TEMPLATE/refactoring-task.md`
- `*_phase_x_feature_y` → **feature PR** (feature → phase): use `.github/PULL_REQUEST_TEMPLATE/refactoring-feature.md`
- `*_phase_x` → **phase PR** (phase → main refactoring branch): use `.github/PULL_REQUEST_TEMPLATE/refactoring-phase.md`

If the current branch name does not match any of the three patterns, ask the user to specify the PR level and template.

Use the PR level selected above and follow only the corresponding subsection below.

#### Step 5A — Task PR

Determine PR title:
- `【ChatService/LLMServiceリファクタリング】【Phase x】【Feature y】タスクz`

Fill in template sections from the actual diff and plan documents:
- タスク/フィーチャー/フェーズ参照: find the matching entry in `server/plan/phases/`.
- 概要: summarize what was implemented.
- チケット: use `${input:redmineTicketUrl}`.
- 主な変更ファイル: table of changed files with description of each change.
- タスク種別: check all that apply.
- Shared boundary チェック: list changed shared files and their rollback subsets.
- Rollback subset 結果: mark applicable ones pass/N/A.
- Test migration map (extraction only): N/A otherwise.
- Static check: check applicable items based on phase.
- plan ドキュメント更新: verify the appropriate docs were updated.

#### Step 5B — Feature PR

Determine PR title:
- `【ChatService/LLMServiceリファクタリング】【Phase x】Feature y`

Fill in template sections from the actual diff and plan documents:
- タスク/フィーチャー/フェーズ参照: find the matching entry in `server/plan/phases/`.
- 概要: summarize what was implemented.
- チケット: use `${input:redmineTicketUrl}`.
- 含まれるタスク PR: look up merged PRs from git log.
- Shared boundary チェック: aggregate changed shared files and rollback subsets across included PRs.
- 終了条件: copy from the README and check each item.
- Rollback subset 結果: mark applicable ones pass/N/A.
- plan ドキュメント更新: verify the appropriate docs were updated.

#### Step 5C — Phase PR

Determine PR title:
- `【ChatService/LLMServiceリファクタリング】Phase x`

Fill in template sections from the actual diff and plan documents:
- タスク/フィーチャー/フェーズ参照: find the matching entry in `server/plan/phases/`.
- 概要: summarize what was implemented.
- チケット: use `${input:redmineTicketUrl}`.
- 含まれるフィーチャー PR: look up merged PRs from git log.
- Shared boundary チェック: aggregate changed shared files and rollback subsets across included PRs.
- 終了条件: copy from the README and check each item.
- Rollback subset 結果: run the full suite and record results.
- plan ドキュメント更新: verify the appropriate docs were updated.

Create the PR:
- `head` = current branch
- `base` = `${input:mergeFromBranch}`
- owner = `MIIDAS-Company`
- repo = `miidas_aica_agent`

Add Copilot as a reviewer.
