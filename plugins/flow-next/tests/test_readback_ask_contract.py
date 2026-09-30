"""Capture and refine read-back: reachability, autofix tokens, Codex rewrite.

Checks that the references capture routes to are reachable, that the autofix
invocation tokens stay reachable from SKILL.md, and that the Codex generator
places its plain-text ask instruction once, on the saved-spec editor offer.
The wording of the asks is not pinned.
"""

from __future__ import annotations

import pathlib
import re
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
PLUGIN = REPO_ROOT / "plugins" / "flow-next"
SKILLS = PLUGIN / "skills"

SPINE = "SKILL.md"


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _corpus(skill_dir: pathlib.Path) -> dict[str, str]:
    """Every markdown file a skill ships, keyed by path relative to the skill."""
    return {
        p.relative_to(skill_dir).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(skill_dir.rglob("*.md"))
        if p.is_file()
    }


def _reachable(corpus: dict[str, str]) -> set[str]:
    """Files reachable from `SKILL.md` by following file mentions (BFS)."""
    seen = {SPINE}
    queue = [SPINE]
    while queue:
        text = corpus[queue.pop()]
        for rel in corpus:
            if rel in seen:
                continue
            if rel in text or rel.rsplit("/", 1)[-1] in text:
                seen.add(rel)
                queue.append(rel)
    return seen


CAPTURE_CORPUS = _corpus(SKILLS / "flow-next-capture")
CAPTURE_REACHABLE = _reachable(CAPTURE_CORPUS)


class CaptureReachability(unittest.TestCase):
    def _assert_reachable(self, token: str) -> None:
        hits = [rel for rel, text in CAPTURE_CORPUS.items() if token in text]
        self.assertTrue(hits, f"no capture file carries {token!r}")
        self.assertTrue(
            [rel for rel in hits if rel in CAPTURE_REACHABLE],
            f"{token!r} only lives in unreachable file(s) {hits}",
        )

    def test_autofix_tokens_reachable(self) -> None:
        for token in ("mode:autofix", "--yes"):
            with self.subTest(token=token):
                self._assert_reachable(token)

    def test_references_reachable(self) -> None:
        workflow = CAPTURE_CORPUS["workflow.md"]
        self.assertIn("[docs/read-back.md](../../docs/read-back.md)", workflow)
        self.assertTrue((PLUGIN / "docs" / "read-back.md").is_file())
        self.assertIn("references/split-proposal.md", CAPTURE_REACHABLE)


class CodexQuestionPlacement(unittest.TestCase):
    def test_negative_footer_is_not_an_ask_anchor(self) -> None:
        source = _read(REPO_ROOT / "scripts" / "sync-codex.sh")
        function = "def is_negative_context(line):" + source.split(
            "def is_negative_context(line):", 1
        )[1].split("\ndef is_table_line", 1)[0]
        namespace = {"re": re}
        # Execute only the repository-owned generator function extracted above.
        exec(compile(function, "sync-codex:is_negative_context", "exec"), namespace)  # noqa: S102
        negative = namespace["is_negative_context"]
        self.assertTrue(negative("Informational only — never a plain-text numbered prompt."))
        self.assertFalse(negative("Use `plain-text numbered prompt` for one short editor question:"))

    def test_mirror_instruction_belongs_to_saved_editor_offer(self) -> None:
        mirror = _read(PLUGIN / "codex" / "skills" / "flow-next-capture" / "workflow.md")
        instruction = "**Ask the user via plain text.**"
        self.assertEqual(mirror.count(instruction), 1)
        editor = mirror[mirror.index("### 5.6a"):mirror.index("### 5.7")]
        self.assertIn(instruction, editor)


if __name__ == "__main__":
    unittest.main()
