"""fn-83.4 — done-evidence provenance.

BASE_COMMIT + done-evidence provenance are load-bearing for impl-review diff
scoping and commit-range provenance: ``base_commit`` + the FULL base..HEAD
commit list survive a real `flowctl done` round-trip against a tmp-repo
fixture (production CLI wire form).
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # sibling test helpers
from flowctl_test_support import FLOWCTL_CMD


# ── Done-evidence provenance: base_commit + full commit list ──────────────

TASK_BODY = """## Description

Evidence fixture task.

## Acceptance

- [ ] done

## Done summary
TBD

## Evidence
- Commits:
- Tests:
- PRs:
"""


class DoneEvidenceProvenance(unittest.TestCase):
    """`flowctl done` round-trips base_commit + a multi-commit list.

    Drives the production CLI wire form (the exact command the worker runs)
    against a tmp .flow fixture — the additive `base_commit` field and the
    full fix-loop commit list must survive into `show --json` evidence.
    """

    def setUp(self) -> None:
        self.tmpdir = pathlib.Path(tempfile.mkdtemp()).resolve()
        self.prev_cwd = pathlib.Path.cwd()
        os.chdir(self.tmpdir)
        flow = self.tmpdir / ".flow"
        (flow / "tasks").mkdir(parents=True)
        (flow / "specs").mkdir(parents=True)
        (flow / "specs" / "fn-9.json").write_text(
            json.dumps({"id": "fn-9", "title": "Fixture", "status": "open"}),
            encoding="utf-8",
        )
        (flow / "specs" / "fn-9.md").write_text("# fn-9\n", encoding="utf-8")
        (flow / "tasks" / "fn-9.2.json").write_text(
            json.dumps({"id": "fn-9.2", "spec": "fn-9", "title": "Fixture"}),
            encoding="utf-8",
        )
        (flow / "tasks" / "fn-9.2.md").write_text(TASK_BODY, encoding="utf-8")

    def tearDown(self) -> None:
        os.chdir(self.prev_cwd)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _flowctl(self, *args: str) -> "subprocess.CompletedProcess[str]":
        return subprocess.run(
            [*FLOWCTL_CMD] + list(args),
            cwd=str(self.tmpdir),
            capture_output=True,
            text=True,
        )

    def test_base_commit_and_full_commit_list_round_trip(self) -> None:
        start = self._flowctl("start", "fn-9.2", "--json")
        self.assertEqual(start.returncode, 0, start.stdout + start.stderr)

        base = "aaaa111122223333444455556666777788889999"
        fix_loop_commits = [
            "bbbb111122223333444455556666777788889999",
            "cccc111122223333444455556666777788889999",
            "dddd111122223333444455556666777788889999",
        ]
        evidence = {
            "commits": fix_loop_commits,
            "base_commit": base,
            "tests": ["pytest -q"],
            "prs": [],
        }
        ev_path = self.tmpdir / "evidence.json"
        ev_path.write_text(json.dumps(evidence), encoding="utf-8")

        done = self._flowctl(
            "done",
            "fn-9.2",
            "--summary",
            "fixture done",
            "--evidence-json",
            str(ev_path),
            "--json",
        )
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

        show = self._flowctl("show", "fn-9.2", "--json")
        self.assertEqual(show.returncode, 0, show.stdout + show.stderr)
        record = json.loads(show.stdout)
        self.assertEqual(record["status"], "done")
        got = record["evidence"]
        # Additive field survives untouched — no migration, no filtering.
        self.assertEqual(got["base_commit"], base)
        # Multi-commit fix-loop tasks fully covered: the FULL ordered list.
        self.assertEqual(got["commits"], fix_loop_commits)
        self.assertEqual(got["tests"], ["pytest -q"])


if __name__ == "__main__":
    unittest.main()
