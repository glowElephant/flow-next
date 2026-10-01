"""`flowctl init` default-merge keeps explicit values and unknown user keys.

An explicit `planSync.crossSpec` is never overwritten, and a key flowctl no
longer reads (the pre-2.0 `planSync.crossEpic`) is preserved untouched.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "plugins" / "flow-next" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import flowctl  # noqa: E402


def _run_init(repo_root: Path) -> dict:
    """Invoke `flowctl init --json` against ``repo_root``."""
    args = mock.MagicMock()
    args.json = True
    args.path = str(repo_root)
    cwd = Path.cwd()
    captured: dict = {}
    try:
        os.chdir(repo_root)
        with mock.patch.object(flowctl, "json_output", side_effect=captured.update):
            flowctl.cmd_init(args)
    finally:
        os.chdir(cwd)
    return captured


class InitKeepsExplicitAndUnknownKeys(unittest.TestCase):
    def test_canonical_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            flow_dir = repo_root / ".flow"
            flow_dir.mkdir()
            (flow_dir / "config.json").write_text(json.dumps({
                "planSync": {
                    "crossEpic": True,    # unknown (retired) key
                    "crossSpec": False,   # explicit canonical value
                },
            }))
            result = _run_init(repo_root)
            cfg = json.loads((flow_dir / "config.json").read_text())
            self.assertEqual(cfg["planSync"]["crossSpec"], False)
            self.assertEqual(cfg["planSync"]["crossEpic"], True)
            self.assertEqual(
                [a for a in result.get("actions", []) if "crossEpic" in a], []
            )


if __name__ == "__main__":
    unittest.main()
