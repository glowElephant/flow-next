# Worker Phase 4.5: memory auto-capture (gated reference)

> **Read only when worker.md Phase 4.5's conditions all hold** (memory enabled, at least one
> NEEDS_WORK → SHIP transition, a non-trivial fix, and none of its skip cases). A conductor running
> the capture on a worker's behalf reads it the same way.

Synthesize a bug-track entry from the NEEDS_WORK findings + the fix you applied. Entry-body prose follows the artifact prose contract in [docs/prose.md](../../../docs/prose.md); proceed without it when the doc is absent.

```bash
FLOWCTL="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/scripts/flowctl"
[ -x "$FLOWCTL" ] || FLOWCTL="<plugin-root>/scripts/flowctl"   # <plugin-root> = the directory two levels above this skill's SKILL.md file (the harness gave you that file's absolute path when the skill loaded); substitute it literally
[ -x "$FLOWCTL" ] || FLOWCTL=".flow/bin/flowctl"

cat > /tmp/memory-body.md <<'EOF'
## Problem
<one-paragraph on what went wrong — surfaced by the review>

## What Didn't Work
<first attempt / naive approach, if relevant>

## Solution
<what actually fixed it — cite file:line when possible>

## Prevention
<what would catch this earlier — pre-commit check, test pattern, lint rule>
EOF

$FLOWCTL memory add \
  --track bug \
  --category <inferred> \
  --title "<one-line summary, <=80 chars>" \
  --module "<primary-affected-file-or-module>" \
  --tags "<tag1>,<tag2>" \
  --symptoms "<one-line — what went wrong>" \
  --root-cause "<one-line — what caused it>" \
  --body-file /tmp/memory-body.md
```

`memory add` always creates unless you pass explicit `--update <id>`. The JSON response always includes `matches` (scored retrieval signal): on high overlap, either re-run with `--update <match-id>` to fold into the existing entry, or accept the create. Moderate overlap creates a new entry with `related_to` cross-reference. The worker owns the update-vs-create judgment.

Optional flags with sensible defaults (omit unless you need to override):
- `--problem-type` — derived from `--category` (`runtime-errors` → `runtime-error`, `build-errors` → `build-error`, `test-failures` → `test-failure`; other categories default to `build-error`). Pass explicitly only when the derived default is wrong.
- `--resolution-type` — defaults to `fix` (alternatives: `workaround`, `documentation`, `refactor`).
- `--symptoms` — defaults to the title.
- `--root-cause` — defaults to `(unspecified)`; populate it for useful entries.

## Inferring category

Map the review's primary issue to one of the 8 bug-track categories:

| Review signal | Category |
|---|---|
| build failed, import missing, compile error | `build-errors` |
| test suite failures, assertion mismatch | `test-failures` |
| null deref, wrong value, crash at runtime | `runtime-errors` |
| N+1 query, slow request, memory leak | `performance` |
| auth bypass, SQL injection, secret leak | `security` |
| API contract mismatch, schema drift, wire format | `integration` |
| data corruption, partial write, migration error | `data` |
| layout broken, wrong color, a11y | `ui` |

When ambiguous, pick the most specific that fits. If truly none fit, default to `build-errors` (the migration classifier does the same). Overlap detection will merge with a similar past entry if one exists.
