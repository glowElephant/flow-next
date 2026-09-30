"""fn-195.2 — setup's commented routing block: template shape, reachability,
uninstall markers, and the regenerated mirror.

Setup proposes ONE commented example block, written verbatim from
`templates/model-routing-snippet.md`. The tests check what a consumer's file
receives and what uninstall matches on:

  (a) template shape — well-formed marker pair, the four tier names, every
      routing line COMMENTED OUT, and no model identifier anywhere (the block is
      the consumer's preferences to fill in, never a detected fact).
  (b) uninstall — `commands/uninstall.md` names both exact marker strings it
      removes.
  (c) setup workflow reaches the template.
  (d) the Codex mirror carries the same template and no stale references.

The wording of setup and uninstall prose is not pinned.

Run:
    python3 -m unittest plugins.flow-next.tests.test_model_routing_scaffold -v
"""

from __future__ import annotations

import pathlib
import re
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
PLUGIN = REPO_ROOT / "plugins" / "flow-next"

TEMPLATE = PLUGIN / "skills" / "flow-next-setup" / "templates" / "model-routing-snippet.md"
UNINSTALL = PLUGIN / "commands" / "uninstall.md"
CANONICAL_WORKFLOW = PLUGIN / "skills" / "flow-next-setup" / "workflow.md"

START = "<!-- flow-next:model-routing:start -->"
END = "<!-- flow-next:model-routing:end -->"

TIERS = ("reviewer", "implementer", "fast scout", "thinking scout")

# Vendor model-identifier shapes. The block ships ZERO of them (spec R2/R5):
# the consumer names the models their own account serves.
MODEL_SLUG_RE = re.compile(
    r"\b("
    r"gpt-\d|o[34]-mini|claude-|opus-?\d|sonnet-?\d|haiku-?\d|fable-?\d"
    r"|grok-\d|composer-\d|gemini-|llama-?\d|mistral"
    r")",
    re.IGNORECASE,
)

def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


# ── (a) template shape ────────────────────────────────────────────────────────


class TemplateShape(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(TEMPLATE.is_file(), f"missing template: {TEMPLATE}")
        self.text = _read(TEMPLATE)
        self.lines = self.text.split("\n")

    def _block_lines(self) -> list:
        si = next(i for i, l in enumerate(self.lines) if l.strip() == START)
        ei = next(i for i, l in enumerate(self.lines) if l.strip() == END)
        return self.lines[si : ei + 1]

    def test_marker_pair_well_formed(self) -> None:
        starts = [l for l in self.lines if l.strip() == START]
        ends = [l for l in self.lines if l.strip() == END]
        self.assertEqual(len(starts), 1, "exactly one start marker")
        self.assertEqual(len(ends), 1, "exactly one end marker")
        si = next(i for i, l in enumerate(self.lines) if l.strip() == START)
        ei = next(i for i, l in enumerate(self.lines) if l.strip() == END)
        self.assertLess(si, ei, "start must precede end")

    def test_every_routing_line_is_commented_out(self) -> None:
        # Between the markers the ONLY active content is the section heading and
        # blank lines. Every tier line ships inside an HTML comment, so nothing
        # is routed until the consumer uncomments it.
        inside = self._block_lines()[1:-1]
        in_comment = False
        for line in inside:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if in_comment:
                if s.endswith("-->"):
                    in_comment = False
                continue
            self.assertTrue(
                s.startswith("<!--"),
                f"active (uncommented) routing content in the block:\n  {line}",
            )
            if not s.endswith("-->"):
                in_comment = True
        self.assertFalse(in_comment, "unterminated HTML comment in the block")

    def test_names_the_four_tiers(self) -> None:
        for tier in TIERS:
            self.assertIn(tier, self.text, f"tier missing from the block: {tier}")

    def test_ships_no_model_identifier(self) -> None:
        hit = MODEL_SLUG_RE.search(self.text)
        self.assertIsNone(
            hit,
            f"routing block ships a concrete model identifier: "
            f"{hit.group(0) if hit else ''}",
        )


# ── (b) uninstall markers ─────────────────────────────


class UninstallMarkers(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(UNINSTALL.is_file(), f"missing: {UNINSTALL}")
        self.text = _read(UNINSTALL)

    def test_both_marker_strings_present(self) -> None:
        self.assertIn(START, self.text)
        self.assertIn(END, self.text)


# ── (c) setup workflow reaches the template ───────────────────────────────────────


class WorkflowReachesTemplate(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(CANONICAL_WORKFLOW.is_file(), f"missing: {CANONICAL_WORKFLOW}")
        self.text = _read(CANONICAL_WORKFLOW)

    def test_workflow_reaches_the_template(self) -> None:
        self.assertIn("templates/model-routing-snippet.md", self.text)


# ── (d) Codex mirror content pin ──────────────────────────────────────────────


class MirrorRoutingProse(unittest.TestCase):
    """The regenerated Codex mirror carries the same routing invariants (fn-195).

    A mirror regenerated from a stale source, or a retired reference left
    behind by an incomplete regen, would ship to every Codex install while the
    canonical checks above stayed green.
    """

    MIRROR = PLUGIN / "codex" / "skills" / "flow-next-setup"

    def setUp(self) -> None:
        self.template = self.MIRROR / "templates" / "model-routing-snippet.md"
        for path in (self.template,):
            self.assertTrue(
                path.is_file(),
                f"missing mirror file: {path} (run ./scripts/sync-codex.sh)",
            )

    def test_mirror_template_keeps_markers_and_tiers(self) -> None:
        text = _read(self.template)
        self.assertIn(START, text)
        self.assertIn(END, text)
        for tier in TIERS:
            self.assertIn(tier, text, f"tier missing from the mirror block: {tier}")

    def test_mirror_template_ships_no_model_identifier(self) -> None:
        hit = MODEL_SLUG_RE.search(_read(self.template))
        self.assertIsNone(
            hit,
            f"mirror routing block ships a concrete model identifier: "
            f"{hit.group(0) if hit else ''}",
        )

    def test_deleted_ceremony_references_are_gone_from_the_mirror(self) -> None:
        # An incomplete regen (rsync without --delete) leaves the retired
        # reference files on disk where the mirror skill can still load them.
        stale = sorted(
            p.name
            for p in (self.MIRROR / "references").glob("model-*.md")
        )
        self.assertEqual(
            stale, [], f"retired routing references still in the mirror: {stale}"
        )

if __name__ == "__main__":
    unittest.main()
