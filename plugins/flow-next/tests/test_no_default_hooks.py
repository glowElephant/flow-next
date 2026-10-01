"""fn-114.1 / fn-114.2 - plugin ships zero hooks by default.

Pins:
  * plugins/flow-next/hooks/ is absent (no hooks.json, no empty dir required)
  * .claude-plugin/plugin.json carries no ``hooks`` key
  * codex mirror ships no hooks.json (sync-codex zero-default)
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
PLUGIN_DIR = HERE.parent.parent
PLUGIN_JSON = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
HOOKS_DIR = PLUGIN_DIR / "hooks"
HOOKS_JSON = HOOKS_DIR / "hooks.json"
CODEX_HOOKS_JSON = PLUGIN_DIR / "codex" / "hooks.json"


class TestNoDefaultHooks(unittest.TestCase):
    def test_hooks_dir_and_hooks_json_absent(self) -> None:
        self.assertFalse(
            HOOKS_JSON.is_file(),
            f"plugin must not ship {HOOKS_JSON.relative_to(PLUGIN_DIR)}",
        )
        # Prefer no hooks/ tree at all; allow neither a residual empty dir
        # nor a dir that still holds files.
        if HOOKS_DIR.exists():
            leftover = sorted(p.name for p in HOOKS_DIR.rglob("*") if p.is_file())
            self.assertEqual(
                leftover,
                [],
                f"plugins/flow-next/hooks/ must be empty or absent; found {leftover}",
            )

    def test_plugin_manifest_has_no_hooks_key(self) -> None:
        self.assertTrue(PLUGIN_JSON.is_file(), f"missing {PLUGIN_JSON}")
        data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        self.assertNotIn(
            "hooks",
            data,
            "plugin.json must not declare a hooks field — zero default registration",
        )

    def test_codex_mirror_ships_no_hooks_json(self) -> None:
        self.assertFalse(
            CODEX_HOOKS_JSON.is_file(),
            "plugins/flow-next/codex/hooks.json must not ship",
        )


if __name__ == "__main__":
    unittest.main()
