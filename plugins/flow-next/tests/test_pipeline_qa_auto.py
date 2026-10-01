"""`pipeline.qa` is the enum `off | on | auto`; the unattended driver reads all
three.

Contract pins only (G2): executable runs of the driver's QA-gate fence. The
`auto` semantics themselves are judgment in the flow skill's routing reference; nothing here asserts prose.

* the `flow --auto` QA gate (`skills/flow-next-flow/auto.md`, formerly
  pilot's) resolves two flags from the root snapshot: the literal `on` sets
  `QA_STAGE_ENABLED=1`, the literal `auto` sets `QA_STAGE_AUTO=1`, anything
  else leaves both 0 - proven by running the fence against each value;
* the flow skill's gate-selection reference exists.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
AUTO_MD = PLUGIN_DIR / "skills" / "flow-next-flow" / "auto.md"
GATE_SELECTION = (
    PLUGIN_DIR / "skills" / "flow-next-flow" / "references" / "gate-selection.md"
)

_POSIX_BASH = unittest.skipIf(
    sys.platform == "win32"
    or shutil.which("bash") is None
    or shutil.which("jq") is None,
    "executable fence test needs a POSIX bash + jq",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _qa_gate_fence(workflow: str) -> str:
    start = workflow.find("QA_STAGE_ENABLED=0\n")
    assert start != -1, "flow --auto QA gate fence not found"
    end = workflow.find("```", start)
    return workflow[start:end]


class AutoQaGateReadsEveryValue(unittest.TestCase):
    @_POSIX_BASH
    def test_fence_resolves_each_literal_to_its_flag(self) -> None:
        fence = _qa_gate_fence(_read(AUTO_MD))
        self.assertIn("PILOT_SNAPSHOT", fence)
        # value -> (QA_STAGE_ENABLED, QA_STAGE_AUTO)
        cases = (
            ("auto", "0", "1"),
            ("on", "1", "0"),
            ("off", "0", "0"),
            ("maybe", "0", "0"),
            (True, "0", "0"),
        )
        for value, enabled, auto in cases:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as td:
                snap = Path(td) / "snap.json"
                snap.write_text(
                    json.dumps({"key": None, "value": {"pipeline": {"qa": value}}})
                )
                script = fence + '\nprintf "\\nENABLED=%s AUTO=%s" "$QA_STAGE_ENABLED" "$QA_STAGE_AUTO"'
                res = subprocess.run(
                    ["bash", "-c", script], capture_output=True, text=True,
                    env={**os.environ, "PILOT_SNAPSHOT": json.dumps({"config": {"pipeline": {"qa": value}}})},
                )
                self.assertEqual(res.returncode, 0, f"{value}: {res.stderr}")
                self.assertTrue(
                    res.stdout.endswith(f"ENABLED={enabled} AUTO={auto}"),
                    f"{value}: {res.stdout!r}",
                )


    @_POSIX_BASH
    def test_selected_candidate_false_freshness_does_not_fall_back_to_another_spec(self):
        script = _qa_gate_fence(_read(AUTO_MD)) + '\nprintf "%s" "$QA_FRESH"'
        payload = {"config": {"pipeline": {"qa": "on"}}, "selected": {"qa_fresh": True},
                   "candidates": [{"id": "fn-2", "qa_fresh": False}]}
        result = subprocess.run(["bash", "-c", script], capture_output=True, text=True,
                                env={**os.environ, "SELECTED_SPEC": "fn-2", "PILOT_SNAPSHOT": json.dumps(payload)})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "false")


    @_POSIX_BASH
    def test_missing_snapshot_stops_instead_of_skipping_qa(self):
        # pipeline.qa=on must never be read as "" because the snapshot was lost
        # between tool calls; the fence stops NEEDS_HUMAN instead.
        env = {k: v for k, v in os.environ.items() if k != "PILOT_SNAPSHOT"}
        script = _qa_gate_fence(_read(AUTO_MD)) + '\nprintf "QA=%s" "$QA_STAGE_ENABLED"'
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q", tmp], check=True)
            result = subprocess.run(["bash", "-c", script], cwd=tmp, env=env,
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("NEEDS_HUMAN", result.stdout)
        self.assertNotIn("QA=", result.stdout)


class AutoRuleRoutesToGateSelection(unittest.TestCase):
    def test_reference_exists(self) -> None:
        self.assertTrue(GATE_SELECTION.is_file())


if __name__ == "__main__":
    unittest.main()
