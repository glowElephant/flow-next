"""Regression contract for Capture's target-aware readiness prompt (fn-128)."""

from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CANONICAL = REPO_ROOT / "plugins" / "flow-next" / "skills" / "flow-next-capture"
MIRROR = REPO_ROOT / "plugins" / "flow-next" / "codex" / "skills" / "flow-next-capture"


def _read(directory: pathlib.Path, name: str) -> str:
    return (directory / name).read_text(encoding="utf-8")


def _ref(directory: pathlib.Path, name: str) -> str:
    return (directory / "references" / name).read_text(encoding="utf-8")


# Branch-disclosure (fn-169) moved the readiness machinery out of workflow.md
# into the references its §5.9 / rewrite gates load. Substance is asserted
# against those references; workflow.md is asserted to still route to them.
MARK_READY_LINK = "[references/mark-ready.md](references/mark-ready.md)"


class CaptureReadinessContract(unittest.TestCase):
    # Only the executable gate lines and the links that reach them are
    # checked; the surrounding prose is not pinned.

    def test_rewrite_offer_follows_target_state(self) -> None:
        for directory in (CANONICAL, MIRROR):
            with self.subTest(directory=directory):
                self.assertIn(
                    '[[ "$REWRITE_WAS_READY" == true ]] && READY_OFFER=true',
                    _ref(directory, "mark-ready.md"),
                )
                self.assertIn(MARK_READY_LINK, _read(directory, "workflow.md"))

    def test_new_capture_retains_adoption_gate(self) -> None:
        for directory in (CANONICAL, MIRROR):
            with self.subTest(directory=directory):
                self.assertIn(
                    '[[ "$READY_ADOPTED" =~ ^[0-9]+$ && "$READY_ADOPTED" -ge 1 ]]',
                    _ref(directory, "mark-ready.md"),
                )
                self.assertIn(MARK_READY_LINK, _read(directory, "workflow.md"))

    def test_tracker_authority_gate(self) -> None:
        for directory in (CANONICAL, MIRROR):
            with self.subTest(directory=directory):
                mark_ready = _ref(directory, "mark-ready.md")
                self.assertIn("tracker.readyState", mark_ready)
                self.assertIn('&& -z "$READY_STATE"', mark_ready)

    def test_rewrite_resets_readiness(self) -> None:
        for directory in (CANONICAL, MIRROR):
            with self.subTest(directory=directory):
                self.assertIn(
                    'spec unready "$SPEC_ID"', _ref(directory, "rewrite-mode.md")
                )
                self.assertIn(
                    "references/rewrite-mode.md", _read(directory, "workflow.md")
                )


if __name__ == "__main__":
    unittest.main()
