"""Chart skill contract: mode-reference reachability, verdict grammar, and no
literal destructive commands. Prose wording is not pinned. Canonical files only.

Run:
    cd plugins/flow-next/tests && python3 -m unittest test_chart_skill_contract -q
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN = REPO_ROOT / "plugins" / "flow-next"
SKILL_DIR = PLUGIN / "skills" / "flow-next-chart"
SHIM = PLUGIN / "commands" / "chart.md"

SKILL_MD = SKILL_DIR / "SKILL.md"
WORKFLOW_MD = SKILL_DIR / "workflow.md"
REFERENCES = SKILL_DIR / "references"
EXAMPLES_MD = REFERENCES / "examples.md"

# Branch-disclosure refactor: workflow.md routes to exactly one mode reference
# per invocation. Prose that used to sit inline in workflow.md now lives in the
# reference for the mode that reaches it. Each contract below is asserted
# against its new home PLUS the link that makes that home reachable.
CHART_MODE_MD = REFERENCES / "chart-mode.md"  # Phase 1 (chart mode)
WORK_MODE_MD = REFERENCES / "work-mode.md"  # Phase 2 + 5 (work mode)
BRIEFING_MD = REFERENCES / "briefing-and-reopen.md"  # Phase 4 + 6
RE_ENTRY_MD = REFERENCES / "re-entry.md"  # Phase 0.2 locator re-entry
TRACKER_PROJECTION_MD = REFERENCES / "tracker-projection.md"  # Phase 0.2b gate


# Exact terminal verdict grammar pinned by R15 / SKILL.md.
VERDICT_GRAMMAR_LINE = (
    "CHART_VERDICT=<RESOLVED|BLOCKED|NEEDS_HUMAN|COMPLETE|NO_WORK> "
    "chart=<id> decision=<D> reason="
)

# Conservative scan for literal destructive shell shapes (R20). Files may
# DESCRIBE such operations in prose but must not embed the literal tokens.
DESTRUCTIVE_LITERALS = (
    re.compile(r"\brm\s+-[A-Za-z]*[rf][A-Za-z]*\b"),
    re.compile(r"\bgit\s+clean\b"),
    re.compile(r"\bgit\s+reset\s+--hard\b"),
    re.compile(r"\bdd\s+if="),
    re.compile(r"\bmkfs\."),
    re.compile(r">\s*/dev/sd[a-z]"),
    re.compile(r"\bshred\b"),
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ChartReferenceReachability(unittest.TestCase):

    def test_mode_references_exist_and_are_reachable(self) -> None:
        """Every mode reference exists and workflow.md links it by path."""
        workflow = _read(WORKFLOW_MD)
        for path in (
            CHART_MODE_MD,
            WORK_MODE_MD,
            BRIEFING_MD,
            RE_ENTRY_MD,
            TRACKER_PROJECTION_MD,
        ):
            with self.subTest(reference=path.name):
                self.assertTrue(path.is_file(), f"missing {path}")
                self.assertIn(
                    f"references/{path.name}",
                    workflow,
                    f"workflow.md must link references/{path.name} "
                    "(prose moved there is unreachable otherwise)",
                )


class ChartVerdictGrammar(unittest.TestCase):
    def test_exact_verdict_grammar_line(self) -> None:
        skill = _read(SKILL_MD)
        examples = _read(EXAMPLES_MD)
        self.assertIn(VERDICT_GRAMMAR_LINE, skill)
        self.assertIn(VERDICT_GRAMMAR_LINE, examples)
        for token in (
            "RESOLVED",
            "BLOCKED",
            "NEEDS_HUMAN",
            "COMPLETE",
            "NO_WORK",
        ):
            self.assertIn(token, skill)

class ChartSafety(unittest.TestCase):
    def test_no_literal_destructive_command_strings(self) -> None:
        for path in (
            SKILL_MD,
            WORKFLOW_MD,
            EXAMPLES_MD,
            CHART_MODE_MD,
            WORK_MODE_MD,
            BRIEFING_MD,
            RE_ENTRY_MD,
            TRACKER_PROJECTION_MD,
            SHIM,
        ):
            text = _read(path)
            for pat in DESTRUCTIVE_LITERALS:
                m = pat.search(text)
                if m is not None:
                    self.fail(
                        f"{path.name}: literal destructive shape {m.group(0)!r} "
                        f"(describe operations; do not embed command strings)"
                    )


if __name__ == "__main__":
    unittest.main()
