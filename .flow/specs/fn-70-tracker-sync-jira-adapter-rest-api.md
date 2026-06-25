# fn-70 tracker-sync Jira adapter — REST API token-first (MCP secondary)

## Goal & Context
<!-- scope: business -->

tracker-sync ships **Linear** and **GitHub** adapters; **Jira is detected but deliberately not offered**. Enterprise portfolio companies overwhelmingly run Jira, and they want flow specs mirrored there — but **portco feedback is that the Atlassian MCP is too limited for this use**; the path that works in their environments and CI is the **Jira REST API with a token**. This spec adds a Jira adapter whose **primary transport is the REST API token** (Atlassian MCP a secondary rung), implementing tracker-sync's normalized interface so `/flow-next:pilot` backlog mode (fn-68) and every other projection can target Jira with no special setup beyond credentials the company already issues.

## Architecture & Data Models
<!-- scope: technical -->

- **New adapter** behind `references/adapter-interface.md` — implements `fetchIssue` / `writeIssue` / `listComments` / `postComment` / `readStatus` / `setStatus`, mapping the Jira wire shape to/from the normalized structs. Reconcile / body-merge / status-sync / comments-sync untouched.
- **Transport: REST API token primary, MCP secondary** — the **inverse of Linear's MCP-first ladder**. Rungs: (1) **Jira Cloud/Data-Center REST v3** with basic auth `email:API_TOKEN` (Cloud) or a Personal Access Token bearer (Data Center) from env (`JIRA_BASE_URL` + `JIRA_EMAIL` + `JIRA_API_TOKEN`, or `JIRA_PAT`); (2) **Atlassian MCP** if registered AND sufficient (treated as best-effort, not relied on — portco-reported limitations); (3) **no-op rung** (receipt note, never crash).
- **ADF body translation** — Jira descriptions/comments use Atlassian Document Format (ADF), not Markdown. The adapter translates normalized Markdown ↔ ADF at the boundary (a Jira-specific concern; reconcile still sees only normalized text). Keep the translation in the adapter, lossy-but-faithful, with a round-trip-safe subset documented.
- **Status fidelity — workflow-aware:** Jira has rich, per-project configurable workflows. `tracker.readyState` maps to a Jira status/category; transitions go through the Jira transition API (you cannot set an arbitrary status directly). The adapter resolves the transition id for the target status and applies it; unknown/unreachable transitions defer + receipt (never force).
- **Issue grain:** one flow spec ↔ one Jira issue (issue key e.g. `PROJ-123` is the durable id). Back-reference via a labeled marker + body anchor.
- **Discovery-ceremony probe extension:** add a Jira signal — `JIRA_BASE_URL`+token present (primary) or a `*.atlassian.net` host with MCP (secondary) — flipping today's "surface but don't offer" to "offer, API-first."
- **Reference doc:** `references/jira.md`, authored against `references/linear-ladder.md` for the ladder shape but **API-first**, with the ADF translation + transition-api status mapping documented.

## API Contracts
<!-- scope: technical -->

- **Detection (ceremony):** `JIRA_BASE_URL` + (`JIRA_EMAIL`+`JIRA_API_TOKEN` | `JIRA_PAT`) ⇒ REST transport (primary). `*.atlassian.net` host + registered Atlassian MCP ⇒ MCP transport (secondary). Surface present AND absent.
- **Auth:** Cloud = HTTP basic `email:API_TOKEN` over HTTPS; Data Center = `Authorization: Bearer <PAT>`. Never store credentials in flow state — read from env each run.
- **Adapter methods:** exact `adapter-interface.md` signatures; ADF↔Markdown only inside the adapter.
- **Config:** `tracker.type: jira`; `tracker.perTracker` carries `baseUrl`, `projectKey`, and a `statusMap` (flow ready/done → Jira status names/ids); `tracker.readyState` resolves through `statusMap`.
- **Status writes** go through the **transitions API** (resolve transition id for target status, POST transition), not a direct status set.
- **Identity:** `sync set-tracker-id <spec> <issue-key> --identifier PROJ-123 --url <browse-url>`; bare `proj-123` resolves via the widened resolver.

## Edge Cases & Constraints
<!-- scope: technical -->

- **MCP insufficiency is expected** — never hard-depend on the Atlassian MCP; the REST token is authoritative. If only MCP is present and it cannot perform a needed op, defer + receipt with a clear "enable REST token" note.
- **ADF round-trips are lossy** — document the supported Markdown subset; preserve unknown ADF nodes on write-back rather than dropping (no silent data loss in the human's description).
- **Transition gating** — a target status may be unreachable from the current status per the project workflow; resolve the legal transition, else defer + receipt (never force an illegal transition).
- **Cloud vs Data Center auth differ** — detect by base URL / token type; support both.
- **Rate limits / 401 / 403** — bounded retry; on auth failure, no-op + actionable receipt; never block.
- **No transport reachable** → no-op rung + receipt; spec-first floor still works.
- **Cross-platform:** canonical Claude names; `sync-codex.sh` regenerates cleanly.

## Acceptance Criteria
<!-- scope: both -->

- **R1:** A Jira adapter implements every `adapter-interface.md` method, mapping Jira wire (incl. ADF) ↔ normalized structs; reconcile/body-merge/status-sync unchanged.
- **R2:** Transport ladder is **REST-token primary** (Cloud basic `email:token`; Data Center PAT bearer) → Atlassian MCP secondary/best-effort → no-op rung. The adapter never hard-depends on the MCP.
- **R3:** Markdown ↔ ADF translation lives in the adapter, round-trip-safe over a documented subset, preserving unknown nodes on write-back (no silent loss).
- **R4:** Status writes go through the Jira transitions API via a configurable `statusMap`; `tracker.readyState` resolves through it; illegal/unreachable transitions defer + receipt, never force.
- **R5:** The discovery ceremony detects Jira API-first (env token) and offers it (replacing today's "surface but don't offer"); MCP detected as a secondary signal.
- **R6:** One flow spec ↔ one Jira issue; issue key stored via `sync set-tracker-id`; back-reference marker written; bare key resolves via the widened resolver.
- **R7:** `references/jira.md` authored (API-first ladder + ADF + transitions); `tracker.type: jira` + `baseUrl`/`projectKey`/`statusMap` config documented; Codex mirror regenerated; docs + flow-next.dev updated; version bumped.
- **R8:** Zero special setup beyond a standard Jira API token the company already issues — no OAuth app, webhook, or Atlassian Connect/Forge app required; spec-first floor when no token present.

## Boundaries
<!-- scope: business -->

- **Adapter only** — no reconcile/body-merge/status-sync changes (transport-blind).
- **API-first, MCP-optional** — explicitly does NOT rely on the Atlassian MCP (portco-reported limits); MCP is a bonus rung, never a requirement.
- **Not a new sync skill** — plugs into `/flow-next:tracker-sync`.
- **GitHub/Linear/GitLab unaffected** — additive adapter.
- **No Atlassian Connect/Forge app** — credentials are a plain API token, nothing to install on the company's Jira.

## Decision Context
<!-- scope: both -->

### Motivation
Enterprise portcos run Jira and want flow specs mirrored there, but the Atlassian MCP is too limited for the job per their feedback — the REST API token is the transport that actually works for them and in CI. tracker-sync's transport-blind interface means Jira is "just another adapter"; the only Jira-specific weight is ADF translation and the transitions-API status model.

### Implementation Tradeoffs
- **REST-token primary, MCP secondary — inverse of Linear:** Linear leads MCP-first because its MCP is rich and OAuth is handled; Jira's MCP is reportedly insufficient, so the API token leads and MCP is a best-effort bonus. The ladder pattern is the same; the rung order flips by tracker.
- **ADF translation in-adapter:** keeps reconcile transport-blind; the cost is a documented lossy subset + unknown-node preservation, accepted to avoid leaking ADF into the merge engine.
- **Transitions API over direct status set:** Jira forbids arbitrary status writes; resolving legal transitions is mandatory and means some target states are unreachable — handled by defer+receipt, never forcing.
- **Plain API token over Connect/Forge app:** the zero-setup promise — companies already issue API tokens; an installable app would be exactly the "special setup" we're avoiding.

## Strategy Alignment
- **Cross-platform parity** track — extends tracker coverage to the dominant enterprise tracker, canonical names + sync-codex mirror.
- Unblocks **fn-68** Jira coverage and Jira mirroring for every tracker-sync projection — the portco-facing requirement.

## Conversation Evidence
> user: "make sure we can handle github, gitlab, jira, linear in an easy and way that will work for companies and doesnt require any special setup on their end"
> user: "portcos seem to want to use the api for jira, limitations with the mcp"
> user: "in general we should build this for linear/github first as we already have those integrations" (⇒ Jira is a follow-on, API-first)

Reference templates: `references/linear-ladder.md` (ladder shape — inverted to API-first here) and `references/adapter-interface.md` (normalized contract).
