# `--explain`

Read only when `EXPLAIN=1`. An explain run writes nothing under `.flow/` and dispatches nothing.

Add `--explain` to the same `--json` judge call Step 2 makes (never a second request). The result
gains an `explain` list holding the `Next:`, `Route:`, `Signal:`, `Skip/narrow:` and `Why not the
alternatives:` lines; print them. The signal names the firing fact-grade Noul and its probability;
the alternatives name the next two kinds and their probabilities. A below-floor result names all
three candidates and says the host decides. When the judge is off at intake (no call is made) or
unavailable, resolve the route from the matrix yourself, print `Next:` and `Skip/narrow:` from that
row, `Route: <route> (host)` or `Route: host (jev-unavailable(<reason>))`, and the reason (`judge:
off` or the unavailable reason) as the `Signal:`. Then stop.

Recommendation shape (also used by closers that recommend a next step): lead with the exact words
or slash command to run next, then

```
Next: <natural-language prompt or slash command>

Route: <name>
Signal: <positive signal matched>
Skip/narrow: <the safe skip or narrow condition>
Skip kind: signal absent | despite unresolved risk
Why not the alternatives: <one line>
```
