## Goal
Author `references/jira.md` transport + core: the **REST v3 + PAT single-rung + no-op** transport (GitHub-shaped — NO MCP rung), the six core methods, auth (Cloud basic vs DC Bearer PAT + self-hosted TLS), identity, and the make-pr PR-link. Records the MCP-evaluated-not-wired decision + evidence. Modeled on `github.md`. (Spec R1-core, R2, R6-link.)

## Files
- `plugins/flow-next/skills/flow-next-tracker-sync/references/jira.md` (new) — authored from `github.md` (single-rung + no-op discipline).
- Reads: `adapter-interface.md`.

## Approach — auth + endpoints verified live 2026-06-28 (`~/work/agent-scripts/flow-smoke/out/FINDINGS-jira.md`)
- **Transport** (cf. github.md rung detection): REST v3 from env (`JIRA_BASE_URL` + credential) → no-op. **No MCP rung** — record the decision in-doc: official Atlassian MCP can't transition/update/link (read-mostly); community MCP is a redundant PAT-wrapper. Transport resolved once at the ceremony (fn-70.1), persisted; runtime = cheap credential-presence check → no-op (never a support-probe).
- **Auth (verified):** Cloud basic `email:API_TOKEN` over `/rest/api/3` (`JIRA_EMAIL`+`JIRA_API_TOKEN`) — confirmed working on Cloud; DC/Server Bearer PAT (`JIRA_PAT`). Label unambiguously (Cloud has no "PAT"). Self-hosted TLS opt-in `JIRA_SSL_VERIFY=false`. Never store creds in flow state.
- **Core six:** `POST /issue` (ADF description + labels — colon labels like `flow:<id>` accepted), `GET /issue/{key}`, `PUT /issue/{key}` (ADF body), `GET`/`POST /issue/{key}/comment` (ADF), `GET /issue/{key}` status. **`comment.author.accountType`** → `authorAuthority` (app⇒bot, customer⇒outsider, atlassian⇒writer; fn-68 contract, fail-closed). Transitions detail → fn-70.3.
- **Identity:** issue key `PROJ-123`; back-reference labeled marker + body anchor.
- **make-pr PR↔issue link (verified):** `POST /rest/api/3/issue/{key}/remotelink {object:{url,title}}` (HTTP 201) — no auto-linkify / `gh`.
- "enterprise teams", not "portco".

## Acceptance
- REST-only single-rung + no-op documented; **MCP-not-wired decision + evidence recorded** (R2).
- Six core methods with concrete REST v3 calls; `authorAuthority` from `accountType` (R1-core).
- Auth split (Cloud basic / DC Bearer PAT) + TLS labelled (R2 / R9 auth).
- PR-link as `remotelink` (R6-link).
- Canonical Claude names.

## Test notes
- Reference doc — prose contract + read-through; testable bits in fn-70.1, mirror in fn-70.4. Auth + remote-link already smoke-tested live.

## Description
TBD

## Done summary
TBD

## Evidence
- Commits:
- Tests:
- PRs:
