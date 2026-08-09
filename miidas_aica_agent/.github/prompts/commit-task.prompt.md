---
agent: agent
---

Commit, push, and open a PR for the completed task. The task.md path is: $ARGUMENTS

If `task.md` cannot be located at the given path, ask the user to provide the path before proceeding.

## Steps

### 1. Derive task identity from the task.md path

Parse the path to extract:
- `phase` — e.g. `phase-4-refactored-extraction`
- `feature` — e.g. `feature-1-refactored-bootstrap`
- `task` — e.g. `task-2-bootstrap-behavioral-proof`

### 2. Stage and commit

First run `git status --short`.

If unrelated user changes exist, do not include them in the commit. If task changes cannot be separated safely from unrelated changes, stop and ask the user how to proceed.

```
git add <task files>
git commit -m "phase {x} / feature {y} / task {z}: done"
```

If `git add <task files>` results in no staged changes, inform the user that the working tree is clean and ask how to proceed.

### 3. Push

Push to the current branch.

```bash
git push --set-upstream origin <current-branch>
```

Use `--set-upstream` so the local branch tracks the remote branch and later plain `git push` / `git pull` works for the user.

### 4. Determine the target branch for the PR

Run `git log --oneline -10`, `git log --oneline --merges`, and `git branch -r` to identify the feature branch this task branch should PR into (typically the parent feature branch, e.g. `feature/NNNNN_*`). If still ambiguous, check the branch naming convention to identify the parent feature branch. If still unclear, ask the user.

### 5. Create PR using GitHub MCP

Use the `mcp_github_create_pull_request` tool to open the PR. Fill in the body using `.github/PULL_REQUEST_TEMPLATE/refactoring-task.md` as the template. Populate every section you can from:
- `task.md` (phase / feature / task path, task type)
- `handoff.md` (changed files, design decisions → 概要)
- `verification.md` (required commands and results)
- `git diff HEAD~1` or the list of changed files (主な変更ファイル)
- The rollback marker results you ran during implementation

Before creating the PR, ask the user for the Redmine ticket URL if they have not already provided it.

- If the user provides a Redmine ticket URL, write that direct link in the チケット section.
- If the user explicitly says there is no ticket or does not want to provide one, leave `Closes #` in the template.
- Do not silently skip this question.

If the user provided a Redmine ticket, write it as a direct link in the チケット section. Do not convert it to `Closes #...`.

PR title format: `【ChatService/LLMServiceリファクタリング】【Phase {x}】【Feature {y}】タスク{z}`

`{x}`, `{y}`, `{z}` は数値のみを使用すること（例: `x=4`, `y=5`, `z=1`）。

After creating the PR, add `copilot-pull-request-reviewer` as a reviewer.
