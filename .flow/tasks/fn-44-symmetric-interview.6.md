---
satisfies: [R12, R13, R14, R15, R18]
---

## Description

Canonical user-facing docs sweep. `docs/teams.md` handover-objects table + walkthrough headers + Symmetric-interview subsection + ASCII flowchart + Lifecycle map mermaid all rewritten to make the one-spec-evolving model unambiguous (currently uses "business spec" / "full spec" nouns that imply two specs). `GLOSSARY.md` Handover-object entry similarly rewritten. `README.md` audit for "two specs" misread + version badge bump to 1.1.0.

**Size:** M
**Files:**
- `plugins/flow-next/docs/teams.md` (multiple surgical edits)
- `GLOSSARY.md` (handover-object entry rewrite)
- `plugins/flow-next/README.md` (badge + audit)

## Approach

`docs/teams.md` surgical edits (repo-scout citations):
- L67 / L68 handover-objects table rows 1-2: "Business spec" / "Full spec" → "Spec — business-layer complete" / "Spec — fully complete" (or similar). Update "Produced by" column to reference `--scope=business` / `--scope=technical` where existing prose says `--strategy --docs`.
- L112 walkthrough header `### [2] Business-layer spec — Handover #1` → `### [2] Spec, business-layer complete — Handover #1`
- L120 walkthrough header `### [3] Full spec — Handover #2` → `### [3] Spec, fully complete — Handover #2`
- L37-55 Lifecycle map mermaid: annotate `/flow-next:interview` node to indicate scoped operation (label change or small branch arrow)
- L269-291 Symmetric-interview subsection + ASCII flowchart: (a) replace `--strategy --docs` with `--scope=business` / `--scope=technical`, (b) rename handover labels from "business spec → tech lead" / "full spec → developer" to "spec biz-layer complete" / "spec fully complete", (c) add paragraph: supplementary design docs (`docs/design/<topic>.md`, ADRs) are separate artefacts cross-linked from the spec, NOT the spec itself.

`GLOSSARY.md:17` Handover-object entry: rewrite "flow-next defines six: business spec (#1), full spec (#2), implementation plan (#3), …" to make handovers #1 and #2 unambiguously the same spec at different completion states. Suggested phrasing: "Six handover states: spec at business-layer completion (#1), spec at full completion (#2), implementation plan (#3), …".

`plugins/flow-next/README.md`: audit for "two specs" misread; mermaid blocks (around L89-105) reference `/flow-next:interview` — verify no inherited misread. Update version badge from `Version-1.0.2` to `Version-1.1.0`.

## Investigation targets

**Required:**
- `plugins/flow-next/docs/teams.md:37-55,65-72,89,112,120,122,124,267,269-291` — all surgical edit points
- `GLOSSARY.md:15-17` — Handover-object entry
- `plugins/flow-next/README.md:1-20` — version badge area
- fn-44 spec R12, R13, R14, R15, R18

**Optional:**
- AI-x-SDLC-Starter-Kit methodology guide cross-link from teams.md (out of scope per fn-44 Boundaries, but verify link target isn't broken)

## Acceptance

- [ ] `docs/teams.md` handover-objects table rows 1-2 use unambiguous same-spec-evolving phrasing
- [ ] `docs/teams.md` walkthrough headers [2] and [3] match table phrasing
- [ ] `docs/teams.md` Symmetric-interview subsection + ASCII flowchart use `--scope=business` / `--scope=technical`; handover labels rewritten
- [ ] Symmetric-interview subsection includes supplementary-design-docs-are-separate paragraph
- [ ] Lifecycle map mermaid annotates `/flow-next:interview` as scoped
- [ ] `GLOSSARY.md` Handover-object entry rewritten; #1 and #2 unambiguously same spec
- [ ] `plugins/flow-next/README.md` version badge bumped to 1.1.0; no "two specs" misread surfaces in audit

## Done summary

## Evidence
