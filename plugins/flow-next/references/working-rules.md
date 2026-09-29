# Working rules

These hold on every route and in every stage. Where a stage's own text asks for more, these win
unless the user or the repository's instructions ask for it.

## Scope

- Ship the smallest change the evidence justifies. Every changed line serves the request.
- No unrequested flags, options, guards, abstractions, refactors, renames, wording changes or
  docs edits. Matching the surrounding code is required; improving it is not.
- Problems you find that the request does not depend on (a flaky test, junk a test run leaves
  behind, a nearby bug) are reported, not fixed. Check whether they exist before your change;
  if they do, they are not yours.
- Files a test run or tool writes into the repository are not part of your change: remove them
  from the diff before handing back, and mention them; do not chase their cause.

## Design

Before writing logic for a feature, name the data it touches and what owns each piece of state
(which record a value belongs to, what is shared). Most wrong designs are wrong ownership.

## Tests

- Run the tests for the code you changed. Do not run the full suite unless the repository's
  instructions require it; CI owns regressions.
- A failing test written before the fix, then passing after it, is the proof. Where that test is
  cheap, write it first. No separate lint, typecheck or commit round for it.
- A test must be able to fail for a defect: it calls the code the way a user does and checks the
  observed result. One that would still pass if the code returned nothing is rewritten or dropped.
- Before handing back, run the change the way a user would (the command, the request, the page)
  and look at the actual result, not only the unit tests.
- Never re-run a suite only to read its output again.

## Attended and unattended

- **Attended** (a person is in the session): they want fast feedback. Ask only what only they can
  answer, one question at a time; settle anything observable by running it. Commit on a local
  branch only when review needs it (review reads commits); never push or open a pull request
  unless asked. Hand discoveries back as offers ("found X, not part of this; want a
  follow-up?").
- **Unattended** (`--auto`): nobody is waiting. Never ask; decide from evidence, and stop only
  for a call only a human can make or an irreversible action. Fix a discovery only when it
  blocks the goal, as its own commit; list the rest as follow-ups in the final report.

## Review

When a review backend is configured, review by risk, not by size. Review every change that
touches persisted or shared state, concurrency, security, data layout or migrations, and every
multi-file feature. A small local fix to output, wording or display is not reviewed; record the
skip and its reason. Read the configuration rather than assuming it, use the configured backend,
and if it cannot run, say so instead of substituting another reviewer. Review is never deferred
to a pull request.

Act on findings the way a careful author would: fix a finding only when it shows the change
itself does the wrong thing in a scenario the request covers. Hardening, extra shutdown or
error paths, broader refactors and style are follow-ups, listed in the handoff, not fixed. After
fixing, re-review once; do not loop.

Attended: hand the result back first, in its own message, and end the turn; then start the review
in the background and report its verdict (and any fix) when it lands. Unattended: the verdict
gates the handoff and any merge.

## Handoff

Short: what changed, how you know it works (the commands you ran and what they showed), and
anything left open. No stage-by-stage narration.
