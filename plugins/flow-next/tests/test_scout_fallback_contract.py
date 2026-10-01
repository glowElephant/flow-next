"""Plumbing contract for scout `.clawpatch/` fallback (fn-50.3).

`flowctl repo-map list --json` in a throwaway git repo with NO `.clawpatch/`
returns `{success:true, count:0, features:[], clawpatch_present:false}` with
exit 0: the production path scouts call degrades to the empty envelope.
(Runs in a temp git repo, not the in-repo fixture, because `repo-map`
resolves `.clawpatch/` from the git toplevel.)

Run:
    python -m unittest discover -s plugins/flow-next/tests \
        -p "test_scout_fallback_contract.py" -v
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling test helpers
from flowctl_test_support import FLOWCTL_CMD


HERE = Path(__file__).resolve()
FIXTURE_NO_CLAWPATCH = (
    HERE.parent / "fixtures" / "scout-without-clawpatch"
)


def _run(
    *args: str, cwd: str | None = None
) -> subprocess.CompletedProcess:
    """Invoke `python flowctl.py <args>` against the given cwd."""
    return subprocess.run(
        [*FLOWCTL_CMD, *args],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=cwd,
        env=os.environ.copy(),
    )


class PlumbingContract(unittest.TestCase):
    """`flowctl repo-map list --json` returns count:0 against no-clawpatch
    fixture — the production-path the agent prose tells scouts to call."""

    def test_repo_map_list_json_against_fixture_returns_count_zero(
        self,
    ) -> None:
        self.assertTrue(
            FIXTURE_NO_CLAWPATCH.is_dir(),
            msg=(
                "fixture dir missing — tests/fixtures/scout-without-clawpatch/"
            ),
        )
        # Fixture must NOT contain a .clawpatch/ subdir; the absence is
        # the contract.
        self.assertFalse(
            (FIXTURE_NO_CLAWPATCH / ".clawpatch").exists(),
            msg=(
                "fixture invalid — scout-without-clawpatch/ must NOT "
                "contain a .clawpatch/ directory"
            ),
        )
        # HERMETIC plumbing check: `repo-map` resolves `.clawpatch/` via
        # get_repo_root() (git toplevel), so running with cwd inside the
        # flow-next repo's own tree would pick up a REAL `.clawpatch/` when a
        # developer has run `/flow-next:map` locally (it's gitignored — absent
        # in CI, but present after dogfooding). The in-repo fixture dir cannot
        # isolate from the repo's git root. Run in a throwaway git repo so the
        # `.clawpatch/` absence is genuine regardless of the host repo's state.
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(
                ["git", "init", td],
                capture_output=True,
                text=True,
                check=True,
            )
            res = _run("repo-map", "list", "--json", cwd=td)
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        payload = json.loads(res.stdout)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["count"], 0)
        self.assertEqual(payload["features"], [])
        self.assertFalse(payload["clawpatch_present"])


if __name__ == "__main__":
    unittest.main()
