# Lighter refine: ask only what would change the build

## Goal & Context
<!-- scope: business -->
<!-- Goal & Context: 25% [user], 55% [paraphrase], 20% [inferred] -->

Refine interviews take far too long, and they produce requirements nobody asked for. With strong current models, spending two hours answering technical questions is rarely worth it. [paraphrase] Two problems drive this: the router recommends refine (especially the technical pass) even in mature projects whose patterns already answer the questions, and innocuous questions such as "should we focus on performance?" turn into harsh acceptance criteria like "must load in 20 ms" that the agent then chases. [paraphrase]

Refinement should focus on what is unclear or unknown, so the agent does not build the wrong thing, not on what implementation will discover or what is obvious. [paraphrase] This is another kind of overengineering, and it runs against the trend toward lighter pipelines: verification and QA stay rigorous, while the steps before the agent acts get lighter. [paraphrase]

Target user: anyone who runs or is routed into `/flow-next:refine`, product owners and developers alike. [inferred]

## Architecture & Data Models
<!-- scope: technical -->

**What refine asks (both passes).**

- One test decides whether a question is asked: a wrong guess would build the wrong thing or ship behaviour the user would reject; the code, the docs, a quick experiment or implementation itself cannot settle it; and it is the answerer's call. Everything else the agent resolves, records, or leaves to work. [paraphrase]
- The topic checklists in the business and technical question banks are replaced by a short note per bank of things to check the spec for and ask about only when unclear (business: who it is for, what done looks like, what is explicitly out, a constraint the domain implies; technical: an irreversible data or contract change, an external interface, a security boundary). The bank files stay because `flowctl scope bank` loads them. [paraphrase]
- Removed: "Expect 40+ questions", the rule that non-functional probes always qualify however thin the spec, and the "dig deep", "continue until complete" and "surface hidden complexity" guidelines. Kept: the fact-versus-decision taxonomy, experiment-answerable questions, a recommended answer with every question, the no-deadlines rule, skipped questions parked rather than assumed, plain language, and rounds that ask the whole frontier. [paraphrase]
- Refine stops when no build-changing question remains. "Nothing worth asking; the spec is clear enough to build" is a valid, good outcome. [paraphrase]
- Precision rule: an answer is recorded at the precision the user gave it. A preference ("performance matters here") goes to Decision Context as guidance, not an acceptance criterion; a number becomes a criterion only when the user stated it; the agent's recommended options never become thresholds; neither pass asks for success metrics or latency budgets unless the spec is about them. [paraphrase]
- The business pass reads `STRATEGY.md` and searches the other project docs for what the spec touches, instead of reading README and CHANGELOG in full before its first question. [inferred]

**When to route to refine (and when not).**

- One rule, stated beside the existing "unresolved product or authority choices route to refine" sentence in the plan-versus-no-plan reference: refine only when at least one open decision can be named that would change what gets built and that only the human can make. Do not refine when the acceptance criteria state the intended behaviour and what remains is how; when the touched area has established patterns; when the only gaps are technical detail, performance or edge cases that implementation, review and QA will surface; when the only uncertainty is criteria capture inferred itself; or for a defect, a structural cleanup or a measured-improvement request. The technical pass needs a named technical fork that is costly to reverse and that the code does not answer (a data model or migration, a public contract, a security boundary). [paraphrase]
- The structured-brief routing row stops defaulting into refine ("narrow or skip refine only after synthesis establishes no material gaps" becomes: skip refine unless a named product or authority decision is open), and the refine row's positive signal requires the open decision to be named. The judge's matching presentation text is synced with its pin tests; the criteria text the judge classifies on is unchanged. [paraphrase]
- Prospect's ranked ideas and promoted ideas recommend `/flow-next:flow <id>` instead of a hard-coded `/flow-next:refine`, so the router decides. [paraphrase]
- Capture's business-refine suggestion that fires on sparse business signals is removed; its `Recommended next:` line already applies the routing rule. [paraphrase]
- Refine's scope recommendation no longer recommends the technical pass because technical sections are empty, and the business pass no longer writes the `*Pending technical-scope interview pass.*` placeholder (removed from the write policy). [paraphrase]

## Acceptance Criteria
<!-- scope: both -->

- **R1:** Both refine passes ask a question only when it passes the one test; the business and technical banks carry a short check-list note instead of topic lists; "Expect 40+", the always-qualify non-functional rule and the dig-deep, continue-until-complete and hidden-complexity guidelines are gone. [paraphrase]
- **R2:** Refine ends as soon as no build-changing question remains, and reports "the spec is clear enough to build" when it asked nothing. [paraphrase]
- **R3:** Refine writes a user's preference to Decision Context as guidance; a numeric or measurable acceptance criterion appears only when the user stated the number or commitment; the agent's recommended options never become thresholds. [paraphrase]
- **R4:** The routing rule for when to refine and when not is stated once in the plan-versus-no-plan reference, and capture, flow and plan apply it. [paraphrase]
- **R5:** The structured-brief and refine routing rows no longer default into refine, and the judge presentation text and pin tests match; the judge's classification criteria text is unchanged. [paraphrase]
- **R6:** Prospect recommends `/flow-next:flow <id>` for survivors and promoted ideas; capture's sparse-business refine suggestion is gone. [paraphrase]
- **R7:** Refine's scope recommendation no longer picks the technical pass because technical sections are empty, and no pass writes the pending-technical placeholder. [paraphrase]
- **R8:** The business pass no longer reads README and CHANGELOG in full before its first question. [inferred]
- **R9:** The refine, capture, prospect and flow pages on flow-next.dev describe the lighter interview and the routing rule; the conduct checklists for refine and capture match; the full test suite passes. [inferred]

## Boundaries
<!-- scope: business -->

- No new mechanism: no question budget, maturity detector, config key or check. [paraphrase]
- Refine is still never dispatched by `flow --auto`; `--scope=research` and chart keep their own triggers. [inferred]
- The business, technical and both scopes and their write policies stay in this spec; collapsing them is the dependent spec that follows. [paraphrase]

## Decision Context
<!-- scope: both -->

### Motivation
<!-- scope: business -->

"refinement/interviews should heavily focus on what is potentially unclear/unknown so that the agent doesn't go off and build things incorrectly, not on things that will be discovered during implementation, are obvious etc." [user] "given then strenght of newer models like opus 5.5 and gpt-6-astra, it is debatable if it is worht answering 2 hours of techincal questions." [user] "there is a gerneral trend towards lighter pipelines as we've seen, dropping planning etc. verification, qa all great but somethings need to be lighter" [user]

## Strategy Alignment

Serves "Agent first" and "Remember the bitter lesson": the agent settles what the code and implementation can settle, and the human answers only decisions that change the build.

## Strategy Conflicts

None found.
