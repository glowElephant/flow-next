---
satisfies: [R1, R5]
---

## Description

Add the **Cua Sandbox** rung — driving an app inside an isolated VM/container — which lifts the Native rung's current hard limitation ("Computer Use is never on a headless/CI path"). Extend `references/cua.md` (created in task .1) with the sandbox surface. **Less-grounded than the local driver** (the local Cua Driver was validated live; the Sandbox SDK was NOT) — read the upstream Sandbox SDK / Lume docs and validate provisioning before asserting behavior.

Still pure host-driven (the host drives the Sandbox SDK / MCP) — **no flowctl plumbing**.

**Size:** M
**Files:** `plugins/flow-next/skills/flow-next-drive/references/cua.md` (extend), `plugins/flow-next/skills/flow-next-drive/SKILL.md` (precedence note for the headless path)

## Approach

- Document the sandbox as the **headless/CI-only** rung in the Native-rung precedence: it is the *only* option on a headless path (local Computer Use can't run there), and ranks below local-takeover on the *attended* path purely on cost/latency — so it does not conflict with task .1's attended ordering.
- **Two backends, very different profiles:** **local** `lume`/QEMU = default, zero-network; **cua.ai cloud** = explicit opt-in only — it *receives the driven screen* (data egress) and bills. Never auto-select the cloud; document the credential + cost + egress implications.
- **Teardown discipline — no leaked VMs:** the rung owns the VM lifecycle; tear down on success AND on error/abort. Surface the first-pull multi-GB "coffee break" so it doesn't look like a hang.
- Detection: `cua` SDK / `lume` present, or a configured cua.ai endpoint. Opt-in per run, never the default native path.
- **Host-agnostic** (consistent with task .1): the sandbox prose must read cleanly in the Codex mirror — run `scripts/sync-codex.sh` and inspect the generated mirror for coherent multi-host wiring; **no `cmp`/byte-identical claim** (skill-local references ride the skill-dir copy + rewrites).

## Investigation targets
**Required:**
- `plugins/flow-next/skills/flow-next-drive/references/cua.md` — the file task .1 created (extend, don't duplicate)
- Sandbox SDK docs: cua.ai/docs (sandbox-sdk) ; Lume: cua.ai/docs/lume/guide/getting-started ; cloud: cua.ai/docs/computer-sdk/cloud-vm-management
**Optional:**
- `plugins/flow-next/skills/flow-next-drive/references/computer-use.md:91-111,144-156` — detection + degradation patterns

## Acceptance
- [ ] `references/cua.md` documents the Cua Sandbox rung: detection, provision + teardown (no leaked VMs), the headless/CI unlock.
- [ ] Local `lume`/QEMU is the default sandbox backend; **cua.ai cloud is explicit opt-in** with credential/cost/data-egress noted and never auto-selected.
- [ ] The sandbox is positioned as headless/CI-only in the precedence list (composes with task .1's attended ordering).
- [ ] `cua-sandbox` is a valid `driver_rung` value; seam unchanged.
- [ ] Reference reads coherently in the Codex mirror after `sync-codex.sh` (inspect; not a byte-identical claim); no flowctl plumbing added.
- [ ] Every unvalidated Sandbox/Lume/cloud behavior is marked **"verify at build"** unless the implementer records an actual provisioning run.

## Done summary
TBD

## Evidence
- Commits:
- Tests:
- PRs:
