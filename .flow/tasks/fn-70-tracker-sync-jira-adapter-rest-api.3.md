## Goal
Extend `references/jira.md` with the Jira-specific weight: Markdown↔ADF translation, the workflow-aware status model (transitions API + statusMap + fn-66 terminal invariant), the relation pair (is-blocked-by links), and `listOpenIssues` (JQL via `/search/jql`). (Spec R1-relation+ninth, R3, R4.) [dep: fn-70.2 — same file.]

## Files
- `plugins/flow-next/skills/flow-next-tracker-sync/references/jira.md` (extend the fn-70.2 doc).
- Reads: `status-sync.md` (fn-66 terminal invariant), `adapter-interface.md` (relation + comment structs).

## Approach — endpoints verified live 2026-06-28 (`~/work/agent-scripts/flow-smoke/out/FINDINGS-jira.md`)
- **ADF translation**: Markdown ↔ ADF (`{"type":"doc","version":1,"content":[...]}` — round-trips exactly) at the boundary, round-trip-safe over a DOCUMENTED subset; preserve unknown ADF nodes on write-back. Reconcile stays transport-blind.
- **Status / transitions**: `GET /rest/api/3/issue/{key}/transitions` returns ids valid **from the current status** → `POST .../transitions {transition:{id}}` (HTTP 204). Never a direct status set. **Terminal detection = `status.statusCategory.key=="done"`** (NOT the status name). `statusMap` (flow ready/done → Jira status); **tolerate a project lacking the target** (e.g. no "In Review") → nearest / defer. fn-66 terminal invariant: locally-`done` → In Review until merge; terminal Done gated on `MERGED`; unreachable transition → defer + receipt.
- **Relations**: `listIssueRelations`/`setIssueRelation` via `POST /rest/api/3/issueLink` type `Blocks` (`outwardIssue` **blocks** `inwardIssue` → current = `inwardIssue` "is blocked by", dep = `outwardIssue`); additive-only / never-delete-non-ours / defer-on-collision.
- **listOpenIssues**: **`POST /rest/api/3/search/jql`** (legacy `GET /search` **removed**, HTTP 410) — `{jql:"project = <projectKey> AND status = \"<readyState>\"", fields, maxResults}`, **cursor pagination** (`isLast`/`nextPageToken`), exact `readyState` (via statusMap), no-op when unset; normalized structs (ADF descriptions translated). REST-only (no MCP).

## Acceptance
- ADF round-trip subset documented + unknown-node preservation (R3).
- Transitions API (per-current-state ids) + statusMap + `statusCategory` terminal signal + fn-66 invariant + defer-on-unreachable + missing-status tolerance (R4).
- Relation pair via `POST /issueLink` `Blocks` (R1-relation).
- `listOpenIssues` via `POST /search/jql`, cursor pagination, exact `readyState`, no-op when unset (R1-ninth).

## Test notes
- Reference doc. ADF round-trip + status model are prose contracts; mirror/parity in fn-70.4. Endpoints already smoke-tested live.

## Description
TBD

## Done summary
TBD

## Evidence
- Commits:
- Tests:
- PRs:
