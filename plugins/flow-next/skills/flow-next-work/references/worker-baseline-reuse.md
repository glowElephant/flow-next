# Worker baseline reuse (gated reference)

> **Read by the worker at the Phase 1 baseline only when the spec's Quick commands include a full
> gate command (a full test suite or a smoke script), or its prompt carries `BASELINE_HANDOFF`.**
> A green receipt or a handoff can then stand in for the baseline run. Without either, run the
> baseline as worker.md Phase 1 states and never read this file.

```bash
# When the repo ships a parallel full-suite entrypoint (flow-next itself: `python3 scripts/run_tests_parallel.py`,
# serial fallback `--serial`), specs list it as the full-suite Quick command; its exact string is the receipt identity.
# Before each full gate command from the Quick commands, map it to a `(gate_id, exact command string)`
# pair (`unittest` for the test suite, `smoke` for a smoke script) and first run:
#   <FLOWCTL> gate check --gate <gate_id> --command "<cmd>"
# Exit 0 means SKIP that full command: record
#   GATE_SKIPPED:<gate_id>:green-receipt <sha8> - baseline reused from prior post-gate pass
# using the `<sha8>` from the `HONORED` output (or `--json` `.sha8`). A reused green receipt
# counts as `baseline: green` via receipt. On exit 1 or 2+, run the full command exactly as
# today: fail closed, and never treat a check error as a skip. Lint/format commands are unchanged:
# always run, never receipted, never skipped.
# Check git log --format= --name-only <verified-sha>..HEAD (not only the net diff).
# A handoff is valid only if every path changed since its verified SHA is under .flow/.
# Any other changed path invalidates it: run the baseline normally.
# When BASELINE_HANDOFF is present, record `baseline: green via handoff (<content>)`
# and SKIP running the focused Quick commands as baseline (lint/format stay exactly
# as stated above: always run, never skipped). The red-baseline
# rules above are unchanged and the handoff never applies to them (a handoff asserts
# green, so the red branch is unreachable via handoff). Full-suite gate commands keep
# their existing receipt-check path unchanged. The wave route keeps its first-task
# baseline. The rolling first batch may reuse the conductor's green spec-base
# baseline for the SAME commands, under the same .flow/-only handoff rule.
```

("The red-baseline rules above" are worker.md Phase 1's Baseline check. When an exit-1/2+ gate check requires the full command, run it under that Phase's suite-output capture rule.)
