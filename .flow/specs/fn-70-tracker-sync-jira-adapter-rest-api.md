# fn-70 tracker-sync Jira adapter — REST PAT + agentic Atlassian MCP (Linear-style ladder)

## Goal & Context
<!-- scope: business -->

tracker-sync ships **Linear** and **GitHub** adapters; **Jira is detected but deliberately not offered**. Enterprise portfolio companies overwhelmingly run Jira and want flow specs mirrored there. This spec adds a Jira adapter that supports **both** transports the way the Linear adapter does — the **Atlassian MCP driven agentically by the host agent** (when registered) and the **Jira REST API via a PAT** — implementing tracker-sync's normalized interface so `/flow-next:pilot` backlog mode (fn-68) and every other projection can target Jira with no special setup beyond credentials the company already issues. The one Jira-specific guarantee: **the REST/PAT path is fully standalone and never requires the MCP**, because portcos report Atlassian-MCP limitations and need the token path to work on its own.

## Architecture & Data Models
<!-- scope: technical -->

- **New adapter** behind `references/adapter-interface.md` — implements `fetchIssue` / `writeIssue` / `listComments` / `postComment` / `readStatus` / `setStatus`, mapping the Jira wire shape to/from the normalized structs. Reconcile / body-merge / status-sync / comments-sync untouched.
- **Transport: a Linear-style detect-best-available ladder with two first-class rungs.** (1) **Atlassian MCP, driven agentically by the host agent** — exactly the way the Linear adapter uses its MCP (the host calls the MCP's issue/comment/transition tools), whenever an Atlassian MCP is registered. (2) **Jira REST v3 via a PAT** — `Authorization: Bearer <PAT>` (Data Center/Server) or email + API token basic auth (Cloud), from env (`JIRA_BASE_URL` + `JIRA_PAT`, or `JIRA_EMAIL` + `JIRA_API_TOKEN`). (3) **no-op rung** (receipt note, never crash). **Both transports are fully supported**; resolution is **env > config > ask**, same as the Linear ladder. The REST/PAT rung is **standalone — it never requires the MCP** — so portcos who hit Atlassian-MCP limitations are fully covered, while shops with a working MCP get the agentic path. Neither rung is a grudging fallback.
- **ADF body translation** — Jira descriptions/comments use Atlassian Document Format (ADF), not Markdown. The adapter translates normalized Markdown ↔ ADF at the boundary (a Jira-specific concern; reconcile still sees only normalized text). Keep the translation in the adapter, lossy-but-faithful, with a round-trip-safe subset documented.
- **Status fidelity — workflow-aware:** Jira has rich, per-project configurable workflows. `tracker.readyState` maps to a Jira status/category; transitions go through the Jira transition API (you cannot set an arbitrary status directly). The adapter resolves the transition id for the target status and applies it; unknown/unreachable transitions defer + receipt (never force).
- **Issue grain:** one flow spec ↔ one Jira issue (issue key e.g. `PROJ-123` is the durable id). Back-reference via a labeled marker + body anchor.
- **Discovery-ceremony probe extension:** add Jira signals — a registered **Atlassian MCP** (agentic rung) AND/OR `JIRA_BASE_URL`+PAT (REST rung) — flipping today's "surface but don't offer" to "offer" with whichever transport(s) are present. Surface present AND absent for both.
- **Reference doc:** `references/jira.md`, authored against `references/linear-ladder.md` (same MCP-or-token ladder shape), with the ADF translation + transition-api status mapping documented, and the standalone-REST guarantee called out.

## API Contracts
<!-- scope: technical -->

- **Detection (ceremony):** registered Atlassian MCP ⇒ agentic MCP transport; `JIRA_BASE_URL` + (`JIRA_PAT` | `JIRA_EMAIL`+`JIRA_API_TOKEN`) ⇒ REST transport. Either suffices; both may be present (resolution env > config > ask). Surface present AND absent for each.
- **Auth:** Cloud = HTTP basic `email:API_TOKEN` over HTTPS; Data Center = `Authorization: Bearer <PAT>`. Never store credentials in flow state — read from env each run.
- **Adapter methods:** exact `adapter-interface.md` signatures; ADF↔Markdown only inside the adapter.
- **Config:** `tracker.type: jira`; `tracker.perTracker` carries `baseUrl`, `projectKey`, and a `statusMap` (flow ready/done → Jira status names/ids); `tracker.readyState` resolves through `statusMap`.
- **Status writes** go through the **transitions API** (resolve transition id for target status, POST transition), not a direct status set.
- **Identity:** `sync set-tracker-id <spec> <issue-key> --identifier PROJ-123 --url <browse-url>`; bare `proj-123` resolves via the widened resolver.

## Edge Cases & Constraints
<!-- scope: technical -->

- **REST/PAT never *requires* the MCP** — the Atlassian MCP is supported agentically (like Linear) when present, but the REST/PAT rung is standalone. If only the MCP is present and it cannot perform a needed op (portco-reported limitations), defer + receipt with a clear "add a Jira PAT for the REST path" note. Both rungs are real; REST/PAT is the always-works floor.
- **ADF round-trips are lossy** — document the supported Markdown subset; preserve unknown ADF nodes on write-back rather than dropping (no silent data loss in the human's description).
- **Transition gating** — a target status may be unreachable from the current status per the project workflow; resolve the legal transition, else defer + receipt (never force an illegal transition).
- **Cloud vs Data Center auth differ** — detect by base URL / token type; support both.
- **Rate limits / 401 / 403** — bounded retry; on auth failure, no-op + actionable receipt; never block.
- **No transport reachable** → no-op rung + receipt; spec-first floor still works.
- **Cross-platform:** canonical Claude names; `sync-codex.sh` regenerates cleanly.

## Acceptance Criteria
<!-- scope: both -->

- **R1:** A Jira adapter implements every `adapter-interface.md` method, mapping Jira wire (incl. ADF) ↔ normalized structs; reconcile/body-merge/status-sync unchanged.
- **R2:** Transport ladder mirrors Linear's — **Atlassian MCP (agentic, host-agent-driven) and Jira REST-v3-via-PAT are both first-class rungs**, detect-best-available (env > config > ask) → no-op rung. The REST/PAT rung is standalone (never requires the MCP) so portcos hitting MCP limits are covered; shops with a working Atlassian MCP get the agentic path.
- **R3:** Markdown ↔ ADF translation lives in the adapter, round-trip-safe over a documented subset, preserving unknown nodes on write-back (no silent loss).
- **R4:** Status writes go through the Jira transitions API via a configurable `statusMap`; `tracker.readyState` resolves through it; illegal/unreachable transitions defer + receipt, never force.
- **R5:** The discovery ceremony detects both Jira transports — a registered Atlassian MCP and/or `JIRA_BASE_URL`+PAT — and offers Jira (replacing today's "surface but don't offer"), using whichever is present.
- **R6:** One flow spec ↔ one Jira issue; issue key stored via `sync set-tracker-id`; back-reference marker written; bare key resolves via the widened resolver.
- **R7:** `references/jira.md` authored (Linear-style MCP-or-PAT ladder + ADF + transitions); `tracker.type: jira` + `baseUrl`/`projectKey`/`statusMap` config documented; Codex mirror regenerated; docs + flow-next.dev updated; version bumped.
- **R8:** Zero special setup beyond a standard Jira API token the company already issues — no OAuth app, webhook, or Atlassian Connect/Forge app required; spec-first floor when no token present.

## Boundaries
<!-- scope: business -->

- **Adapter only** — no reconcile/body-merge/status-sync changes (transport-blind).
- **Both transports supported; REST/PAT never *requires* the MCP** — the Atlassian MCP is driven agentically (like Linear) when present; the REST/PAT path is standalone so portcos hitting MCP limits are covered. Neither is a grudging fallback; the only asymmetry is that REST/PAT is the always-works floor.
- **Not a new sync skill** — plugs into `/flow-next:tracker-sync`.
- **GitHub/Linear/GitLab unaffected** — additive adapter.
- **No Atlassian Connect/Forge app** — credentials are a plain API token, nothing to install on the company's Jira.

## Decision Context
<!-- scope: both -->

### Motivation
Enterprise portcos run Jira and want flow specs mirrored there. We support the same agentic MCP-or-token ladder as Linear — but because portcos report Atlassian-MCP limitations, the REST/PAT path must also work entirely on its own (the transport that runs in their environments and CI). tracker-sync's transport-blind interface means Jira is "just another adapter"; the only Jira-specific weight is ADF translation and the transitions-API status model.

### Implementation Tradeoffs
- **Same agentic MCP-or-token ladder as Linear, two real rungs:** Jira mirrors Linear's detect-best-available shape — Atlassian MCP driven agentically by the host agent, OR REST v3 via a PAT. Not "API-first because the MCP is bad"; both are supported. The one Jira-specific rule is that the REST/PAT rung is standalone and never depends on the MCP, because portcos hit Atlassian-MCP limits and need the token path to stand alone.
- **ADF translation in-adapter:** keeps reconcile transport-blind; the cost is a documented lossy subset + unknown-node preservation, accepted to avoid leaking ADF into the merge engine.
- **Transitions API over direct status set:** Jira forbids arbitrary status writes; resolving legal transitions is mandatory and means some target states are unreachable — handled by defer+receipt, never forcing.
- **Plain API token over Connect/Forge app:** the zero-setup promise — companies already issue API tokens; an installable app would be exactly the "special setup" we're avoiding.

## Strategy Alignment
- **Cross-platform parity** track — extends tracker coverage to the dominant enterprise tracker, canonical names + sync-codex mirror.
- Unblocks **fn-68** Jira coverage and Jira mirroring for every tracker-sync projection — the portco-facing requirement.

## Conversation Evidence
> user: "make sure we can handle github, gitlab, jira, linear in an easy and way that will work for companies and doesnt require any special setup on their end"
> user: "portcos seem to want to use the api for jira, limitations with the mcp"
> user: "rest api via pat token, we will support mcp too agentically, similar to linear i think" (⇒ BOTH transports first-class — agentic MCP like Linear + standalone REST/PAT; not API-only)
> user: "in general we should build this for linear/github first as we already have those integrations" (⇒ Jira is a follow-on)

Reference templates: `references/linear-ladder.md` (same MCP-or-token ladder shape) and `references/adapter-interface.md` (normalized contract).
