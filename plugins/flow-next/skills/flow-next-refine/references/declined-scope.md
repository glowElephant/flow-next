# Refine — declined-scope ledger

Read when the person declines a feature or scope as product judgment: we could build it, and we are choosing not to.

Record it in `.flow/memory/declined/<concept-slug>.md` on the first such refusal: a title, the decision in one line, short reasoning, then `## Prior requests` opened with today's date and the request that just came in. When the file already exists, append the dated line to `## Prior requests` and leave the decision untouched. Write the file yourself, like the rest of `.flow/memory/`; there is no flowctl verb for it. The entry follows the artifact prose contract in [docs/prose.md](../../../docs/prose.md) when that doc exists.

Never write an entry for scope declined because it already exists, is already planned, or lives in another spec. That is an answer, not a refusal, and recording it would teach the next planner that shipped capability is rejected scope. A skipped question is not a decline either; it goes to `## Open Questions`.
