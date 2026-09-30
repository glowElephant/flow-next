"""Chart and flow surfaces: files, mirror copies, CLI help and documented tokens.

Fails when the canonical chart/flow skills or their Codex mirror copies are
missing, `flowctl chart --help` loses a subcommand or docs/flowctl.md stops
naming a subcommand, error class, envelope field or config key, or the chart
workflow stops reaching its mode references. Prose wording is not pinned.

Run:
    cd plugins/flow-next/tests && python3 -m unittest test_chart_docs_inventory -q
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling test helpers
from flowctl_test_support import FLOWCTL_CMD


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN = REPO_ROOT / "plugins" / "flow-next"
DOCS = PLUGIN / "docs"
SKILLS = PLUGIN / "skills"
COMMANDS = PLUGIN / "commands"
CODEX = PLUGIN / "codex"

# Branch-disclosure refactor: chart prose that used to sit inline in SKILL.md /
# workflow.md now lives in the mode reference that reaches it. Contracts are
# asserted against their new home, plus the link that keeps the home reachable.
CHART_SKILL_DIR = SKILLS / "flow-next-chart"
CHART_REFERENCES = CHART_SKILL_DIR / "references"
CHART_MODE_REFS = (
    "chart-mode.md",  # Phase 1 chart mode
    "work-mode.md",  # Phase 2 + 5 work mode
    "briefing-and-reopen.md",  # Phase 4 + 6 briefing / reopen
    "re-entry.md",  # Phase 0.2 locator re-entry
    "tracker-projection.md",  # Phase 0.2b projection gate
)

# The flow skill's routing references, checked in the Codex mirror.
FLOW_SKILL_DIR = SKILLS / "flow-next-flow"
FLOW_ROUTING_REFS = (
    "route-matrix.md",
    "spec-count.md",
    "plan-vs-no-plan.md",
    "gate-selection.md",
    "prototype-before-ask.md",
    "tail.md",
)

# Subcommands from the live CLI - keep in sync with flowctl chart --help.
EXPECTED_CHART_SUBCOMMANDS = frozenset(
    {
        "create",
        "show",
        "list",
        "add-decision",
        "park-question",
        "remove-question",
        "wire-decision",
        "frontier",
        "claim",
        "release-claim",
        "attach-asset",
        "resolve",
        "out-of-scope",
        "abandon",
        "briefing",
        "reopen",
        "locate",
        "link-spec",
    }
)

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ChartDocsFilesExist(unittest.TestCase):
    def test_canonical_chart_and_flow_skills_exist(self) -> None:
        for rel in (
            "skills/flow-next-chart/SKILL.md",
            "skills/flow-next-chart/workflow.md",
            "skills/flow-next-flow/SKILL.md",
            "commands/chart.md",
            "commands/flow.md",
        ):
            path = PLUGIN / rel
            self.assertTrue(path.is_file(), f"missing {path.relative_to(REPO_ROOT)}")

    def test_codex_mirror_chart_and_flow_exist(self) -> None:
        """Host regenerates the mirror after docs land; assert unconditionally.

        The mirror carries skills only - command shims are Claude-side and
        are not mirrored (sync-codex.sh emits skills/agents/references/
        templates).
        """
        mirrored = [
            "skills/flow-next-chart/SKILL.md",
            "skills/flow-next-chart/workflow.md",
            "skills/flow-next-flow/SKILL.md",
        ]
        # Mode references carry the branch-disclosed prose - the mirror is
        # useless without them.
        mirrored += [
            f"skills/flow-next-chart/references/{name}" for name in CHART_MODE_REFS
        ]
        mirrored += [
            f"skills/flow-next-flow/references/{name}" for name in FLOW_ROUTING_REFS
        ]
        for rel in mirrored:
            path = CODEX / rel
            self.assertTrue(
                path.is_file(),
                f"missing Codex mirror {path.relative_to(REPO_ROOT)} "
                "(host must run ./scripts/sync-codex.sh after this task)",
            )


class ChartFlowctlDocsParity(unittest.TestCase):
    def test_help_subcommands_match_docs(self) -> None:
        proc = subprocess.run(
            [*FLOWCTL_CMD, "chart", "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        help_text = proc.stdout
        # argparse lists choices in braces or as indented names
        found = set()
        for name in EXPECTED_CHART_SUBCOMMANDS:
            if re.search(rf"\b{re.escape(name)}\b", help_text):
                found.add(name)
        self.assertEqual(
            found,
            EXPECTED_CHART_SUBCOMMANDS,
            f"flowctl chart --help missing {EXPECTED_CHART_SUBCOMMANDS - found}",
        )

        docs = _read(DOCS / "flowctl.md")
        # chart section must document each subcommand
        chart_section = docs
        idx = docs.find("## chart")
        self.assertGreater(idx, 0, "docs/flowctl.md must have ## chart section")
        # take until next top-level ## that is not a subsection under chart... 
        # next major after chart is "## flowctl tracker"
        end = docs.find("## flowctl tracker", idx)
        chart_section = docs[idx:end] if end > idx else docs[idx:]
        missing = [s for s in sorted(EXPECTED_CHART_SUBCOMMANDS) if s not in chart_section]
        self.assertEqual(missing, [], f"flowctl.md chart section missing subcommands: {missing}")

    def test_envelope_error_classes_documented(self) -> None:
        docs = _read(DOCS / "flowctl.md")
        for cls in (
            "not_found",
            "conflict",
            "invalid_state",
            "invalid_graph",
            "stale_claim",
            "validation",
            "io",
        ):
            self.assertIn(cls, docs, f"flowctl.md must document error class {cls}")

    def test_envelope_section_names_its_fields(self) -> None:
        docs = _read(DOCS / "flowctl.md")
        start = docs.find("### v1 JSON envelope")
        self.assertGreater(start, 0, "flowctl.md must have a v1 JSON envelope section")
        end = docs.find("### Subcommands", start)
        self.assertGreater(end, start, "v1 JSON envelope section must be bounded")
        section = docs[start:end]
        for token in (
            "supersedes_stale",
            "alias_collision",
            "`alias`",
            "`first`",
            "`second`",
            "`index`",
            "`title`",
        ):
            self.assertIn(token, section, f"v1 envelope section must name {token}")

    def test_config_keys_documented(self) -> None:
        docs = _read(DOCS / "flowctl.md")
        for key in (
            "chart.maxDecisions",
            "chart.claimStaleAfter",
            "tracker.charts",
        ):
            self.assertIn(key, docs)


class ChartReachabilityAndTokens(unittest.TestCase):
    def test_workflow_reaches_mode_references_and_verdict(self) -> None:
        workflow = _read(CHART_SKILL_DIR / "workflow.md")
        for name in CHART_MODE_REFS:
            self.assertIn(
                f"references/{name}",
                workflow,
                f"workflow.md must link references/{name}",
            )
            self.assertTrue((CHART_REFERENCES / name).is_file(), name)
        skill = _read(CHART_SKILL_DIR / "SKILL.md")
        self.assertIn("CHART_VERDICT", skill + workflow)

    def test_flowctl_doc_names_chart_tokens(self) -> None:
        text = _read(DOCS / "flowctl.md")
        for token in (
            "chart locate",
            "schema_version",
            "CHART_VERDICT",
            "blocked_by",
            "depends_on",
            "attach-asset",
        ):
            self.assertIn(token, text, f"flowctl.md missing {token!r}")


if __name__ == "__main__":
    unittest.main()
