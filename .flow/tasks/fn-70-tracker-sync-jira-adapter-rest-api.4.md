## Goal
Regenerate the Codex mirror and complete the full doc sweep — flipping "Jira out of scope" everywhere — + changelog. (Spec R8, R9.) [dep: fn-70.1, .2, .3.]

## Files
- `bash scripts/sync-codex.sh` → regenerate `plugins/flow-next/codex/` mirror.
- `plugins/flow-next/docs/tracker-sync.md` — flip the "Jira out of scope" line to supported; document `tracker.type jira` + `baseUrl`/`projectKey`/**`authScheme`/`apiVersion`/`sslVerify`**/`statusMap`.
- `plugins/flow-next/skills/flow-next-tracker-sync/SKILL.md` — confirm the ceremony table's "Jira out of scope" line is flipped (fn-70.1) and consistent.
- **`plugins/flow-next/skills/flow-next-tracker-sync/references/adapter-interface.md`** — update the implemented-by table, the `issue.tracker` enum, the receipt-transport enum (add `rest`), the Jira `authorAuthority` mapping note, and the `listOpenIssues` Jira semantics.
- **Doc sweep — every stale "Linear/GitHub" / "Jira out of scope" enumeration:** `plugins/flow-next/docs/flowctl.md`, `plugins/flow-next/docs/skills.md`, `teams.md`, root `README.md`, `GLOSSARY.md`, the Codex `openai.yaml` description + `scripts/sync-codex.sh` registration line.
- `CHANGELOG.md` — `## Unreleased` entry (NO version bump).
- `~/work/flow-next.dev`: tracker-sync page (Jira), **BOTH navbars** (`site.ts` + `astro.config.mjs`), changelog `## Unreleased`. **`FLOW_NEXT_VERSION` is NOT changed by this task** (the batched release bumps it later).
- Downstream narrative (AI×SDLC / GF microsite) — only if they enumerate trackers.
- `plugins/flow-next/tests/test_tracker_sync_mirror_parity.py` (or the existing parity test) — assert canonical `jira.md` is mirrored into `plugins/flow-next/codex/` AND the `openai.yaml` description includes Jira.

## Approach
- Deterministic sync-codex regen; commit mirror with canonical.
- Sweep every "supported trackers" / "Jira out of scope" site → Jira supported. Verify both flow-next.dev navbars (slug-set diff).
- Verify zero-setup floor (R9): a standard Jira credential (Cloud API token or DC/Server PAT) — no OAuth app / webhook / Connect / Forge.

## Acceptance
- Mirror regenerated + parity test green (R8).
- docs/tracker-sync.md + SKILL.md "Jira out of scope" flipped; flow-next.dev (page + BOTH navbars + changelog) (R8).
- CHANGELOG `## Unreleased`; no version bump.
- Downstream narrative checked.
- Full suite + flow-next.dev `pnpm build` green.

## Test notes
- Mirror/parity + full suite + docs-site build. No live Jira.

## Description
TBD

## Done summary
TBD

## Evidence
- Commits:
- Tests:
- PRs:
