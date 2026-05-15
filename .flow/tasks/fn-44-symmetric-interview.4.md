## Description

**DROPPED FROM SCOPE — DO NOT IMPLEMENT.**

The `## Agent Authority Envelope` idea was considered during fn-44 planning and explicitly removed. Operator authority belongs at the project level (CLAUDE.md / AGENTS.md / `knowledge/decisions/`), not per-spec. Workers running as subagents cannot call `AskUserQuestion` (Claude Code issues #18721, #20275); an Envelope demanding mid-task escalation would stall Ralph autonomous loops. The spec is implementable or it isn't — no halfway-implementable state.

The fn-44 spec has been rewritten to remove every reference to Agent Authority Envelope. R10 was deleted (the R-ID gap is intentional and preserved per fn-29 append-only rules). `agents/worker.md` should NOT be modified for this task.

T9's dependency on this task has been removed; nothing downstream waits on this work.

**This task remains in the task list as a tombstone only. Skip it.**

## Acceptance

- [ ] No code change for this task (intentional)
- [ ] Worker readers recognise the DROPPED notice and skip

## Done summary

## Evidence
