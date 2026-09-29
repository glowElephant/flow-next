---
name: flow-next-work
description: Execute a flow-next spec or task end-to-end with worker subagents, gates, and commits. Use when asked to work on, implement, or execute fn-N.
user-invocable: false
---

# Flow work

Execute a plan systematically. Focus on finishing.

**`.flow/` is the only task tracker.** A run that recorded task state in a markdown TODO, a plan file, TodoWrite, or any other tracker has broken this — all task state is read and written via `flowctl`.

## Preamble

**CRITICAL: flowctl is BUNDLED — NOT installed globally.** `which flowctl` will fail (expected). Define once; subsequent blocks (here and in `phases.md`) use `$FLOWCTL`:

```bash
FLOWCTL="${CODEX_HOME:-$HOME/.codex}/scripts/flowctl"
[ -x "$FLOWCTL" ] || FLOWCTL="<plugin-root>/scripts/flowctl"   # <plugin-root> = the directory two levels above this skill's SKILL.md file (the harness gave you that file's absolute path when the skill loaded); substitute it literally
[ -x "$FLOWCTL" ] || FLOWCTL=".flow/bin/flowctl"
```

**Hard requirements (non-negotiable):**
- **Every completed task passes through `flowctl done` and a verified `done` status.** A task treated as finished while `flowctl show <task>` still reads `todo` or `in_progress` has broken this.
- **Staging is the files you changed plus `.flow/` (`git add -- <files> .flow/`), never `git add -A`** — `.flow/` carries the run's task state; files a test run or tool wrote stay out of the diff. A commit whose diff omits the run's `.flow/` writes has broken this.
- **Completion is claimed only after `flowctl show <task>` reports `status: done`.** A completion claim printed ahead of that read has broken this.
- **`$flow-next-impl-review` is dispatched only on a green tree.** A review sent while tests or Quick commands are red has broken this.

**Role**: execution lead, plan fidelity first.
**Goal**: complete every task in order with tests.

## Autonomous Mode (questions off, no receipt obligations)

Before gates, treat this host-expanded block as literal prompt data, never shell:

<work-arguments>
$ARGUMENTS
</work-arguments>

Strip standalone whitespace token `mode:autonomous` into `WORK_ARGS`; preserve
all else verbatim (spaces/quotes/globs). Set/export `AUTONOMOUS=1` if found or
`FLOW_AUTONOMOUS=1`; otherwise set/export `AUTONOMOUS=0`.

Continue with `WORK_ARGS`; carry the exported marker into later shell fragments.
If `AUTONOMOUS=1`:

- **No setup question is asked** (branch + review questions below are suppressed). A run that puts either question to the user under `AUTONOMOUS=1` has broken this.
- **Branch defaults deterministically to `--branch=new`** when no explicit branch option is present — under autonomy "the user's answer" never exists, and defaulting to the current branch could commit straight to main. A chained spec (`flowctl spec chain` names a parent) forks from the parent's remote tip instead of main (phases.md Phase 2). **Name the new branch exactly the spec's `branch_name` field** (`$FLOWCTL show <spec-id> --json | jq -r '.branch_name'`) — the branch matrix of `flow --auto`, its all-done PR probe, and make-pr's branch-match spec detection all key on that name; an ad-hoc name breaks continuity across hops and invocations.
- **Review** = explicit `--review` passthrough if present, else the configured backend (`none` when `REVIEW_BACKEND` is `ASK`).
- **Never hang on a question.** A genuinely unanswerable ambiguity → stop cleanly with a one-line `NEEDS_HUMAN: <reason>` report instead of asking.

## Input

Full request after mode parsing: `$WORK_ARGS`

Accepts:
- Flow spec ID `fn-N-slug` (e.g., `fn-1-add-oauth`) or legacy `fn-N`/`fn-N-xxx` to work through all tasks
- Flow task ID `fn-N-slug.M` (e.g., `fn-1-add-oauth.2`) or legacy `fn-N.M`/`fn-N-xxx.M` to work on single task
- Markdown spec file path (creates spec from file, then executes)
- Idea text (creates minimal spec + single task, then executes)
- Chained instructions like "then review with /flow-next:impl-review"

Examples:
- `/flow-next:work fn-1-add-oauth`
- `/flow-next:work fn-1-add-oauth.3`
- `/flow-next:work fn-1` (legacy formats fn-1, fn-1-xxx still supported)
- `/flow-next:work docs/my-feature-spec.md`
- `/flow-next:work Add rate limiting`
- `/flow-next:work fn-1-add-oauth then review via /flow-next:impl-review`

If no input provided, ask for it.

## FIRST: Parse Options or Ask Questions

Check configured backend:
```bash
REVIEW_BACKEND=$($FLOWCTL review-backend)
```
Returns: `ASK` (not configured), or `rp`/`codex`/`copilot`/`cursor`/`claude`/`host`/`none` (configured).

### Option Parsing (skip questions if found in arguments)

Parse `WORK_ARGS` for these patterns. If found, use them and skip corresponding questions:

**Branch mode**:
- `--branch=current` or `--current` or "current branch" or "stay on this branch" → current branch
- `--branch=new` or `--new-branch` or "new branch" or "create branch" → new branch
- `--branch=worktree` or `--worktree` or "isolated worktree" or "worktree" → isolated worktree

**Review mode**:
- `--review=codex` or "review with codex" or "codex review" or "use codex" → Codex CLI
- `--review=copilot` or "review with copilot" or "copilot review" → GitHub Copilot CLI
- `--review=cursor` or "review with cursor" or "cursor review" → Cursor CLI (`cursor-agent`)
- `--review=claude` or "review with claude" or "claude review" → Claude Code CLI (`claude -p`; same-family on a Claude Code host, recorded in the receipt)
- `--review=host` or "host review" or "host-native review" → host-native fresh-context reviewer subagent (cross-family pin from the AGENTS.md model-routing section)
- `--review=rp` or "review with rp" or "rp chat" or "repoprompt review" → RepoPrompt chat (via `flowctl rp chat-send`)
- `--review=none` or `--no-review` or "no review" or "skip review" → no review
- `--review=export` or "export review" or "external llm" → REFUSE at parse time, before any dispatch: export is not an impl-review backend — never fall through to the configured backend and never pass it as `REVIEW_MODE`; stop and point at `/flow-next:plan-review --review=export`, where export lives

(All non-`none` review modes route through `$flow-next-impl-review`, which resolves the
configured/overridden backend — codex, copilot, cursor, claude, rp, or host — itself.)

**No-plan (direct spec execution)**:
- `--no-plan` or "no plan" or "skip planning" or "work directly without planning" → set `NO_PLAN=1`; it pre-answers Phase 1's zero-task fork so the fork's ask never fires when intent is stated
- The spec's own `no_plan` field (`no_plan: true` in `$FLOWCTL show <spec-id> --json`, set at capture time or via `flowctl spec set-no-plan`) counts the same as the flag: it is an explicit human instruction carried by the item, read at Phase 1's fork, never inferred
- Contradictory signals (the flag or field says direct, the prose asks to plan first) → the fork asks instead of guessing
- Existing intentional tasks govern despite a stale direct signal. A sole `implicit_owner` task under `no_plan: true` retains the direct route on resume; Phase 1 resolves the distinction.
- The fork's recommendation comes from the shared rule in [`plan-vs-no-plan.md`](../flow-next-flow/references/plan-vs-no-plan.md), read only when the fork fires; implementation review, coverage, completion policy and opt-in QA remain unchanged on this route.
- The fork's semantics (ask, autonomous refusal, durable choice, implicit-task mint) live in phases.md Phase 1's gated [references/no-plan-route.md](references/no-plan-route.md), read only when the fork fires

**Autonomous mode**:
- `AUTONOMOUS=1` → suppress all setup questions; use the defaults above.

### If the options are absent from the arguments

**If `AUTONOMOUS=1` (autonomous mode):** ask nothing — apply the autonomous defaults and continue to the workflow.

**Otherwise (interactive)**: do not ask about the branch. Stay on the current branch when it is
not the default branch, otherwise create a new one (named for the spec's `branch_name`), and say
which in one line. Ask only when `REVIEW_BACKEND` is `ASK`: then read
[references/setup-questions.md](references/setup-questions.md) and ask its review question before
reading or writing anything else.

Done when: the branch mode (and, under `REVIEW_BACKEND=ASK`, the review mode) is resolved from
arguments, this default, the user's answer, or the autonomous defaults.

## Workflow

Read [working-rules.md](../../references/working-rules.md) first; it holds on every phase and in every worker dispatch.

After setup questions answered, read [phases.md](phases.md) and execute each phase in order.

**One task is implemented inline by this conversation** (phases.md Phase 3). Several tasks, or a
task that goes to a worker, follow [references/multi-task.md](references/multi-task.md), which owns
scheduling (rolling or wave), workers, review ownership after integration, and the completion
review gate.

## Tracker sync (opt-in, off by default)

A tracker touchpoint fires only when `flowctl sync active --json` reports `active: true` and its
event is opted in; otherwise nothing happens and [references/tracker-touchpoints.md](references/tracker-touchpoints.md)
is never read. A tracker key (`wor-17`, `wor-17.1`) resolves to its linked spec or task through
`flowctl show`, never a new spec. Phase 5's `Tracker sync:` summary slot runs on every run.

## Guardrails

- **The branch is chosen before the run starts.** A run that began on an unresolved branch choice has broken this.
- **A plan or spec exists before implementation starts.** A run that began with no `.flow/` spec has broken this.
- **Tests run.** A task marked done before the focused tests for the code it changed ran has broken this.
- **No task is left half-done.** A run that ends with a task still `in_progress` and no `NEEDS_HUMAN`/blocked report has broken this.
- **Task tracking lives in `.flow/` via `flowctl`.** A run tracking tasks in TodoWrite, or writing a plan file outside `.flow/`, has broken this.
