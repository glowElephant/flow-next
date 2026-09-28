# End-to-end study: flow-next vs vanilla Claude Code across routes

## Goal & Context
<!-- Goal & Context: 30% [user], 60% [paraphrase], 10% [inferred] -->

The maintainer wants a general comparison of `/flow-next:flow --auto` against vanilla Claude Code with no skills, across the kinds of work the router supports, to see where flow-next helps, where it costs, and where gains can still be had. [paraphrase] The questions are whether the output is better, what the wall-clock and token cost is, what verification and proof a serious organisation gets from each, and what individual flow-next artifacts (the feature map, the clawpatch semantic map, `STRATEGY.md`) contribute. [paraphrase] The answer decides which public claims can be made, and it gives optimisation work a measured baseline for where flow-next's own overhead goes. [paraphrase]

Prior evidence: three agent-evals studies (feature-map-2026-09, defect-intake-map-2026-09, live-routes-map-2026-09) found a maintained feature map roughly halves turns and wall time when a task does not say where in the app the problem is, but both arms there were plain `claude -p` sessions, so the gain belongs to the map artifact, not to flow-next, and flow-next's own overhead has never been measured. [paraphrase]

Nothing from this study is public until a verdict supports it. [user]

## Architecture & Data Models

- **Where it runs.** A private harness in the agent-evals repository, following its `METHODOLOGY.md` and `lib/evalkit.py`: preregistered, model held constant, every draw retained. Scripts only; nothing in the flow-next repo changes and flowctl gains no telemetry. [paraphrase]
- **Arms (stage 1).** (a) vanilla Claude Code, `claude -p` with no plugins, no skills and no flow-next instruction text, given the task only; (c) `/flow-next:flow --auto` on the same task, from the same starting state, with the shipped default configuration. The implementing model is the same in both. Arm (c)'s configured reviewer (backend, model, effort) is recorded and counts toward its tokens, cost and wall time. [paraphrase]
- **Cases (stage 1).** Five, each a real task with a known-good reference outcome: a simple bug, a hard bug, a small feature, a large feature, and one hill climb (one metric toward a stated target). Bugs may come from earlier agent-evals studies and fixtures; the large feature is replayed from real history (a merged feature in gno, flow-swarm, dettivo-linux, or an external repository), starting from its base commit with the original intent. Other repositories are fine. [user] Further router routes (a structural cleanup, a read-only question, a design fork settled by a prototype) are an optional second wave, each only if stage 1 leaves budget. [paraphrase]
- **Ablations (stage 2).** Arm (c) with and without one artifact at a time, only on the cases where the artifact can plausibly matter: the feature map (`/flow-next:features`) on a case with a drivable UI and a not-located report; the clawpatch semantic map (`/flow-next:map`) on the large feature or the hard bug; `STRATEGY.md` on the large feature. The one-time cost of producing each artifact is measured separately and reported beside the per-task effect, with the number of tasks after which the saving covers it. The earlier vanilla-plus-map arm (b) is kept as the map's vanilla-side ablation. [paraphrase]
- **Isolation for parallel development.** Arm (c) runs a frozen snapshot of a tagged flow-next release loaded with `--plugin-dir`, never the live checkout. Every draw runs in its own throwaway clone with its own Claude configuration directory, so flow-next development continues in parallel without touching a running study. [paraphrase]
- **Measurement.** Concrete metrics come from the stream logs and the checkout: success against hidden acceptance tests written before any draw and never visible to the agent, wall-clock, turns, tokens and dollar cost per model (implementer and reviewer), human stops (`NEEDS_HUMAN` and any interrupt), and the diff size. Soft outcomes come from a blinded LLM judge from a different model family than the implementer, scoring each final state against the reference with a fixed rubric: correctness, completeness, scope discipline (no unrequested machinery), code and test quality, and verification and proof (is there reproducible evidence a reviewer at a serious organisation could audit: tests that fail before and pass after, requirement-to-evidence traceability, a review record). The judge never sees which arm produced the output. [paraphrase]
- **Overhead attribution.** For arm (c), turns, wall time and tokens are split into flow-next machinery (skill loading, routing and judge calls, receipts, reviews, worker dispatch) and work on the task, from the stream logs by a rule fixed in the preregistration. [paraphrase]
- **Efficiency.** Draws run through the harness in parallel where they do not share a machine resource that the metric depends on; wall-clock-gating draws run one at a time on an otherwise idle machine. The draw count per cell is set in the preregistration to the minimum that can reach its decision bar. [paraphrase]

## Edge Cases & Constraints

- A case on which arm (c) cannot reach its natural endpoint (no merge target, no drivable app) uses a preregistered sub-goal for every arm on that case. [inferred]
- An arm (c) draw that stalls, errors or stops for a human is scored as a failed draw with its elapsed cost, never dropped or rerun silently; a stop that asks a genuine human-owned question is recorded as such, since vanilla had no way to ask. [paraphrase]
- The judge's rubric and the hidden acceptance tests are frozen before the first draw; a judge output that cannot be parsed is reported as unscored and counted. [inferred]
- A faster arm that produces a worse outcome does not win; the primary comparison is time and cost to an outcome that passes the hidden tests and the judge's correctness bar. [paraphrase]

## Acceptance Criteria

- **R1:** Before any draw, a preregistration is committed in agent-evals naming the hypotheses, the arms, the five stage-1 cases with their sources and reference outcomes, the stage-2 ablation cells, the hidden acceptance tests, the judge model and rubric, the metrics and decision bars, the draw count per cell, the held-constant implementing model, the overhead attribution rule, the frozen flow-next version, and the proposed spend. No draw runs until the maintainer has approved the spend. Errors: a draw run before approval, or any bar, rubric or test changed after the first gating draw, is recorded as a deviation and cannot carry the verdict. [paraphrase]
- **R2:** Stage 1 runs arms (a) and (c) on the simple bug, hard bug, small feature, large feature and hill-climb cases from the same starting states with the same implementing model; arm (a) runs with no plugins, skills or flow-next instruction text. [user]
- **R3:** Every draw records hidden-test success, wall-clock, turns, tokens and cost per model, human stops, diff size, and the blinded judge's rubric scores, and results are reported per case and pooled. [paraphrase]
- **R4:** For arm (c), machinery versus task work is broken out by the preregistered attribution rule, and spans the rule cannot place are reported as unattributed. [paraphrase]
- **R5:** Stage 2 reports, for each ablated artifact (feature map, clawpatch map, `STRATEGY.md`) on its preregistered cases, the per-task effect with and without it and its one-time production cost, with the break-even task count. [user]
- **R6:** The harness runs arm (c) from a frozen snapshot of a tagged flow-next release in per-draw throwaway clones and configuration directories, so flow-next development continues during the study. [user]
- **R7:** The verdict states, per case and pooled, where flow-next is better, equal or worse than vanilla on outcome quality, wall-clock, cost and verification, names the largest measured sources of flow-next overhead as optimisation targets, and keeps every draw including failures in the record; public text carries only conclusions the verdict supports. [paraphrase]

## Boundaries

- Evaluation only: no flow-next product change is made in this spec; improvements it suggests become their own specs. [paraphrase]
- Study data, logs, the preregistration and scripts stay in the private agent-evals repository. [user]
- No new benchmark framework: the harness reuses agent-evals' existing evalkit and fixture patterns. [paraphrase]

## Decision Context

### Motivation

"flow-next:flow --auto vs vanilla claude code with 0 skills"; "llm-judge for outcomes and the soft questions, concreate measurement for metrics"; "pretty long running, so would want to be able to work on flow-next in parallel". [user] The five cases cover the router's main shapes without the cost of every route; the ablations answer what each artifact buys rather than assuming it. [paraphrase] Supersedes this spec's earlier scope (defect tasks only, located versus not-located, on one fixture app), which becomes the feature-map ablation inside stage 2. [paraphrase]

## Strategy Alignment

STRATEGY.md lists idea-to-merge wall-clock as a key metric worth measuring; "Remember the bitter lesson" asks that machinery be evaluated against its absence with preregistered bars, and arm (a) is that absence for flow-next as a whole.

## Strategy Conflicts

None found.
