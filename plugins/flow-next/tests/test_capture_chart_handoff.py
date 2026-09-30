"""Capture chart-briefing handoff: the reference exists and the spine reaches it.

The chart-briefing prose lives in references/chart-briefing.md, which
workflow.md's chart-briefing gate loads. Only reachability is checked here;
the wording of the reference is not pinned.
"""

from __future__ import annotations

import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CANONICAL = REPO_ROOT / "plugins" / "flow-next" / "skills" / "flow-next-capture"
CHART_REF_LINK = "[references/chart-briefing.md](references/chart-briefing.md)"


class CaptureChartHandoffContract(unittest.TestCase):
    def test_skill_files_exist(self) -> None:
        for name in ("SKILL.md", "workflow.md", "phases.md"):
            self.assertTrue((CANONICAL / name).is_file(), name)
        self.assertTrue(
            (CANONICAL / "references" / "chart-briefing.md").is_file(),
            "references/chart-briefing.md",
        )

    def test_workflow_reaches_chart_briefing_reference(self) -> None:
        workflow = (CANONICAL / "workflow.md").read_text(encoding="utf-8")
        self.assertIn(CHART_REF_LINK, workflow)


if __name__ == "__main__":
    unittest.main()
