"""Machine-read verdict lines stay in the skill files drivers grep.

Canonical files and their codex mirror copies.
"""

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PLUGIN = REPO / "plugins" / "flow-next"
SKILLS = PLUGIN / "skills"
MIRROR_SKILLS = PLUGIN / "codex" / "skills"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def both_copies(rel: str):
    """Canonical file + its codex-mirror copy (mirror must exist)."""
    canonical = SKILLS / rel
    mirrored = MIRROR_SKILLS / rel
    assert canonical.exists(), f"missing canonical file: {rel}"
    assert mirrored.exists(), f"missing codex mirror copy: {rel}"
    return [canonical, mirrored]


class VerdictLinesTestCase(unittest.TestCase):
    """Machine-read verdict lines remain."""

    def test_verdict_lines_remain(self):
        for path in both_copies("flow-next-plan-review/SKILL.md"):
            self.assertIn("BLOCKED: DESIGN_CONFLICT", read(path))
        for path in both_copies("flow-next-flow/auto.md"):
            self.assertIn("PILOT_VERDICT=<ADVANCED|NO_WORK|", read(path))
        for path in both_copies("flow-next-land/SKILL.md"):
            self.assertIn("LAND_VERDICT=<verdict|NO_WORK>", read(path))


if __name__ == "__main__":
    unittest.main()
