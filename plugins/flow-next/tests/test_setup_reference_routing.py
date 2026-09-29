"""fn-130.3 — Setup reached-path router contracts."""

from __future__ import annotations

import unittest
from pathlib import Path


PLUGIN = Path(__file__).resolve().parent.parent
REPO = PLUGIN.parents[1]
SETUP = PLUGIN / "skills" / "flow-next-setup"
WORKFLOW = SETUP / "workflow.md"
REFS = SETUP / "references"
EVIDENCE = REPO / "optimization" / "reached-path" / "setup-routing-evidence.json"


class SetupReferenceRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_no_routing_or_pin_reference_is_routed(self) -> None:
        # fn-195.2: the probe-and-pin ceremony and the routing menu are deleted,
        # not skipped - so no setup reference exists to route to, and the
        # workflow must not link one.
        for gone in ("references/model-pins.md", "references/model-routing-"):
            self.assertNotIn(gone, self.text, gone)
        for stale in REFS.glob("model-*.md"):
            self.fail(f"deleted routing/pin reference regrew: {stale.name}")

    def test_optional_payloads_are_not_in_common_workflow(self) -> None:
        self.assertNotIn("cursor-agent --list-models", self.text)
        self.assertNotIn("codex accept-probe", self.text)
        self.assertNotIn("### Dispatch pins (host agent picked)", self.text)

    # Live-file hash/char freeze removed 2026-08-07 (.flow/criteria.md G1).


if __name__ == "__main__":
    unittest.main()
