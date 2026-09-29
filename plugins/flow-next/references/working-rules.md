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

## Tests

- Run the tests for the code you changed. Do not run the full suite unless the repository's
  instructions require it; CI owns regressions.
- A failing test written before the fix, then passing after it, is the proof. Where that test is
  cheap, write it first. No separate lint, typecheck or commit round for it.
- Never re-run a suite only to read its output again.

## Attended and unattended

- **Attended** (a person is in the session): they want fast feedback. Ask only what only they can
  answer, one question at a time; settle anything observable by running it. Leave work
  uncommitted unless asked. Hand discoveries back as offers ("found X, not part of this; want a
  follow-up?").
- **Unattended** (`--auto`): nobody is waiting. Never ask; decide from evidence, and stop only
  for a call only a human can make or an irreversible action. Fix a discovery only when it
  blocks the goal, as its own commit; list the rest as follow-ups in the final report.

## Handoff

Short: what changed, how you know it works (the commands you ran and what they showed), and
anything left open. No stage-by-stage narration.
