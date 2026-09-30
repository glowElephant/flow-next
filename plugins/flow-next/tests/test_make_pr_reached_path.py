"""Make PR chain-detect ordering in the shipped preflight script."""

from __future__ import annotations

import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
SKILL = REPO / "plugins" / "flow-next" / "skills" / "flow-next-make-pr"


class MakePrReachedPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        scripts = SKILL.parents[1] / "scripts"
        cls.workflow = (scripts / "make-pr-preflight.sh").read_text(encoding="utf-8")

    def test_landed_range_and_current_base_skip_chain_parent(self) -> None:
        fence = self.workflow.split("# fence:chain-detect", 1)[1].split("# --- §0.5", 1)[0]
        closed_probe = fence.index('spec closed-in-range --base "$CHAIN_BASE" --json')
        skip = fence.index("'.spec_ids | index($dep) != null'")
        parent_read = fence.index('DEP_JSON=$("$FLOWCTL" show')
        self.assertLess(closed_probe, skip)
        self.assertLess(skip, parent_read)
        landed = next(line for line in fence.splitlines()
                      if 'DEP_PR_STATE' in line and 'branch --show-current' in line)
        for token in ('"MERGED"', '.baseRefName', 'then continue; fi'):
            self.assertIn(token, landed)
        self.assertLess(fence.index(landed), fence.index('refs/pull/$DEP_PR_NUMBER/head'))
        self.assertIn('spec closed-in-range --base "${BASE_REF:-$CHAIN_BASE}" --json', fence)
        self.assertIn("'.spec_ids[-1] // empty'", fence)


if __name__ == "__main__":
    unittest.main()
