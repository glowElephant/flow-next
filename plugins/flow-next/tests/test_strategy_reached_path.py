"""Strategy entry point reaches its branch references (canonical and Codex mirror)."""

import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
STRATEGY = REPO / "plugins/flow-next/skills/flow-next-strategy"
MIRROR = REPO / "plugins/flow-next/codex/skills/flow-next-strategy"

# file -> references it must link, so each branch's text stays reachable.
ROUTES = {
    "SKILL.md": ("references/first-run.md", "references/update.md"),
    "references/first-run.md": ("references/interview.md", "references/strategy-template.md"),
    "references/update.md": ("references/interview.md",),
}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class StrategyReachedPathTests(unittest.TestCase):
    def _check(self, root: Path) -> None:
        for name, targets in ROUTES.items():
            text = _text(root / name)
            for target in targets:
                with self.subTest(root=root.name, file=name, target=target):
                    self.assertIn(target, text)
                    self.assertTrue((root / target).is_file(), target)

    def test_canonical_entry_reaches_branch_references(self) -> None:
        self._check(STRATEGY)

    def test_codex_mirror_entry_reaches_branch_references(self) -> None:
        if not (MIRROR / "references/first-run.md").exists():
            self.skipTest("Codex mirror not regenerated")
        self._check(MIRROR)


if __name__ == "__main__":
    unittest.main()
