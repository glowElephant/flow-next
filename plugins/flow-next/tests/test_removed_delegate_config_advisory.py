"""Advisory for configs still carrying removed keys (flow-98 R1/R5, fn-195 R6).

The packaged codex-delegation subsystem is gone (the six `work.delegate*`
keys) and so is the model-pin role map with its staleness stamp (the
`models.*` block). A repo whose `.flow/config.json` still carries them keeps
working - flowctl ignores the keys - and gets ONE advisory line per
invocation naming them and pointing at the agentic route (the
/flow-next:setup model-routing block plus the `flowctl usage` recipes).

7.0 removed the HTML render lenses; `artifacts.html.enabled` gets the same
advisory, pointing at /flow-next:visual or an HTML page asked for in
conversation. `pipeline.chainStages` gets it too: `flow --auto` already runs
QA then make-pr as consecutive hops.

Pinned here: presence detection is raw-file-only, the advisory is one line
per invocation (never one per key), it goes to stderr so `--json` stays
parseable, it never blocks, and a fresh repo is silent.
"""

from __future__ import annotations

import argparse
import contextlib
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

FLOWCTL_PY = Path(__file__).resolve().parent.parent / "scripts" / "flowctl.py"


def _load_flowctl() -> Any:
    spec = importlib.util.spec_from_file_location(
        "flowctl_removed_delegate_advisory_under_test", FLOWCTL_PY
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


LEGACY_CONFIG = {
    "work": {
        "delegate": "codex",
        "delegateModel": "gpt-5.6-terra",
        "delegateEffort": "medium",
        "delegateSandbox": "yolo",
        "delegateConsent": True,
        "delegateDecision": "auto",
    },
    "land": {
        "release": True, "reviewSignal": "silence", "automatedReviewers": "",
        "reviewTrigger": "", "ciFixBudget": 3, "cleanReviewCommentPattern": "",
        "requestReviewers": "", "patienceMinutesAfterReview": None,
    },
    "models": {
        "roles": {"review": {"codex": "gpt-5.6-terra:medium"}},
        "verifiedAt": "2026-07-19",
        "verifiedWith": {"codex": "0.144"},
    },
    "artifacts": {"html": {"enabled": True}},
    "pipeline": {"qa": "off", "chainStages": "on"},
}


class RemovedDelegateAdvisoryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp())
        self.prev_cwd = Path.cwd()
        os.chdir(self.tmpdir)
        self.flowctl = _load_flowctl()
        (self.tmpdir / ".flow").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        os.chdir(self.prev_cwd)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_config(self, cfg: dict) -> None:
        (self.tmpdir / ".flow" / "config.json").write_text(
            json.dumps(cfg), encoding="utf-8"
        )

    def _config_get(self, key: str) -> tuple[dict, str]:
        """Run `config get <key> --json`; return (payload, stderr)."""
        ns = argparse.Namespace(key=key, json=True, raw=False)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.flowctl.cmd_config_get(ns)
        return json.loads(out.getvalue()), err.getvalue()

    # -- detection (raw file only) --

    def test_all_removed_keys_detected(self) -> None:
        self._write_config(LEGACY_CONFIG)
        self.assertEqual(
            self.flowctl.removed_config_keys_present(),
            list(self.flowctl.REMOVED_CONFIG_KEYS),
        )

    def test_fresh_repo_detects_nothing(self) -> None:
        self.assertEqual(self.flowctl.removed_config_keys_present(), [])
        self._write_config({"memory": {"enabled": True}})
        self.assertEqual(self.flowctl.removed_config_keys_present(), [])

    def test_single_key_detected(self) -> None:
        self._write_config({"work": {"delegate": "codex"}})
        self.assertEqual(
            self.flowctl.removed_config_keys_present(), ["work.delegate"]
        )

    # -- the advisory line --

    def test_note_is_one_actionable_line_naming_the_keys(self) -> None:
        note = self.flowctl.removed_config_keys_note(
            ["work.delegate", "models.roles"]
        )
        self.assertEqual(note.count("\n"), 0)
        self.assertIn("work.delegate", note)
        self.assertIn("models.roles", note)
        # Actionable: names the replacement route, not just the removal.
        # fn-197: the guide is read via `flowctl usage`, not a repo copy.
        self.assertIn("flowctl usage", note)
        self.assertIn("AGENTS.md", note)

    def test_html_lens_key_note_points_at_the_replacement(self) -> None:
        note = self.flowctl.removed_config_keys_note(["artifacts.html.enabled"])
        self.assertEqual(note.count("\n"), 0)
        self.assertIn("artifacts.html.enabled", note)
        self.assertIn("/flow-next:visual", note)
        self.assertNotIn("flowctl usage", note)

    def test_config_get_emits_one_stderr_line_and_still_answers(self) -> None:
        self._write_config(LEGACY_CONFIG)
        payload, err = self._config_get("memory.enabled")
        # Never blocks: the read still answers normally.
        self.assertIs(payload["value"], True)
        self.assertEqual(len([ln for ln in err.splitlines() if ln.strip()]), 1)
        self.assertIn("work.delegate", err)

    def test_advisory_prints_at_most_once_per_invocation(self) -> None:
        self._write_config(LEGACY_CONFIG)
        self._config_get("memory.enabled")
        _payload, err = self._config_get("memory.enabled")
        self.assertEqual(err, "")

    def test_fresh_repo_is_silent(self) -> None:
        self._write_config({"memory": {"enabled": True}})
        _payload, err = self._config_get("memory.enabled")
        self.assertEqual(err, "")

    def test_advisory_never_pollutes_json_stdout(self) -> None:
        self._write_config(LEGACY_CONFIG)
        payload, _err = self._config_get("memory.enabled")
        self.assertEqual(payload["key"], "memory.enabled")

    # -- removed keys are gone from the reader --

    def test_defaults_have_no_work_namespace(self) -> None:
        self.assertNotIn("work", self.flowctl.get_default_config())

    def test_removed_keys_read_as_unset(self) -> None:
        self._write_config({"memory": {"enabled": True}})
        for key in ("work.delegate", "work.delegateModel"):
            payload, _err = self._config_get(key)
            self.assertIsNone(payload["value"], key)

    def test_html_lens_key_has_no_default_and_warns(self) -> None:
        self.assertNotIn("artifacts", self.flowctl.get_default_config())
        self._write_config({"artifacts": {"html": {"enabled": True}}})
        payload, err = self._config_get("artifacts.html.enabled")
        self.assertIs(payload["value"], True)
        self.assertIn("artifacts.html.enabled", err)

    def test_chain_stages_key_has_no_default_and_warns(self) -> None:
        self.assertEqual(self.flowctl.get_default_config()["pipeline"], {"qa": "off"})
        self._write_config({"pipeline": {"qa": "on", "chainStages": "on"}})
        payload, err = self._config_get("pipeline.qa")
        self.assertEqual(payload["value"], "on")
        self.assertEqual(err.count("\n"), 1)
        self.assertIn("pipeline.chainStages", err)
        self.assertIn("consecutive hops", err)

    def test_models_block_is_not_validated_or_read(self) -> None:
        # fn-195: no role-map validation on write, no merged default.
        self.assertNotIn("models", self.flowctl.get_default_config())


if __name__ == "__main__":
    unittest.main()
