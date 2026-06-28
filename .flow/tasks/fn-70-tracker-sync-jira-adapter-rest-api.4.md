## Goal
Regenerate the Codex mirror and complete the full doc sweep — flipping "Jira out of scope" everywhere — + changelog. (Spec R8, R9.) [dep: fn-70.1, .2, .3.]

## Files
- `bash scripts/sync-codex.sh` → regenerate `plugins/flow-next/codex/` mirror.
- `plugins/flow-next/docs/tracker-sync.md` — flip the "Jira out of scope" line to supported; document `tracker.type jira` + `baseUrl`/`projectKey`/`statusMap`.
- `plugins/flow-next/skills/flow-next-tracker-sync/SKILL.md` — confirm the ceremony table's "Jira out of scope" line is flipped (fn-70.1) and consistent.
- `CHANGELOG.md` — `## Unreleased` entry (NO version bump).
- `~/work/flow-next.dev`: tracker-sync page (Jira), **BOTH navbars** (`site.ts` + `astro.config.mjs`), changelog `## Unreleased`; `FLOW_NEXT_VERSION` for the batched release.
- Downstream narrative (AI×SDLC / GF microsite) — only if they enumerate trackers.
- `plugins/flow-next/tests/` — extend a mirror/parity test to cover Jira.

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
