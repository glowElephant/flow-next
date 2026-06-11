# Optional HTML artifact mode: spec & PR render lenses

## Conversation Evidence

> user (turn 1): "i am considering html artifacts for the SPEC and the PR, look at ALL of this research"
> user (turn 1): "lavish looks especially interesting for the spec html artifact, not sure if we can wrap, don't really like more dependencies, but consider it"
> user (turn 1): "this would be an optional html mode, when activated (via setup/config) the corresponding skills can load a progressively disclosed file for generating plans and prs as beautifully rendered html pages that provide MAX usability in terms of legibility, diagrams, everything great. this will stop us bogging down flow-next for users that want to stick to default markdown for everything."
> user (turn 1): "in addition markdown/tracker-sync will 100% stay the source of truth, all html outputs, even when activated are addition artifacts to assist the human, both pos/pms/devs etc, ofc the markdown spec and make-pr stuff can link to these new html artifacts (not sure how to show them on github though)"
> user (turn 1): "The goal of all of this and this fits our strategy is to make the human touchpoints (spec review, plan review, diff review as efficient and DX friendly as possible)"
> user (turn 1): "this would result in a new mainline feature of flow-next to be surfaced as such on the flow-next.dev landing page and in the relevant sections such as the SPECS section, TEAMS, REVIEW etc and a new page something like SPECS/visual aids, review/visual aids or something better."
> user (turn 1): "I also thing that some of the main STRATEGY pages on flow-next.dev need a full pass, ie. the new autonomous stuff is missing, and a general perfect description of the entire pipleine (unless i missed it), there should be a page STRATEGY/pipeline perhaps?"
> user (turn 1): "before writing this spec or capturing it etc, lets decide on a path and smoke test it by using previous specs/prs and generating such artifacts to see how useful it all is, i'm optimistic"
> user (turn 2): "install lavish-axi for me (obviously we would document this and mention it during setup if the user opts in to html mode)"
> user (turn 3): "also the next release version will be 2.0.0 to symbolise the large leaps we've made"
> user (turn 3): "this may need updated too if we're updating the pipeline diagrams etc, as an aside for this spec" [re: flow-next.dev Introduction page pipeline narrative]
> user (turn 3): "does it make sense to only do the spec/plan via lavish, i mean the agentic editing of a PR doesnt make sense does it?"
> user (turn 3): "will we offer only the spec or the spec + plan (tasks), i tend to now think of the plan as implementation detail but could be useful for users not doing autonomous work? i think it would be the same pathway, we would just generate the html using information from the spec and/or the spec + tasks probably?"
> user (turn 4): "the lavish editor is definitely a large boon that we should document as optional but useful for specs, so lavish is a go as an optional dep"
> user (turn 4): "how does it connect to the agent, will this work if the claude code/codex session is no longer running etc"
> [context: smoke test 2026-06-12 — two artifacts generated from real history (fn-52 spec visualizer with interactive task DAG + R-ID matrix; PR #171 review instrument with churn map + review checklist), verified rendering + Lavish annotate-loop round-trip. Research: Anthropic "unreasonable effectiveness of HTML", Kun Chen 40-PRs/day artifact-review workflow, diff-derived-PR-body consensus, self-contained single-file contract.]

## Goal & Context
<!-- scope: business -->
<!-- Source-tag breakdown: 75% [user] / 25% [paraphrase] -->

flow-next's human touchpoints — spec review, plan review, diff review — are markdown-only today. This feature adds an **optional HTML artifact mode**: when activated via setup/config, the corresponding skills load a progressively disclosed reference file and generate beautifully rendered, self-contained HTML pages alongside their markdown output — maximum usability in legibility, diagrams, and review ergonomics, for POs/PMs/devs alike. Markdown (and tracker-sync) stays 100% the source of truth; every HTML output is an *additional* regenerable artifact — a **render lens**, never the record. Users who stick with default markdown see zero change — the mode existing must not bog down flow-next for them. Goal (strategy-aligned): make the human touchpoints as efficient and DX-friendly as possible. Validated by smoke test on real history before speccing — both artifact shapes (spec visualizer, PR review instrument) proved materially better review surfaces than their markdown sources.

## Architecture & Data Models
<!-- scope: technical -->

- **Activation:** an artifacts/html config block in `.flow/` config, written by the setup ceremony; OFF by default. When off, skills load nothing extra (zero token cost, zero behavior change).
- **Progressive disclosure:** one shared reference file (design system + generation rules + per-artifact-type guidance) loaded by participating skills only when the mode is active. Carries an explicit anti-slop design contract (own palette/typography rules, no CDN fonts, no external requests).
- **Spec artifact — one pathway, state-dependent rendering:** generated from the spec (and tasks when present). Pre-plan → spec-only view (thesis, acceptance criteria, boundaries, decision context) for business review; post-plan → same generator adds the plan layer (task dependency DAG with critical path, R-ID→task coverage matrix). The plan is implementation detail but stays valuable for non-autonomous users — free, since it is the same pathway reading the same flowctl export.
- **PR artifact — read-only review instrument:** derived from the diff (never commit messages), verified against the spec's R-ID export before publishing; churn grouped by review intent (canonical vs generated-mirror vs mechanical), R-ID→evidence table, where-to-look checklist.
- **Lavish integration (optional, detect-best-available):** `lavish-axi` is never required. When on PATH and the session is interactive, spec/plan artifacts open as a Lavish session — annotations map to edits of the markdown source of truth, then the lens regenerates. Architecture verified: standalone local server, state in `~/.lavish-axi/state.json`, agent side is pull-only (`lavish-axi poll` CLI subprocess, no MCP) — feedback is session-spanning and survives agent death; any later session drains the queue. Autonomous/Ralph contexts never poll (never block on a human).
- Canonical skill files use Claude-native tool names; the sync script handles the Codex mirror, per repo convention.

## Edge Cases & Constraints
<!-- scope: technical -->

- **GitHub cannot render committed HTML** and rejects .html PR attachments — markdown spec/PR bodies link to the artifacts with local-open guidance (optional third-party raw-preview link); do not over-engineer hosting. [user: "not sure how to show them on github though"]
- **Self-contained or nothing:** zero external requests (fonts included) — the artifact must open identically from disk, in Lavish, in CI archives, and printed. Lavish's portability guarantee depends on this.
- **Lavish absence/death is invisible:** no lavish on PATH → plain open; server idle-stop → artifact still renders as a static page. Never a hard dependency, never an error path.
- **Autonomous discipline:** pilot/Ralph runs may generate artifacts but never open polls; at most a receipt note that a session has pending prompts.
- **Stale-lens risk:** artifacts regenerate at their lifecycle touchpoints; an artifact is never parsed back as state (one-way derivation).

## Acceptance Criteria
<!-- scope: both -->

- **R1:** HTML artifact mode is opt-in via setup/config, OFF by default; with the mode off, every skill behaves byte-identically to today (no disclosure file loaded, no artifacts generated). [user]
- **R2:** When active, participating skills load a progressively disclosed shared reference file carrying the generation rules and an explicit anti-slop design system (own typography/palette; no CDN fonts; no purple-gradient defaults). [user]/[paraphrase]
- **R3:** Markdown and tracker-sync remain the sole source of truth; every HTML output is an additional regenerable artifact, never parsed back as state. [user]
- **R4:** Spec artifact uses ONE generation pathway with state-dependent rendering: spec-only before tasks exist; spec+plan layer (task DAG, R-ID coverage matrix) once tasks exist. [user]/[paraphrase]
- **R5:** PR artifact is diff-derived (never from commit messages) and verified against the spec's R-ID export before publishing; it is a read-only review instrument. [user]/[paraphrase]
- **R6:** All artifacts are self-contained single-file HTML — inline CSS/JS, zero external requests, print-friendly. [paraphrase]
- **R7:** Lavish (`lavish-axi`) ships as an optional dependency: detected on PATH, never required; when present + interactive, spec/plan artifacts open as Lavish sessions and annotation feedback maps to markdown-source edits followed by lens regeneration. [user]
- **R8:** The PR artifact never enters the annotate-edit loop; autonomous/Ralph contexts never run a Lavish poll. [user]/[paraphrase]
- **R9:** The setup ceremony, when the user opts into HTML mode, documents and offers the lavish-axi install (including the session-spanning feedback model and idle-stop/resume behavior). [user]
- **R10:** Markdown spec and make-pr output link to their HTML artifacts; the GitHub display limitation is documented with local-open guidance. [user]
- **R11:** Artifacts live in a dedicated regenerable location under `.flow/`, commit-or-gitignore per project. [inferred]
- **R12:** flow-next.dev surfaces this as a mainline feature: landing page, SPECS/TEAMS/REVIEW sections, a new visual-aids page (both navbars), changelog entry, build gate green. [user]
- **R13:** flow-next.dev strategy/pipeline pass ships in the same workstream: a pipeline page (e.g. STRATEGY/pipeline), the missing autonomy-suite content, and the Introduction page's pipeline narrative updated to match. [user]
- **R14:** Released as **2.0.0** — repo docs, Codex mirror regen, manifest/version lockstep, CHANGELOG. [user]

## Boundaries
<!-- scope: business -->

- **Fully opt-in** — markdown-only users see zero new steps, zero new prerequisites, zero token overhead (preserves the zero-dep base contract). [user]
- HTML is NOT a storage format and never becomes one — no state lives in artifacts. [user]
- Lavish is NOT wrapped, bundled, or required — detect-on-PATH only (same shape as clawpatch//flow-next:map). [user]
- PR-artifact annotations → GitHub review comments / resolve-pr input: explicitly OUT of scope (plausible future increment). [paraphrase]
- Review-report artifacts (impl-review / plan-review / qa findings as HTML) are a later increment, not this spec. [inferred]
- The codex-apop delegation hardening idea is deliberately deferred behind this feature ("bigger bang for our buck"). [user]

## Strategy Alignment

- **Spec-driven team patterns** — directly serves the human-touchpoint efficiency thesis; gives POs/PMs a first-class review surface. [strategy:Spec-driven team patterns]
- **Ralph autonomous mode** — artifacts generate in loops but never block them; Lavish feedback is session-spanning, matching re-anchoring. [strategy:Ralph autonomous mode]
- **Cross-platform parity** — canonical Claude-native files, Codex mirror via the sync script. [strategy:Cross-platform parity]

## Decision Context
<!-- scope: both — conditionally substructured -->

### Motivation
Make spec review, plan review, and diff review as efficient and DX-friendly as possible — the human touchpoints are where flow-next's quality discipline meets actual people [user]. Research convergence (Anthropic's HTML-as-default push, the 40-PRs/day artifact-review workflow, the diff-derived PR-body consensus) plus a successful smoke test on real history (fn-52 spec, PR #171) justify a mainline feature, prioritized over the codex delegation hardening ("bigger bang for our buck") [user]. The leap is release-worthy: 2.0.0 [user].

### Implementation Tradeoffs
**Lavish: detect, don't wrap** [user: "lavish is a go as an optional dep"] — its portable-artifacts guarantee means plain self-contained HTML gets the annotate loop for free when present; wrapping would add a Node dependency to the zero-dep base for no gain. Verified pull-only architecture (CLI long-poll, global state file, no MCP) keeps coupling at zero and makes feedback session-spanning. **One artifact pathway, not two** [user] — spec-vs-plan is a rendering question (what state exists), not a product question; avoids a config axis. **Annotate loop scoped to spec/plan** [user: "agentic editing of a PR doesnt make sense"] — a PR artifact derives from an immutable diff; GitHub already owns review comments; duplicating that surface creates a sync problem.

## Requirement coverage

| Req | Task(s) |
|-----|---------|
| R1–R14 | TBD — populate via /flow-next:plan |
