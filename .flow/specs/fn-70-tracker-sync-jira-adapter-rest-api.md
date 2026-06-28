# fn-70 tracker-sync Jira adapter — REST v3 + PAT (single rung, GitHub-shaped)

## Goal & Context
<!-- scope: business -->

tracker-sync ships **Linear** and **GitHub** adapters; **Jira is detected but deliberately not offered**. Enterprise teams overwhelmingly run Jira and want flow specs mirrored there. This spec adds a Jira adapter implementing tracker-sync's normalized interface so `/flow-next:pilot` backlog mode (fn-68) and every other projection can target Jira with **no special setup beyond a credential the company already issues** — covering Jira **Cloud and self-hosted Data Center/Server**.

**Transport decision (2026-06-28): REST v3 via PAT is the sole supported transport** — a single-rung + no-op adapter shaped like the GitHub adapter, NOT a Linear-style MCP ladder. The Atlassian MCP was evaluated and is **not wired**: the *official* Atlassian Remote MCP (GA Feb 2026) is read-mostly — it **cannot transition issue status, update existing fields, or set issue/epic links**, exactly the writes a two-way sync needs; the *community* MCP (`sooperset/mcp-atlassian`) is a REST-wrapper needing its own Docker server + the same PAT, so it adds setup for no capability flow-next's native REST path lacks. (This supersedes the earlier "support MCP too, like Linear" intent, on the evidence.)

## Architecture & Data Models
<!-- scope: technical -->

- **New adapter** behind `references/adapter-interface.md` (nine methods — fn-68 added `listOpenIssues`): the six core (`fetchIssue`/`writeIssue`/`listComments`/`postComment`/`readStatus`/`setStatus`), the **fn-64 relation pair** (`listIssueRelations`/`setIssueRelation`) via Jira native **issue links** ("is blocked by"), and **`listOpenIssues`** — all over **Jira REST v3**, mapping the Jira wire shape (incl. ADF) to/from the normalized structs. Reconcile/body-merge/status-sync untouched.
- **Transport: REST v3 + PAT, single rung + no-op** (GitHub-shaped). The credential/transport is resolved **once at the discovery ceremony** and persisted to config — `env > config`, **no per-run re-probe** (mirrors `cmd_review_backend`). Runtime: REST v3 from env (`JIRA_BASE_URL` + a credential) → else **no-op rung** (receipt note, never crash). The only runtime check is a cheap "is the configured credential present" — never a rung re-scan / support-probe.
- **Auth (two schemes — detected at ceremony, persisted):** Jira **Cloud** = HTTP basic `email:API_TOKEN` (`JIRA_EMAIL`+`JIRA_API_TOKEN`, an *API token*, not a PAT); Jira **Data Center/Server** = `Authorization: Bearer <PAT>` (`JIRA_PAT`). Label unambiguously so a Cloud user isn't told to make a non-existent "PAT". **Self-hosted TLS:** opt-in `JIRA_SSL_VERIFY=false` for internal-CA/self-signed certs (documented, never silent). Never store creds in flow state — read env each run.
- **Backlog enumeration (`listOpenIssues`):** **`POST /rest/api/3/search/jql`** — the legacy `GET /rest/api/3/search` was **removed** (HTTP 410, CHANGE-2046; verified live 2026-06-28) — body `{jql, fields, maxResults}`; JQL `project = <projectKey> AND status = "<readyState>"`, exact `tracker.readyState` (via `statusMap`), no-op + note when unset. **Cursor pagination** (`isLast` + `nextPageToken`), NOT offset (`total`/`startAt`). Returns normalized `issue` structs (ADF descriptions translated). Scope JQL to the project (Free-tier rate limits).
- **ADF body translation** — Jira REST v3 descriptions/comments use Atlassian Document Format. The adapter translates normalized Markdown ↔ ADF at the boundary (Jira-specific; reconcile sees only normalized text). Lossy-but-faithful over a documented subset; preserve unknown ADF nodes on write-back. (Verified 2026-06-28: description + comment bodies are `{"type":"doc","version":1,"content":[...]}` and round-trip exactly.)
- **Comment `authorAuthority` (fn-68 contract):** populate from `comment.author.accountType` — `app` ⇒ `bot`, `customer` (JSM portal) ⇒ `outsider`, `atlassian` ⇒ `writer` (optionally refined via project-role/group membership), unknown ⇒ fail-closed. The comment author object carries `accountId`/`accountType`/`displayName` but **no inline role** (verified 2026-06-28), so writer-vs-outsider beyond `accountType` needs a role lookup or a default-writer-for-internal-project rule.
- **Status fidelity — workflow-aware + fn-66 terminal invariant.** Jira has rich per-project workflows. `tracker.readyState` maps via `statusMap`; status writes go through the **transitions API** (`GET /issue/{key}/transitions` returns ids valid **from the current status** → `POST /issue/{key}/transitions {transition:{id}}`; verified 2026-06-28), never a direct set. **Terminal detection = `status.statusCategory.key`** (`new`|`indeterminate`|`done`), NOT the status *name* (names are project-renamable). Honor the fn-66 invariant: locally-`done` → **In Review** until merge, terminal **Done** gated on `MERGED` PR evidence. **Not every project has the assumed statuses** — the default team-managed workflow is To Do/In Progress/Done with **no "In Review"** (verified 2026-06-28); `statusMap` must tolerate a missing target (map to nearest / defer + receipt), never assume the In-Review rung exists. Sharp edge: a target transition may be unreachable from the current state → defer + receipt, never a forced/illegal jump.
- **Activation gate (flowctl):** extend `TRACKER_TYPES` to include `"jira"` (deterministic enum edit — the single line that activates `tracker.type: jira`).
- **PR↔issue link (make-pr):** projects to Jira as a **remote link** (or a URL comment) in-adapter — no auto-linkify/`gh`; Smart-Commit keys not relied on.
- **Issue grain:** one flow spec ↔ one Jira issue (key `PROJ-123` is the durable id); back-reference via labeled marker + body anchor.
- **Discovery ceremony — three coupled sites:** the probe table (add the `JIRA_BASE_URL`+credential REST signal, flipping today's "surface but don't offer"), the **ASK** step (offer Jira), the **config-write** block (`tracker.type jira` + `perTracker.baseUrl`/`projectKey`/`statusMap`). The transport is decided here and persisted — no runtime re-probe.
- **Reference doc:** `references/jira.md`, authored against `references/github.md` (single-rung + transitions-status shape) with the ADF translation + transitions-API status model documented. "enterprise teams", not "portco". Records the **MCP-evaluated-not-wired decision + evidence** so a future spec can revisit without re-researching.

## API Contracts
<!-- scope: technical -->

- **Detection (ceremony, once):** `JIRA_BASE_URL` + (`JIRA_PAT` | `JIRA_EMAIL`+`JIRA_API_TOKEN`) ⇒ REST transport available. Resolution `env > config > ask`; persisted at the ceremony. Surface present AND absent.
- **Auth:** Cloud basic (`email:API_TOKEN`) vs DC/Server Bearer PAT — distinct env vars, labelled in `references/jira.md`.
- **Adapter methods:** exact `adapter-interface.md` signatures; ADF↔Markdown only inside the adapter.
- **Config:** `tracker.type: jira`; `tracker.perTracker` carries `baseUrl`, `projectKey`, `statusMap` (flow ready/done → Jira status names/ids); `tracker.readyState` resolves through `statusMap`.
- **Status writes** go through the **transitions API** (resolve transition id for target status, POST transition).
- **Identity:** `sync set-tracker-id <spec> <issue-key> --identifier PROJ-123 --url <browse-url>`; bare `proj-123` resolves via the widened resolver.

## Edge Cases & Constraints
<!-- scope: technical -->

- **No credential reachable** → no-op rung + actionable receipt ("set `JIRA_BASE_URL` + a token"); spec-first floor still works.
- **ADF round-trips are lossy** — document the supported Markdown subset; preserve unknown ADF nodes on write-back (no silent loss).
- **Transition gating** — a target status may be unreachable from the current status per the workflow; resolve the legal transition, else defer + receipt (never force).
- **Cloud vs Data Center auth differ** — detect by token type at the ceremony; support both.
- **Self-hosted TLS** — opt-in `JIRA_SSL_VERIFY=false` for internal-CA certs; never silent / never default-off.
- **Rate limits / 401 / 403** — bounded retry; auth failure → no-op + actionable receipt; never block. (Free/Standard Cloud tiers have stricter limits — scope JQL to the project.)
- **Cross-platform:** canonical Claude names; `sync-codex.sh` regenerates cleanly.

## Acceptance Criteria
<!-- scope: both -->

- **R1:** A Jira adapter implements **all nine** `adapter-interface.md` methods over **REST v3** — six core + the fn-64 relation pair via "is blocked by" issue links (`POST /issueLink`, type `Blocks`: `outwardIssue` blocks `inwardIssue`) + `listOpenIssues` (**`POST /search/jql`** — `GET /search` is removed/410 — exact `readyState`, no-op when unset) — mapping Jira wire (incl. ADF `doc`) ↔ normalized structs; reconcile/body-merge/status-sync unchanged.
- **R2:** Transport is **REST v3 + PAT, single rung + no-op** (GitHub-shaped) — **no MCP rung**. The credential/transport is resolved **once at the ceremony** and persisted (`env > config`); runtime does no rung re-probe, only a cheap credential-presence check → no-op when absent. The MCP-evaluated-not-wired decision + evidence is recorded in `references/jira.md`.
- **R3:** Markdown ↔ ADF translation lives in the adapter, round-trip-safe over a documented subset, preserving unknown nodes on write-back (no silent loss).
- **R4:** Status writes go through the transitions API (per-current-state transition ids) via a configurable `statusMap`; `tracker.readyState` resolves through it; illegal/unreachable transitions defer + receipt, never force. **Terminal detection keys on `status.statusCategory.key=="done"`, not the status name.** `statusMap` tolerates a project that lacks the configured target (e.g. no "In Review") — map to nearest / defer, never assume it exists. The **fn-66 terminal-status invariant** is honored (locally-`done` → In Review until merge; terminal Done gated on `MERGED`; a deferred unreachable terminal transition surfaced via receipt, never forced).
- **R5:** The discovery ceremony detects the Jira REST transport (`JIRA_BASE_URL`+credential) and **offers + writes** Jira across all three sites (probe / ASK / config-write), replacing today's "surface but don't offer"; the transport choice is **persisted, not re-probed per run**.
- **R6:** One flow spec ↔ one Jira issue; key stored via `sync set-tracker-id`; back-reference marker written; bare key resolves; **make-pr's PR link projects to Jira as a remote link / URL comment**.
- **R7:** `TRACKER_TYPES` (flowctl) extended to include `jira` so `sync active` recognizes `tracker.type: jira` via the type path (deterministic flowctl edit).
- **R8:** `references/jira.md` authored (REST single-rung + ADF + transitions; Cloud-vs-DC auth labelled; MCP-not-wired decision recorded; "enterprise teams"); `tracker.type: jira` + `baseUrl`/`projectKey`/`statusMap` documented; Codex mirror regenerated; **full doc sweep** (per CLAUDE.md) — flip `docs/tracker-sync.md` + the SKILL.md ceremony "Jira out of scope" line + flow-next.dev tracker-sync page + **BOTH navbars** + changelog + `FLOW_NEXT_VERSION`; downstream narrative (AI×SDLC/GF) only if they enumerate trackers; version bumped.
- **R9:** Zero special setup beyond a standard Jira credential the company already issues (Cloud API token or DC/Server PAT) — no OAuth app, MCP server, webhook, or Connect/Forge app; spec-first floor when no credential present.

## Boundaries
<!-- scope: business -->

- **Adapter only** — no reconcile/body-merge/status-sync changes (transport-blind).
- **REST/PAT is the sole transport; no MCP rung** — the official Atlassian MCP can't perform the writes a two-way sync needs (transitions/updates/links), and the community MCP is a redundant PAT-wrapper requiring its own setup. (If an Atlassian MCP happens to be registered, flow-next still uses REST/PAT — the MCP is neither required nor used.)
- **Not a new sync skill** — plugs into `/flow-next:tracker-sync`.
- **GitHub/Linear/GitLab unaffected** — additive adapter.
- **No Atlassian Connect/Forge app, no MCP dependency** — credentials are a plain API token, nothing to install on the company's Jira.

## Decision Context
<!-- scope: both -->

### Motivation
Enterprise teams run Jira and want flow specs mirrored there. tracker-sync's transport-blind interface means Jira is "just another adapter"; the Jira-specific weight is ADF translation + the transitions-API status model.

### Implementation Tradeoffs
- **REST/PAT single-rung, not a Linear-style MCP ladder (decided 2026-06-28, MCP evaluated):** the *official* Atlassian Remote MCP (GA Feb 2026) is read-mostly — Atlassian's own community threads confirm it **cannot transition status, update existing fields, or set issue/epic links** (only basic-issue create, read, comment, JQL). A two-way sync needs exactly those writes, so the MCP can't be the transport. The *community* MCP (`sooperset/mcp-atlassian`) wraps the full REST API but is a third-party Docker server needing the same PAT — redundant with flow-next's native REST path and itself "special setup." So Jira is GitHub-shaped: REST v3 + PAT, single rung. Reverses the earlier "support MCP too, like Linear" intent on the evidence.
- **Transport resolved once at the ceremony, persisted (like review-backend):** no per-run "is the MCP/token good" probing — `env > config`, the no-op rung is the only runtime fallback. Avoids "checking for support all the time."
- **ADF translation in-adapter:** keeps reconcile transport-blind; cost is a documented lossy subset + unknown-node preservation.
- **Transitions API over direct status set:** Jira forbids arbitrary status writes; some target states are unreachable → defer+receipt, never force.
- **Live-API smoke-tested (2026-06-28, dociq.atlassian.net, throwaway project deleted after):** every adapter op validated against real Jira REST v3 — create/read/update issue, ADF `doc` round-trip, transitions, `Blocks` link, remote link, JQL search, colon-labels. Surfaced three corrections now folded in: the `/search`→`/search/jql` removal (410), `statusCategory.key` as the terminal signal (not status name), and that "In Review" isn't universal. Evidence: `~/work/agent-scripts/flow-smoke/out/FINDINGS-jira.md`.
- **Plain API token over Connect/Forge/MCP:** the zero-setup promise — companies already issue API tokens.

## Strategy Alignment
- **Cross-platform parity** track — extends tracker coverage to the dominant enterprise tracker (Cloud + self-hosted DC/Server), canonical names + sync-codex mirror.
- Unblocks **fn-68** Jira coverage and Jira mirroring for every tracker-sync projection — the enterprise-facing requirement.

## Conversation Evidence
> user: "make sure we can handle github, gitlab, jira, linear in an easy and way that will work for companies and doesnt require any special setup on their end"
> user: "portcos seem to want to use the api for jira, limitations with the mcp"
> user: "rest api via pat token, we will support mcp too agentically, similar to linear i think" (original intent — superseded below on evidence)
> user: "[fn-69/70] also support self-hosted installations ... check the mcp route and PAT options of self hosted"
> user: "if the mcp support is too bad for one or the other decide whether to support or just go via pat token" (⇒ delegated the call; verified 2026-06-28 the official Atlassian MCP can't transition/update/link — too limited for a two-way sync — so Jira goes REST/PAT-only, no MCP rung; community MCP is a redundant PAT-wrapper)

Reference templates: `references/github.md` (single-rung transport, transitions-status) and `references/adapter-interface.md` (normalized contract).
