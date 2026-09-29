# Conduct checklist — `quality-auditor`

A correct run audits the diff along **one** named axis of the two-axis in-host audit — correctness or standards — and reports within that axis's tiers, caps, and output budget.

- [ ] The report covers exactly the axis named in the dispatch's `AXIS:` line; findings belonging to the other axis appear as at most 2 untiered `Out-of-axis observation:` lines. A dispatch with no `AXIS:` line produces a correctness-axis report opened by `Axis defaulted: correctness (no AXIS line in dispatch)`. A silent default, or a both-axes report, has broken this.
- [ ] A standards-axis report contains no `### Critical` section and no finding tiered Critical, and its summary carries `Blocking: none possible (standards axis)` in place of a `Ship:` verdict.
- [ ] Finding caps hold — at most 8 tiered / 3 Consider on the correctness axis, at most 5 tiered / 3 Consider on standards — and any overflow is declared as `+N over cap` in the `Suppressed findings:` line rather than dropped silently.
- [ ] A diff that cannot be produced yields `Audit FAILED: <reason>` and stops. A clean verdict emitted over an unresolved base or an empty diff has broken this.
- [ ] Every verification statement carries exactly one of the five evidence labels — claimed / cited / walked / executed / reproduced — and a safety claim that did not reach *executed* is stated at its actual label. A walked safety property presented as verified or tested has broken this.
- [ ] Structural checks fire within their bounds: type leakage only on types the diff introduces or newly exposes; the file-size check only on files that cross 1000 lines in this diff, tiered at most Should-Fix; a shallow-module finding only with its falsifiable sign; and a finding whose natural fix is a comment names the structural constraint instead.
