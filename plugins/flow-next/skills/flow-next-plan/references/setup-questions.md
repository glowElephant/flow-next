# Plan setup questions

Load this reference only when the SKILL.md setup gate fired — `REVIEW_BACKEND`
is `ASK` (not configured) and the run is not autonomous. Configured backends and
`AUTONOMOUS=1` never reach this file.

Ask the setup questions below as plain text — never via the `AskUserQuestion` tool. Drop a question whose option the arguments already set.

An explicit `--review=rp` argument (parsed in SKILL.md) is still honored while RepoPrompt support is deprecated (removed in 8.0.0); the menu no longer offers it.

```
Quick setup before planning:

1. **Plan depth** — How detailed?
   a) Short — problem, acceptance, key context only
   b) Standard — + approach, risks, test notes
   c) Deep — + phases, alternatives, rollout plan

2. **Review** — Run Carmack-level review after?
   a) Codex CLI
   b) Export for external LLM
   c) None (configure later)

(Reply: "1a 2c", or just tell me naturally)
```

Wait for response. Parse naturally — user may reply terse ("1a 2b") or ramble via voice.

**Defaults when empty/ambiguous:**
- Depth = the SKILL.md **Depth** default
- Research = `repo-scout`
- Review = configured backend if set, else `none`
