"""Capture read-back: the shared doc exists, and the Codex generator's
negative-context detector does not treat a negated footer as an ask anchor.
"""

from __future__ import annotations

import pathlib
import re
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
PLUGIN = REPO_ROOT / "plugins" / "flow-next"


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


class CaptureReferences(unittest.TestCase):
    def test_read_back_doc_exists(self) -> None:
        self.assertTrue((PLUGIN / "docs" / "read-back.md").is_file())


class CodexQuestionPlacement(unittest.TestCase):
    def test_negative_footer_is_not_an_ask_anchor(self) -> None:
        source = _read(REPO_ROOT / "scripts" / "sync-codex.sh")
        function = "def is_negative_context(line):" + source.split(
            "def is_negative_context(line):", 1
        )[1].split("\ndef is_table_line", 1)[0]
        namespace = {"re": re}
        # Execute only the repository-owned generator function extracted above.
        exec(compile(function, "sync-codex:is_negative_context", "exec"), namespace)  # noqa: S102
        negative = namespace["is_negative_context"]
        self.assertTrue(negative("Informational only — never a plain-text numbered prompt."))
        self.assertFalse(negative("Use `plain-text numbered prompt` for one short editor question:"))


if __name__ == "__main__":
    unittest.main()
