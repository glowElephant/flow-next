"""Spec-scaffold invariants.

  (e) `flowctl spec skeleton` produces byte-for-byte identical output to
      the bundled templates/spec.md with YAML frontmatter stripped, run from
      a directory with no repo-root SPEC.md / spec.md override.

Additionally: a spec written under the older layout (scope-owner markers,
`### Motivation` / `### Implementation Tradeoffs` under Decision Context)
still loads unchanged.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling test helpers
from flowctl_test_support import FLOWCTL_CMD

# fn-139.1: the tracker package sits beside flowctl.py; under a test module
# sys.path[0] is THIS directory, not scripts/, so it would not import.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


HERE = Path(__file__).resolve()
PLUGIN_DIR = HERE.parent.parent
FLOWCTL_PY = PLUGIN_DIR / "scripts" / "flowctl.py"


def _run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [*FLOWCTL_CMD, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        # flowctl reconfigures its stdio to UTF-8; decode the same way, or a
        # Windows runner's cp1252 default mangles the template's em-dashes
        # and the byte-for-byte skeleton comparison fails for no real reason.
        encoding="utf-8",
        timeout=30,
    )


# ============================================================================
# R22 (e): byte-for-byte skeleton parity with bundled templates/spec.md.
# ============================================================================
# fn-220 moved the baseline to the canonical template. Expected output is
# computed from plugins/flow-next/templates/spec.md (YAML frontmatter
# stripped). Changing the scaffold means editing that file.


def _strip_leading_yaml_frontmatter(text: str) -> str:
    """The CLI's own helper, imported so this test pins CLI behaviour, not a copy."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("flowctl_r22_under_test", FLOWCTL_PY)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod._strip_leading_yaml_frontmatter(text)


def _expected_skeleton_from_template() -> str:
    raw = (PLUGIN_DIR / "templates" / "spec.md").read_text(encoding="utf-8")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    return _strip_leading_yaml_frontmatter(raw)


class TestR22E_SpecSkeletonByteForByte(unittest.TestCase):
    """R22 (e): `flowctl spec skeleton` equals bundled templates/spec.md
    with YAML frontmatter stripped. Runs outside this repo, whose own
    root SPEC.md would otherwise win the template cascade."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.cwd = Path(tmp.name)

    def test_skeleton_byte_for_byte_matches_baseline(self) -> None:
        proc = _run("spec", "skeleton", cwd=self.cwd)
        self.assertEqual(proc.returncode, 0)
        expected = _expected_skeleton_from_template()
        self.assertEqual(
            proc.stdout,
            expected,
            "R22 (e) violation: `flowctl spec skeleton` output diverges "
            "from bundled templates/spec.md (frontmatter stripped). The "
            "scaffold is that file — edit it to change the baseline.",
        )

    def test_skeleton_json_envelope_matches(self) -> None:
        """`flowctl spec skeleton --json` wraps the same text in a JSON
        envelope; the embedded skeleton field is byte-for-byte identical."""
        proc = _run("spec", "skeleton", "--json", cwd=self.cwd)
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["skeleton"], _expected_skeleton_from_template())


class TestOldLayoutSpecLoadsUnchanged(unittest.TestCase):
    """fn-276 R4: a spec written under the removed per-scope layout (owner
    markers, Motivation / Implementation Tradeoffs sub-headings) loads,
    validates, and reads back byte-for-byte; nothing rewrites it."""

    OLD_BODY = (
        "# Old layout\n\n"
        "## Goal & Context\n<!-- scope: business -->\n\nWhy it exists.\n\n"
        "## Acceptance Criteria\n<!-- scope: both -->\n\n"
        "- **R1:** It works. Errors: none. [user]\n\n"
        "## Decision Context\n<!-- scope: both — conditionally substructured -->\n\n"
        "### Motivation\n<!-- scope: business -->\n\nProduct reason.\n\n"
        "### Implementation Tradeoffs\n<!-- scope: technical -->\n\nTech reason.\n"
    )

    def test_old_layout_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(_run("init", "--json", cwd=root).returncode, 0)
            plan = root / "old.md"
            plan.write_text(self.OLD_BODY, encoding="utf-8")
            created = _run(
                "spec", "create", "--title", "Old layout",
                "--plan-file", str(plan), "--json", cwd=root,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            spec_id = json.loads(created.stdout)["id"]
            valid = _run("validate", "--spec", spec_id, "--json", cwd=root)
            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
            body = _run("cat", spec_id, cwd=root)
            self.assertEqual(body.returncode, 0, body.stderr)
            self.assertIn(self.OLD_BODY.split("\n", 1)[1], body.stdout)


if __name__ == "__main__":
    unittest.main()
