"""fn-99 R1/R2/R9 and 2026-07-15 guidance-eval evidence-shape guard.

The old block named --evidence-json but never showed its schema; agents reliably
invented invalid evidence. Both snippets carry the setup-block markers and a
parseable inline evidence example.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


HERE = Path(__file__).resolve()
TESTS_DIR = HERE.parent
PLUGIN_DIR = TESTS_DIR.parent
TEMPLATES = PLUGIN_DIR / "skills" / "flow-next-setup" / "templates"


def _read(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8").replace("\r\n", "\n")


class SetupSnippetLockstepTest(unittest.TestCase):
    def test_markers_and_inline_evidence_shape(self) -> None:
        for name in ("claude-md-snippet.md", "agents-md-snippet.md"):
            with self.subTest(template=name):
                content = _read(name)
                self.assertEqual(content.splitlines()[0], "<!-- BEGIN FLOW-NEXT -->")
                self.assertEqual(
                    next(line for line in reversed(content.splitlines()) if line.strip()),
                    "<!-- END FLOW-NEXT -->",
                )
                line = next(line for line in content.splitlines() if '"commits"' in line)
                match = re.search(r"(\{.*\})", line)
                self.assertIsNotNone(match)
                evidence = json.loads(match.group(1))  # type: ignore[union-attr]
                self.assertEqual(set(evidence), {"commits", "tests", "prs"})
                self.assertTrue(
                    all(
                        isinstance(value, list)
                        and all(isinstance(item, str) for item in value)
                        for value in evidence.values()
                    )
                )


if __name__ == "__main__":
    unittest.main()
