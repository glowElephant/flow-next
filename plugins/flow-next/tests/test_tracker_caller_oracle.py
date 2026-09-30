"""Tracker caller oracle matrix and reachability guards."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_COMMIT = "410756ef8f27d14c3cfbcbffe66356c67fd255ad"
ORACLE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "tracker_callers"
    / f"oracle-{SOURCE_COMMIT}.json"
)
EVENTS = {
    "capture",
    "interview",
    "plan",
    "work.firstClaim",
    "work.done",
    "completionReview",
    "makePr",
    "resolvePr",
    "qa",
    "land.merged",
    "chart",  # fn-135.5 optional chart lifecycle projection
}
REQUIRED_CALLER_FIELDS = {
    "id",
    "file",
    "event",
    "config_key",
    "legal_config_values",
    "resolved_facade_op",
    "unconditional_behavior",
    "content_input",
    "expected_receipt",
    "config_reads",
    "argv",
    "imports",
    "stdout",
    "stderr",
}

SKILLS = "plugins/flow-next/skills"

# The oracle is commit-addressed and immutable: its `file` field names each
# caller's home in the pre-teardown tree. The fn-169 branch-disclosure wave
# moved several caller bodies off the always-loaded spine into the reference
# their gate loads, so the CURRENT tree splits some callers across two files.
# This map names the current home(s); assertions about the current tree read
# the concatenation, and `_GATE_EDGES` pins that the spine still loads the
# reference (reachability, not mere existence).
CURRENT_CALLER_FILES = {
    "capture": (
        f"{SKILLS}/flow-next-capture/workflow.md",
        f"{SKILLS}/flow-next-capture/references/tracker-integration.md",
    ),
    "interview": (
        f"{SKILLS}/flow-next-refine/SKILL.md",
        f"{SKILLS}/flow-next-refine/references/post-write-back.md",
    ),
    "plan": (
        f"{SKILLS}/flow-next-plan/SKILL.md",
        f"{SKILLS}/flow-next-plan/steps.md",
        f"{SKILLS}/flow-next-plan/references/tracker-projection.md",
    ),
    "qa": (
        f"{SKILLS}/flow-next-qa/workflow.md",
        f"{SKILLS}/flow-next-qa/references/autonomy.md",
    ),
    "chart": (
        f"{SKILLS}/flow-next-chart/workflow.md",
        f"{SKILLS}/flow-next-chart/references/tracker-projection.md",
    ),
}

# spine file -> reference token it must name for the moved caller body to be
# reachable on the branch that needs it.
_GATE_EDGES = (
    (
        f"{SKILLS}/flow-next-capture/workflow.md",
        "references/tracker-integration.md",
    ),
    (
        f"{SKILLS}/flow-next-refine/SKILL.md",
        "references/post-write-back.md",
    ),
    (f"{SKILLS}/flow-next-plan/steps.md", "references/tracker-projection.md"),
    (f"{SKILLS}/flow-next-qa/workflow.md", "references/autonomy.md"),
    (f"{SKILLS}/flow-next-chart/workflow.md", "references/tracker-projection.md"),
    (
        f"{SKILLS}/flow-next-work/phases.md",
        "references/tracker-touchpoints.md",
    ),
)


class TrackerCallerOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
        cls.callers = {
            caller["id"]: caller for caller in cls.oracle["callers"]
        }

    @staticmethod
    def _current_files(caller: dict) -> tuple[str, ...]:
        return CURRENT_CALLER_FILES.get(caller["id"], (caller["file"],))

    def test_moved_caller_bodies_stay_reachable(self) -> None:
        """Every caller body parked in a reference must be named by the
        always-loaded file that gates it."""
        for spine, ref_token in _GATE_EDGES:
            with self.subTest(spine=spine):
                text = (REPO_ROOT / spine).read_text(encoding="utf-8")
                self.assertIn(
                    ref_token,
                    text,
                    f"{spine} does not load {ref_token} — the tracker caller "
                    "body it owns would be unreachable",
                )

    def test_matrix_is_authoritative_and_complete(self) -> None:
        self.assertEqual(set(self.callers), EVENTS)
        self.assertEqual(
            {caller["event"] for caller in self.callers.values()},
            EVENTS,
        )
        self.assertEqual(
            self.oracle["per_event_enum"],
            ["off", "pull", "push", "reconcile", "comment"],
        )

        for caller in self.callers.values():
            self.assertEqual(set(caller), REQUIRED_CALLER_FIELDS, caller["id"])
            for relative in self._current_files(caller):
                self.assertTrue((REPO_ROOT / relative).is_file(), relative)
            self.assertTrue(caller["expected_receipt"])
            self.assertIn("off", caller["legal_config_values"])
            self.assertTrue(caller["resolved_facade_op"])
            self.assertTrue(caller["content_input"])
            for observation in ("argv", "imports"):
                self.assertEqual(
                    set(caller[observation]),
                    {"inactive", "active"},
                    f"{caller['id']}:{observation}",
                )
            self.assertEqual(
                set(caller["config_reads"]),
                {"inactive", "active"},
                caller["id"],
            )
            for stream in ("stdout", "stderr"):
                self.assertEqual(
                    caller[stream],
                    {"inactive": "", "active_success": ""},
                    f"{caller['id']}:{stream}",
                )
            self.assertEqual(caller["argv"]["inactive"], [])
            self.assertEqual(caller["imports"]["inactive"], [])

    def test_repeatable_synthesized_comments_name_stable_evidence_tokens(
            self) -> None:
        """Every repeated comment caller must distinguish occurrences.

        The facade rejects evidence-less comments; each caller names the
        `evidence=` field with a per-occurrence stable value.
        """
        expected = {
            (
                "plugins/flow-next/skills/flow-next-work/"
                "references/tracker-touchpoints.md"
            ): (
                "evidence=<task-id>@<final-evidence-commit-sha>",
                "evidence=<reviewed-head-sha>",
            ),
            (
                "plugins/flow-next/skills/flow-next-work/"
                "references/tracker-retro-fire.md"
            ): (
                "evidence=<task-id>@<final-evidence-commit-sha>",
                "evidence=<reviewed-head-sha>",
            ),
            (
                "plugins/flow-next/skills/flow-next-capture/"
                "references/tracker-integration.md"
            ): ("evidence=<sha256-of-current-spec-file>",),
            (
                "plugins/flow-next/skills/flow-next-refine/"
                "references/post-write-back.md"
            ): ("evidence=<sha256-of-current-spec-file>",),
            (
                "plugins/flow-next/skills/flow-next-plan/"
                "references/tracker-projection.md"
            ): ("evidence=<sha256-of-current-spec-file>",),
            "plugins/flow-next/skills/flow-next-qa/workflow.md": (
                "evidence=<tested-head-sha>",
            ),
            "plugins/flow-next/skills/flow-next-resolve-pr/workflow.md": (
                "evidence=<post-resolution-pr-head-sha>",
            ),
            "plugins/flow-next/skills/flow-next-land/workflow.md": (
                "evidence=<merge-commit-sha>",
            ),
            "plugins/flow-next/skills/flow-next-tracker-sync/SKILL.md": (
                "evidence=<token>",
            ),
            "plugins/flow-next/skills/flow-next-tracker-sync/steps.md": (
                "evidence=<token>",
            ),
            (
                "plugins/flow-next/skills/flow-next-tracker-sync/"
                "references/comments-sync.md"
            ): ("evidence=<stable-token>",),
        }
        for relative, tokens in expected.items():
            text = (REPO_ROOT / relative).read_text(encoding="utf-8")
            for token in tokens:
                self.assertIn(token, text, f"{relative}: {token}")

if __name__ == "__main__":
    unittest.main()
