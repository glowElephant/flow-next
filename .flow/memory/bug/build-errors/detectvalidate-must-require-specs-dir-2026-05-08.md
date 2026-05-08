---
title: detect/validate must require SPECS_DIR even when EPICS_DIR present
date: "2026-05-08"
track: bug
category: build-errors
module: plugins/flow-next/scripts/flowctl.py
tags: [fn-43, rename, detect, validate, write-location, backward-compat]
problem_type: build-error
symptoms: "flowctl detect/validate passed on a repo with epics/ but no specs/, then cat/set-plan crashed on .flow/specs/<id>.md"
root_cause: "directory-validation OR'd specs/ and epics/ as if interchangeable, but markdown is always at specs/"
resolution_type: fix
---

## Problem
fn-43.1 made `cmd_detect` and `validate_flow_root` accept the legacy `.flow/epics/` directory as a substitute for the required `.flow/specs/` directory. That logic is wrong: spec markdown always lives at `.flow/specs/<id>.md` regardless of whether the JSON metadata is in legacy `epics/` or canonical `specs/`. A 0.x repo with only `epics/` (no `specs/`) would pass `flowctl detect` and `flowctl validate --all`, then crash later on `cat`, `set-plan`, or `export-cognitive-aid` when those commands try to read the markdown.

## What Didn't Work
The original "either dir satisfies the storage requirement" check assumed the two locations were interchangeable, but that's only true for the JSON sidecar. Markdown placement was unchanged in the rename — both 0.x and 1.0+ keep it at `.flow/specs/<id>.md`.

## Solution
Always require `SPECS_DIR` in the directory-existence checks. The JSON-side fallback (probing `epics/` when `specs/<id>.json` is missing) handles the metadata-location story; markdown gets its invariant location requirement back. Verified by adding a test: a directory with `epics/` + meta.json but no `specs/` now correctly reports `valid: false, issues: ['specs/ missing']` instead of passing detect.

## Prevention
When a rename / migration introduces a "dual-location" reading story, separate the markdown invariant from the JSON-fallback logic. Markdown has been at `.flow/specs/` since 0.x; only the JSON metadata moved. Treating them as a single dual-location set was the conceptual slip. Future rename tasks: enumerate which artefacts moved vs which stayed, and lock down the unmoved invariants explicitly in the directory-validation pass.
