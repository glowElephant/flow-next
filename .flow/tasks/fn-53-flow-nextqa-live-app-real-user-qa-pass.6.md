---
satisfies: [R12]
---

## Description
Complete the three-surface docs, the `flowctl.md` config-key documentation, the CHANGELOG credit, and the version bump. flow-next.dev + mickel.tech are maintainer post-merge. (Split from the former single docs/registration task per plan-review finding #8 to stay M-sized.)

**Size:** M
**Files:** `plugins/flow-next/docs/README.md`, `README.md`, `CLAUDE.md`, `.flow/usage.md`, `plugins/flow-next/docs/teams.md`, `plugins/flow-next/docs/platforms.md`, `plugins/flow-next/docs/ralph.md`, `plugins/flow-next/docs/flowctl.md`, `CHANGELOG.md` (+ version-bump surfaces)

## Approach
- **Same-PR repo docs (R12 + planning-surfaced misses):** new QA reference row in `docs/README.md`; `/flow-next:qa` row + workflow-diagram node in root `README.md`; Where-to-look row in `CLAUDE.md`; opt-in note in `.flow/usage.md`; optional QA lifecycle stage in `teams.md` (Mermaid + walkthrough); **`platforms.md`** fn-51-dependency note; **`ralph.md`** `qa_verdict`-receipt note; **`flowctl.md#config`** documents the new `tracker.perEvent.qa` (`off|comment`) leaf — the review-flagged config-doc surface.
- **CHANGELOG:** `### Added` entry **crediting rayfernando-skills (Apache-2.0)**, matching the existing BRB-credit precedent (CHANGELOG ~:56,68) and the make-pr structure.
- **Version bump:** adding a skill is a feature → `./scripts/bump.sh minor flow-next` (the canonical command per `agent_docs/releasing.md`; verify all version surfaces with `jq` after, and that the .5 mirror stays in sync).
- **Maintainer post-merge (do NOT block the PR):** flow-next.dev QA page + sidebar + lifecycle/workflow pages + docs-site changelog + `pnpm build`; mickel.tech flow-next app page. Note these as Gordon's follow-up.

## Investigation targets
**Required:**
- `plugins/flow-next/docs/README.md`, root `README.md` (commands table + workflow diagram), `CLAUDE.md` (Where-to-look table), `plugins/flow-next/docs/teams.md` (lifecycle Mermaid), `plugins/flow-next/docs/platforms.md`, `plugins/flow-next/docs/ralph.md`, `plugins/flow-next/docs/flowctl.md` (config section)
- `agent_docs/releasing.md` — CHANGELOG + docs-site format
- `CHANGELOG.md` — the existing BRB-credit precedent to match

## Key context
- DEPENDS on .5 (registration/sync) so the docs describe the final shipped skill + mirror.
- Final-integration impl-review must use the spec-merge-base, not this task's start commit (memory gotcha).

## Acceptance
- [ ] All same-PR repo doc surfaces updated: `docs/README.md`, root `README.md` (table + diagram), `CLAUDE.md`, `.flow/usage.md`, `teams.md`, `platforms.md`, `ralph.md`, **`flowctl.md` (`tracker.perEvent.qa` config)**
- [ ] CHANGELOG `### Added` entry credits rayfernando-skills (Apache-2.0); version bumped (minor) across all four surfaces; mirror stays in sync
- [ ] flow-next.dev + mickel.tech flagged as maintainer post-merge (not blocking)

## Done summary

_(filled on completion)_

## Evidence

_(filled on completion)_
