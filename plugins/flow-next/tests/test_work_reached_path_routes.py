"""Live routing/reference contracts for Work's reached-path extraction (fn-130.8).

The delegation-route contracts retired with the packaged codex-delegation
subsystem (flow-98); the common work lifecycle + wave-join contracts remain.
"""

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

    # Evidence-ledger archaeology removed 2026-08-07 - shipped optimizations are
    # history, not invariants. (Lineage baseline-commit pin and the stored
    # route-matrix shape checks deleted; live skill-file contracts remain.)

    def test_no_delegation_route_regrowth(self) -> None:
        """flow-98: the packaged delegation path is deleted, not deprecated."""
        for name, text in (("SKILL.md", self.skill), ("phases.md", self.phases)):
            with self.subTest(file=name):
                self.assertNotIn("delegate:codex", text)
                self.assertNotIn("codex-delegation", text)
                self.assertNotIn("work.delegate", text)
        for stale in ("codex-delegation.md", "codex-delegation-selection.md"):
            with self.subTest(reference=stale):
                self.assertFalse((WORK / "references" / stale).exists())

    def test_common_work_lifecycle_routes_and_no_forbidden_gate_regrowth(self) -> None:
        """Routes only: phases.md reaches multi-task.md, which reaches the
        wave-join and host-deferred review references."""
        self.assertIn("references/multi-task.md", self.phases)
        multi = _text(WORK / "references" / "multi-task.md")
        for reference in ("wave-join.md", "host-deferred-review.md"):
            with self.subTest(reference=reference):
                self.assertTrue((WORK / "references" / reference).is_file())
                self.assertRegex(multi, r"\]\((?:references/)?" + reference.replace(".", r"\.") + r"[)#]")
        self.assertNotIn("plan-sync-probe", self.phases)
        self.assertNotIn("PLAN_DEVIATION", self.phases)

if __name__ == "__main__":
    unittest.main()
