# Interactive setup question (gated reference)

Read only on an interactive run (`AUTONOMOUS=0`) whose arguments carried no review option while
`REVIEW_BACKEND` is `ASK` (no backend configured). The branch is never asked: SKILL.md picks it
and says which. Ask this one question, then wait for the answer before reading or writing
anything else:

```
Review after implementation?
a) Codex CLI
b) RepoPrompt
c) None (configure later with --review)
```

Parse the answer naturally. An empty or unclear answer means `none`.
