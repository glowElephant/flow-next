# Review, QA, and completion-review selection

## Implementation review

Runs per `review.backend` or the invocation's `--review=<backend>` flag on every route, including direct and defect routes, for the changes [working-rules.md](../../../references/working-rules.md) names by risk; `/flow-next:impl-review` resolves the backend itself. It is never deferred to a pull request; timing and the risk rule follow working-rules.md. `none` skips with `skipped(config: review=none)`. A qualifying `flowctl triage-skip --base <ref>` receipt (docs-only, lockfile-only, release-chore, generated-only) records `mode: triage_skip` and satisfies the gate. Flow never lowers the gate and never fabricates a verdict.

## Design review

`flow-next:flow-next-plan-review <spec-id>` runs on an explicit request or when the route names design risk. It reviews a spec with zero tasks; task decomposition is never a prerequisite.

## Live QA

`pipeline.qa` is a string enum `off | on | auto`; any other value is `off`.

- `off`: QA runs only when the user invokes `/flow-next:qa`.
- `on`: QA runs at all-tasks-done, before make-pr, on every spec.
- `auto`: QA runs at all-tasks-done when the spec's acceptance describes UI behaviour on a drivable surface **and** a target can be started (a documented start command, a deploy URL, or `.flow/features/`). Otherwise the stage records `skipped(config: pipeline.qa=auto: <no UI-observable criteria | no drivable surface | no startable target>)` and the route advances.

For `auto` only, decide the two halves; the QA gate never asks Jev, so a run with a key and one without decide the same way:

- **UI-observable criteria** is your judgment, read from the acceptance criteria and the repo (`.flow/features/`, the prime QA-readiness line): does the acceptance describe behaviour a user could observe on a screen, page, window or rendered widget, rather than CLI output, file contents or library behaviour? A UI with no surface the QA skill can drive records `no drivable surface`.
- **Startable target** comes from code: this hop's route result carries `decision.startable_target_fact`, resolved from a documented start command, deploy URL or `.flow/features/`. `null` records `no startable target`; never invent one.

QA runs when both halves hold. Record `stage: qa - ran (target: <cmd>)` or `stage: qa - skipped(config: pipeline.qa=auto: <no UI-observable criteria | no drivable surface | no startable target>)`. `off` and `on` never ask.

QA never hard-blocks the loop; `NEEDS_WORK` and `BLOCKED` advance to make-pr, and their findings become open items on a draft PR. The evidence-aware subtraction inside QA is unchanged: runtime, UI, and integration criteria are always re-driven; deterministic re-runnable tests subtract.

## Completion review

Unchanged single-task policy: with one minted task whose acceptance is the whole spec, the per-task implementation review is the integration check and completion review records `skipped(policy: single-task, per-task SHIP covers spec surface)`. Multi-task plans run `flow-next:flow-next-spec-completion-review` as configured.

## Receipts

Every stage flow routes or skips records one line in the receipt surface that stage already writes - the task's done summary for task-scoped stages, the run's final report for run-scoped ones:

```
stage: <name> - ran [<start>..<end>] | skipped(<policy|config|empty|error>: <detail>) | failed(<reason>: <detail>)
```

`flowctl usage --stages <spec-id>` summarizes the task-scoped lines. A skipped stage is an event with a reason, never an absence.
