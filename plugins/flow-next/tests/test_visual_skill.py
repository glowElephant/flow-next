"""The /flow-next:visual skill: files, shim frontmatter, reachability.

Checks the skill and its command shim exist, the shim frontmatter carries the
bare command name and a description (hosts parse both), the shim reaches the
skill, and the shipped skill never links maintainer-only `agent_docs/`. The
skill's wording is not pinned.

Run:
    cd plugins/flow-next/tests && python3 -m unittest test_visual_skill -q
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN = REPO_ROOT / "plugins" / "flow-next"

SKILL_DIR = PLUGIN / "skills" / "flow-next-visual"
SKILL_MD = SKILL_DIR / "SKILL.md"
SHIM = PLUGIN / "commands" / "visual.md"

CONDUCT_VISUAL = REPO_ROOT / "agent_docs" / "conduct" / "visual.md"
CONDUCT_README = REPO_ROOT / "agent_docs" / "conduct" / "README.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _skill_dir_prose() -> str:
    return "\n".join(_read(p) for p in sorted(SKILL_DIR.rglob("*.md")))


def _split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter, body) for a markdown file with YAML frontmatter."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m is not None, "file has no YAML frontmatter"
    return m.group(1), text[m.end() :]


class VisualSkillFiles(unittest.TestCase):
    def test_skill_and_shim_exist(self) -> None:
        self.assertTrue(SKILL_MD.is_file(), f"missing {SKILL_MD}")
        self.assertTrue(SHIM.is_file(), f"missing {SHIM}")


class VisualShimContract(unittest.TestCase):
    def test_shim_bare_colon_free_name_and_description(self) -> None:
        front = _split_frontmatter(_read(SHIM))[0]
        name = re.search(r"^name:\s*(.+)$", front, re.M)
        self.assertIsNotNone(name, "shim frontmatter has no name")
        value = name.group(1).strip().strip("\"'")
        self.assertEqual(
            value,
            "visual",
            "shim name must be the bare, colon-free command name",
        )
        desc = re.search(r"^description:\s*(.+)$", front, re.M)
        self.assertIsNotNone(desc, "shim frontmatter has no description")
        self.assertTrue(
            desc.group(1).strip().strip("\"'"),
            "shim description must be non-empty",
        )

    def test_shim_invokes_the_skill(self) -> None:
        self.assertIn("flow-next-visual", _read(SHIM))


class VisualConductChecklist(unittest.TestCase):
    """R8: maintainer doc exists, indexed, and never referenced at runtime."""

    def test_conduct_page_exists_and_is_indexed(self) -> None:
        self.assertTrue(CONDUCT_VISUAL.is_file(), f"missing {CONDUCT_VISUAL}")
        readme = _read(CONDUCT_README)
        self.assertIn("(visual.md)", readme)

    def test_skill_files_never_reference_the_conduct_page(self) -> None:
        prose = _skill_dir_prose() + "\n" + _read(SHIM)
        self.assertNotIn("conduct/", prose)
        self.assertNotIn("agent_docs", prose)


if __name__ == "__main__":
    unittest.main()
