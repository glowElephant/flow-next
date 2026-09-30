# capture: manual smoke (maintainer checklist)

Moved out of the shipped skill in 7.0; never loaded at runtime.

> Maintainer-facing. A capture session never needs this file; it is the manual validation
> description for prose changes to the skill.

## Manual smoke

The skill itself is markdown — there's no unit-test surface. The validation is invoking `/flow-next:capture` in a real session. Expected behavior:

- Phase 0 walks `.flow/specs/`, runs memory search if memory is initialized, detects compaction, applies idempotency. Branches into duplicate-detection question if ≥2 strong matches; exits cleanly on `abort`.
- Phase 1 emits a `## Conversation Evidence` block with verbatim user quotes (≤30 lines).
- Template decides the sections: with the bundled template the saved spec carries `## Conversation Evidence`; with a repo-root `SPEC.md` whose `auxiliary_sections` list omits it, the saved spec does not, and untagged lines are still checked against the Phase 1 evidence.
- Phase 2 tags only what capture authored: user-verbatim criteria stay untagged (and are findable in the evidence), rewording is `[paraphrase]`, fill-in is `[inferred]`. Stated business context lands in its owning section as the user's words or `[paraphrase]`; with no business signal nothing is added.
- Phase 3 fires must-ask cases only when (a) title is genuinely ambiguous, (b) acceptance is untestable, (c) scope-conflict persists. Optional ambiguities are deferred to Phase 4.
- Phase 4 materializes the body once and checks source-tag findability. An N>1 split gets one explicit choice, never a second body-approval question. Pre-rewrite readiness is observed before the write; no readiness question runs yet. Autofix retains its draft-only result without `--yes`.
- After Phase 5 writes the body, the saved-spec summary and editor offer run. The editor opens the actual spec and its changes are reread before follow-ups; a correction shows only its diff and never asks for generic re-approval. Stopping review preserves the saved file. Separate glossary and readiness questions keep their conditions and honor answers already supplied by the user. Capture-only intent never dispatches implementation.
- Phase 5 calls `flowctl spec create --plan-file <literal draft path>` (consumes the §4.1 draft file — no heredoc re-authoring). Approved term-adds written via `flowctl glossary add` (5.8, interactive only). Consented mark-ready written via `flowctl spec ready` (5.9, interactive only). Rewrite branch (5.3) runs idempotent `spec unready` unconditionally; `READY_RESET` gates the Phase 6 announcement. With no glossary (or a husk), 2.7/5.8 are silent no-ops; with readiness un-adopted, 4.2's predicate / 5.9 question and write / all readiness close lines are silent no-ops — zero behavior change.
- Phase 6 prints `Spec captured at …`, `Tracker sync:` only when the bridge is active, and `Recommended next:` judged from `plan-vs-no-plan.md` (omitted under `from:flow`, where the conductor reports the next step); no command menu, no business-refine suggestion.

The two autofix end-states (`--yes` absent vs present) are stated once in [autofix-mode.md](../../plugins/flow-next/skills/flow-next-capture/references/autofix-mode.md) § Autofix exit summary — smoke both against that wording.
