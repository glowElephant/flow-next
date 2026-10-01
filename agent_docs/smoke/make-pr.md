# make-pr: manual smoke (maintainer checklist)

Moved out of the shipped skill in 7.0; never loaded at runtime.

Maintainer reference for `workflow.md`. Not part of any render path: the skill never
reads this file at runtime. It complements the focused tests of the skill’s executable fences.

Expected behavior for a native invocation:

- `command -v gh` missing → exit 1 with install instructions.
- `gh auth status` failing → exit 1 with login instructions.
- `--base <branch>` resolves `origin/<branch>`; a stale local branch cannot widen the export. An invalid remote branch stops before composition.
- Branch with no `branch_name` match in any `.flow/specs/*.json` AND no positional spec id → preflight prints `NO_SPEC` and exits 4; make-pr takes the no-spec path (`gh pr create` with the handoff as the body), with no question and no spec created.
- Tasks not all done + interactive → warn on stderr + proceed (open items force a draft via create-and-finalize); autonomous exits 2; `--dry-run` warns and continues. No `AskUserQuestion` for open tasks.
- Branch with an OPEN PR → exit 1 with `/flow-next:resolve-pr` hint.
- Branch with a CLOSED or MERGED PR (no OPEN) → continues cleanly. **This is the load-bearing check** — validated empirically: bare `gh pr view --json url` rc=0 for closed/merged PRs would false-positive without the `select(.state == "OPEN")` filter.
- Branch with no PR history at all (`gh pr view` exits 1) → continues cleanly.
- Autonomous mode (`FLOW_AUTONOMOUS=1`) → no `AskUserQuestion` calls in Phase 0; deterministic exit codes on missing context.
- Phase 1.5 persists the structured PR cognitive-aid and renders its supported current briefing as the body.

- Completed spec close commit precedes export and aid composition; close failure stops both.
- Group `files: []` is valid; omitted `files` is rejected. Outcome `pass` requires a green executed gate.
