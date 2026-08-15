#!/usr/bin/env python3
"""`userPromptSubmitted` Copilot CLI hook: watch for A-0's continuous
question/answer log (`brainstorm-qa-log.md`, see issue-brainstorm-phase's
SKILL.md) going stale during an active Brainstorm/Design dialogue, and raise
an OS notification if so.

This is a WATCHDOG, not a replacement for A-0's logging discipline: command
hooks for `userPromptSubmitted` cannot inject anything back into the
conversation or block/modify the prompt (`modifiedPrompt` is honored only
for SDK-based hooks, not `type: "command"` shell hooks per GitHub's own
hooks-reference docs) -- this script can only alert a human, out-of-band,
that the log seems to have stopped growing.

"Is a brainstorm dialogue currently active" is checked against real repo
state every time (current branch + workflow-state.json), never inferred
from the log file's mere presence -- that file legitimately survives on
disk long after the phase has moved on, and would otherwise cause false
positives forever after a real brainstorm session ends. See
plugin/source/harness/copilot/skills/issue-cycle-init/SKILL.md's bootstrap
step for how `.github/hooks/brainstorm_log_watchdog.py` (a copy of this
file) and `brainstorm-log-watchdog.json` are installed into a target repo.

Never raises: a watchdog must not break the session it is watching over.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable

STALE_THRESHOLD = 3
BASE_BRANCH_RE = re.compile(r"^feature/(\d+)/base$")


def read_stdin_payload() -> dict:
    if sys.stdin.isatty():
        return {}
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def current_branch(cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    branch = result.stdout.strip()
    return branch or None


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def resolve_tmp_dir(cwd: Path) -> str:
    config = _read_json(cwd / ".issue-workflow.json")
    if isinstance(config, dict):
        value = config.get("tmp_dir")
        if isinstance(value, str) and value:
            return value
    return "tmp"


def active_brainstorm_feature_slug(cwd: Path) -> str | None:
    """Return the active issue's `feature_slug` if a brainstorm dialogue is
    genuinely in progress right now (current branch matches
    `feature/<n>/base` AND that issue's workflow-state.json says
    `phase: "brainstorm"`/`status: "in_progress"`), else None."""
    branch = current_branch(cwd)
    if not branch:
        return None
    match = BASE_BRANCH_RE.match(branch)
    if not match:
        return None
    issue_no = match.group(1)
    state = _read_json(cwd / "spec" / issue_no / "workflow-state.json")
    if not isinstance(state, dict):
        return None
    if state.get("phase") != "brainstorm" or state.get("status") != "in_progress":
        return None
    feature_slug = state.get("feature_slug")
    return feature_slug if isinstance(feature_slug, str) and feature_slug else None


def notify_macos(message: str) -> None:
    if sys.platform != "darwin":
        return
    script = f'display notification "{message}" with title "GitHub Copilot"'
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
    except Exception:
        pass


def check(cwd: Path, notify: Callable[[str], None] = notify_macos) -> dict:
    feature_slug = active_brainstorm_feature_slug(cwd)
    if feature_slug is None:
        return {"active": False}

    tmp_dir = cwd / resolve_tmp_dir(cwd) / feature_slug
    log_file = tmp_dir / "brainstorm-qa-log.md"
    watchdog_state_file = tmp_dir / "brainstorm-log-watchdog-state.json"

    if not log_file.is_file():
        return {"active": True, "log_exists": False}

    current_mtime = log_file.stat().st_mtime
    watchdog_state = _read_json(watchdog_state_file) or {}
    last_seen_mtime = watchdog_state.get("last_seen_mtime")
    stale_count = watchdog_state.get("stale_count", 0)
    if not isinstance(stale_count, int):
        stale_count = 0

    if last_seen_mtime == current_mtime:
        stale_count += 1
    else:
        stale_count = 0

    notified = False
    if stale_count >= STALE_THRESHOLD:
        notify(
            "brainstorm-qa-log.md が更新されていません。"
            "継続ログの追記が止まっていないか確認してください。"
        )
        notified = True
        stale_count = 0

    watchdog_state_file.parent.mkdir(parents=True, exist_ok=True)
    watchdog_state_file.write_text(
        json.dumps({"last_seen_mtime": current_mtime, "stale_count": stale_count}),
        encoding="utf-8",
    )
    return {"active": True, "log_exists": True, "stale_count": stale_count, "notified": notified}


def main() -> int:
    payload = read_stdin_payload()
    cwd_value = payload.get("cwd") if isinstance(payload.get("cwd"), str) else None
    cwd = Path(cwd_value) if cwd_value else Path.cwd()
    try:
        result = check(cwd)
    except Exception as exc:  # noqa: BLE001 -- a watchdog must never crash the session
        result = {"active": False, "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
