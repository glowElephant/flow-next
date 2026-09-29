# Working rules

These hold on every route and in every stage. Where a stage's own text asks for more, these win
unless the user or the repository's instructions ask for it.

## Scope

- Ship the smallest change the evidence justifies. Every changed line serves the request.
- No unrequested flags, options, config or environment overrides, guards, abstractions, refactors,
  renames, wording changes or docs edits. Matching the surrounding code is required; improving it is not.
- Problems you find that the request does not depend on (a flaky test, junk a test run leaves
  behind, a nearby bug) are reported, not fixed. Check whether they exist before your change;
  if they do, they are not yours.
- Files a test run or tool writes into the repository are not part of your change: remove them
  from the diff before handing back, and mention them; do not chase their cause.
- When asked whether to widen the scope, "no" is a fine answer; say why in one line.
- A refactor that does not make the code easier to follow is reverted.

## Design

Before writing logic for a feature, name the data it touches and what owns each piece of state
(which record a value belongs to, what is shared). Most wrong designs are wrong ownership.

Build in small steps, each checked before the next, and commit them in an order that shows the
work is right (the failing test, then the fix). When two fixes built on the same idea have
failed, question the idea before trying a third.

## Tests

- Run the tests for the code you changed. Do not run the full suite unless the repository's
  instructions or the user ask for it; then run it once, at the end, not again after later fixes
  (re-check those with focused tests). CI owns regressions.
- A failing test written before the fix, then passing after it, is the proof. Where that test is
  cheap, write it first. No separate lint, typecheck or commit round for it.
- A test must be able to fail for a defect: it calls the code the way a user does and checks the
  observed result. One that would still pass if the code returned nothing is rewritten or dropped.
- Before handing back, run the change the way a user would (the command, the request, the page)
  and look at the actual result, not only the unit tests.
- Never re-run a suite only to read its output again.

## Attended and unattended

- **Attended** (a person is in the session): they want fast feedback. Ask only what only they can
  answer, and put related questions in one prompt rather than one per turn; settle anything
  observable by running it. Do not ask where a sensible default exists (a branch, a readiness
  flag): take it and say so in one line. Commit on a local
  branch only when review needs it (review reads commits); never push or open a pull request
  unless asked. List discoveries in the handoff as follow-ups ("found X, not part of this");
  the person decides what to pick up.
- **Unattended** (`--auto`): nobody is waiting. Never ask; decide from evidence, and stop only
  for a call only a human can make or an irreversible action. Fix a discovery only when it
  blocks the goal, as its own commit; list the rest as follow-ups in the final report. Keep a
  Decisions list in the final report and the pull request body: each default you chose, finding
  you declined and review you skipped, with the evidence behind it.

## Review

When a review backend is configured, review by risk, not by size. Review every change that
touches persisted or shared state, concurrency, security, data layout or migrations, and every
multi-file feature. A small local fix to output, wording or display is not reviewed; record the
skip and its reason. Read the configuration rather than assuming it, use the configured backend,
and if it cannot run, say so instead of substituting another reviewer. Review is never deferred
to a pull request.

Act on findings the way a careful author would: fix a finding only when it shows the change
itself does the wrong thing in a scenario the request covers. Hardening, extra shutdown or
error paths, broader refactors, style and problems that existed before the change are
follow-ups: list them in the handoff and do not ask whether to fold them in; the person asks if
they want one. When a finding points at unrequested machinery your change added, remove it.
After fixing, re-review once with a single reviewer looking at the fixes; do not loop. Fixes
after that re-review, including ones the person asks for, are verified with focused tests, not
another review.

Attended: hand the result back first, in its own message, and end the turn; then start the review
in the background and report its verdict (and any fix) when it lands. Unattended: the verdict
gates the handoff and any merge.

## Pull requests and follow-ups

A route that has no spec never creates one just to open a pull request: when a pull request is
asked for, open it directly (`gh pr create`) with the handoff as its body. Follow-ups are listed
in the handoff (and the pull request body), not captured as specs, attended or unattended; the
person decides later which become specs.

## Handoff

Short: what changed, how you know it works (the commands you ran and what they showed), and
anything left open. No stage-by-stage narration.

- Mark each claim as measured (you ran it and saw the result), inferred (it follows from what you
  read) or a guess.
- Name the run done the way a user would (the command, the request, the page) and what it
  showed, or `not run: <reason>`.
- Never hand the person a check you could have run yourself.
