# Plan — declined-scope ledger

Read when the plan rejects scope as product judgment: we could build it, and we are choosing not to.

Record it in `.flow/memory/declined/<concept-slug>.md` on the first such refusal: a title, the decision in one line, short reasoning, then `## Prior requests` opened with today's date and this request. When the file already exists, append the dated line to `## Prior requests` and leave the decision untouched. Write the file directly, like the rest of `.flow/memory/`; it is memory, not a plan artifact, so the rule that specs and tasks go through `flowctl` is unchanged. Its prose follows [docs/prose.md](../../../docs/prose.md) when that doc exists.

Never write an entry for scope declined because it already exists, is already planned, or belongs to another spec: that is not a refusal, and recording it would teach the next planner that shipped capability is rejected scope. Size-and-sequencing trims ("not this task", "not this milestone") are ordinary `## Boundaries` lines, not ledger entries.
