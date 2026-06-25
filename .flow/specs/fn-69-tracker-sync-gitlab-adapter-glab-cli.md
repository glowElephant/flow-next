# fn-69 tracker-sync GitLab adapter — `glab` CLI + token transport

## Goal & Context
<!-- scope: business -->

tracker-sync projects a flow spec to a tracker issue and reconciles two-way. It ships **Linear** (MCP → GraphQL ladder) and **GitHub** (`gh` CLI) adapters today; **GitLab has none**. Companies on GitLab — a large share of self-managed and EU/regulated shops — currently cannot mirror flow specs to their tracker, and `/flow-next:pilot` backlog mode (fn-68) cannot surface its async gap-questions to a GitLab issue.

This spec adds a **GitLab adapter** implementing tracker-sync's normalized transport interface, modelled directly on the GitHub adapter: a single CLI rung (`glab`) plus a token fallback, reduced-fidelity status mapping, and a no-op rung when nothing is reachable. **Zero special setup on the company's side** — it prefers the `glab` session a developer is already logged into (or a CI token already present), never a flow-next-specific provisioning step.

## Architecture & Data Models
<!-- scope: technical -->

- **New adapter** behind the existing `references/adapter-interface.md` contract — implements `fetchIssue` / `writeIssue` / `listComments` / `postComment` / `readStatus` / `setStatus`, mapping the GitLab wire shape to/from the normalized `issue` / `comment` / `status` structs. Reconcile, body-merge, status-sync, comments-sync are untouched (transport-blind).
- **Transport: `glab` CLI primary, REST token fallback** — mirrors the GitHub adapter's single-rung + no-op shape (`references/github.md`). Detect `glab auth status` exit 0; else a `GITLAB_TOKEN` / `CI_JOB_TOKEN` env token against the GitLab REST API (`/api/v4`); else **no-op rung** (receipt note, never a crash). Self-managed GitLab hosts honored via `glab`'s configured host or `CI_SERVER_URL`.
- **Issue grain:** one flow spec ↔ one GitLab issue (the issue IID/global-id is the durable dedupe key for `sync set-tracker-id`). Back-reference written as a `flow::<id>` scoped label + body marker, mirroring the GitHub adapter's label convention.
- **Status fidelity is reduced** (like GitHub): GitLab issues are open/closed with optional board labels, not a rich workflow. Map flow ready/done to open/closed + a configurable label set (`tracker.readyState` resolves to a GitLab label or the open/closed pair). Record reduced fidelity on the receipt.
- **Discovery-ceremony probe extension:** add a `glab authenticated` signal (and `GITLAB_TOKEN` present) to the ceremony's probe table so the bridge auto-detects GitLab the same way it detects `gh`.
- **Reference doc:** `references/gitlab.md`, authored against `references/github.md` as the template; canonical Claude tool names; `sync-codex.sh` regenerates the Codex mirror.

## API Contracts
<!-- scope: technical -->

- **Detection signal (ceremony):** `glab auth status` exit 0 ⇒ GitLab transport available; or `GITLAB_TOKEN`/`CI_JOB_TOKEN` set ⇒ headless REST transport. Surface present AND absent in the ceremony output.
- **Adapter methods:** exact `adapter-interface.md` signatures; normalized structs only at the boundary.
- **Config:** `tracker.type: gitlab`; `tracker.perTracker` carries `projectPath` (group/project) and `host` (for self-managed); `tracker.readyState` maps to a GitLab label or open/closed.
- **Identity:** `sync set-tracker-id <spec> <issue-iid> --identifier <project>#<iid> --url <web_url>`; bare `#<iid>` resolves via the widened resolver.

## Edge Cases & Constraints
<!-- scope: technical -->

- **No transport reachable** → no-op rung + receipt note; never crash (matches GitHub/Linear no-op behavior).
- **Self-managed hosts** — never assume gitlab.com; resolve host from `glab` config or `CI_SERVER_URL`.
- **Reduced status fidelity** — surface it on the receipt; do not fabricate a rich workflow GitLab doesn't have.
- **Rate limits / transient REST errors** — bounded retry, then defer + receipt; never block (R11/R12 of tracker-sync).
- **Label-as-status collisions** — if the configured ready label is absent on the project, fall back to open/closed and note it.
- **Cross-platform:** canonical Claude names; `sync-codex.sh` regenerates cleanly.

## Acceptance Criteria
<!-- scope: both -->

- **R1:** A GitLab adapter implements every `adapter-interface.md` method, mapping GitLab wire ↔ normalized structs; reconcile/body-merge/status-sync are unchanged.
- **R2:** Transport ladder: `glab` CLI primary → `GITLAB_TOKEN`/`CI_JOB_TOKEN` REST fallback → no-op rung (receipt note, no crash). Self-managed hosts honored.
- **R3:** The discovery ceremony detects GitLab (`glab` auth or token) and surfaces present/absent alongside the existing signals.
- **R4:** One flow spec ↔ one GitLab issue; durable dedupe key stored via `sync set-tracker-id`; back-reference label + body marker written.
- **R5:** Status maps flow ready/done ↔ GitLab open/closed (+ optional label), reduced fidelity recorded on the receipt; `tracker.readyState` honored.
- **R6:** `references/gitlab.md` authored from the GitHub template; `tracker.type: gitlab` config documented; Codex mirror regenerated; docs + flow-next.dev updated; version bumped.
- **R7:** Zero special setup — works from an existing `glab` session or a CI token with no flow-next-specific provisioning; spec-first floor when neither present.

## Boundaries
<!-- scope: business -->

- **Adapter only** — no change to reconcile, body-merge, status who-wins, or comment dedup (all transport-blind already).
- **Not a new sync skill** — plugs into `/flow-next:tracker-sync`.
- **Reduced-fidelity status is acceptable** — GitLab has no rich workflow; do not invent one.
- **GitHub/Linear unaffected** — additive adapter.

## Decision Context
<!-- scope: both -->

### Motivation
GitLab is a major tracker with no flow-next adapter; companies on it are locked out of tracker projection and of fn-68 backlog mode's gap-surfacing. The GitHub adapter already proves the single-CLI-rung + reduced-status shape; GitLab is the same shape with `glab` instead of `gh`, so the cost is low and the architecture is settled.

### Implementation Tradeoffs
- **Model on the GitHub adapter, not the Linear ladder:** GitLab, like GitHub, is a git host with a thin issue workflow — the `gh`/single-rung + reduced-status template fits far better than Linear's MCP-first rich-workflow ladder.
- **`glab` primary over raw REST:** reuses the auth the developer already has (zero setup); REST token is the headless/CI fallback.
- **Reduced status fidelity accepted:** matches GitHub; honest receipts over fabricated workflow states.

## Strategy Alignment
- **Cross-platform parity** track — broadens tracker coverage with canonical names + sync-codex mirror.
- Unblocks **fn-68** (pilot backlog mode) GitLab coverage and every other tracker-sync projection (capture/interview/make-pr) for GitLab shops.

## Conversation Evidence
> user: "make sure we can handle github, gitlab, jira, linear in an easy and way that will work for companies and doesnt require any special setup on their end"
> user: "in general we should build this for linear/github first as we already have those integrations" (⇒ GitLab is a follow-on after Linear+GitHub)

Reference templates: `references/github.md` (single-rung `gh` transport, reduced-fidelity status) and `references/adapter-interface.md` (normalized contract).
