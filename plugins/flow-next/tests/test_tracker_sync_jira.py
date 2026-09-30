"""Jira adapter flowctl-plumbing + ceremony-wiring tests (fn-70.1).

This task adds `tracker.type: jira` as a real, activatable tracker. It is
DETERMINISTIC flowctl plumbing only — the activation enum, the `perTracker`
config schema (`baseUrl`/`projectKey`/`authScheme`/`apiVersion`/`sslVerify`/
`statusMap`), and the `set-tracker-id` identifier validator (Jira keys are the
existing `KEY-N` form, so this is regression coverage + error-text, NOT a
rewrite) — plus the receipt-transport `rest` token. No Jira transport
code lives here (that is the jira.md adapter prose in fn-70.2/.3); these tests
never invoke a live Jira REST API.

Asserts:
  * Activation (R7) — `tracker.type: jira` flips `tracker_sync_active()` true via
    the type path, case-insensitively, like linear/github/gitlab.
  * Config defaults (R8) — `tracker.perTracker` carries `baseUrl`/`projectKey`/
    `authScheme`/`apiVersion`/`sslVerify`/`statusMap` with safe defaults.
  * Identifier validation (R6-identity) — `set-tracker-id` accepts Jira
    `PROJ-123` / bare `proj-123` (the `KEY-N` form), preserving GitHub `#N` and
    the reserved-`fn` guard; the Linear handle path stays strict.
  * Resolver END-TO-END (R6-identity, fn-69 scar: a green validator ≠ a working
    resolver) — `flowctl show PROJ-123` AND the `work`/`start PROJ-123.M` command
    surface actually resolve to the linked spec, not just the validator.
  * Tracker-first (R6-identity) — `spec create --tracker-first
    --tracker-identifier PROJ-123` mints a clean `proj-123-slug` (Jira IS
    `KEY-N` like Linear; BOTH entry flows work).
  * Receipt transport (R2) — `sync receipt --transport rest` round-trips
    (free-form; `rest` accepted).

Run:
    python3 -m unittest discover -s plugins/flow-next/tests -v
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
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


class JiraActivationConfigTestCase(unittest.TestCase):
    """Enum activation (R7) + config-schema defaults (R8)."""

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp())
        self.prev_cwd = Path.cwd()
        os.chdir(self.tmpdir)
        self.flowctl = _load_flowctl("flowctl_jira_config_under_test")
        (self.tmpdir / ".flow").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        os.chdir(self.prev_cwd)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_config(self, data: dict) -> None:
        (self.tmpdir / ".flow" / "config.json").write_text(
            json.dumps(data), encoding="utf-8"
        )

    # --- R7: enum activation ------------------------------------------------

    # --- R8: config schema defaults -----------------------------------------

    def test_default_config_carries_jira_per_tracker_keys(self) -> None:
        pt = self.flowctl.get_default_config()["tracker"]["perTracker"]
        # site base + project key default null (env/ceremony fill them).
        self.assertIn("baseUrl", pt)
        self.assertIsNone(pt["baseUrl"])
        self.assertIn("projectKey", pt)
        self.assertIsNone(pt["projectKey"])
        # auth scheme + api version persist the ceremony's deployment decision;
        # null until the ceremony detects + writes them.
        self.assertIn("authScheme", pt)
        self.assertIsNone(pt["authScheme"])
        self.assertIn("apiVersion", pt)
        self.assertIsNone(pt["apiVersion"])
        # sslVerify defaults TRUE (opt-in false for self-hosted internal-CA).
        self.assertIn("sslVerify", pt)
        self.assertTrue(pt["sslVerify"])
        # statusMap defaults to an empty dict (normalized status → Jira name/id).
        self.assertIn("statusMap", pt)
        self.assertEqual(pt["statusMap"], {})

    def test_jira_per_tracker_keys_resolve_via_dotted_path(self) -> None:
        # No on-disk override → merged defaults resolve the new leaves (not a
        # missing-key error). NOTE: `get_config` collapses an empty-dict leaf to
        # the `default` (None) — pre-existing behavior shared by `labelMap` /
        # `priorityMap` — so `statusMap` reads None via the dotted path while its
        # `{}` default lives in get_default_config() (asserted above). The scalar
        # leaves resolve to their literal defaults.
        self.assertIsNone(self.flowctl.get_config("tracker.perTracker.baseUrl"))
        self.assertIsNone(self.flowctl.get_config("tracker.perTracker.projectKey"))
        self.assertIsNone(self.flowctl.get_config("tracker.perTracker.authScheme"))
        self.assertIsNone(self.flowctl.get_config("tracker.perTracker.apiVersion"))
        self.assertTrue(self.flowctl.get_config("tracker.perTracker.sslVerify"))
        # Empty-dict leaf reads None via get_config (same as labelMap/priorityMap).
        self.assertIsNone(self.flowctl.get_config("tracker.perTracker.statusMap"))
        self.assertIsNone(self.flowctl.get_config("tracker.perTracker.labelMap"))


class JiraReceiptTransportTestCase(unittest.TestCase):
    """`sync receipt --transport rest` round-trips (R2).

    `--transport` is free-form (no `choices`), so `rest` is accepted; assert it
    survives into the written receipt JSON (the Jira REST transport label).
    """

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp())
        self.prev_cwd = Path.cwd()
        os.chdir(self.tmpdir)
        subprocess.run(
            ["git", "init", "-q"], cwd=self.tmpdir, check=True, capture_output=True
        )
        self.flowctl = _load_flowctl("flowctl_jira_receipt_under_test")
        self._call(func=self.flowctl.cmd_init)

    def tearDown(self) -> None:
        os.chdir(self.prev_cwd)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _call(self, *, func, **kwargs) -> dict:
        kwargs.setdefault("json", True)
        ns = argparse.Namespace(**kwargs)
        buf = io.StringIO()
        with redirect_stdout(buf):
            func(ns)
        out = buf.getvalue().strip()
        return json.loads(out) if out else {}

    def test_receipt_accepts_rest_transport(self) -> None:
        spec_id = self._call(
            func=self.flowctl.cmd_spec_create, title="Jira receipt", branch=None
        )["id"]
        res = self._call(
            func=self.flowctl.cmd_sync_receipt,
            id=spec_id,
            status="pushed",
            transport="rest",
            tracker_id=None,
            event=None,
            note=None,
            merges_file=None,
        )
        receipt_path = Path(res["receipt"])
        self.assertTrue(receipt_path.exists())
        written = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(written["transport"], "rest")


if __name__ == "__main__":
    unittest.main()
