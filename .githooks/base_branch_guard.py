#!/usr/bin/env python3
"""Shared git hook logic: on a `feature/<id>/base` branch, only let through
`spec/<id>/...` paths that match a known-good allowlist.

Why an allowlist instead of denying `*.draft.md`: a live run showed an
external skill (`superpowers:brainstorming`) commit *and push* a
`design.draft.md` straight to `feature/<id>/base`, bypassing the WIP branch
-> clean branch -> human-reviewed PR flow entirely. Blocking that one
filename pattern only guards against the specific mistake already seen --
any other unexpected file shape under `spec/<id>/` (a stray WIP snapshot
left on base, a renamed draft, a new artifact nobody taught this guard
about yet) would sail through untouched. An allowlist inverts that: only
paths this harness is *known* to write directly to base are permitted,
so any future deviation is rejected by default rather than by exception.

The allowlist is scoped to `spec/` only. Everything outside `spec/` (real
product code, docs, config) is untouched by this check -- release-phase
merges legitimately bring arbitrary files onto base, and this guard has no
opinion about those. Only the harness's own bookkeeping namespace is locked
down.

Prompt-level instructions to an external skill ("don't commit") are not
reliable here: the invocation happened mid-dialogue, and a context
compaction event (see `session.compaction_start`/`session.compaction_complete`
in the live Copilot session log) summarized that instruction away before the
skill actually wrote and committed the file. No amount of re-wording a
prompt survives a compaction event we don't control, so this check is
enforced by git hooks instead -- a mechanism that doesn't depend on any
model "remembering" anything.

Installed via `.githooks/` + `git config core.hooksPath .githooks`
(`issue-cycle-init`'s bootstrap copies the hook files once per repo;
`issue-cycle`'s common pre-checks re-assert the `core.hooksPath` config on
every invocation, since that setting is per-clone, not shared by the repo
files themselves). This is plain git hook support built into git itself --
no separate tool (e.g. the `pre-commit` pip framework) needs to be
installed.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

BASE_BRANCH_PATTERN = re.compile(r"^feature/[^/]+/base$")
ZERO_SHA = "0" * 40

# Every path a harness phase skill is documented to commit directly onto
# `feature/<id>/base` (see issue-cycle/issue-*-phase SKILL.md's "base ブラン
# チへの安全な書き込み手順" sections and issue_state.py's run_write). Anything
# under `spec/` that matches none of these is rejected.
SPEC_ALLOWLIST_PATTERNS = [
    re.compile(r"^spec/[^/]+/issue\.md$"),
    re.compile(r"^spec/[^/]+/workflow-state\.json$"),
    re.compile(r"^spec/[^/]+/state/.+$"),
    re.compile(r"^spec/[^/]+/design/.+$"),
    re.compile(
        r"^spec/[^/]+/docs/exec-plans/pending/[^/]+/(plan|tasks|design)\.md$"
    ),
    re.compile(
        r"^spec/[^/]+/docs/exec-plans/pending/[^/]+/(plan|tasks|design)\.approval\.json$"
    ),
]


class CliError(Exception):
    """A user-facing error; reported as {"error": ...} with exit code 2.

    Distinct from a *blocked* commit/push (exit code 1) -- this is for
    "the check itself could not run", e.g. a broken git invocation.
    """


class ErrorCapturingArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliError(message)


def is_base_branch(branch: str) -> bool:
    return bool(BASE_BRANCH_PATTERN.match(branch))


def is_allowed_spec_path(path: str) -> bool:
    return any(pattern.match(path) for pattern in SPEC_ALLOWLIST_PATTERNS)


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, text=True
    )


def find_disallowed_spec_files_in_tree(repo_root: Path, tree_ish: str) -> list[str]:
    result = _run_git(repo_root, "ls-tree", "-r", "--name-only", tree_ish)
    if result.returncode != 0:
        raise CliError(f"git ls-tree {tree_ish} failed: {result.stderr.strip()}")
    return [
        line
        for line in result.stdout.splitlines()
        if line.startswith("spec/") and not is_allowed_spec_path(line)
    ]


def current_branch(repo_root: Path) -> str | None:
    result = _run_git(repo_root, "symbolic-ref", "--short", "-q", "HEAD")
    if result.returncode != 0:
        return None
    branch = result.stdout.strip()
    return branch or None


def check_commit(repo_root: Path) -> dict:
    """Inspect the tree that `git commit` is about to create (the current
    index, via `git write-tree`) -- catches the problem before the commit
    object even exists, regardless of which tool/process ran `git commit`."""
    branch = current_branch(repo_root)
    if branch is None or not is_base_branch(branch):
        return {"blocked": False, "branch": branch}

    tree_result = _run_git(repo_root, "write-tree")
    if tree_result.returncode != 0:
        raise CliError(f"git write-tree failed: {tree_result.stderr.strip()}")
    tree = tree_result.stdout.strip()

    disallowed = find_disallowed_spec_files_in_tree(repo_root, tree)
    if disallowed:
        return {"blocked": True, "branch": branch, "files": disallowed}
    return {"blocked": False, "branch": branch}


def check_push_ref(repo_root: Path, local_ref: str, local_sha: str) -> dict:
    """Inspect one `<local-ref> <local-sha>` pair from pre-push's stdin --
    a backstop for anything that reached a local commit without going
    through `check_commit` (e.g. `git commit --no-verify`, a cherry-pick, a
    commit made before the hooks were configured on this clone)."""
    branch_match = re.match(r"^refs/heads/(.+)$", local_ref)
    if not branch_match:
        return {"blocked": False, "reason": "not a branch ref"}
    branch = branch_match.group(1)
    if not is_base_branch(branch):
        return {"blocked": False, "branch": branch}
    if local_sha == ZERO_SHA:
        return {"blocked": False, "branch": branch, "reason": "branch deletion"}

    disallowed = find_disallowed_spec_files_in_tree(repo_root, local_sha)
    if disallowed:
        return {"blocked": True, "branch": branch, "files": disallowed}
    return {"blocked": False, "branch": branch}


def check_push_stdin(repo_root: Path, stdin_text: str) -> list[dict]:
    """pre-push's stdin contract: one line per ref being pushed, each
    `<local-ref> <local-sha> <remote-ref> <remote-sha>`."""
    results = []
    for line in stdin_text.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 4:
            raise CliError(f"malformed pre-push input line: {line!r}")
        local_ref, local_sha, _remote_ref, _remote_sha = parts
        results.append(check_push_ref(repo_root, local_ref, local_sha))
    return results


def _read_stdin() -> str:
    return sys.stdin.read()


def build_parser() -> argparse.ArgumentParser:
    parser = ErrorCapturingArgumentParser(
        description="Allowlist spec/<id>/... paths on feature/<id>/base branches."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root (default: cwd)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "check-commit",
        help="pre-commit: inspect the tree the current index would produce.",
    )
    subparsers.add_parser(
        "check-push",
        help="pre-push: inspect each ref passed on stdin (git's pre-push contract).",
    )
    return parser


def main() -> int:
    try:
        parser = build_parser()
        args = parser.parse_args()
        repo_root = Path(args.repo_root)
        if args.command == "check-commit":
            result = check_commit(repo_root)
            results = [result]
        elif args.command == "check-push":
            results = check_push_stdin(repo_root, _read_stdin())
        else:
            raise CliError(f"unknown command: {args.command}")
    except CliError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2

    blocked = [r for r in results if r.get("blocked")]
    for result in results:
        print(json.dumps(result, ensure_ascii=False))
    if blocked:
        print(
            "\nBLOCKED: these spec/<id>/... paths are not on this harness's "
            "allowlist for a feature/<id>/base branch:\n  "
            + "\n  ".join(f for r in blocked for f in r.get("files", []))
            + "\n\nOnly issue.md, workflow-state.json, state/**, design/**, and "
            "the promoted plan.md/tasks.md/design.md (+ *.approval.json) are "
            "permitted directly on base. Draft artifacts (*.draft.md), grill "
            "iteration files, and spec/<id>/wip/** belong on a wip/<phase> "
            "branch, reviewed via a feature/<id>/<phase> PR, and only reach "
            "base through promote_artifact.py's rename. If an external skill "
            "(e.g. superpowers:brainstorming) wrote and committed this itself, "
            "undo that commit and redo it through the phase skill's "
            "WIP-branch -> PR flow instead.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
