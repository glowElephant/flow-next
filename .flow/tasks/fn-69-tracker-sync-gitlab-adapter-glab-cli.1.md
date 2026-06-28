## Goal
Make `tracker.type: gitlab` a real, activatable tracker: the deterministic flowctl bits (activation enum, config schema, identifier validator) + the discovery-ceremony's three coupled sites (probe / ASK / config-write), plus Python tests. This wiring makes the GitLab adapter (fn-69.2) reachable end-to-end. (Spec R3, R4-identity, R7.)

## Files
- `plugins/flow-next/scripts/flowctl.py` (+ byte-identical `.flow/bin/flowctl.py`):
  - `TRACKER_TYPES` (flowctl.py:1030) — add `"gitlab"` (one-line set membership; the legitimate "validate this enum" flowctl edit). Confirm both use-sites (1522, 21012) inherit via the shared constant.
  - `get_default_config()` — add `tracker.perTracker.project` (group/project path, parallel to GitHub's `repo`) + `tracker.perTracker.host` (self-managed base) schema defaults.
  - `validate_tracker_identifier` (used at cmd_sync_set_tracker_id, flowctl.py:20502) — widen to accept the GitLab `<project>#<iid>` and bare `#<iid>` forms (the fn-64.1-style widening github.md used for `#N` / `owner/repo#N`); keep the strict display-form-only return.
- `plugins/flow-next/skills/flow-next-tracker-sync/steps.md` — the THREE coupled ceremony sites:
  - Probe table (Phase 1, ~steps.md:38) — add a `glab auth status` / `GITLAB_TOKEN`|`CI_JOB_TOKEN` row.
  - ASK step (~steps.md:51) — add a GitLab option to the tracker-choice question (extend the existing linear/github choice, do NOT fork a 4th hardcoded path).
  - Config-write block (~steps.md:55-66) — emit `tracker.type gitlab` + `perTracker.project`/`host` (analogous to the `repo` write).
- `plugins/flow-next/skills/flow-next-tracker-sync/SKILL.md` — the four-signal probe table: add the GitLab signal row.
- `plugins/flow-next/tests/test_tracker_sync_*.py` — new tests.

## Approach
- Deterministic flowctl only here — enum + config schema + identifier validator. No transport code, no judgment (that is the adapter prose in fn-69.2). Keep `AskUserQuestion` canonical (sync-codex rewrites for the mirror in fn-69.3).
- Mirror the existing GitHub branches in steps.md/SKILL.md verbatim-in-shape; the ceremony stays env > config > ASK.

## Acceptance
- `tracker.type: gitlab` flips `sync active` true via the type path (R7).
- `set-tracker-id` accepts `<project>#<iid>` + bare `#<iid>`; rejects malformed (R4-identity).
- Ceremony offers GitLab and writes `tracker.type gitlab` + `perTracker.project`/`host` on confirmation; surfaces present AND absent (R3).
- Config schema carries the new `perTracker` keys with safe defaults.
- Tests cover: enum activation, config defaults, identifier validation (valid + invalid GitLab forms), ceremony config-write shape. Full suite stays green.

## Test notes
- Python stdlib unittest; mirror existing `test_tracker_sync_*`. No network — test plumbing + validator, never live `glab`.

## Description
TBD

## Done summary
TBD

## Evidence
- Commits:
- Tests:
- PRs:
