---
agent: agent
---

Implement the task at: $ARGUMENTS

## Setup

Parse the task.md path from `$ARGUMENTS` to extract:
- `phase` — e.g. `phase-4-refactored-extraction`
- `feature` — e.g. `feature-1-refactored-bootstrap`
- `task` — e.g. `task-1-conversation-state`
- `taskDir` — the directory containing the task.md (e.g. `server/plan/phases/<phase>/features/<feature>/<task>/`)
- `featureDir` — parent feature directory
- `phaseDir` — parent phase directory

## Gather context

Read the following files before spawning the agent.

1. `server/plan/refactoring_plan.md`
2. `server/plan/architecture.md`
3. `<phaseDir>/README.md`
4. `<featureDir>/README.md`
5. `<taskDir>/task.md`
6. `server/plan/phases/status.md`
7. `server/plan/phases/gate_a_scenario_matrix.md`
8. Any `handoff.md` files in preceding task directories listed as dependencies in the feature README.

## Invoke the Implement Cycle agent

Spawn the `Implement Cycle` subagent with a self-contained prompt that includes:

- **Task identity**: phase, feature, task names and their directory paths.
- Context payload per policy above: full text when possible, otherwise heading-scoped extracts with explicit file-path references for omitted sections.
- **Scope rules** from the task.md (allowed/disallowed changes).
- **Completion criteria** from the task.md (verification.md requirements, rollback subsets, branch coverage target, handoff requirements).
- **Instruction**: implement the task, run all required verification commands, update `handoff.md`, `verification.md`, and `server/plan/phases/status.md` before finishing.
- **Python environment**: always use `.venv-server` under workspace root as the virtual environment (e.g. `.venv-server/bin/python`).

## Context budget and fallback policy

Default behavior:
- Pass full file contents for all gathered files whenever context budget allows.

If full-text injection risks context-limit failure, apply this fallback in order:

1. Keep full text for highest-priority files:
	- `<taskDir>/task.md`
	- `<featureDir>/README.md`
	- `<phaseDir>/README.md`
2. For large supporting docs (`server/plan/refactoring_plan.md`, `server/plan/architecture.md`, `server/plan/phases/gate_a_scenario_matrix.md`, `server/plan/phases/status.md`):
	- Extract and pass only required sections (by heading) that are directly relevant to the target task's scope, dependency, completion criteria, rollback subset, and verification commands.
	- Include exact file paths for all omitted sections.
3. If a single file is still too large:
	- Split by heading blocks and inject in deterministic chunks (top-down order), prioritizing sections referenced by `task.md` and feature dependencies.
4. Explicitly instruct the subagent:
	- If additional context is needed from omitted sections, request specific file paths/headings before implementation.

Do not fail due to context overflow. Prefer partial structured context + explicit file references over truncating the prompt mid-stream.
