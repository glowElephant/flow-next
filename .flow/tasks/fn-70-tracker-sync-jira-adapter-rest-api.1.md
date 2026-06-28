## Goal
Make `tracker.type: jira` a real, activatable tracker and flip the ceremony from "surface but don't offer" to "offer": the deterministic flowctl bits (activation enum, config schema, identifier validator) + the discovery-ceremony three sites (probe the REST signal, ASK offers Jira, config-write) + Python tests. The transport (REST/PAT) is **resolved once here and persisted** — no per-run re-probe (mirrors `cmd_review_backend`). (Spec R5, R7.)

## Files
- `plugins/flow-next/scripts/flowctl.py` (+ byte-identical `.flow/bin/flowctl.py`): `TRACKER_TYPES`:1030 add `"jira"`; `get_default_config()` add `tracker.perTracker.baseUrl` + `projectKey` + `statusMap`; `validate_tracker_identifier` (flowctl.py:20502) accept `PROJ-123` / bare `proj-123`.
- `plugins/flow-next/skills/flow-next-tracker-sync/steps.md` — three ceremony sites: probe (add the `JIRA_BASE_URL` + credential REST signal — Cloud `JIRA_EMAIL`+`JIRA_API_TOKEN` OR DC/Server `JIRA_PAT`; flip today's "surface but don't offer"; **NO MCP probe** — Jira is REST-only per the fn-70 transport decision), ASK (offer Jira), config-write (`tracker.type jira` + `perTracker.baseUrl`/`projectKey`/`statusMap`). Persist the transport choice; runtime reads config.
- `plugins/flow-next/skills/flow-next-tracker-sync/SKILL.md` — probe table: flip Jira from out-of-scope to a real REST offer.
- `plugins/flow-next/tests/test_tracker_sync_*.py` — new tests.

## Approach
- Deterministic flowctl + ceremony prose only. **Single transport (REST/PAT) — no MCP rung, no detect-best-available**; the ceremony confirms the credential + persists, runtime uses config (`env > config`). `statusMap` config dict, default empty. Keep `AskUserQuestion` canonical (mirror in fn-70.4).

## Acceptance
- `tracker.type: jira` flips `sync active` true (R7).
- `set-tracker-id` accepts `PROJ-123` / bare `proj-123` (R6-identity portion).
- Ceremony offers Jira (REST signal) across all three sites; surfaces present AND absent; transport **persisted, not re-probed** (R5).
- Config schema carries `baseUrl`/`projectKey`/`statusMap` defaults.
- Tests: enum, config, identifier, ceremony config-write shape. Full suite green.

## Test notes
- stdlib unittest; no live Jira.

## Description
TBD

## Done summary
TBD

## Evidence
- Commits:
- Tests:
- PRs:
