"""Capture's gated references stay reachable from workflow.md.

Chart-briefing, mark-ready and rewrite-mode prose live in references that
workflow.md's gates load. Only reachability is checked here; the wording of
the references is not pinned.
"""

from __future__ import annotations

import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CANONICAL = REPO_ROOT / "plugins" / "flow-next" / "skills" / "flow-next-capture"
GATED_REFERENCES = ("chart-briefing.md", "mark-ready.md", "rewrite-mode.md")


class CaptureReferenceReachability(unittest.TestCase):
    def test_workflow_reaches_gated_references(self) -> None:
        workflow = (CANONICAL / "workflow.md").read_text(encoding="utf-8")
        for name in GATED_REFERENCES:
            with self.subTest(reference=name):
                self.assertTrue((CANONICAL / "references" / name).is_file(), name)
                self.assertIn(f"references/{name}", workflow)


if __name__ == "__main__":
    unittest.main()
