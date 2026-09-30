"""Both Cursor installers (bash + PowerShell) purge excluded paths from the dest.

A stale excluded dir (e.g. codex/) left in ~/.cursor/plugins/local/flow-next
breaks setup's Cursor-vs-Codex detection. Text checks only, so this runs on
every CI leg without rsync or pwsh.
"""

from __future__ import annotations

import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
PLUGIN_DIR = HERE.parent.parent           # plugins/flow-next
REPO_ROOT = PLUGIN_DIR.parent.parent      # repo root

SH = REPO_ROOT / "scripts" / "install-cursor.sh"
PS1 = REPO_ROOT / "scripts" / "install-cursor.ps1"


class TestInstallCursorParity(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(SH.is_file(), f"missing {SH.relative_to(REPO_ROOT)}")
        self.assertTrue(PS1.is_file(), f"missing {PS1.relative_to(REPO_ROOT)}")
        self.sh = SH.read_text(encoding="utf-8")
        self.ps1 = PS1.read_text(encoding="utf-8")

    def test_installers_purge_excluded_paths(self) -> None:
        # A stale excluded dir (e.g. codex/) left in the dest must be removed so the
        # install is a TRUE mirror — setup's Cursor-vs-Codex detection keys on codex/
        # being absent. rsync --delete alone does NOT remove excluded paths; robocopy
        # /MIR + /XD skips excluded dirs from its purge. Both need explicit handling.
        self.assertIn(
            "--delete-excluded",
            self.sh,
            "install-cursor.sh must pass rsync --delete-excluded so a stale "
            "excluded codex/ is removed from the dest (plain --delete won't).",
        )
        # PowerShell side: explicit Remove-Item of the excluded dirs after robocopy.
        self.assertRegex(
            self.ps1,
            r"(?is)Remove-Item.*codex",
            "install-cursor.ps1 must explicitly Remove-Item the excluded dirs "
            "(robocopy /MIR + /XD does not purge them).",
        )

if __name__ == "__main__":
    unittest.main()
