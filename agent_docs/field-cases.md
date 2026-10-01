# Field cases

Dated dogfood runs kept for maintainers. Moved verbatim from the shipped `plugins/flow-next/docs/orchestration.md`; shipped docs carry no dated runs (see [docs-conventions.md](docs-conventions.md)). Cross-references in the moved text point at sections of that page.

## Field case: one paragraph, 38 PRs landed

One unattended run building a Linux desktop app in a private repo landed **38 pull requests**, steered by a single paragraph of standing policy with nobody in the loop. Each item was planned or worked directly by judgment, reviewed by another model family, QA'd in the running app, CI-green, and merged with a receipt.

The policy steered both routing axes. The host chose the pipeline shape per item and the model per job; the build driver (pilot ticks then; `flow --auto` now) advanced the work toward pull requests, and land handled CI and review convergence through merge.

| Run outcome, as of 5 September 2026 | Result |
|---|---|
| Pull requests landed | 38 |
| Steering | One paragraph of standing policy, nobody in the loop |
| Pipeline shape | Planned or worked directly, chosen by judgment per item |
| Review | Another model family reviewed each item |
| Live QA | Each item exercised in the running app |
| Merge evidence | CI green and a receipt for each merged pull request |

The useful pattern is the malleable pipeline. One policy can send a fully understood change directly to work and give another change a planning pass, while assigning models and verification to suit the job. Rung 5 below shows how to write that kind of standing policy for your own repo.
