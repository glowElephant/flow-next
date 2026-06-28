## Goal
Regenerate the Codex mirror from the canonical fn-69.1/.2 files and complete the full doc sweep + changelog so GitLab is a documented, shipped tracker. (Spec R8, R9-verification.)

## Files
- `bash scripts/sync-codex.sh` → regenerates `plugins/flow-next/codex/` (mirror of steps.md / SKILL.md / gitlab.md).
- `plugins/flow-next/docs/tracker-sync.md` — add GitLab to the supported-trackers list + the new `perTracker.project`/`host` config.
- `CHANGELOG.md` — `## Unreleased` entry (batched-release rule — NO version bump).
- `~/work/flow-next.dev`:
  - the tracker-sync docs page — add GitLab.
  - **BOTH navbars** — `src/lib/site.ts` navGroups + `astro.config.mjs` sidebar (CLAUDE.md "Navigation — TWO sources").
  - changelog `## Unreleased` entry; `FLOW_NEXT_VERSION` left for the batched release.
- Downstream narrative (AI×SDLC / GF microsite) — ONLY if they enumerate supported trackers (check; one-line tracker-list touch or skip).
- `plugins/flow-next/tests/` — extend a tracker-sync mirror/parity test to cover GitLab canonical↔mirror.

## Approach
- sync-codex.sh is deterministic — run it, diff the mirror, commit the regenerated output with the canonical changes.
- Doc sweep: GitLab joins Linear/GitHub in every "supported trackers" enumeration; verify the slug-set diff across BOTH flow-next.dev navbars.
- Verify the zero-setup floor (R9): docs state GitLab works from an existing `glab` session or a CI token, no flow-next provisioning; spec-first floor when neither present.

## Acceptance
- Codex mirror regenerated + parity test green (R8).
- docs/tracker-sync.md + flow-next.dev (page + BOTH navbars + changelog) updated (R8).
- CHANGELOG.md `## Unreleased` entry; no version bump (batched-release rule).
- Downstream narrative checked (updated iff they list trackers).
- Full test suite + flow-next.dev `pnpm build` green.

## Test notes
- Mirror-safety/parity test + full suite + docs-site build. No live GitLab.

## Description
TBD

## Done summary
TBD

## Evidence
- Commits:
- Tests:
- PRs:
