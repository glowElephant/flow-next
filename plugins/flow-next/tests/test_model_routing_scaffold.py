"""fn-195.2 — setup's commented routing block: template shape, reachability,
uninstall markers, and the regenerated mirror.

Setup proposes ONE commented example block, written verbatim from
`templates/model-routing-snippet.md`. The tests check what a consumer's file
receives and what uninstall matches on:

  (a) template shape — well-formed marker pair, the four tier names, every
      routing line COMMENTED OUT, and no model identifier anywhere (the block is
      the consumer's preferences to fill in, never a detected fact).
  (b) uninstall — the marker-removal transform, and `commands/uninstall.md`
      names both exact marker strings it removes.
  (c) setup workflow reaches the template.
  (d) the Codex mirror carries the same template and no stale references, and
      its agent floors match the generator baselines.

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


# ── (b) uninstall marker removal ─────────────────────────────


def remove_marker_block(text: str) -> tuple:
    """Reference of the uninstall.md deterministic damaged-marker algorithm.

    Exactly one start AND exactly one end AND start precedes end → remove the
    block inclusive and return (new_text, True). Any other marker state →
    return (text unchanged, False). Line-based; never parses block content.
    """
    lines = text.split("\n")
    starts = [i for i, l in enumerate(lines) if l.strip() == START]
    ends = [i for i, l in enumerate(lines) if l.strip() == END]
    if len(starts) == 1 and len(ends) == 1 and starts[0] < ends[0]:
        del lines[starts[0] : ends[0] + 1]
        return "\n".join(lines), True
    return text, False


_BLOCK = f"{START}\n## Model routing\n\n<!-- reviewer: <model> -->\n{END}"
_SURROUND_HEAD = "# CLAUDE.md\n\nSome earlier content.\n\n"
_SURROUND_TAIL = "\n\nSome trailing content.\n"


class UninstallRemovalTransform(unittest.TestCase):
    def test_well_formed_removed_inclusive(self) -> None:
        text = _SURROUND_HEAD + _BLOCK + _SURROUND_TAIL
        out, removed = remove_marker_block(text)
        self.assertTrue(removed)
        self.assertNotIn(START, out)
        self.assertNotIn(END, out)
        self.assertNotIn("reviewer: <model>", out)  # inner content gone too
        # Surrounding content survives.
        self.assertIn("Some earlier content.", out)
        self.assertIn("Some trailing content.", out)

    def test_zero_starts_untouched(self) -> None:
        text = _SURROUND_HEAD + f"## Model routing\n{END}" + _SURROUND_TAIL
        out, removed = remove_marker_block(text)
        self.assertFalse(removed)
        self.assertEqual(out, text)

    def test_zero_ends_untouched(self) -> None:
        text = _SURROUND_HEAD + f"{START}\n## Model routing\n" + _SURROUND_TAIL
        out, removed = remove_marker_block(text)
        self.assertFalse(removed)
        self.assertEqual(out, text)

    def test_two_starts_untouched(self) -> None:
        text = _SURROUND_HEAD + f"{START}\nfoo\n{START}\nbar\n{END}" + _SURROUND_TAIL
        out, removed = remove_marker_block(text)
        self.assertFalse(removed)
        self.assertEqual(out, text)

    def test_two_ends_untouched(self) -> None:
        text = _SURROUND_HEAD + f"{START}\nfoo\n{END}\nbar\n{END}" + _SURROUND_TAIL
        out, removed = remove_marker_block(text)
        self.assertFalse(removed)
        self.assertEqual(out, text)

    def test_out_of_order_untouched(self) -> None:
        # end precedes start → damaged; leave untouched.
        text = _SURROUND_HEAD + f"{END}\n## Model routing\n{START}" + _SURROUND_TAIL
        out, removed = remove_marker_block(text)
        self.assertFalse(removed)
        self.assertEqual(out, text)

    def test_no_markers_untouched(self) -> None:
        text = _SURROUND_HEAD + "## Model routing\nplain content\n" + _SURROUND_TAIL
        out, removed = remove_marker_block(text)
        self.assertFalse(removed)
        self.assertEqual(out, text)


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

class MirrorAgentFloors(unittest.TestCase):
    """The regenerated Codex agent floors are reproducible from the generator.

    fn-195.5 review P1: a mirror regen run without env overrides silently
    downgraded 18 shipped agent floors and dropped 8 effort settings, because
    sync-codex.sh's baselines had drifted from the committed mirror. The
    baselines in sync-codex.sh ARE the shipped truth now; this pin fails the
    moment the committed TOMLs and the generator disagree, whichever moved.
    """

    SYNC = REPO_ROOT / "scripts" / "sync-codex.sh"
    CODEX_AGENTS = REPO_ROOT / "plugins" / "flow-next" / "codex" / "agents"
    CANON_AGENTS = REPO_ROOT / "plugins" / "flow-next" / "agents"

    def _baseline(self, name: str) -> str:
        match = re.search(rf'{name}="([^"]+)"', self.SYNC.read_text(encoding="utf-8"))
        assert match, f"{name} not found in sync-codex.sh"
        return match.group(1)

    def test_committed_floors_match_generator_baselines(self) -> None:
        fast = self._baseline("_SCOUT_FAST_BASELINE")
        intelligent = self._baseline("_SCOUT_INTELLIGENT_BASELINE")
        sync_text = self.SYNC.read_text(encoding="utf-8")
        scouts_match = re.search(
            r'INTELLIGENT_SCOUTS="([^"]+)"', sync_text
        )
        intelligent_scouts = set(scouts_match.group(1).split()) if scouts_match else None

        def floor_for(stem: str, alias: str) -> str | None:
            if alias == "haiku":
                return fast
            if alias == "opus":
                return intelligent
            if alias == "sonnet":
                # sync-codex routes sonnet via INTELLIGENT_SCOUTS membership,
                # falling back to fast — mirror that instead of assuming.
                if intelligent_scouts is None:
                    return intelligent
                return intelligent if stem in intelligent_scouts else fast
            return None
        checked = 0
        for md in sorted(self.CANON_AGENTS.glob("*.md")):
            match = re.search(r"^model:\s*(\S+)", md.read_text(encoding="utf-8"), re.M)
            if not match or match.group(1) == "inherit":
                continue
            # claude-md-scout is renamed agents-md-scout on the Codex side
            # (sync-codex.sh rename map) - INTELLIGENT_SCOUTS uses that name too,
            # so resolve the rename BEFORE the floor lookup.
            stem = "agents-md-scout" if md.stem == "claude-md-scout" else md.stem
            floor = floor_for(stem, match.group(1))
            if floor is None:
                continue
            toml = self.CODEX_AGENTS / f"{stem}.toml"
            self.assertTrue(toml.is_file(), f"mirror agent missing: {toml.name}")
            text = toml.read_text(encoding="utf-8")
            got = re.search(r'^model = "([^"]+)"', text, re.M)
            self.assertIsNotNone(got, f"{toml.name}: no model floor")
            self.assertEqual(
                got.group(1), floor,
                f"{toml.name}: floor {got.group(1)!r} != generator baseline "
                f"{floor!r} — regen ran with env overrides or a baseline moved "
                f"without a deliberate bump",
            )
            if "mini" not in floor and "spark" not in floor:
                self.assertIn(
                    'model_reasoning_effort = "', text,
                    f"{toml.name}: reasoning effort dropped",
                )
            checked += 1
        self.assertGreaterEqual(checked, 15, "pin lost its subjects — agent set shrank?")


if __name__ == "__main__":
    unittest.main()
