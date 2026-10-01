"""Opt-in `tracker.perEvent` leaves for land and qa, through the production CLI.

`tracker.perEvent.land.merged` tunes only land's optional verdict comment (the
merge->Done projection rides the bridge-active predicate, not this leaf);
`tracker.perEvent.qa` gates qa's verdict comment. Both default `off`, so a
bare `enabled=true` activates no lifecycle-event sync.

Each row runs `init` -> `config get` -> `config set` -> `config get` through
`scripts/flowctl.py` as a subprocess, then checks that sibling leaves keep
their defaults and the activation predicate stays off. The defaults-dict shape
and the verb enum are read in-process.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling test helpers
from flowctl_test_support import FLOWCTL_CMD  # noqa: E402

# The tracker package sits beside flowctl.py; under a test module sys.path[0]
# is THIS directory, not scripts/, so it would not import.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

FLOWCTL_PY = Path(__file__).resolve().parent.parent / "scripts" / "flowctl.py"

# (leaf key under tracker.perEvent, opt-in verb)
LEAVES = (
    ("land.merged", "push"),
    ("qa", "comment"),
)
# Sibling leaves that must keep their `off` default when a row's leaf is set.
SIBLINGS = ("completionReview", "work.firstClaim")
# Default `off` leaves of the same nested perEvent object.
DEFAULT_OFF = (
    "capture", "interview", "plan", "makePr", "resolvePr", "completionReview",
    "work.firstClaim", "land.merged", "qa",
)


def _load_flowctl() -> Any:
    spec = importlib.util.spec_from_file_location("flowctl_perevent_leaves_under_test", FLOWCTL_PY)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _flowctl(cwd: Path, *args: str) -> dict[str, Any]:
    proc = subprocess.run(
        [*FLOWCTL_CMD, *args, "--json"],
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "FLOW_NO_DEPRECATION": "1"},
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"rc={proc.returncode}: args={args} stdout={proc.stdout!r} stderr={proc.stderr!r}"
        )
    return json.loads(proc.stdout.decode("utf-8"))


def _get(pe: dict, dotted: str) -> Any:
    node = pe
    for part in dotted.split("."):
        node = node[part]
    return node


class PerEventLeafTestCase(unittest.TestCase):
    def test_leaf_defaults_off_round_trips_and_leaves_siblings_alone(self) -> None:
        for leaf, verb in LEAVES:
            key = f"tracker.perEvent.{leaf}"
            with self.subTest(leaf=leaf), tempfile.TemporaryDirectory() as td:
                repo = Path(td)
                subprocess.check_call([*FLOWCTL_CMD, "init", "--json"], cwd=str(repo), stdout=subprocess.DEVNULL)
                # Fresh repo merges the default `off`, not null.
                self.assertEqual(_flowctl(repo, "config", "get", key)["value"], "off")
                self.assertEqual(_flowctl(repo, "config", "set", key, verb)["value"], verb)
                self.assertEqual(_flowctl(repo, "config", "get", key)["value"], verb)
                for sibling in SIBLINGS:
                    self.assertEqual(
                        _flowctl(repo, "config", "get", f"tracker.perEvent.{sibling}")["value"],
                        "off",
                        sibling,
                    )
                # Opting a leaf in never activates the bridge (no type / not enabled).
                self.assertFalse(_flowctl(repo, "sync", "active")["active"])

    def test_default_shape_and_verbs(self) -> None:
        flowctl = _load_flowctl()
        pe = flowctl.get_default_tracker_config()["perEvent"]
        for leaf in DEFAULT_OFF:
            with self.subTest(default=leaf):
                self.assertEqual(_get(pe, leaf), "off")
        for verb in ("off", *(v for _, v in LEAVES)):
            with self.subTest(verb=verb):
                self.assertIn(verb, flowctl.TRACKER_PER_EVENT_LEAVES)


if __name__ == "__main__":
    unittest.main()
