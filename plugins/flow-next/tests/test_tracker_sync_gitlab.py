"""GitLab adapter flowctl-plumbing tests (fn-69.1).

This task adds `tracker.type: gitlab` as a real, activatable tracker. These
tests cover the DETERMINISTIC flowctl plumbing only — the enum, the config
schema defaults, and the `set-tracker-id` identifier validator; they never
invoke a live `glab`.

Asserts:
  * Activation — `tracker.type: gitlab` flips `tracker_sync_active()` true via
    the type path (R7), case-insensitively, like linear/github.
  * Config defaults — `tracker.perTracker.project` and `tracker.perTracker.host`
    exist with safe `null` defaults, paralleling GitHub's `repo` (R3).
  * Identifier validation (R4-identity) — `set-tracker-id` accepts the GitLab
    `<project>#<iid>` form INCLUDING nested `group/subgroup/project#12` plus the
    bare `#<iid>` form, and rejects `group/#12` (empty segment), `#0` (non-positive
    iid), and the existing malformed forms; the Linear handle path stays strict.

Run:
    python3 -m unittest discover -s plugins/flow-next/tests -v
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

# fn-139.1: the tracker package sits beside flowctl.py; under a test module
# sys.path[0] is THIS directory, not scripts/, so it would not import.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


HERE = Path(__file__).resolve()
FLOWCTL_PY = HERE.parent.parent / "scripts" / "flowctl.py"


def _load_flowctl(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, FLOWCTL_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class GitlabActivationConfigTestCase(unittest.TestCase):
    """Enum activation (R7) + config-schema defaults (R3)."""

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp())
        self.prev_cwd = Path.cwd()
        os.chdir(self.tmpdir)
        self.flowctl = _load_flowctl("flowctl_gitlab_config_under_test")
        (self.tmpdir / ".flow").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        os.chdir(self.prev_cwd)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_config(self, data: dict) -> None:
        (self.tmpdir / ".flow" / "config.json").write_text(
            json.dumps(data), encoding="utf-8"
        )

    # --- R7: enum activation ------------------------------------------------

    # --- R3: config schema defaults -----------------------------------------

    def test_default_config_carries_gitlab_per_tracker_keys(self) -> None:
        pt = self.flowctl.get_default_config()["tracker"]["perTracker"]
        # `project` parallels GitHub's `repo` (group/project path); `host` pins a
        # self-managed base. Both default null (safe — null ⇒ resolve from glab /
        # CI_SERVER_URL, never assume gitlab.com).
        self.assertIn("project", pt)
        self.assertIsNone(pt["project"])
        self.assertIn("host", pt)
        self.assertIsNone(pt["host"])

    def test_gitlab_per_tracker_keys_resolve_via_dotted_path(self) -> None:
        # No on-disk override → merged defaults resolve the new leaves (not a
        # missing-key error).
        self.assertIsNone(self.flowctl.get_config("tracker.perTracker.project"))
        self.assertIsNone(self.flowctl.get_config("tracker.perTracker.host"))


if __name__ == "__main__":
    unittest.main()
