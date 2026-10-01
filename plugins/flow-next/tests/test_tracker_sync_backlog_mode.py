"""Backlog and question-valve contracts: wire verbs, flags and comment markers.

Checks the wire verbs the prose invokes exist, the fences pass JSON
locators, and the comment-marker grammar flowctl parses is the one the
semantic reference documents. Prose wording is not pinned.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from flowctl_tracker.wire import WIRE_VERBS  # noqa: E402
from flowctl_tracker.types import ErrorClass, TrackerError  # noqa: E402
from flowctl_tracker.wire import github, gitlab, jira, linear  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = REPO_ROOT / "plugins/flow-next/skills/flow-next-tracker-sync"
STEPS = (SKILL_ROOT / "steps.md").read_text(encoding="utf-8")
COMMENTS = (SKILL_ROOT / "references/comments-sync.md").read_text(encoding="utf-8")
# The backlog driver is `flow --auto --backlog`: auto.md carries the enforcing
# guards, references/backlog-mode.md the SELECT/TRIAGE/ASK workflow.
PILOT_ROOT = REPO_ROOT / "plugins/flow-next/skills/flow-next-flow"
PILOT_WORKFLOW = (PILOT_ROOT / "auto.md").read_text(encoding="utf-8")
PILOT_BACKLOG = (
    PILOT_ROOT / "references/backlog-mode.md"
).read_text(encoding="utf-8")


class BacklogWireContractTests(unittest.TestCase):
    def test_list_open_is_a_deterministic_wire_verb(self) -> None:
        self.assertIn("list-open", WIRE_VERBS)
        self.assertIn("`wire list-open`", STEPS)

    def test_relation_and_question_ops_have_executable_wire_verbs(self) -> None:
        self.assertIn("relation-list", WIRE_VERBS)
        self.assertIn("question", WIRE_VERBS)
        self.assertIn("tracker wire relation-list --locator", STEPS)
        self.assertIn("tracker wire question --locator", STEPS)
        for flag in (
            "--subject-id",
            "--blocked-stage",
            "--reason-code",
            "--question-slug",
        ):
            self.assertIn(flag, STEPS)

    def test_direct_wire_reads_pass_json_locators(self) -> None:
        # The wire verbs reject a bare identifier; every direct read passes the JSON locator.
        for text in (PILOT_WORKFLOW, PILOT_BACKLOG):
            for verb in ("comment-list", "relation-list"):
                self.assertNotRegex(text, rf"wire {verb} --locator <")
                self.assertIn(f'wire {verb} --locator "$LOCATOR"', text)
        self.assertIn('{"durable":issue.id,"display":issue.identifier}', PILOT_BACKLOG)

    def test_unset_ready_state_is_a_noop_for_every_provider(self) -> None:
        def forbidden_execute(_request):
            raise AssertionError("unset readyState must not execute transport")

        for provider in (github, gitlab, jira):
            with self.subTest(provider=provider.__name__):
                self.assertEqual(
                    provider.list_open({"tracker": {}}, forbidden_execute),
                    {"issues": [], "truncated": False},
                )
        # Linear refuses instead of returning a silent empty (fn-182.2 / #311):
        # a caller can handle a refusal, it cannot detect a blind enumeration.
        out = linear.list_open({"tracker": {}}, forbidden_execute)
        self.assertIsInstance(out, TrackerError)
        self.assertIs(out.cls, ErrorClass.UNRESOLVED)
        self.assertEqual(out.subtype, "ready_state")

class QuestionValveContractTests(unittest.TestCase):
    def test_closed_marker_families_remain_in_semantic_reference(self) -> None:
        for marker in (
            "flow-next:sync",
            "flow-next:question",
            "flow-next:answer",
            "flow-next:status",
        ):
            self.assertIn(marker, COMMENTS)

    def test_question_identity_fields(self) -> None:
        self.assertIn("subjectId", COMMENTS)
        self.assertIn("questionSlug", COMMENTS)

    def test_flat_tracker_answer_matches_by_id(self) -> None:
        self.assertIn("answer id=<hash>", COMMENTS)


if __name__ == "__main__":
    unittest.main()
