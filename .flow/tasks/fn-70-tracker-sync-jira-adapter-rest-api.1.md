## Goal
Make `tracker.type: jira` a real, activatable tracker and flip the ceremony from "surface but don't offer" to "offer": the deterministic flowctl bits (activation enum, config schema incl. `authScheme`/`apiVersion`, identifier validator) + the discovery-ceremony sites (probe / ASK / config-write **+ readiness branch**) + Python tests. The transport + auth scheme are **resolved once here and persisted** — no per-run re-probe (mirrors `cmd_review_backend`). (Spec R5, R6-identity, R7.)

## Files
- `plugins/flow-next/scripts/flowctl.py` (+ byte-identical `.flow/bin/flowctl.py`): `TRACKER_TYPES`:1030 add `"jira"`; `get_default_config()` add `tracker.perTracker.baseUrl` + `projectKey` + **`authScheme` (`cloud-basic`|`bearer-pat`) + `apiVersion` (`3`|`2`) + optional `sslVerify`** + `statusMap` schema defaults; `validate_tracker_identifier` (flowctl.py:20502) — `PROJ-123`/`proj-123` **likely already pass the `KEY-N` grammar**, so this is **regression tests + error-text/docs**, NOT a risky rewrite (preserve GitHub `#N` + reserved `fn`); **receipt-transport — add `rest` to the `--transport` validation/parser** (+ `.flow/bin` mirror) **+ tests** (or, if `--transport` is free-form, add a test asserting `rest` is accepted). Deterministic flowctl edit.
- `plugins/flow-next/skills/flow-next-tracker-sync/steps.md` — ceremony sites:
  - probe (add the `JIRA_BASE_URL` + credential REST signal — Cloud `JIRA_EMAIL`+`JIRA_API_TOKEN` OR DC/Server `JIRA_PAT`; flip "surface but don't offer"; **NO MCP probe** — Jira is REST-only per the fn-70 transport decision).
  - ASK (offer Jira).
  - config-write (`tracker.type jira` + `perTracker.baseUrl`/`projectKey`/**`authScheme`/`apiVersion`**/`statusMap` — auth scheme + api version **detected from the credential/deployment** and persisted; credentials stay in env).
  - **Readiness branch (R5 — mirror Linear/GitHub):** collect `readyState`; validate the status exists in the project when creds are available, else allow skip → no-op backlog lane.
  - **Tracker-first caveat (rp-review B2):** add a **Jira → tracker-first** line to Phase 2's existing caveat (fn-69 set it to "Linear `KEY-N` tracker-first; GitHub `#N` / GitLab `<project>#<iid>` flow-first"). Jira `PROJ-123` IS `KEY-N`, so it **joins tracker-first like Linear** (BOTH entry flows work) — distinct from GitHub/GitLab flow-first-only.
- `plugins/flow-next/docs/tracker-sync.md` — the grab/entry-flow section: state Jira is **tracker-first capable** (`KEY-N` like Linear), distinct from GitHub `#N` / GitLab `<project>#<iid>` flow-first-only.
- `plugins/flow-next/skills/flow-next-tracker-sync/SKILL.md` — probe table: flip Jira from out-of-scope to a real REST offer.
- `plugins/flow-next/tests/test_tracker_sync_*.py` — new tests.

## Approach
- Deterministic flowctl + ceremony prose only. **Single transport (the Jira REST API + token) — no MCP rung, no detect-best-available**; the ceremony confirms the credential, detects deployment (Cloud vs DC/Server → `authScheme`/`apiVersion`), and persists; runtime uses config (`env > config`). `statusMap` config dict, default empty. **Identity:** durable `tracker.id` = immutable Jira `id`; the link flow accepts a `key`, resolves it to the `id` before persisting (key→id resolution is the adapter's, fn-70.2; this task just keeps the validator accepting the key form). Keep `AskUserQuestion` canonical (mirror in fn-70.4).

## Acceptance
- `tracker.type: jira` flips `sync active` true (R7).
- `set-tracker-id` accepts `PROJ-123` / bare `proj-123` (regression test; preserves `#N` + `fn`); **AND end-to-end resolver tests prove `flowctl show PROJ-123` + `work`/`start PROJ-123.M` (the real resolver command surface) actually resolve to the linked spec** — not just the validator (fn-69 scar: a green validator ≠ a working resolver) (R6-identity).
- **Jira is tracker-first** (`KEY-N` like Linear): `spec create --tracker-first --tracker-identifier PROJ-123` mints a clean `proj-123-slug` (test); steps.md Phase 2 caveat + `docs/tracker-sync.md` grab section state Jira tracker-first, distinct from GitHub/GitLab flow-first (R6-identity, rp-review B2).
- Ceremony offers Jira (REST signal) across probe / ASK / config-write **+ readiness branch**; surfaces present AND absent; transport + auth scheme **persisted, not re-probed** (R5).
- Config schema carries `baseUrl`/`projectKey`/`authScheme`/`apiVersion`/`sslVerify`/`statusMap` defaults.
- Tests: enum, config (incl. authScheme/apiVersion defaults), identifier regression, and a **steps.md presence/grep assertion** (probe row + ASK option + config-writes + readiness branch present — ceremony is prose). Full suite green.

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
