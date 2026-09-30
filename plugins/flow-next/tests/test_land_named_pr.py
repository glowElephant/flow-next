"""Land's terminal verdict line: the grammar the flow tail parses.

The land prose itself is not pinned; only the machine-read verdict line is.
"""
from pathlib import Path
import unittest

LAND = Path(__file__).resolve().parents[1] / "skills" / "flow-next-land"


class LandVerdictGrammarTest(unittest.TestCase):
    def test_verdict_line_grammar(self):
        skill = (LAND / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            'LAND_VERDICT=<verdict|NO_WORK> prs=<n> pr=<url|-> reason="<one line>"',
            skill,
        )


if __name__ == "__main__":
    unittest.main()
