"""Plan's legacy-copy residue probe stays in step with LEGACY_COPY_ARTIFACTS."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
SKILLS = ROOT / "skills"
CODEX_SKILLS = ROOT / "codex" / "skills"
PLAN = "flow-next-plan"


class ResidueProbeParity(unittest.TestCase):
    """The two skill residue probes stay in byte-step with LEGACY_COPY_ARTIFACTS.

    flowctl's constant is documented as the single source of truth, but the
    setup and plan probes restate the paths in prose bash. This pin fails the
    moment any of the three lists drifts (fn-197 audit finding).
    """

    PROBE_FILES = (
        SKILLS / PLAN / "SKILL.md",
        CODEX_SKILLS / PLAN / "SKILL.md",
    )

    def _constant(self) -> list[str]:
        import ast

        src = (REPO_ROOT / "plugins" / "flow-next" / "scripts" / "flowctl.py").read_text(
            encoding="utf-8"
        )
        match = re.search(r"LEGACY_COPY_ARTIFACTS = (\[[^\]]+\])", src)
        assert match, "LEGACY_COPY_ARTIFACTS not found"
        return [entry.rstrip("/") for entry in ast.literal_eval(match.group(1))]

    def _probe_paths(self, text: str) -> list[str]:
        match = re.search(r"for p in ((?:[^;]|\n)*?);?\s*do", text)
        assert match, "residue probe for-loop not found"
        tokens = match.group(1).replace("\\\n", " ").split()
        return [token.rstrip("/") for token in tokens if token.startswith(".flow/")]

    def test_probe_lists_equal_the_constant(self) -> None:
        expected = sorted(self._constant())
        for probe in self.PROBE_FILES:
            with self.subTest(file=str(probe.relative_to(ROOT))):
                got = sorted(self._probe_paths(probe.read_text(encoding="utf-8")))
                self.assertEqual(got, expected, f"{probe} probe drifted from LEGACY_COPY_ARTIFACTS")


if __name__ == "__main__":
    unittest.main()
