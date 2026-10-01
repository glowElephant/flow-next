"""`config get --raw` distinguishes an unset key from an explicit false/true.

Setup's first-run probe relies on this: a merged read returns the default,
`--raw` returns null for an unset key and the stored value otherwise.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
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


def _load_flowctl() -> Any:
    spec = importlib.util.spec_from_file_location(
        "flowctl_config_alias_under_test", FLOWCTL_PY
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class ConfigRawReadTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp())
        self.prev_cwd = Path.cwd()
        os.chdir(self.tmpdir)
        self.flowctl = _load_flowctl()
        flow_dir = self.tmpdir / ".flow"
        flow_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        os.chdir(self.prev_cwd)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_config(self, data: dict) -> None:
        config_path = self.tmpdir / ".flow" / "config.json"
        config_path.write_text(json.dumps(data), encoding="utf-8")

    def test_raw_file_probe_distinguishes_unset_from_false(self) -> None:
        self._write_config({"planSync": {"enabled": True}})
        sentinel = self.flowctl._get_config_from_file("planSync.crossSpec")
        self.assertIs(sentinel, self.flowctl._CONFIG_RAW_SENTINEL)
        self._write_config({"planSync": {"crossSpec": False}})
        value = self.flowctl._get_config_from_file("planSync.crossSpec")
        self.assertIs(value, False)
        self.assertIs(self.flowctl.get_config("planSync.crossSpec"), False)

    def _run_config_get_cli(self, key: str, *extra: str) -> dict:
        ns = argparse.Namespace(
            key=key,
            json=True,
            raw="--raw" in extra,
        )
        import contextlib

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.flowctl.cmd_config_get(ns)
        return json.loads(buf.getvalue())

    def test_cli_raw_absent_key_returns_null(self) -> None:
        self._write_config({"planSync": {"enabled": True}})
        out = self._run_config_get_cli("planSync.crossSpec", "--raw")
        self.assertIsNone(out["value"])
        self.assertTrue(out.get("raw"))
        self.assertTrue(out.get("success"))

    def test_cli_raw_explicit_false_returns_false(self) -> None:
        self._write_config({"planSync": {"crossSpec": False}})
        out = self._run_config_get_cli("planSync.crossSpec", "--raw")
        self.assertIs(out["value"], False)
        self.assertTrue(out.get("raw"))

    def test_cli_raw_explicit_true_returns_true(self) -> None:
        self._write_config({"scouts": {"github": True}})
        out = self._run_config_get_cli("scouts.github", "--raw")
        self.assertIs(out["value"], True)
        self.assertTrue(out.get("raw"))

    def test_cli_default_merges_unset_to_default_value(self) -> None:
        self._write_config({"planSync": {"enabled": True}})
        out = self._run_config_get_cli("planSync.crossSpec")
        self.assertIs(out["value"], False)
        self.assertNotIn("raw", out)

if __name__ == "__main__":
    unittest.main()
