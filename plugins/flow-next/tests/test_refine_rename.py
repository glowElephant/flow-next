"""fn-238 R15-R18: the refine research scope and the why-scout.

Behavior or contract only (G2):
  - refine's research reference and plan's research step write the exact
    `## Resolved via Research` heading flowctl parses from the spec body;
  - the why-scout is read-only by tools (frontmatter the host enforces);
  - every pointer the new prose names resolves.

Run:
    python3 -m unittest plugins.flow-next.tests.test_refine_rename -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
PLUGIN = HERE.parent.parent
SKILLS = PLUGIN / "skills"

REFINE = SKILLS / "flow-next-refine"
RESEARCH_REF = REFINE / "references" / "research-scope.md"
PLAN_STEPS = SKILLS / "flow-next-plan" / "steps.md"
ROUTE_MATRIX = SKILLS / "flow-next-flow" / "references" / "route-matrix.md"
WHY_SCOUT = PLUGIN / "agents" / "why-scout.md"

SECTION = "## Resolved via Research"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _frontmatter(text: str) -> dict[str, str]:
    assert text.startswith("---")
    end = text.index("\n---", 3)
    out: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def _links(text: str) -> list[str]:
    return re.findall(r"\]\(([^)#]+\.md)(?:#[^)]*)?\)", text)


class ResearchSectionHeading(unittest.TestCase):

    def test_both_writers_name_the_heading_flowctl_parses(self) -> None:
        for path in (RESEARCH_REF, PLAN_STEPS):
            with self.subTest(writer=path.name):
                self.assertIn(SECTION, _read(path))

class WhyScoutIsReadOnly(unittest.TestCase):
    def test_tool_enforced_read_only(self) -> None:
        fm = _frontmatter(_read(WHY_SCOUT))
        self.assertEqual(fm["name"], "why-scout")
        tokens = {t.strip() for t in fm["disallowedTools"].split(",")}
        self.assertEqual(tokens, {"Edit", "Write", "Task"})
        self.assertEqual(fm["readonly"], "true")

class PointersResolve(unittest.TestCase):
    def test_relative_links_in_new_prose_resolve(self) -> None:
        for path in (RESEARCH_REF, REFINE / "SKILL.md", PLAN_STEPS, WHY_SCOUT, ROUTE_MATRIX):
            for link in _links(_read(path)):
                if link.startswith("http"):
                    continue
                target = (path.parent / link).resolve()
                self.assertTrue(target.is_file(), f"{path.name}: {link} -> {target}")

if __name__ == "__main__":
    unittest.main()
