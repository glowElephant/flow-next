# End-to-end study: flow-next vs vanilla Claude Code across routes

## Goal & Context
<!-- Goal & Context: 30% [user], 60% [paraphrase], 10% [inferred] -->

The maintainer wants a general comparison of `/flow-next:flow --auto` against vanilla Claude Code with no skills, across the kinds of work the router supports, to see where flow-next helps, where it costs, and where gains can still be had. [paraphrase] The questions are whether the output is better, what the wall-clock and token cost is, what verification and proof a serious organisation gets from each, and what individual flow-next artifacts (the feature map, the clawpatch semantic map, `STRATEGY.md`) contribute. [paraphrase] The answer decides which public claims can be made, and it gives optimisation work a measured baseline for where flow-next's own overhead goes. [paraphrase]

Prior evidence: three agent-evals studies (feature-map-2026-09, defect-intake-map-2026-09, live-routes-map-2026-09) found a maintained feature map roughly halves turns and wall time when a task does not say where in the app the problem is, but both arms there were plain `claude -p` sessions, so the gain belongs to the map artifact, not to flow-next, and flow-next's own overhead has never been measured. [paraphrase]

Nothing from this study is public until a verdict supports it. [user]

## Architecture & Data Models

- **Where it runs.** A private harness in the agent-evals repository, following its `METHODOLOGY.md` and `lib/evalkit.py`: preregistered, model held constant, every draw retained. Scripts only; nothing in the flow-next repo changes and flowctl gains no telemetry. [paraphrase]
- **Sessions, not one-shot calls.** Every draw is a multi-turn Claude Code session driven through the Claude Agent SDK (the same agent loop as Claude Code) on the chosen subscription, not a single `claude -p` call. If the SDK cannot run on the subscription, sessions instead drive the real Claude Code interface through herdr, with the same simulated person and logging. A simulated person works with the agent the way a real user would: opens with a realistic, rough request rather than a finished spec, answers the agent's questions (`AskUserQuestion` is routed to the simulator) from a hidden brief of what they actually want, reviews the result, and pushes back when it falls short, up to a preregistered number of follow-ups. The simulator never reveals the hidden acceptance tests. [paraphrase]
- **Arms (stage 1).** (a) vanilla Claude Code with no plugins, no skills and no flow-next instruction text; (c) flow-next used the way its docs recommend, on a repository prepared the way a real flow-next user's repository would be: `/flow-next:setup` run, a `STRATEGY.md`, the clawpatch semantic map (`/flow-next:map`), and the feature map (`/flow-next:features`) when the case has a drivable UI. In each draw the simulated person makes the request through attended `/flow-next:flow`, and once the spec is captured the run continues with `/flow-next:flow --auto` (`--auto` does not take raw intent). Shipped default configuration otherwise. [paraphrase] Both arms get the same simulated person and the same starting state. The implementing model is the same in both. Arm (c)'s configured reviewer (backend, model, effort) is recorded and counts toward its tokens and wall time. [paraphrase]
- **Cases (stage 1).** Five, each a real task with a known-good reference outcome: a simple bug, a hard bug, a small feature, a large feature, and one hill climb (one metric toward a stated target). Bugs may come from earlier agent-evals studies and fixtures; the large feature is replayed from real history (a merged feature in gno, flow-swarm, dettivo-linux, or an external repository), starting from its base commit with the original intent. Other repositories are fine, and for the hard bug, public repositories and benchmarks built around hidden or seeded real bugs are the fallback when real history gives no strong candidate. [user] Further router routes (a structural cleanup, a read-only question, a design fork settled by a prototype) are an optional second wave, each only if stage 1 leaves budget. [paraphrase]
- **Repository preparation.** Each case repository is prepared once for arm (c), before its draws, and every draw starts from a copy of that prepared state. A repository that already carries an artifact (for example its own `STRATEGY.md`) keeps it; missing ones are produced with the flow-next skill that owns them, driven by the simulated person playing the maintainer. Preparation cost (turns, wall time, tokens, human attention) is measured once per repository and reported beside the per-task results, with the number of tasks after which it pays for itself. Arm (a) starts from the unprepared repository. [paraphrase]
- **Ablations (stage 2).** Leave-one-out from the prepared state: arm (c) with one artifact removed at a time (`STRATEGY.md`, the clawpatch map, the feature map), only on the cases where that artifact can plausibly matter (the feature map on a case with a drivable UI and a not-located report; the clawpatch map on the large feature or the hard bug; `STRATEGY.md` on the large feature). Each artifact's contribution is the prepared result minus the leave-one-out result, set against its share of the preparation cost. The earlier vanilla-plus-map arm (b) stays as an optional vanilla-side check of the feature map. [paraphrase]
- **Isolation for parallel development.** Arm (c) runs a frozen snapshot of a tagged flow-next release loaded with `--plugin-dir`, never the live checkout. Every draw runs in its own throwaway clone with its own Claude configuration directory, so flow-next development continues in parallel without touching a running study. [paraphrase]
- **Measurement.** Concrete metrics come from the session logs and the checkout: success against hidden acceptance tests written before any draw and never visible to the agent, wall-clock, agent turns, tokens per model (implementer, reviewer, simulator reported separately and excluded from the arm's cost), human attention (the simulated person's turns, questions answered, follow-up corrections and words written), `NEEDS_HUMAN` stops, and the diff size. Soft outcomes come from a blinded LLM judge from a different model family than the implementer, scoring each final state against the reference with a fixed rubric: correctness, completeness, scope discipline (no unrequested machinery), code and test quality, and verification and proof (is there reproducible evidence a reviewer at a serious organisation could audit: tests that fail before and pass after, requirement-to-evidence traceability, a review record). The judge never sees which arm produced the output. [paraphrase]
- **Overhead attribution.** For arm (c), turns, wall time and tokens are split into flow-next machinery (skill loading, routing and judge calls, receipts, reviews, worker dispatch) and work on the task, from the stream logs by a rule fixed in the preregistration. [paraphrase]
- **Subscriptions.** Draws run on whichever subscription has usage left at run time; no separate spend approval. The run log records which account and model served each draw. [user]
- **Efficiency.** Draws run through the harness in parallel where they do not share a machine resource that the metric depends on; wall-clock-gating draws run one at a time on an otherwise idle machine. The draw count per cell is set in the preregistration to the minimum that can reach its decision bar. [paraphrase]

## Edge Cases & Constraints

- A case on which arm (c) cannot reach its natural endpoint (no merge target, no drivable app) uses a preregistered sub-goal for every arm on that case. [inferred]
- An arm (c) draw that stalls, errors or stops for a human is scored as a failed draw with its elapsed cost, never dropped or rerun silently; a stop that asks a genuine human-owned question is recorded as such, since vanilla had no way to ask. [paraphrase]
- The judge's rubric and the hidden acceptance tests are frozen before the first draw; a judge output that cannot be parsed is reported as unscored and counted. [inferred]
- A faster arm that produces a worse outcome does not win; the primary comparison is time and cost to an outcome that passes the hidden tests and the judge's correctness bar. [paraphrase]

## Acceptance Criteria

- **R1:** Before any study draw, a preregistration is committed in agent-evals naming the hypotheses, the arms, the stage-1 cases with their sources and reference outcomes, the stage-2 ablation cells, the hidden acceptance tests, the simulated person's briefs and follow-up policy, the judge model and rubric, the metrics and decision bars, the draw count per cell, the held-constant implementing model, the overhead attribution rule and the frozen flow-next version. Errors: any bar, rubric, brief or test changed after the first gating draw is recorded as a deviation and cannot carry the verdict. [paraphrase]
- **R2:** Stage 1 runs arms (a) and (c) on the simple bug, hard bug, small feature, large feature and hill-climb cases from the same starting states with the same implementing model; arm (a) runs with no plugins, skills or flow-next instruction text. [user]
- **R3:** Every draw records hidden-test success, wall-clock, turns, tokens and cost per model, human stops, diff size, and the blinded judge's rubric scores, and results are reported per case and pooled. [paraphrase]
- **R4:** For arm (c), machinery versus task work is broken out by the preregistered attribution rule, and spans the rule cannot place are reported as unattributed. [paraphrase]
- **R5:** Stage 2 reports, for each ablated artifact (feature map, clawpatch map, `STRATEGY.md`) on its preregistered cases, the per-task effect with and without it and its one-time production cost, with the break-even task count. [user]
- **R6:** The harness runs arm (c) from a frozen snapshot of a tagged flow-next release in per-draw throwaway clones and configuration directories, so flow-next development continues during the study. [user]
- **R8:** Case selection is its own step before preregistration. Each candidate case is scored against written criteria: a realistic task of its shape (simple bug, hard bug, small feature, large feature, hill climb); a known-good reference outcome and hidden acceptance tests derived from it; a starting state that can be reproduced exactly; little chance the fix is memorised (recent or private history preferred); and a result that can separate the arms (not trivially solved by both, not impossible for both, checked in harness validation). The chosen cases, the rejected candidates and the reasons are recorded. [user]
- **R9:** Harness validation runs before any study draw: pilot sessions in both arms on a throwaway case confirm isolation (fresh clone and configuration per draw, frozen plugin, no leakage between draws), complete logging of turns, tokens, wall time and human attention, the simulated person's behaviour (answers from its brief, never leaks the hidden tests, follows the follow-up policy), the judge's calibration against known-good and known-bad outcomes, and the run-to-run spread used to set draw counts. The first check is that the Agent SDK runs on the chosen subscription; if it does not, the harness switches to driving Claude Code through herdr before any other check. When the SDK is used, a few real Claude Code sessions driven through herdr with the same briefs are compared against SDK sessions to confirm the SDK runs behave like real usage. Study draws start only when every check passes; failures are fixed and rechecked. [user]
- **R10:** Every draw is a multi-turn session with the simulated person, and the verdict reports human attention per arm (turns, questions, corrections, words) beside agent cost and wall time. [user]
- **R7:** The verdict states, per case and pooled, where flow-next is better, equal or worse than vanilla on outcome quality, wall-clock, cost and verification, names the largest measured sources of flow-next overhead as optimisation targets, and keeps every draw including failures in the record; public text carries only conclusions the verdict supports. [paraphrase]

## Boundaries

- Evaluation only: no flow-next product change is made in this spec; improvements it suggests become their own specs. [paraphrase]
- Study data, logs, the preregistration and scripts stay in the private agent-evals repository. [user]
- No new benchmark framework: the harness reuses agent-evals' existing evalkit and fixture patterns. [paraphrase]

## Decision Context

### Motivation

"flow-next:flow --auto vs vanilla claude code with 0 skills"; "llm-judge for outcomes and the soft questions, concreate measurement for metrics"; "pretty long running, so would want to be able to work on flow-next in parallel". [user] "picking the things we test against, the bug, the feature etc will be critical"; "we need to really test the harness first, also it can't be 100 claude -p calls, we need a way to simulate people working inside of claude code". [user] "we can use herdr and drive claude code instead of the agent sdk perhaps, only if agent sdk doesnt work with our sub". [user] The five cases cover the router's main shapes without the cost of every route; the ablations answer what each artifact buys rather than assuming it. [paraphrase] Supersedes this spec's earlier scope (defect tasks only, located versus not-located, on one fixture app), which becomes the feature-map ablation inside stage 2. [paraphrase]


## Picking this up (for a fresh agent)

**Status.** Not ready and not a flow-next build task. This study runs by hand in the private agent-evals repository (`~/work/agent-evals`); do not run it through `/flow-next:work` or `flow --auto` in this repository, and change nothing in flow-next itself. Follow agent-evals `METHODOLOGY.md` and reuse `lib/evalkit.py`. Put everything under `studies/flow-vs-vanilla-2026-09/` on a study branch there.

**Order of work.**

1. Build the harness (Claude Agent SDK sessions, simulated person, logging, judge), then run the R9 validation on a throwaway case until every check passes.
2. Case selection (R8): a candidate shortlist per slot, scored against the R8 criteria, goes to the maintainer; the maintainer confirms the five cases before any preparation or preregistration. Record rejected candidates and reasons.
3. Prepare each chosen repository for arm (c) and measure the preparation cost.
4. Write and commit the preregistration (R1), including the simulated person's briefs, the hidden tests, the judge rubric and the decision bars.
5. Stage 1 draws, then stage 2 leave-one-out ablations, then the verdict (R7).

**Harness facts already validated (2026-09-28, Claude Code 2.1.280, `claude-agent-sdk` for Python via `uv run --with claude-agent-sdk`).**

- The Agent SDK runs on the maintainer's Claude subscription with no API key: remove `ANTHROPIC_API_KEY` from the environment, and the init message reports `apiKeySource: none`. Herdr-driven Claude Code is only needed for the realism comparison in R9, not as a fallback.
- Isolation per draw: a fresh temporary directory as `CLAUDE_CONFIG_DIR` holding only a copy of the chosen subscription's `.credentials.json` (currently the cl2 account at `~/.claude-instances/sub2-cli/.credentials.json`, which has the most usage left; never the default `~/.claude` account unless the maintainer says so), passed through `ClaudeAgentOptions(env=...)`; `setting_sources=[]`; the working directory is a throwaway clone. With this, the session sees no user instructions, none of the maintainer's installed plugins and no MCP servers. Delete both temporary directories after the draw.
- Vanilla arm: `plugins=[]` and `disallowed_tools=["Skill"]`, so no skill can be invoked. Claude Code's own built-in plugins (`agents-md`, `telemetry`) still load in both arms; that is expected and fine (`agents-md` reads the target repository's own `AGENTS.md`, identical in both arms).
- Flow-next arm: `plugins=[{"type": "local", "path": "<frozen snapshot of plugins/flow-next at a release tag>"}]`, Skill tool allowed. Claude Code's built-in skills stay available in this arm; that is fine. Log every Skill call in both arms.
- Simulated person: a `can_use_tool` callback intercepts `AskUserQuestion`, generates the answer from the case's hidden brief, and returns `PermissionResultAllow(updated_input={**input, "answers": {question_text: answer}})`; all other tools are allowed as usual. Follow-up turns (review and pushback) go through `ClaudeSDKClient.query` on the same client.
- Cost and usage come from the SDK's `ResultMessage` (`total_cost_usd`, usage) and the stream; the simulator's and judge's own model use is logged separately and excluded from the arms' cost.

**Decided.** The implementing model is Opus 5.5 in both arms. The judge is a different model family (gpt-6-astra through the codex CLI unless the preregistration says otherwise) and never sees which arm produced an output. Draws run on whichever subscription has usage left. The verdict and any public claim follow R7.

**Still open, decided in the preregistration.** The five cases (from the shortlist), draw counts (from the R9 run-to-run spread), the follow-up limit for the simulated person, and the decision bars.

## Strategy Alignment

STRATEGY.md lists idea-to-merge wall-clock as a key metric worth measuring; "Remember the bitter lesson" asks that machinery be evaluated against its absence with preregistered bars, and arm (a) is that absence for flow-next as a whole.

## Strategy Conflicts

None found.
