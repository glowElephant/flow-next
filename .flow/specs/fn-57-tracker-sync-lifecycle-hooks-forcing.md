## Conversation Evidence

> user: "you didn't link the pr properly, tracker sync didn't work somehow"
> user: "why did it not happen before, i had similar issues in codex in another project"
> user (relaying a Codex session in another project, GNO-3): "you also didn't do it on the work steps, you also didn't link the pr etc etc, help me understand if my prompting in the skills was wrong or was this a one-off thing"
> [Codex agent's diagnosis, shared by user]: "Not your prompting. Mostly my execution miss. ... these hooks are prose/checklist obligations, not executable gates. The skill says 'invoke tracker-sync' but the actual snippet body is `:`. That makes it agent-discipline-dependent. ... The durable fix is to make flow-next-work / flow-next-make-pr call a real flowctl sync lifecycle ... or equivalent wrapper, so missing tracker sync is observable and receipts are required before final."
> user: "do we have issues with our tracker-sync stuff"
> user: "yes capture it"
> user: "this is not just for linear right, but for all trackers?"

> [agent investigation this session, confirming the diagnosis against the code]: make-pr §4.6a (the PR↔issue `Ref <identifier>` line) IS deterministic bash that appends to the body before `gh pr create` (workflow.md:1341-1343) — the miss there was execution-fidelity (the agent hand-rolled `gh pr create` and skipped it). The lifecycle hooks — `work.firstClaim → In Progress` (phases.md:210), `work.done → comment` (:282), make-pr §5.6 enhancement — are executable GATES wrapping a `:` no-op whose only body is a prose comment ("invoke the flow-next-tracker-sync skill"). On the MCP rung (no `LINEAR_API_KEY`), flowctl has no MCP access, so the action is inherently agent-driven and can't be a pure flowctl call.

> user (2026-06-09, re-scoping review): "i forgot about it as i was wary of adding more determinism, but this might make sense if it's a light touch that doesn't introduce a ton of overhead, and no overhead for users that don't user the sync-tracker stuff" ... "minimal but effective solution"
> user (2026-06-09): "push it to linear, it should be a blocker of the other ones we just did" [fn-58/59/60 — the loop-orchestration chain]
> [agent re-review 2026-06-09, against flowctl + skills]: receipt plumbing already ships — `flowctl sync receipt` (status enum `pushed|pulled|merged|updated|diverged|queued|errored|noop`, `--transport`, `--note`, guard-safe `.flow/sync-runs/`), emitted by the tracker-sync skill per run. Two gaps: receipts carry NO event field, and NOTHING reads them back (no check/audit command). The failure mode was reproduced live this session: capture ran with `perEvent.capture: reconcile` active and silently skipped the touchpoint — no skill run, no receipt, no signal.

## Goal & Context
<!-- scope: business -->

<!-- Source-tag breakdown: 55% [user] / 25% [paraphrase] / 20% [inferred] -->

flow-next's tracker-sync bridge (fn-52, shipped) wires lifecycle touchpoints — claim a task → move the issue In-Progress, finish a task → post a comment, open a PR → link it to the issue. In real use these touchpoints **silently don't fire**: a PR opened without its issue link, work steps that never moved the tracker. [user] It has happened on more than one host — both a Claude session and a Codex session in a separate project (GNO-3) hit it [user] — so it is **not a prompting problem and not model-specific** [paraphrase]. Root cause: the lifecycle hooks are **prose/checklist obligations, not executable gates** — the skill says "invoke the tracker-sync skill" but the actual snippet body is a `:` no-op, making them agent-discipline-dependent, and nothing fails when they are skipped. [paraphrase] When an agent is driving the loud gates (tests, review, PR-create — which fail visibly), the quiet tracker side-effects get dropped. [inferred] This spec makes the tracker lifecycle **observable and forcing** so a configured-but-didn't-fire touchpoint is a detectable gap, not a silent one. [paraphrase]/[inferred]

This is **tracker-agnostic — for ALL trackers, not just Linear**: Linear and GitHub today (and any future adapter), via the bridge's transport-blind adapter interface. [user] The Linear symptoms surfaced it, but the weakness is in the shared lifecycle-hook layer that every adapter routes through. [inferred]

## Architecture & Data Models
<!-- scope: technical -->

The split is the existing flow-next architecture rule (mechanical → deterministic/flowctl + receipts; judgment → skill), applied to the tracker hooks — with one deliberate narrowing: **flowctl never mutates the tracker; it only audits.** All tracker mutations stay agent-driven through the tracker-sync skill on every transport. [user]/[inferred]

Receipt plumbing already ships (`flowctl sync receipt` — status enum, `--transport`, `--note`, guard-safe `.flow/sync-runs/`; the tracker-sync skill emits one per run). The minimal delta is four pieces, tracker-agnostic because they live in the shared receipt/lifecycle layer every adapter routes through: [inferred]

- **`--event <perEvent-key>` on `sync receipt`** — tags each receipt with the lifecycle touchpoint it served (`work.firstClaim`, `work.done`, `capture`, `makePr`, ...). The existing `noop` status + `--note` already expresses skipped-with-reason; no enum widening. [inferred]
- **`flowctl sync check <spec-id> --events <triggered-this-run>`** — a new **read-only, local-only** audit: bridge inactive → silent constant-time exit (the zero-overhead path); active → for each triggered + configured event, verify a matching receipt exists; print `OK` / `MISSING:<event>` lines. It runs independently of the touchpoints, so a wholesale-skipped dispatch block is still caught. [paraphrase]/[inferred]
- **End-of-skill check + retro-fire** — work (end-of-run summary), capture (final phase), and make-pr (final output) each add one `sync check` call; on `MISSING` the skill retro-fires the missed touchpoint via the tracker-sync skill, re-checks, and surfaces the result in the summary it already prints. The summary line is the forcing function. [inferred]
- **make-pr fidelity repair** — after `gh pr create`, deterministically verify the §4.6a ref line landed in the PR body (`gh pr view --json body`) and repair via `gh pr edit` when absent — mechanical, no judgment; `gh` is already a make-pr prereq. [inferred]

**Agent-only transports** (e.g. Linear's MCP rung — flowctl can't call it) need no special case: mutation is agent-driven everywhere, and the audit only reads local receipts. **Judgment ops** — the agentic 3-way body reconcile/merge — stay a skill for every tracker; this spec does not touch them. [inferred]

## Edge Cases & Constraints
<!-- scope: technical -->

- **Bridge inactive / event opted-out** is a legitimate `skipped` (no-op), not a failure — must read as a clean receipt, never an error. [inferred]
- **Execution-fidelity gap (make-pr §4.6a):** the ref-append is already deterministic but an agent that hand-rolls `gh pr create` bypasses it — the forcing function must catch "PR opened but no issue link" even when the skill's own bash wasn't run literally. [inferred]
- **Best-effort, never blocking the primary work:** a tracker failure must stay non-fatal (the PR is already open; the task is already done) — observability must not turn a tracker hiccup into a hard stop. [inferred]
- **Ralph-safe:** receipts + any queue behavior must preserve the autonomous-loop invariants. [inferred]

## Acceptance Criteria
<!-- scope: both -->

- **R1:** Sync receipts are **event-tagged**: `flowctl sync receipt` gains `--event <perEvent-key>`, and every tracker-sync invocation from a lifecycle touchpoint records which event it served. The existing status enum + `--note` express skipped/errored — no enum widening. [paraphrase]
- **R2:** A new **read-only** `flowctl sync check <spec-id> --events <triggered>` compares the events that triggered during a run against config + receipts and reports `OK` / `MISSING:<event>` per touchpoint; **work, capture, and make-pr run it before their final summary, retro-fire any `MISSING` touchpoint via the tracker-sync skill, re-check, and surface the outcome** — a missing tracker side-effect is caught in-run, not discovered later by the user. [paraphrase]
- **R3:** flowctl gains **no tracker-mutation code** — all status / comment / link mutations stay agent-driven through the tracker-sync skill on every transport; the only deterministic additions are the read-only audit and the make-pr ref verify/repair. [user]
- **R4:** The make-pr **PR↔issue link reliably fires on a real `/flow-next:make-pr` run for whichever tracker is active** — the execution-fidelity gap (agent hand-rolls `gh pr create` and skips the deterministic ref-append) is closed by a deterministic post-create verify (`gh pr view --json body` contains the ref when the bridge is active + linked) with `gh pr edit` repair when absent. [user]/[inferred]
- **R5:** On any **agent-only transport** (e.g. Linear's MCP rung — flowctl can't call it) where the op is inherently agent-driven, the forcing function is the **receipt gate** (the agent must record the event receipt), since the op cannot be a pure flowctl call. [inferred]
- **R6:** The **agentic 3-way body merge stays a skill** — for every tracker — this spec hardens only the mechanical status / comment / link touchpoints, not the judgment-bearing reconcile. [inferred]
- **R7:** The hardening is **tracker-agnostic**: it lives in the shared receipt / lifecycle-hook layer and applies uniformly to **every adapter — Linear, GitHub, and any future tracker** — never Linear-only. [user]
- **R8:** **Zero overhead when the bridge is inactive or the event is opted out**: `sync check` exits silently in constant time — no output, no receipts, no prompts; non-tracker users see no change anywhere in their workflow. [user]
- **R9:** Docs updated — `tracker-sync.md` (receipt/check lifecycle, retro-fire), `flowctl.md` (`sync check`, `--event`), and `linear-mcp.md` **corrected**: the claude.ai Linear MCP returns identifiers, never UUIDs, so first-link requires the GraphQL rung (`LINEAR_API_KEY`); site changelog entry + plugin version bump. [user]/[inferred]

## Boundaries
<!-- scope: business -->

- **NOT** a rewrite of the tracker-sync bridge (fn-52, shipped) — a reliability hardening of its lifecycle hooks. [inferred]
- **NOT** making the body reconcile deterministic — that legitimately stays an agentic skill. [user: "make ... call a real flowctl sync lifecycle ... or equivalent wrapper" applies to the mechanical parts]
- **NOT** building tracker mutations (GraphQL/gh status, comment, attach ops) into flowctl — the original draft's deterministic-transport idea is deliberately cut per the maintainer's light-touch constraint; mutation stays in the skill. [user]
- **NOT** hook-based enforcement — no PreToolUse/Stop machinery; the forcing function is the end-of-skill check + visible summary line. [user]
- **NOT** changing the opt-in / opt-out config model (`perEvent`, default-on-after-ceremony) — only how reliably the opted-in events fire and are observed. [inferred]
- Tracker side-effects stay **best-effort / non-fatal** to the primary work loop — observability adds a receipt, never a hard block on a tracker failure. [inferred]

## Decision Context
<!-- scope: both — conditionally substructured -->

### Motivation

A bridge whose lifecycle hooks silently no-op erodes the whole value proposition — the user believes the tracker mirrors flow state, but PRs land unlinked and issues never move, and the user only finds out by accident (as happened on FLOW-5 and in the GNO-3 Codex session). [user]/[inferred] Making the hooks observable + forcing converts "did the agent remember?" into a checkable property, the same way Ralph's receipts make autonomous state transitions auditable. [paraphrase]/[inferred]

This also hardens the layer the autonomous loop chain (fn-58 readiness projection, fn-59 pilot, fn-60 land) rides on — which is why it blocks that chain. [user]

### Implementation Tradeoffs
<!-- scope: technical -->

Receipts alone cannot close the loop — they are written *by* the tracker-sync skill, and the observed failure mode is the dispatch block being skipped wholesale (reproduced live 2026-06-09: capture ran with `perEvent.capture: reconcile` active and silently skipped the touchpoint — no skill run, no receipt, no signal). Hence the check must run independently of the touchpoints, at end-of-skill. The original draft's "deterministic mutations via gh/GraphQL transports" was cut deliberately: it builds per-tracker mutation surface into flowctl, duplicates the skill, and contradicts the light-touch constraint — the audit is read-only; the mutations stay agentic. Check + retro-fire converts "did the agent remember?" into "the skill cannot finish without either receipts or a visible `MISSING` line." [user]/[inferred]

## Requirement coverage

| R-ID | Task |
|------|------|
| R1–R9 | TBD — populate via /flow-next:plan |
