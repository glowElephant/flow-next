"""Unit tests for the canonical spec template (fn-44.9, covers R11 / R20).

Asserts:
  - `plugins/flow-next/templates/spec.md` carries the canonical H2 sections
    in order (flowctl validate and brief parse these headings).
  - The Codex mirror, when present, ships its own `codex/templates/spec.md`
    byte-for-byte identical to the canonical source (R20).
"""

from __future__ import annotations

import unittest
from pathlib import Path


HERE = Path(__file__).resolve()
PLUGIN_DIR = HERE.parent.parent
TEMPLATE_PATH = PLUGIN_DIR / "templates" / "spec.md"
CODEX_TEMPLATE_PATH = PLUGIN_DIR / "codex" / "templates" / "spec.md"


# Canonical 7-section sequence per R11 + R21.
CANONICAL_SECTIONS = [
    "## Goal & Context",
    "## Architecture & Data Models",
    "## API Contracts",
    "## Edge Cases & Constraints",
    "## Acceptance Criteria",
    "## Boundaries",
    "## Decision Context",
]


class TestTemplateStructure(unittest.TestCase):
    """R11: template contains the 7 canonical sections in declared order."""

    def setUp(self) -> None:
        self.body = TEMPLATE_PATH.read_text(encoding="utf-8")
        self.lines = self.body.splitlines()

    def test_all_canonical_sections_present(self) -> None:
        for section in CANONICAL_SECTIONS:
            self.assertIn(
                section, self.body, f"missing canonical section: {section}"
            )

    def test_canonical_sections_in_declared_order(self) -> None:
        # Find each canonical heading at column 1, record line index, assert
        # monotonically increasing.
        positions: list[int] = []
        for section in CANONICAL_SECTIONS:
            for idx, line in enumerate(self.lines):
                if line == section:
                    positions.append(idx)
                    break
            else:
                self.fail(f"section {section!r} not found at column 1")
        self.assertEqual(
            positions,
            sorted(positions),
            f"canonical sections out of order: {positions}",
        )


class TestCodexMirrorShipsTemplate(unittest.TestCase):
    """R20: Codex mirror, when present, ships its own copy of the template
    byte-for-byte identical to canonical."""

    def test_mirror_template_exists_and_matches_canonical(self) -> None:
        if not CODEX_TEMPLATE_PATH.is_file():
            self.skipTest(
                f"codex mirror not regenerated: {CODEX_TEMPLATE_PATH} missing "
                f"— run `bash scripts/sync-codex.sh`"
            )
        canonical = TEMPLATE_PATH.read_bytes()
        mirror = CODEX_TEMPLATE_PATH.read_bytes()
        self.assertEqual(
            canonical,
            mirror,
            "codex mirror template diverges from canonical — re-run sync-codex.sh",
        )

    def test_mirror_skill_paths_resolve_to_mirror_template(self) -> None:
        """After sync, skill markdown in the mirror uses
        `../../templates/spec.md` which resolves to
        `codex/templates/spec.md` (the mirror copy)."""
        if not CODEX_TEMPLATE_PATH.is_file():
            self.skipTest("codex mirror not regenerated")
        mirror_skills = PLUGIN_DIR / "codex" / "skills"
        candidates = [
            mirror_skills / "flow-next-refine" / "SKILL.md",
            mirror_skills / "flow-next-capture" / "workflow.md",
            mirror_skills / "flow-next-plan" / "steps.md",
        ]
        for path in candidates:
            if not path.is_file():
                continue
            body = path.read_text(encoding="utf-8")
            # The path string should appear as `../../templates/spec.md` —
            # resolves to `codex/templates/spec.md` from a skill at
            # `codex/skills/<name>/<file>.md` (2 levels up).
            for line in body.splitlines():
                if "templates/spec.md" in line and "](" in line:
                    self.assertIn(
                        "../../templates/spec.md",
                        line,
                        f"{path.name}: expected `../../templates/spec.md` "
                        f"after sync, found stale: {line!r}",
                    )


if __name__ == "__main__":
    unittest.main()
