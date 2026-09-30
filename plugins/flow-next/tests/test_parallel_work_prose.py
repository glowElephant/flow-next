"""fn-118 — prompt-guided parallel planning and work contracts.

Locks contract tokens, handover grammar, and mirror parity on both canonical
Claude surfaces and the generated Codex mirror. fn-118 adds no scheduler,
schema, or deterministic path-overlap machinery.

Prose pins are retired (agent_docs/adding-skills.md "Shipped skill text"):
only field names, executable fragments, links and mirror rewrites remain.
"""

from __future__ import annotations

import pathlib
import re
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
PLUGIN = REPO_ROOT / "plugins" / "flow-next"

# The multi-task conductor (wave dispatch) lives in references/multi-task.md.
CANONICAL_WORK = PLUGIN / "skills" / "flow-next-work" / "references" / "multi-task.md"
MIRROR_WORK = PLUGIN / "codex" / "skills" / "flow-next-work" / "references" / "multi-task.md"
# Branch-disclosure refactor: the wave join/handover-consumption prose moved
# verbatim out of the always-loaded phases.md into the reached-path reference
# phases.md links from its parallel-wave branch. Same contract, new home.
CANONICAL_WAVE_JOIN = (
    PLUGIN / "skills" / "flow-next-work" / "references" / "wave-join.md"
)
MIRROR_WAVE_JOIN = (
    PLUGIN
    / "codex"
    / "skills"
    / "flow-next-work"
    / "references"
    / "wave-join.md"
)
CANONICAL_WORKER = PLUGIN / "agents" / "worker.md"
MIRROR_WORKER = PLUGIN / "codex" / "agents" / "worker.toml"
# The parallel-wave / host-deferred handover contract moved verbatim out of the
# worker into a gated reference the worker reads at Phase 0 on those routes.
CANONICAL_HANDOVER = (
    PLUGIN / "skills" / "flow-next-work" / "references" / "worker-handover.md"
)
MIRROR_HANDOVER = (
    PLUGIN / "codex" / "skills" / "flow-next-work" / "references" / "worker-handover.md"
)


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


class ParallelWorkConductorProse(unittest.TestCase):
    def _assert_contract(self, path: pathlib.Path, join: pathlib.Path) -> None:
        text = _read(path)
        join_text = _read(join)
        # Handover field names the worker reads, on both sides of the wave.
        for field in ("HANDOVER_SUMMARY", "HANDOVER_EVIDENCE"):
            self.assertIn(field, text)
            self.assertIn(field, join_text)
        # The parallel branch reaches the join reference.
        self.assertIn("wave-join.md", text)

    def test_canonical(self) -> None:
        self._assert_contract(CANONICAL_WORK, CANONICAL_WAVE_JOIN)
        self.assertIn(
            "flow-next:flow-next-impl-review <task-id> --base "
            "<task-normalized-integrated-base> --review=<backend>",
            _read(CANONICAL_WAVE_JOIN),
        )

    def test_codex_mirror(self) -> None:
        self._assert_contract(MIRROR_WORK, MIRROR_WAVE_JOIN)
        text = _read(MIRROR_WAVE_JOIN)
        self.assertIn(
            "$flow-next-impl-review <task-id> --base "
            "<task-normalized-integrated-base> --review=<backend>",
            text,
        )
        self.assertNotIn(
            "/flow-next:impl-review <task-id> --base "
            "<task-normalized-integrated-base> --review=<backend>",
            text,
        )


class ParallelWorkerHandoverProse(unittest.TestCase):
    def _assert_contract(self, path: pathlib.Path, handover: pathlib.Path) -> None:
        text = _read(path)
        handover_text = _read(handover)
        # Prose-quality pins removed 2026-08-07 - judged via .flow/criteria.md
        # G1, not grep. Tokens, executable fragments, and ordering only below.
        self.assertIn("PARALLEL_WAVE", text)
        self.assertIn("HANDOVER_SUMMARY", text)
        self.assertIn("HANDOVER_EVIDENCE", text)
        # The worker reads the handover reference before its anchor call, and
        # the link resolves in both layouts.
        links = [m for m in re.findall(r"\]\(([^)]+)\)", text) if m.endswith("worker-handover.md")]
        self.assertTrue(links, path)
        for rel in links:
            self.assertTrue((path.parent / rel).resolve().is_file(), rel)
        link_pos = text.index("worker-handover.md")
        anchor_pos = text.index("<FLOWCTL> anchor <TASK_ID> --md")
        self.assertLess(link_pos, anchor_pos)
        self.assertIn('EXPECTED_WORKSPACE="$(cd -- "<WORKSPACE>" && pwd -P)"', handover_text)
        self.assertIn('EVIDENCE_FILE="<resolved task-unique HANDOVER_EVIDENCE path>"', handover_text)
        # Standard-branch completion keeps its executable fragments.
        self.assertIn('SUMMARY_FILE="<resolved task-unique HANDOVER_SUMMARY path>"', text)
        self.assertIn(
            '--range "$BASE_COMMIT..HEAD"', text
        )

    def test_canonical(self) -> None:
        self._assert_contract(CANONICAL_WORKER, CANONICAL_HANDOVER)

    def test_codex_mirror(self) -> None:
        self._assert_contract(MIRROR_WORKER, MIRROR_HANDOVER)


if __name__ == "__main__":
    unittest.main()
