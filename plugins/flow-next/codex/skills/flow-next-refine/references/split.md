# Refine — split proposal

Read before the write-back when the refined criteria reach 8 or more, or visibly serve more than one independently shippable outcome.

Apply [spec-count.md](../../flow-next-flow/references/spec-count.md): it owns what counts and the independence partition. Propose a split only when its partition yields more than one spec; a large but cohesive set is one spec, and the summary says so.

**Ask the user via plain text.** Render the options below as a numbered list `1.` … `N.`, followed by a final option `N+1. Other — type your own answer`. Print the question, then the numbered list, then **stop and wait for the user's next message before continuing**. Parse the reply as: a bare number `1`–`N+1` → that option; the literal text of an option label → that option; free text after `Other` → custom answer.

When it does, print the allocation as ordinary markdown (per-spec titles, allocated criteria, dependency edges), then ask one short `plain-text numbered prompt`: `keep-single` (the default), `split-as-proposed`, or `adjust`.

On `split-as-proposed`:

- Create each new spec with one `$FLOWCTL spec create --title "<title>" --plan-file <literal path> --json` call. Its body is self-contained, and its allocated criteria are renumbered from R1 in the new spec.
- Remove the moved criteria from the source spec's write-back.
- Record the edges with `$FLOWCTL spec add-dep <spec-id> <depends-on-id> --json`.

Criteria a review has already judged are never moved or renumbered: keep them in place and record the proposal in `## Decision Context` instead. An unattended run never splits; it records the proposal in `## Decision Context` as `### Split proposal (unactioned)`.
