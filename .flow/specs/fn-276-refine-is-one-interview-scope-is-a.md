# Refine is one interview; scope is a filter

## Goal & Context
<!-- scope: business -->
<!-- Goal & Context: 25% [user], 55% [paraphrase], 20% [inferred] -->

Refine today is three interviews: business, technical and both, each with its own question bank, its own write policy enforced by `flowctl scope`, section bookkeeping between passes (Decision Context split into two sub-headings), and a scope question before anything is asked. [paraphrase] After the lighter-refine spec, one rule decides every question, so the separate passes are machinery the interview no longer needs. [paraphrase]

The maintainer's direction: collapse refine into one interview and keep scope as a filter so people can keep working as they have been, and let the filter take scopes that are not predefined, such as QA. [paraphrase]

Target user: product owners, developers, QA engineers and anyone else who refines a spec, alone or in separate sessions. [inferred]

## Architecture & Data Models
<!-- scope: technical -->

- **One interview.** Refine asks the open decisions that would change what gets built (the lighter-refine test), whether product, technical or anything else, and writes each answer to the section it belongs in. [paraphrase]
- **Scope is an optional free-text filter.** `--scope=<anything>` (business, technical, QA, security, ...) focuses the interview on that audience's decisions; the agent interprets the lens. `--biz` and `--tech` stay as aliases. No scope means no filter and no scope question up front. [paraphrase]
- **Removed:** the scope question, the per-scope write policies and the `flowctl scope` subcommands that enforce them, the Decision Context sub-heading split driven by passes, the two-phase `both` run, and the per-scope question-bank files (their check notes fold into one short list). [paraphrase]
- **Kept:** existing specs load unchanged (their section layout is left as written), answers never overwrite a section the user did not touch this session without saying so in the read-back, `--scope=research` stays a distinct no-questions research mode, and write-back and read-back are unchanged. [paraphrase]

## Acceptance Criteria
<!-- scope: both -->

- **R1:** Refine runs one interview with no scope question; each answer is written to the section it belongs in. [paraphrase]
- **R2:** `--scope=<value>` accepts any value, including values with no predefined meaning such as `qa`, and focuses the questions on that audience's decisions; `--biz` and `--tech` still work. [paraphrase]
- **R3:** `--scope=research` keeps its current no-questions research behaviour. [inferred]
- **R4:** The per-scope write policies, the `flowctl scope` subcommands that serve only them, the pass-driven Decision Context split, the `both` two-phase run and the per-scope bank files are removed with their tests; specs written under the old layout still load and refine without being rewritten. [paraphrase]
- **R5:** The read-back names every section the session changed, so a person refining their own layer sees any change outside it. [inferred]
- **R6:** The refine page and scope docs on flow-next.dev, the conduct checklist and the flowctl reference match, and the full test suite passes. [inferred]

## Boundaries
<!-- scope: business -->

- No new mechanism replaces the removed write policies; the read-back is the safeguard. [paraphrase]
- Capture, plan and chart are unchanged beyond references to the removed scope behaviour. [inferred]

## Decision Context
<!-- scope: both -->

### Motivation
<!-- scope: business -->

"we do that and keep the scope as a filter so ppl can work as they have been, it should also work for scopes like QA that aren't defined" [user] The per-scope machinery existed so a product owner and a developer could refine their own layers without overwriting each other; a read-back that names every changed section keeps that visible without write policies. [paraphrase]

Depends on the lighter-refine spec, which changes the same refine files first.

## Strategy Alignment

Serves "Agent first": the scope becomes guidance for the interviewer instead of enforced structure.

## Strategy Conflicts

None found.
