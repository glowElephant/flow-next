---
name: flow-next-impl-review
description: John Carmack-level implementation review via Codex, RepoPrompt, Copilot, Cursor, Claude or a host reviewer. Use when reviewing code changes, PRs, or implementations. Triggers on /flow-next:impl-review.
user-invocable: false
---

# Implementation review

You coordinate; the configured backend reviews. Never author a verdict yourself, and use one
backend for the whole review. Read [working-rules.md](../../references/working-rules.md) first:
its Review section decides which findings you fix.

Arguments: `[task or spec id] [--base <commit>] [--review=<backend>] [--deep[=passes]]
[--validate] [--interactive] [--no-triage] [focus areas]`. Without `--base` the whole branch is
reviewed against main.

## 1. Setup

One Bash call; fill the three literals from the arguments.

```bash
set -e
FLOWCTL="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/scripts/flowctl"
[ -x "$FLOWCTL" ] || FLOWCTL="<plugin-root>/scripts/flowctl"   # <plugin-root> = the directory two levels above this skill's SKILL.md file (the harness gave you that file's absolute path when the skill loaded); substitute it literally
[ -x "$FLOWCTL" ] || FLOWCTL=".flow/bin/flowctl"
REVIEW_ID="<task or spec id, or empty for a branch review>"
BACKEND="<value of --review, or empty>"
DIFF_BASE="<value of --base, or empty>"
[ -n "$BACKEND" ] || BACKEND=$("$FLOWCTL" review-backend "$REVIEW_ID")
[ -n "$DIFF_BASE" ] || { DIFF_BASE=main; git rev-parse -q --verify main >/dev/null || DIFF_BASE=master; }
echo "FLOWCTL=$FLOWCTL BACKEND=$BACKEND DIFF_BASE=$DIFF_BASE"
git diff --shortstat "$DIFF_BASE"...HEAD
```

- `ASK`: stop; no backend is configured (`/flow-next:setup`, or pass `--review=<backend>`).
- `none`: no review; say so.
- `export`: refuse; manual export review lives in `/flow-next:plan-review --review=export`.
- Any other backend than `codex`, any of `--deep`, `--validate`, `--interactive`, `--no-triage`,
  or an instruction about the reviewers ("one reviewer", "three model families"): read
  [other-paths.md](other-paths.md) and follow it for steps 2-3, then come back to step 4.

Shell state does not survive between Bash calls: each block below resolves `FLOWCTL` again and
takes `REVIEW_ID` and `DIFF_BASE` as literals.

## 2. Codex review

Run each review command as one blocking foreground Bash call with a 600-second timeout. Never
run it in the background: its completion would not resume you.

```bash
FLOWCTL="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/scripts/flowctl"
[ -x "$FLOWCTL" ] || FLOWCTL="<plugin-root>/scripts/flowctl"   # <plugin-root> = the directory two levels above this skill's SKILL.md file (the harness gave you that file's absolute path when the skill loaded); substitute it literally
[ -x "$FLOWCTL" ] || FLOWCTL=".flow/bin/flowctl"
REVIEW_ID="<literal or empty>"; DIFF_BASE="<literal>"
ROUTE="$("$FLOWCTL" review-route ${REVIEW_ID:+"$REVIEW_ID"} --rotate-stale --json)" || { printf '%s\n' "$ROUTE" >&2; exit 1; }
ACTION="$(jq -r '.action' <<<"$ROUTE")"; TASK_ID="$(jq -r '.task_id // empty' <<<"$ROUTE")"
RECEIPT_PATH="$(jq -r '.receipt_path' <<<"$ROUTE")"
echo "TASK_ID=$TASK_ID RECEIPT_PATH=$RECEIPT_PATH"
case "$ACTION" in
  stop) jq -r '.message' <<<"$ROUTE" >&2; exit 1 ;;
  fix-then-rereview) echo "RESUMED: the receipt holds findings still to fix; go to step 4"; exit 0 ;;
esac
TRIAGE=(--receipt "$RECEIPT_PATH" --base "$DIFF_BASE" --no-llm); [ -n "$TASK_ID" ] && TRIAGE+=(--task "$TASK_ID")
if OUT=$("$FLOWCTL" triage-skip --json "${TRIAGE[@]}" 2>/dev/null); then
  echo "Triage-skip: $(jq -r '.reason // "trivial diff"' <<<"$OUT")"; echo "VERDICT=SHIP"; exit 0
fi
args=(); [ -n "$TASK_ID" ] && args+=("$TASK_ID")
args+=(--base "$DIFF_BASE" --receipt "$RECEIPT_PATH" --json)
# The default is three reviewers. For a small diff in one area that touches no persisted or
# shared state, concurrency, security or data layout, set ONE_REVIEWER=1 for a single reviewer.
ONE_REVIEWER=0
[ "$ONE_REVIEWER" = 1 ] && args+=(--draw correctness)
"$FLOWCTL" codex impl-review-fanout "${args[@]}"
```

A branch review (no task) passes the caller's focus areas with `--focus "<areas>"`. Triage
passing means lockfile, docs, release or generated files only: the review is done.

## 3. Merge and finalize

The fan-out JSON lists each draw's `<axis>.review.md`, its `rid`, and the finalize command. Read
each review and write a merge plan to a file: `{"keep":["correctness:1"],"collapse":{"contracts:2":"correctness:1"}}`,
where references are `<axis>:<finding number>`. Collapse findings that describe the same defect
onto the one with the strongest evidence; leave out findings with no concrete failing scenario in
the change. Then, in the foreground:

```bash
FLOWCTL="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/scripts/flowctl"
[ -x "$FLOWCTL" ] || FLOWCTL="<plugin-root>/scripts/flowctl"   # <plugin-root> = the directory two levels above this skill's SKILL.md file (the harness gave you that file's absolute path when the skill loaded); substitute it literally
[ -x "$FLOWCTL" ] || FLOWCTL=".flow/bin/flowctl"
"$FLOWCTL" codex impl-review-fanout-finalize --rid "<rid>" --merge-plan "<plan path>" --json
```

flowctl computes the verdict (the worst draw wins; failed draws do not vote) and writes the
receipt. Report `VERDICT=<verdict>` with the kept findings; your own reading never changes it.
Finalize before you change or commit anything: a commit moves HEAD past the reviewed head,
flowctl refuses the round, and the retry is a full fresh review instead of the scoped re-review.

## 4. Act on the verdict

- `SHIP`: done. Report the verdict and any follow-ups.
- `MAJOR_RETHINK`: the approach is wrong. Stop with `BLOCKED: DESIGN_CONFLICT` and the
  reviewer's rationale; do not patch finding by finding.
- `NEEDS_HUMAN`: stop and hand the reviewer's question to the person.
- `NEEDS_WORK`: one fix pass, then one re-review. Fix only the findings working-rules says to
  fix; list the rest as follow-ups. Never ask the person which to fix. Run focused tests for the
  fixes and commit only the files you changed, with one `Declined #<n>: <reason>` line in the
  commit message for each finding you listed as a follow-up (the re-review reads them). Then
  re-review once, in the foreground:

```bash
FLOWCTL="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/scripts/flowctl"
[ -x "$FLOWCTL" ] || FLOWCTL="<plugin-root>/scripts/flowctl"   # <plugin-root> = the directory two levels above this skill's SKILL.md file (the harness gave you that file's absolute path when the skill loaded); substitute it literally
[ -x "$FLOWCTL" ] || FLOWCTL=".flow/bin/flowctl"
REVIEW_ID="<literal or empty>"; DIFF_BASE="<literal>"
ROUTE="$("$FLOWCTL" review-route ${REVIEW_ID:+"$REVIEW_ID"} --json)"
TASK_ID="$(jq -r '.task_id // empty' <<<"$ROUTE")"; RECEIPT_PATH="$(jq -r '.receipt_path' <<<"$ROUTE")"
"$FLOWCTL" codex impl-review ${TASK_ID:+"$TASK_ID"} --base "$DIFF_BASE" --receipt "$RECEIPT_PATH"
```

  The re-review resumes the reviewer's session and its verdict is terminal: report surviving
  findings, never start a second fix pass, unless working-rules.md's review loop applies (an unattended run, or a request to review until SHIP). In that loop, fix and re-review the same
  way until SHIP or the round cap. When the reviewer keeps only findings you declined under
  working-rules.md's rule, end the loop and print `OVERRIDDEN: <n> declined findings` with each
  finding and both sides' reasons after `VERDICT=NEEDS_WORK`; the caller completes the task on it.

If a review command ends without a verdict (a transport error), retry it once. `ESCALATE:`,
`TRANSPORT_UNHEALTHY`, `NOT_RETRYABLE:` and other refusals end this review: report the message
as printed and stop. Never widen the reviewer's sandbox, call `codex` directly, or reset review
state to get past one.
