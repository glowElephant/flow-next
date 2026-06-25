# fn-67 /flow-next:guide — opinionated router over flow-next's skill flows

## Goal & Context
<!-- scope: business -->

flow-next ships ~28 skills. A user — especially a new adopter, or Gordon mid-session — cannot hold the whole map in their head: *which* skill, in *what* order, with which flags, and where the non-obvious branches and guardrails are. Claude Code already surfaces individual skill descriptions and will often propose "run X next", so a thin "which skill is next?" router adds little. The gap is **judgment**: the canonical *paths* through flow-next (the flows), the branch points and when to take each, the sequencing rules, and the hard-won "do it this way / never do that" opinions that today live scattered across `CLAUDE.md`, `docs/`, and tribal memory.

`/flow-next:guide` is a **user-invoked, opinionated flow map**. Inspired by Matt Pocock's `/ask-matt` router (`mattpocock/skills`), but explicitly NOT a skill-name autocomplete: it encodes the *right way* to move from idea → shipped PR (and the maintenance / autonomous / review side-flows), co-authored with Gordon so the opinions are real and current. You type `/flow-next:guide` when you know the destination but not the route — it tells you the route, the next concrete command, and the trap to avoid — and it can hand you straight off into the right skill.

The reference model is `~/repos/mattpocock-skills/skills/engineering/ask-matt/SKILL.md` — a flows-not-list structure (main flow, on-ramps, standalone, crossing-sessions, precondition) with opinions baked into every branch ("keep steps 1–3 in one context window", "don't triage agent-ready issues"). We want flow-next's equivalent, grounded in flow-next's real skills and conventions.

## Architecture & Data Models
<!-- scope: technical -->

A single SKILL.md at `plugins/flow-next/skills/flow-next-guide/SKILL.md`, registered as `/flow-next:guide`. **User-invoked**: `disable-model-invocation: true` in frontmatter; the `description` is a human-facing one-liner (no trigger list). It is mostly **reference content** (an opinionated map), not a multi-step procedure — but it MAY end an interaction by dispatching the user into the chosen skill (prose `/flow-next:<skill>` invocation, the platform's normal skill hand-off), and MAY ask a clarifying question to disambiguate the user's situation before recommending a route.

The map is organized as **flows**, mirroring ask-matt's spine but populated with flow-next reality:

- **The main flow — idea → shipped PR.** The spine most work travels:
  `prospect`/`strategy` (upstream framing, optional) → **author a spec** (create directly per CLAUDE.md, or `/flow-next:capture` from a conversation) → `/flow-next:interview` (deep Q&A refine, `--scope=business|technical|both`) → `/flow-next:plan` (break spec into tasks) → `/flow-next:plan-review` (Carmack-level gate) → `/flow-next:work` (implement, task-by-task) → `/flow-next:make-pr` (cognitive-aid PR body) → `/flow-next:resolve-pr` (review feedback) → `/flow-next:land` (CI-fix → merge → release; opt-in).
- **Autonomous drivers (a parallel rail over the same skills).** `/flow-next:pilot` (host-driven single-tick conductor, `/loop`- or `/goal`-driven) and Ralph (`/flow-next:ralph-init`, external shell loop) — when to reach for each vs driving manually; the readiness gate as the human control point.
- **Maintenance / health.** `/flow-next:prime` (agent-readiness assessment), `/flow-next:map` (semantic feature index), `/flow-next:audit` + `/flow-next:memory-migrate` (memory hygiene), `/flow-next:strategy` (STRATEGY.md), `/flow-next:setup` / `/flow-next:uninstall`.
- **Review / QA side-flows.** `/flow-next:impl-review`, `/flow-next:spec-completion-review`, `/flow-next:qa` (live-app), and how they slot into the main flow.
- **Tracker bridge.** `/flow-next:tracker-sync` (Linear/GitHub projection) — distinct from `/flow-next:sync` (plan-sync); when and why.

**Sourcing discipline (the part that keeps it true):** the opinions are not invented at author time — they are extracted from the live repo (`CLAUDE.md`, `STRATEGY.md`, `GLOSSARY.md`, `docs/`, each skill's SKILL.md) and **confirmed with Gordon** during authoring. The skill body cross-references the canonical docs rather than duplicating them, so it degrades gracefully as the docs evolve.

## API Contracts
<!-- scope: technical -->

- **Invocation:** `/flow-next:guide` (user-only). Optional free-text argument describing the situation ("I have a rough idea and a codebase", "PR has review comments", "memory feels stale") → the guide recommends the route for that situation instead of printing the whole map.
- **Output:** an opinionated recommendation — the relevant flow, the **single next concrete command** to run, and the key trap to avoid — plus an offer to hand off into that skill. Bare invocation (no argument) prints the full flow map.
- **Frontmatter:** `name: flow-next-guide`, one-line human-facing `description`, `disable-model-invocation: true`.
- **Cross-platform:** canonical Claude tool names; `scripts/sync-codex.sh` regenerates the Codex mirror (`AskUserQuestion` → numbered prompt; any `Task` → `spawn_agent`). Registered in marketplace/plugin manifests and the docs-site navigation (both navbars — see CLAUDE.md "Navigation — TWO sources").

## Edge Cases & Constraints
<!-- scope: technical -->

- **Not an autocomplete.** If the recommendation collapses to "run the skill whose name matches your words", it has failed its purpose — every route must carry at least one opinion/branch/guardrail the bare skill description does not already give. This is the acceptance bar, not a nice-to-have.
- **`disable-model-invocation` cross-platform.** Claude Code honors it (user-only). If a target platform (Codex/Droid) does not, the skill stays *reachable* and merely also becomes model-invokable — harmless for a read-only guide. Do not rely on the flag for correctness; rely on it for token economy on Claude.
- **Staleness risk.** A hand-maintained map drifts when skills are added/renamed/removed. Mitigations: (a) cross-reference canonical docs instead of duplicating; (b) `agent_docs/adding-skills.md` gains a checklist line "update /flow-next:guide if the skill changes a flow"; (c) the map names flows and decisions (slow-changing) over exhaustive per-skill prose (fast-changing).
- **No new flowctl plumbing.** Pure skill content; no Python, no state, no receipts. (Architecture rule: host agent is the intelligence; this is reference + light dispatch.)
- **Self-reference / loop.** The guide never recommends itself; it never dispatches another user-invoked skill that would dead-end (it points the human at what to *type*, consistent with the user-invoked → user-invoked reachability limit).
- **Opinion provenance.** Every baked-in opinion must trace to a confirmed source (a CLAUDE.md rule, a shipped convention like "Linear Done reserved for merged PRs" (fn-66), or an explicit Gordon decision during authoring) — no fabricated best-practices.

## Acceptance Criteria
<!-- scope: both -->

- **R1:** A new user-invoked skill `/flow-next:guide` exists at `plugins/flow-next/skills/flow-next-guide/SKILL.md` with `disable-model-invocation: true` and a one-line human-facing `description` (no trigger list).
- **R2:** Bare `/flow-next:guide` prints an opinionated flow map organized as flows (main idea→PR flow, autonomous drivers, maintenance/health, review/QA, tracker bridge) — not a flat alphabetical skill list.
- **R3:** Given a free-text situation argument, the guide recommends the matching flow, the single next concrete command, and the key trap to avoid, and offers to hand off into that skill.
- **R4:** Every recommended route carries at least one opinion, branch condition, sequencing rule, or guardrail beyond what the target skill's own description states (the "not an autocomplete" bar).
- **R5:** Baked-in opinions are sourced from the live repo (`CLAUDE.md` / `STRATEGY.md` / docs / shipped conventions) or an explicit Gordon decision — none fabricated; the body cross-references canonical docs rather than duplicating them.
- **R6:** The skill covers, at minimum, every currently shipped `/flow-next:*` user-facing command, each placed in exactly one flow with its role stated.
- **R7:** Cross-platform parity — canonical Claude names; `sync-codex.sh` regenerates the Codex mirror cleanly; the skill is registered in plugin/marketplace manifests.
- **R8:** Docs + flow-next.dev updated — skill page, BOTH navbars (`DocsRail`/`site.ts` + Starlight `astro.config.mjs`), changelog entry, and the command reference; plugin version bumped per the release process.
- **R9:** `agent_docs/adding-skills.md` gains a step reminding authors to update `/flow-next:guide` when a new/renamed/removed skill changes a flow (staleness mitigation).

## Boundaries
<!-- scope: business -->

- **Read + route, not execute.** The guide recommends and hands off; it does not run plans, edit code, touch git, or mutate flow state. (It may dispatch the user into another skill, which then does its own thing.)
- **No flowctl changes.** Zero new Python/CLI surface; pure skill content.
- **Not the docs site.** It complements, never replaces, the docs at flow-next.dev — it is the in-session "where do I go from here", cross-linking out for depth.
- **Token-reduction refactor is OUT of scope** (the `disable-model-invocation` sweep across the other 27 skills). This spec sets the flag on the *guide skill itself* only; the repo-wide invocation/description refactor is a separate, deliberately-deferred decision (reported 2026-06-23, not yet specced).
- **Personal-brand naming rejected.** `/ask-gordon` (the `/ask-matt` analogue) is not used — flow-next is a published plugin installed by non-Gordon users; the neutral, self-describing `/flow-next:guide` wins.

## Decision Context
<!-- scope: both — conditionally substructured -->

### Motivation
<!-- scope: business -->

Triggered by Matt Pocock's `/ask-matt` router landing in `mattpocock/skills` (2026-06). The insight that transfers: as user-invoked skills multiply past what a human can remember, the cure is a **router skill that names the others and when to reach for each**. flow-next is past that threshold (~28 skills). But Gordon's explicit steer sharpened the goal: Claude Code *already* proposes the next skill most of the time, so a bare "which skill?" router is low-value. The value is **opinionated, co-authored flow guidance** — the routes, branches, sequencing, and guardrails that are not visible in any single skill description. The guide is where flow-next's tribal knowledge becomes navigable in-session.

### Implementation Tradeoffs
<!-- scope: technical -->

- **User-invoked over model-invoked:** a guide the model auto-fires would be noise; this is a thing a human reaches for when lost. `disable-model-invocation: true` also keeps its description a cheap human-facing one-liner (the same economy Matt measured at ~63% off description cost across his user-invoked set) — a small down-payment on the larger token-reduction idea that this spec deliberately leaves unspecced.
- **Opinionated map over generated index:** an auto-generated skill index would always be current but never *opinionated* — and opinion is the whole point. We accept hand-maintenance + staleness risk (mitigated by doc cross-refs, an `adding-skills.md` checklist line, and naming slow-changing flows over fast-changing per-skill prose) in exchange for real judgment.
- **Reference-heavy, light dispatch:** mostly a read; the only "action" is handing the user into the chosen skill. No flowctl plumbing — consistent with the repo's "host agent is the intelligence" architecture rule.
- **Rejected — fold in the token-reduction sweep:** keeping the repo-wide `disable-model-invocation` refactor out keeps this spec shippable on its own and lets the larger refactor be evaluated on its own merits (Gordon chose "report only" on 2026-06-23).

## Strategy Alignment
<!-- STRATEGY.md cross-check at author time -->

- Lowers the adoption / recall cost of the flow-next skill suite — supports the "spec-driven SDLC that teams actually run" thrust by making the canonical flows discoverable in-session.
- **Cross-platform parity** track — canonical Claude names + sync-codex mirror.
- Reinforces *"the host agent IS the intelligence"* — no new flowctl engine; the guide is curated reference + judgment.

## Conversation Evidence

> user: "New /ask-matt skill - A router that guides you through the entire skill system … good idea for us too, a /ask-gordon skill, add a spec to flow/linear"
> user (on naming): "lets do guide"
> user (the load-bearing steer): "it should really have opinionated answers that we work together on, not just 'which skill next' claude code already proposes them most of the time"
> user (on token-reduction): "Just report, no spec yet"

Reference implementation reviewed: `mattpocock/skills` `skills/engineering/ask-matt/SKILL.md` (flows-not-list structure; opinions baked into branches) and `docs/invocation.md` (user-invoked vs model-invoked; description economy).
