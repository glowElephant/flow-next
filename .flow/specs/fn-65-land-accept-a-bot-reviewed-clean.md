# fn-65 land: accept a bot "reviewed-clean" comment as the silence signal (not just formal reviews)

> **Origin:** found live while landing PR #176 (fn-64) on 2026-06-17. The `silence` gate read 0 automated reviews of the final head and would have stalled at `NEEDS_HUMAN`; the merge only happened because a human recognized Codex's clean-review *comment* and merged by judgment. Captured by Gordon.

## Goal & Context

`/flow-next:land`'s `silence` review signal (the default) is satisfied by "an automated review of the current head + zero unresolved threads + patience window elapsed." Land detects automated reviews **only** via the formal reviews API (`gh api repos/<o>/<r>/pulls/<n>/reviews`, workflow.md:231) — the `AUTO_REVIEW_CURRENT` loop.

But the Codex GitHub reviewer (`chatgpt-codex-connector[bot]`) only files a **formal review** when it has findings. On a **clean** pass it posts an **issue comment** instead — e.g. *"Codex Review: Didn't find any major issues. **Reviewed commit:** `8ff0e50f46`"* — which never appears in the reviews API. So `AUTO_REVIEW_CURRENT` reads `0`, and land reports `AWAITING_REVIEW` → after the window, `NEEDS_HUMAN` ("no automated review arrived within the patience window").

Net effect: **an unattended land loop will NOT auto-merge a PR whose only change since the last finding was approved-by-silence** — the exact converged-clean state land exists to merge. This bit the fn-64 land (PR #176): CI green, P2 fixed + thread resolved, Codex re-reviewed the new head **clean via comment**, but land's reviews-API-only check couldn't see it. A human merged on judgment; the loop alone would have dead-ended.

## Architecture & Data Models

The fix lives entirely in the `silence` (and `<login>`) signal evaluation in `plugins/flow-next/skills/flow-next-land/workflow.md §2.6` — the host-agent gate read, no flowctl change.

- **Current detection (reviews-only).** `AUTO_REVIEW_PRESENT` / `AUTO_REVIEW_CURRENT` are computed from `pulls/<n>/reviews` filtered to `[bot]`-suffix logins + `land.automatedReviewers`, head-current via `commit_id == HEAD_OID || submitted_at > LAST_PUSH`.
- **Add a second evidence source — clean-review comments.** Also scan `issues/<n>/comments` for a comment by an automated-reviewer login whose body matches a configurable clean-review pattern AND names the current head SHA. A match sets `AUTO_REVIEW_CURRENT = 1` exactly like a formal review of the head would. The SHA must match (prefix-safe against the short `8ff0e50f46` form GitHub renders) so a stale "reviewed `<old-sha>`" comment never satisfies the head-current rule — the same invariant the reviews path already enforces via `commit_id`.
- **Pattern is configurable, conservative default.** A new optional key `land.cleanReviewCommentPattern` (default a Codex-shaped regex, e.g. `Didn'?t find any (major )?issues|No issues found`) plus the existing `land.automatedReviewers` allowlist gate which logins count. Empty/unmatched → the comment is ignored (no behavior change from today). Only a comment that BOTH comes from an automated reviewer AND matches the pattern AND names the current head counts.
- **Threads still gate independently.** This only supplies the "a reviewer saw this head" signal; `UNRESOLVED == 0` and `WINDOW_ELAPSED == 1` are unchanged, so a clean-comment never bypasses an open thread.

## API Contracts

- No flowctl change. One new optional config key `land.cleanReviewCommentPattern` (string regex; default the Codex-shaped pattern; empty disables the comment path). Document alongside `land.reviewSignal` / `land.automatedReviewers`.
- workflow.md §2.6: after the reviews-API loop, add a comment-scan loop (`gh api --paginate issues/<n>/comments --jq '.[]|[.user.login,.body]|@tsv'`) that sets `AUTO_REVIEW_CURRENT=1` on a (login ∈ automated) ∧ (body matches pattern) ∧ (body contains current head SHA, prefix-tolerant) match. `--dry-run` reports the matched comment as the satisfying evidence.

## Edge Cases & Constraints

- **Stale clean-comment:** a "Reviewed commit `<old-sha>`" comment from before the last push must NOT satisfy the gate — require the CURRENT head SHA in the body (prefix match handles GitHub's abbreviated SHA).
- **Bot with no SHA in its clean comment:** if the matched comment does not name a resolvable head SHA, do NOT count it (can't prove head-current) — fall through to the existing wait/NEEDS_HUMAN path. Conservative by design.
- **Approve signal unaffected:** `land.reviewSignal=approve` still requires a formal `APPROVED`; the comment path applies only to `silence` and `<login>` (a `<login>` bot that comments-clean should count the same way).
- **No new merge license:** the change only lets land *see* a clean review it currently misses — CI-green, zero-unresolved-threads, and window-elapsed gates are unchanged. It never merges with an open thread or a red check.
- **Backward compatible:** empty/unset `land.cleanReviewCommentPattern` with a non-Codex reviewer = today's behavior exactly.

## Acceptance Criteria

- **R1:** When the only head-current review evidence is an automated-reviewer **issue comment** matching the clean-review pattern AND naming the current head SHA, the `silence` signal is satisfied (given CI green, 0 unresolved threads, window elapsed) and land merges.
- **R2:** A clean-review comment naming a **stale** (non-current) SHA does NOT satisfy the gate — land keeps waiting / reports `NEEDS_HUMAN` past the window, exactly as today.
- **R3:** A clean-review comment from a **non-automated** login (not `[bot]`-suffixed, not in `land.automatedReviewers`) is ignored.
- **R4:** The comment path never bypasses an unresolved thread or red CI — those gates are evaluated unchanged.
- **R5:** `land.cleanReviewCommentPattern` is configurable; empty disables the comment path (pure reviews-API behavior, no regression).
- **R6:** Docs updated in BOTH surfaces: repo `plugins/flow-next/skills/flow-next-land/workflow.md §2.6` (+ SKILL.md config table if present) AND flow-next.dev `autonomous/land.mdx` "The merge gate, precisely" — both describe that a bot can signal clean via a SHA-named comment and how land treats it. Codex mirror regenerated if the canonical land skill prose changes.

## Boundaries

- **Scope is the `silence`/`<login>` comment-detection only** — no change to `approve`, the patience window, CI tri-state, resolve-pr dispatch, the merge mechanics, or the post-merge tail.
- **Not a general NLP pass on comments** — a single configurable pattern + the automated-reviewer allowlist + a head-SHA presence check. No sentiment analysis, no "looks approving" inference.
- **No new auto-merge authority** — land's merge gate (CI + threads + window) is untouched; this only restores detection of a review land already intends to honor.
- **Don't try to make Codex file formal reviews** — that's the bot's behavior, out of our control; land adapts to it.

## Decision Context

The `silence` signal was built precisely for "bot reviewers that comment but never file formal APPROVEs" (land.mdx), but the implementation only reads the formal reviews API — which a no-findings Codex pass never writes to. So the feature's stated intent and its detection disagree exactly on the bot it was built for. PR #176 is the proof: every real gate was green and the reviewer had demonstrably re-reviewed the head clean, yet land-as-implemented could not see it.

Keeping the match **configurable + allowlist-gated + head-SHA-anchored** preserves land's conservative posture (never merge unreviewed, never honor a stale review) while closing the blind spot. The alternative — telling users to switch to `reviewSignal=approve` — doesn't work for Codex (it never APPROVEs), so the comment path is the right fix for the default bot-review flow.
