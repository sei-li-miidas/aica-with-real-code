---
agent: agent
description: Fetch PR review comments and implement fixes, one commit per discussion thread
---


## PR Selection


First, determine the actual current branch name (e.g., using `git rev-parse --abbrev-ref HEAD`).
Then, attempt to find an open pull request in `MIIDAS-Company/miidas_aica_agent` where the source branch ("from" branch) matches the current branch name.

- If such a PR is found, use its PR number for all subsequent steps.
- If no such PR is found, prompt the user for a PR number:
  PR number: ${input:prNumber:PR number to respond to (e.g. 237)}

Let `PR_NUMBER` be the PR number determined above (either found automatically or provided by user input).
Use `PR_NUMBER` for all subsequent workflow steps.

## Workflow

### Step 1 — Fetch review comments

Use the GitHub MCP tools to fetch all review comments and reviews on PR #${PR_NUMBER} in `MIIDAS-Company/miidas_aica_agent`.

Collect:
- All inline review comments (with their `id`, file path, line, body, and whether they are resolved)
- All PR-level review bodies
- For each comment thread, note the discussion/comment ID (used for commit messages)

Filter out:
- Already resolved threads
- Comments that are praise only (no actionable request)

### Step 2 — Categorize comments

For each unresolved comment, categorize it as:
- **code change**: requires editing one or more files
- **reply only**: a question or clarification that doesn't require a code change

Group **code change** comments by logical change (a single comment thread = one commit).
For **reply only** comments, compose a reply that directly answers the question or acknowledges the point.

### Step 3 — Per-discussion approval loop

For **each** comment thread (both code change and reply only), repeat the following before doing anything:

**3a. Analyze and present**

Present a summary to the user:
- The comment body (quoted)
- Your assessment: is this a code change or a reply only?
- What you plan to do:
  - For code change: which file(s) to edit, what change, and why
  - For reply only: the reply you intend to post

Then ask the user: **"Go, or do you want to change the approach?"**

**3b. Wait for approval**

Do not proceed until the user explicitly says "go" (or equivalent). If the user suggests a different approach, update your plan and present it again before asking again.


**3c. Execute**

Once the user approves:

- For **code change**:
  1. Implement the fix.
  2. Before committing, always run the tests and make sure all tests pass.
  3. If tests fail, attempt to fix the issue. If you cannot resolve it, inform the user with the failure details and ask how to proceed (skip this comment, retry, or abort).
  4. If all tests pass, present the exact commit message and a short summary of changes, then ask the user for approval to commit.
  5. Do not commit until the user explicitly approves.
  6. After approval, commit with the message `#discussion_r<comment_id>`.
  7. Post a reply summarizing what was changed and why, including the commit hash as a clickable link (e.g., [hash](https://github.com/MIIDAS-Company/miidas_aica_agent/commit/<hash>)).
     ※This prompt file can be written in English, but replies to GitHub discussions must always be in Japanese（ディスカッションへの返信は必ず日本語で記載してください）.

- For **reply only**:
  1. Post the reply using `mcp_github_add_reply_to_pull_request_comment`.

Proceed to the next discussion thread only after the current one is fully done.

### Step 4 — Push

After all commits are made, push the current branch:
```
git push origin HEAD
```

### Step 5 — Summary

Report:
- List of commits made (discussion ID → what was changed)
- List of replies posted (discussion ID → reply content)
