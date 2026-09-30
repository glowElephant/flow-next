"""Spec-id routing: mint-site command shape and reachability.

Covers the commands the mint sites run (config key, CLI flags, snapshot jq
path, the durable-id argument) and that each spine loads its mint reference.
The surrounding prose is not pinned.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
SKILLS = PLUGIN / "skills"

PLAN_STEPS = SKILLS / "flow-next-plan" / "steps.md"
PLAN_MINT_REF = SKILLS / "flow-next-plan" / "references" / "tracker-first-mint.md"
WORK_MINT_REF = SKILLS / "flow-next-work" / "references" / "spec-id-mint.md"
WORK_PHASES = SKILLS / "flow-next-work" / "phases.md"
CAPTURE_WF = SKILLS / "flow-next-capture" / "workflow.md"
CAPTURE_TRACKER_REF = (
    SKILLS / "flow-next-capture" / "references" / "tracker-integration.md"
)

# Each site is the spine file plus the reference its gate loads.
PLAN_SITE = [PLAN_STEPS, PLAN_MINT_REF]
WORK_SITE = [WORK_PHASES, WORK_MINT_REF]
CAPTURE_SITE = [CAPTURE_WF, CAPTURE_TRACKER_REF]

MINT_SITES = {
    "plan": PLAN_SITE,
    "work": WORK_SITE,
    "capture": CAPTURE_SITE,
}


def _read(path) -> str:
    """Read one path, or concatenate a list of paths that jointly form one site."""
    if isinstance(path, (list, tuple)):
        return "\n".join(p.read_text(encoding="utf-8") for p in path)
    return path.read_text(encoding="utf-8")


class SpecIdConfigReadBudget(unittest.TestCase):
    """Mint sites route from a root snapshot, never a per-leaf read, and
    never take a SECOND snapshot when the skill already holds one."""

    # Match an actual invocation - the flowctl binary followed by the leaf.
    LEAF_INVOCATION = re.compile(
        r"""(?:\$FLOWCTL|"\$FLOWCTL"|\$\{FLOWCTL\}|flowctl(?:\.py)?)\s+config\s+get\s+tracker\.specIds"""
    )

    def test_no_per_leaf_specids_read_at_any_mint_site(self) -> None:
        for name, path in MINT_SITES.items():
            with self.subTest(site=name):
                hit = self.LEAF_INVOCATION.search(_read(path))
                self.assertIsNone(
                    hit,
                    f"{name}: per-leaf read invoked: {hit.group(0) if hit else ''}",
                )

    def test_sites_holding_a_snapshot_do_not_take_a_second(self) -> None:
        for name, path in (("plan", PLAN_SITE), ("capture", CAPTURE_SITE)):
            text = _read(path)
            with self.subTest(site=name):
                self.assertLessEqual(
                    text.count("config get --json"),
                    1,
                    f"{name}: more than one root snapshot taken",
                )

    def test_work_mint_reuses_phase0_snapshot(self) -> None:
        ref = _read(WORK_MINT_REF)
        self.assertNotIn("config get --json", ref)
        self.assertLessEqual(_read(WORK_PHASES).count("config get --json"), 1)

class SpecIdRoutingGate(unittest.TestCase):
    """Every mint site routes on tracker.specIds and loads its reference."""

    def test_gates_load_their_mint_reference(self) -> None:
        for name, spine, ref_name in (
            ("plan", PLAN_STEPS, "references/tracker-first-mint.md"),
            ("work", WORK_PHASES, "references/spec-id-mint.md"),
            ("capture", CAPTURE_WF, "references/tracker-integration.md"),
        ):
            with self.subTest(site=name):
                self.assertIn(
                    ref_name,
                    _read(spine),
                    f"{name}: spine does not load {ref_name} - the mint gate "
                    "is unreachable",
                )


class TrackerFirstMintIsLinked(unittest.TestCase):
    """Every tracker-first mint passes the durable id in the same call; a mint
    with only the display identifier leaves the spec unlinked and the next
    lifecycle touchpoint opens a second remote issue."""

    SITES = {
        "capture": CAPTURE_TRACKER_REF,
        "plan": PLAN_MINT_REF,
        "work": WORK_MINT_REF,
    }

    def test_each_tracker_first_mint_passes_durable_id(self) -> None:
        for name, path in self.SITES.items():
            with self.subTest(site=name):
                text = path.read_text(encoding="utf-8")
                mints = [
                    line for line in text.splitlines()
                    if "spec create --tracker-first" in line
                ]
                self.assertTrue(mints, f"{name}: no tracker-first mint found")
                for line in mints:
                    self.assertRegex(
                        line, r"(?<!\S)--tracker-id(?=[\s=])",
                        f"{name}: tracker-first mint without --tracker-id "
                        "publishes an unlinked spec",
                    )


if __name__ == "__main__":
    unittest.main()
