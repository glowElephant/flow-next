# memory-migrate: manual smoke (maintainer checklist)

Moved out of the shipped skill in 7.0; never loaded at runtime.

The skill itself is markdown — there's no unit-test surface. The validation is invoking `/flow-next:memory-migrate` in a real session. Expected behavior:

- Phase 0 detects legacy files via `flowctl memory list-legacy --json`, skips already-migrated ones, applies scope hint, prints triage summary.
- Phase 1 iterates entries one per tool call; mechanical defaults applied unless body warrants override; ambiguous entries asked (interactive) or marked needs-review (autofix).
- Phase 2 writes via `flowctl memory add --track <t> --category <c> ...`. Slug uniqueness handled.
- Phase 3 verifies round-trip + prints report.
- Phase 4 (optional) renames originals to `_migrated/<filename>.bak`; first-run writes `_migrated/.gitignore: *`.

In autofix mode (`/flow-next:memory-migrate mode:autofix`), Phase 1 ambiguity routes to needs-review, Phase 4 default-declines, and the report is the sole deliverable.

If Phase 0 produces an empty `WORKING_SET` (all files already migrated, or no legacy files exist), the skill exits cleanly with the appropriate message.
