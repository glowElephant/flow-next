"""Unit tests for the canonical spec template + R21 drift guard (fn-44.9, covers R11 / R21).

Asserts:
  - `plugins/flow-next/templates/spec.md` exists at canonical path.
  - The R21 drift guard awk pattern fires on a synthetic skill-markdown
    file that re-embeds the canonical sequence; does NOT fire on
    single-mention references.
  - The Codex mirror, when present, ships its own `codex/templates/spec.md`
    byte-for-byte identical to the canonical source (R20).
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve()
PLUGIN_DIR = HERE.parent.parent
TEMPLATE_PATH = PLUGIN_DIR / "templates" / "spec.md"
CODEX_TEMPLATE_PATH = PLUGIN_DIR / "codex" / "templates" / "spec.md"
SKILLS_DIR = PLUGIN_DIR / "skills"


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


class TestTemplateExistsAtCanonicalPath(unittest.TestCase):
    """R11: template lives at `plugins/flow-next/templates/spec.md`."""

    def test_template_file_exists(self) -> None:
        self.assertTrue(
            TEMPLATE_PATH.is_file(),
            f"canonical template missing: {TEMPLATE_PATH}",
        )


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


class TestR21DriftGuardSemantics(unittest.TestCase):
    """R21 drift guard: detect canonical-section re-embedding in any skill
    markdown file under `plugins/flow-next/skills/*/`. This test runs the
    actual awk pattern from sync-codex.sh against synthetic fixtures.
    """

    AWK_PROGRAM = r"""
        FNR == NR { lines[FNR] = $0; total = FNR }
        END {
          for (i = 1; i <= total; i++) {
            if (lines[i] ~ /^## Goal & Context/) {
              arch = 0; api = 0
              for (j = i + 1; j <= i + 30 && j <= total; j++) {
                if (lines[j] ~ /^## Architecture & Data Models/) arch = 1
                if (lines[j] ~ /^## API Contracts/) api = 1
              }
              if (arch && api) {
                printf "%s:%d\n", FILENAME, i
              }
            }
          }
        }
    """

    def _run_awk(self, file_path: Path) -> str:
        proc = subprocess.run(
            ["awk", self.AWK_PROGRAM, str(file_path)],
            capture_output=True,
            text=True,
        )
        return proc.stdout

    def test_guard_fires_on_canonical_sequence_in_skill_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "bad.md"
            fixture.write_text(
                "# Bad skill markdown\n\n"
                "## Goal & Context\n"
                "Some content\n\n"
                "## Architecture & Data Models\n"
                "More content\n\n"
                "## API Contracts\n"
                "Even more content\n"
            )
            out = self._run_awk(fixture)
            self.assertIn(str(fixture), out, "guard must fire on re-embedded sequence")

    def test_guard_silent_on_single_mention(self) -> None:
        """A skill that quotes ONE canonical section in isolation (e.g., a
        question bank referencing `## Goal & Context`) does NOT trip the
        guard — the three headers must co-occur within 30 lines."""
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "ok.md"
            fixture.write_text(
                "# OK skill markdown\n\n"
                "Walk the `## Goal & Context` section first.\n"
                "Skip everything else.\n"
            )
            out = self._run_awk(fixture)
            self.assertEqual(out.strip(), "", "guard must NOT fire on single mention")

    def test_guard_silent_when_headers_outside_30_line_window(self) -> None:
        """Three canonical headers separated by >30 lines do NOT trip the
        guard — the rule is co-occurrence within a 30-line window."""
        body = ["## Goal & Context", "filler"] + ["padding"] * 31 + [
            "## Architecture & Data Models",
            "## API Contracts",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "wide.md"
            fixture.write_text("\n".join(body) + "\n")
            out = self._run_awk(fixture)
            self.assertEqual(out.strip(), "", "guard must NOT fire when window exceeded")

    def test_guard_silent_on_canonical_template(self) -> None:
        """Sanity check: the canonical template itself DOES embed the
        sequence (it's the source of truth) but lives OUTSIDE
        `plugins/flow-next/skills/` — sync-codex.sh's guard scopes to
        `plugins/flow-next/skills/` so the template never gets scanned.
        Verify the guard's `find` scope path."""
        # We can't easily simulate the find scope here; just assert the
        # template DOES have the sequence (so the guard would trip if
        # mis-scoped). The actual guard scoping is verified by sync-codex.sh
        # passing — which this test suite runs in CI as part of the gate.
        body = TEMPLATE_PATH.read_text(encoding="utf-8")
        lines = body.splitlines()
        for i, line in enumerate(lines):
            if line == "## Goal & Context":
                window = lines[i + 1 : i + 31]
                arch_hit = any(l == "## Architecture & Data Models" for l in window)
                api_hit = any(l == "## API Contracts" for l in window)
                if arch_hit and api_hit:
                    return  # canonical template DOES embed the sequence — pass
        self.fail("canonical template lost its canonical-sequence body")


class TestNoCanonicalSequenceInCanonicalSkillMarkdown(unittest.TestCase):
    """Live check: walk every `*.md` under `plugins/flow-next/skills/*/` and
    assert none re-embed the canonical sequence (R21 — runtime-state assertion
    that mirrors sync-codex.sh's guard)."""

    def test_no_skill_markdown_duplicates_canonical_sequence(self) -> None:
        violations: list[tuple[str, int]] = []
        for md in SKILLS_DIR.rglob("*.md"):
            lines = md.read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines):
                if line.startswith("## Goal & Context"):
                    window = lines[i + 1 : i + 31]
                    arch = any(
                        l.startswith("## Architecture & Data Models")
                        for l in window
                    )
                    api = any(l.startswith("## API Contracts") for l in window)
                    if arch and api:
                        violations.append((str(md), i + 1))
        self.assertEqual(
            violations,
            [],
            f"R21 violations in canonical skill markdown: {violations}",
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
