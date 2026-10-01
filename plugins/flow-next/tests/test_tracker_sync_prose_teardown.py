"""Tracker-sync shell fences never call a provider API directly.

Provider transport is owned by `flowctl tracker`; a fence that shells out
to `gh api`, `glab api` or `curl` regrows the duplicated transport.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TRACKER_SKILL = REPO_ROOT / "plugins/flow-next/skills/flow-next-tracker-sync"

# Explicit inventory. These are the canonical files that formerly duplicated
# executable provider calls. Add a new adapter document here before it ships.
PROSE_INVENTORY = (
    "SKILL.md",
    "steps.md",
    "references/adapter-interface.md",
    "references/linear-ladder.md",
    "references/linear-mcp.md",
    "references/linear-graphql.md",
    "references/github.md",
    "references/gitlab.md",
    "references/jira.md",
)

BASH_FENCE = re.compile(r"^```(?:bash|sh|shell)\s*$\n(.*?)^```\s*$", re.MULTILINE | re.DOTALL)
EXECUTABLE_INVOCATION = re.compile(
    r"(?:\bgh\s+api\b|\bglab\s+api\b|\bcurl\s+-sS\b|\bPOST\s+/rest/api\b)"
)


class TrackerSyncProseTeardownTests(unittest.TestCase):
    def _texts(self) -> dict[str, str]:
        return {
            relative: (TRACKER_SKILL / relative).read_text(encoding="utf-8")
            for relative in PROSE_INVENTORY
        }

    def test_no_executable_provider_invocations_in_shell_fences(self) -> None:
        matches: list[str] = []
        for relative, text in self._texts().items():
            for fence_number, fence in enumerate(BASH_FENCE.findall(text), start=1):
                for match in EXECUTABLE_INVOCATION.finditer(fence):
                    matches.append(
                        f"{relative}:shell-fence-{fence_number}:{match.group(0)}"
                    )
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
