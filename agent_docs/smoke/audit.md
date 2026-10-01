# audit: manual smoke (maintainer checklist)

Moved out of the shipped skill in 7.0; never loaded at runtime.

The skill itself is markdown — there's no unit-test surface. The validation is invoking `/flow-next:audit` in a real session. Expected behavior:

- Phase 0 walks `.flow/memory/`, lists per-cluster counts, reports legacy skip count if `pitfalls.md` etc. exist. Decision entries (`knowledge/decisions/`) are picked up automatically by the categorized schema.
- Phase 0.5 walks every `GLOSSARY.md` on the ancestor chain via `flowctl glossary list --json`, greps tracked code per-term + per-`_Avoid_` alias, marks zero-hit terms stale via Edit tool with `<!-- stale: ... -->`, surfaces alias-creep, advises on husks.
- Phase 0.75 pre-scans recurrence artifacts BEFORE auto-Keep, so a recurrence-qualified entry with an unchanged module still reaches Phase 1; hardened entries get the gate-liveness check only.
- Phase 1 produces evidence per entry. For 3+ entries, parallel investigation subagents run.
- Phase 2 classifies; Replace candidates with insufficient evidence reclassify as mark-stale. Decision entries use the calibrated judging question and the supersede shape for Replace. Precedence: correctness > Consolidate > Harden.
- Phase 3 (interactive) groups Keeps / Updates for batched confirmation; presents Consolidate / Replace / Delete, Harden candidates (gate type + draft artifact + evidence + accept / different-gate-type / decline), and glossary alias-creep individually via blocking-question tool.
- Phase 4 persists memory actions via `flowctl memory apply --plan`; specialized stale/harden helpers retain their status invariants. Decision Replace = supersede (write new + edit old's `decision_status` + `superseded_by`; never `git rm`). Harden writes the artifact, verifies the gate fires, then `flowctl memory mark-hardened <id> --gate-ref "..."` — verification failure leaves the entry `active`; never `git rm`. Glossary stale = Edit comment after term heading.
- Phase 5 prints the report (memory section incl. `Hardened: N` with gate type / artifact path / gate-ref, glossary section + husk advisories); offers commit options based on git context.
- Phase 6 checks CLAUDE.md / AGENTS.md for `.flow/memory/` mention; offers minimal addition if missing.

In autofix mode (`/flow-next:audit mode:autofix`), Phase 3 is skipped, ambiguous entries are marked stale, glossary alias-creep surfaces as a recommendation only, Harden candidates and un-graduation proposals appear under Recommended without any artifact write or demotion, and the report is the sole deliverable.

If Phase 0 produces nothing (no categorized entries, only legacy) AND Phase 0.5 produces nothing (no glossary files), the skill exits cleanly with the legacy-skip count.
