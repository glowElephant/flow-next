"""Two-axis in-host quality audit — dispatch handshake.

The Phase 4 audit dispatches the quality-auditor agent twice (AXIS: correctness
/ AXIS: standards). The dispatch lines and the agent must use the same AXIS
tokens, on the canonical surfaces and the generated Codex mirror. The wording
of the auditor charter and the aggregation prose is not pinned.
"""

from __future__ import annotations

import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
PLUGIN = REPO_ROOT / "plugins" / "flow-next"

AUDITOR = PLUGIN / "agents" / "quality-auditor.md"
CANONICAL_WORK = PLUGIN / "skills" / "flow-next-work" / "phases.md"
MIRROR_WORK = PLUGIN / "codex" / "skills" / "flow-next-work" / "phases.md"
MIRROR_AUDITOR = PLUGIN / "codex" / "agents" / "quality-auditor.toml"
CONDUCT_INDEX = REPO_ROOT / "agent_docs" / "conduct" / "README.md"

AXES = ("AXIS: correctness", "AXIS: standards")


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


class AuditorAxisHandshake(unittest.TestCase):
    def test_auditor_reads_both_axes(self) -> None:
        for path in (AUDITOR, MIRROR_AUDITOR):
            text = _read(path)
            for axis in AXES:
                with self.subTest(path=path.name, axis=axis):
                    self.assertIn(axis, text)


class WorkPhaseFourDispatch(unittest.TestCase):
    def _assert_dispatch(self, text: str, dispatch_literal: str) -> None:
        self.assertEqual(text.count(dispatch_literal), 2)
        for axis in AXES:
            self.assertIn(axis, text)

    def test_canonical(self) -> None:
        self._assert_dispatch(
            _read(CANONICAL_WORK), "Task flow-next:quality-auditor"
        )

    def test_codex_mirror(self) -> None:
        # sync-codex.sh rewrites the dispatch spelling for the Codex surface.
        self._assert_dispatch(
            _read(MIRROR_WORK), "Use the quality_auditor agent"
        )


class ConductChecklist(unittest.TestCase):
    def test_checklist_is_indexed(self) -> None:
        self.assertTrue((REPO_ROOT / "agent_docs" / "conduct" / "quality-auditor.md").is_file())
        self.assertIn("quality-auditor.md", _read(CONDUCT_INDEX))


if __name__ == "__main__":
    unittest.main()
