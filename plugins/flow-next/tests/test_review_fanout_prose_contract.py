"""fn-215 fan-out workflow contract (completion review R8/R15).

Grep-shaped assertions on the flowctl command and flag tokens the fan-out
workflows invoke, and executable-line greps for the round lifecycle. No prose,
heading or phrasing assertions. Canonical files and the generated Codex mirror
are both checked.
"""

from __future__ import annotations

import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
PLUGIN = REPO_ROOT / "plugins" / "flow-next"

CANONICAL = PLUGIN / "skills" / "flow-next-impl-review"
MIRROR = PLUGIN / "codex" / "skills" / "flow-next-impl-review"


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


class CodexWorkflowFanoutContract(unittest.TestCase):
    """workflow-codex.md: command/flag tokens."""

    def _texts(self) -> list[str]:
        return [
            _read(CANONICAL / "workflow-codex.md"),
            _read(MIRROR / "workflow-codex.md"),
        ]

    def test_fanout_commands_and_flags_present(self) -> None:
        for text in self._texts():
            self.assertIn("impl-review-fanout ", text)
            self.assertIn("review-route ", text)
            self.assertIn("--rotate-stale", text)
            self.assertIn("impl-review-fanout-finalize", text)
            self.assertIn("--draw ", text)
            self.assertIn("--merged-file", text)
            self.assertIn("--rid", text)
            self.assertIn("--receipt", text)

    def test_merge_plan_flag_in_executable_block(self) -> None:
        # Finalize consumes judgments and derives the survivor count.
        for text in self._texts():
            self.assertTrue(any(line.lstrip().startswith("args=(") and "--merge-plan" in line
                                for line in text.splitlines()))


class HostWorkflowFanoutContract(unittest.TestCase):
    """workflow-host.md: round-lifecycle executable lines."""

    def _texts(self) -> list[str]:
        return [
            _read(CANONICAL / "workflow-host.md"),
            _read(MIRROR / "workflow-host.md"),
        ]

    def test_one_increment_one_record_executable_lines(self) -> None:
        # Exactly one executable increment line and one executable record line
        # (FLOWCTL invocations), pinning the one-increment/one-record shape.
        for text in self._texts():
            increment_lines = [
                line
                for line in text.splitlines()
                if "review-rounds increment" in line and "FLOWCTL" in line
            ]
            record_lines = [
                line
                for line in text.splitlines()
                if "review-rounds record" in line and "FLOWCTL" in line
            ]
            self.assertEqual(len(increment_lines), 1)
            self.assertEqual(len(record_lines), 1)

    def test_sequential_fallback_names_review_route(self) -> None:
        for text in self._texts():
            self.assertIn("review-route ", text)


if __name__ == "__main__":
    unittest.main()
