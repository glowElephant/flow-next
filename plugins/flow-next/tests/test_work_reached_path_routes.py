"""Live routing/reference contracts for Work's reached-path extraction (fn-130.8):
phases.md reaches multi-task.md, which links the wave-join and host-deferred
review references."""

from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
WORK = REPO_ROOT / "plugins" / "flow-next" / "skills" / "flow-next-work"


def _text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")


class WorkReachedPathRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = _text(WORK / "SKILL.md")
        cls.phases = _text(WORK / "phases.md")

    def test_common_work_lifecycle_routes(self) -> None:
        """Routes only: phases.md reaches multi-task.md, which reaches the
        wave-join and host-deferred review references."""
        self.assertIn("references/multi-task.md", self.phases)
        multi = _text(WORK / "references" / "multi-task.md")
        for reference in ("wave-join.md", "host-deferred-review.md"):
            with self.subTest(reference=reference):
                self.assertTrue((WORK / "references" / reference).is_file())
                self.assertRegex(multi, r"\]\((?:references/)?" + reference.replace(".", r"\.") + r"[)#]")

if __name__ == "__main__":
    unittest.main()
