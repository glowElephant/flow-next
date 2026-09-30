"""Review prompts: the machine-parsed contract only.

Prompt wording is not pinned. Prose changes are deliberate and measured (see
agent_docs/adding-skills.md "Shipped skill text"). What stays pinned is what a
parser reads back from the reviewer: the fenced-JSON tally keys the prompt asks
for must be the keys ``extract_review_json_block`` accepts. Verdict-tag grammar
is covered in test_review_prompt_template_parity.py.

Run:
    python3 -m unittest plugins.flow-next.tests.test_prompt_text_pinned -v
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

HERE = Path(__file__).resolve()


def _load_flowctl() -> Any:
    flowctl_path = HERE.parent.parent / "scripts" / "flowctl.py"
    if not flowctl_path.is_file():
        raise RuntimeError(f"flowctl.py not found at {flowctl_path}")
    spec = importlib.util.spec_from_file_location("flowctl_prompt_pin", flowctl_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


flowctl = _load_flowctl()

TALLY_KEYS = ("suppressed_count", "classification_counts", "unaddressed", "deep_findings")

DELETED_FITTER_MARKERS = (
    # Each was the visible half of a content fitter; a reappearance is a
    # fitter reappearing.
    "_CURSOR_DIFF_TRUNC_MARKER",
    "_CURSOR_DIFF_OMITTED_MARKER",
    "_CURSOR_PROMPT_TRUNC_MARKER",
)


class TestTallyBlockMatchesParser(unittest.TestCase):
    def test_prompt_names_every_key_the_parser_reads(self) -> None:
        for key in TALLY_KEYS:
            with self.subTest(key=key):
                self.assertIn(f"`{key}`", flowctl.REVIEW_JSON_TALLY_BLOCK)

    def test_parser_accepts_the_prompt_example_shape(self) -> None:
        example = {
            "suppressed_count": {"50": 3},
            "classification_counts": {"introduced": 2, "pre_existing": 4},
            "unaddressed": ["R3"],
        }
        output = "findings\n```json\n" + json.dumps(example) + "\n```\n<verdict>SHIP</verdict>"
        block = flowctl.extract_review_json_block(output)
        self.assertIsNotNone(block)
        for key in example:
            with self.subTest(key=key):
                self.assertIn(key, block)


class TestFitterMarkersStayDeleted(unittest.TestCase):
    """No prompt may tell a reviewer its evidence was shortened."""

    def test_no_fitter_marker_returns(self) -> None:
        for name in DELETED_FITTER_MARKERS:
            with self.subTest(constant=name):
                self.assertFalse(
                    hasattr(flowctl, name),
                    f"{name} is back - a content fitter returned with it. "
                    "The review prompt carries identities, not payloads.",
                )


if __name__ == "__main__":
    unittest.main()
