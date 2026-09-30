"""Cursor-host detection and review-backend mapping fences in setup.

Only fence code is checked (canonical only; the Codex mirror is not the
Cursor host path). The surrounding setup prose is not pinned.
"""

from __future__ import annotations

import unittest
from pathlib import Path


HERE = Path(__file__).resolve()
PLUGIN = HERE.parent.parent
WORKFLOW = PLUGIN / "skills" / "flow-next-setup" / "workflow.md"


def _read() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


class TestCursorPositiveDetection(unittest.TestCase):
    """Detection never depends on codex/ absence."""

    def setUp(self) -> None:
        self.assertTrue(WORKFLOW.is_file(), f"missing {WORKFLOW}")
        self.text = _read()

    def test_no_codex_absence_rung(self) -> None:
        # Old misclassifier — must be gone from the detection fence.
        self.assertNotIn('[ ! -d "${PLUGIN_ROOT}/codex" ]', self.text)

    def test_positive_cursor_home_path_signal(self) -> None:
        # Positive discriminator: PLUGIN_ROOT under ~/.cursor (CURSOR_HOME_ABS).
        self.assertIn("CURSOR_HOME_ABS", self.text)
        self.assertIn("PLUGIN_ROOT_ABS", self.text)
        self.assertIn("${HOME}/.cursor", self.text)
        self.assertIn('"${CURSOR_HOME_ABS}"/*', self.text)
        # Still requires CURSOR_AGENT + .cursor-plugin manifest.
        self.assertIn("${CURSOR_AGENT:-}", self.text)
        self.assertIn(".cursor-plugin/plugin.json", self.text)


class TestReviewBackendMapping(unittest.TestCase):
    """The answer label the menu offers maps to the host backend."""

    def setUp(self) -> None:
        self.text = _read()

    def test_host_label_is_offered(self) -> None:
        self.assertIn('"label": "Host (Recommended)"', self.text)

    def test_host_maps_to_review_backend(self) -> None:
        self.assertIn('"Host"*) REVIEW_BACKEND="host"', self.text)
        # Host branch before Cursor* so labels don't collide.
        host_case = self.text.index('"Host"*) REVIEW_BACKEND="host"')
        cursor_case = self.text.index('"Cursor"*|"cursor"*) REVIEW_BACKEND="cursor"')
        self.assertLess(host_case, cursor_case)


if __name__ == "__main__":
    unittest.main()
