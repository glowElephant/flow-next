"""Codex-mirror parity for the GitLab and Jira tracker adapter documentation.

The Codex mirror at `plugins/flow-next/codex/` is a DERIVED artifact regenerated
by `scripts/sync-codex.sh`. A missing sync rule silently degrades Codex parity, so
this test checks the per-adapter references survive the sync:

  * The canonical `references/<adapter>.md` is mirrored into the codex/ tree (the
    adapter reference must exist on the Codex side, not only Claude's).
  * The mirror's `<adapter>.md` is content-faithful to the canonical: every
    non-blank line of the canonical survives into the mirror modulo the sync
    script's leading-whitespace normalization inside fenced code blocks. (Neither
    gitlab.md nor jira.md carries `AskUserQuestion` prose, so no tool-name rewrite
    applies; a faithful copy is the contract.)

These guards prevent canonical/mirror drift after the provider references were
reduced to transport-shape documentation.

Run:
    python3 -m unittest discover -s plugins/flow-next/tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[3]

TRACKER_SKILL = REPO_ROOT / "plugins" / "flow-next" / "skills" / "flow-next-tracker-sync"
TRACKER_MIRROR = REPO_ROOT / "plugins" / "flow-next" / "codex" / "skills" / "flow-next-tracker-sync"

CANON_GITLAB = TRACKER_SKILL / "references" / "gitlab.md"
MIRROR_GITLAB = TRACKER_MIRROR / "references" / "gitlab.md"

CANON_JIRA = TRACKER_SKILL / "references" / "jira.md"
MIRROR_JIRA = TRACKER_MIRROR / "references" / "jira.md"



def _normalize(text: str) -> list[str]:
    """Content lines with ALL runs of whitespace collapsed to one space, blanks dropped.

    The sync script normalizes whitespace (it collapses the leading/internal
    indentation the canonical uses inside fenced code-block comments to a single
    space) and deliberately STRIPS the canonical's trailing "Codex mirror
    (sync-codex.sh)..." meta-note (the R4 no-meta-file-refs rule). So an exact byte
    compare is brittle by design. We collapse whitespace and compare *content*,
    which still catches any genuine content drift while tolerating those transforms.
    """
    out = []
    for ln in text.splitlines():
        collapsed = re.sub(r"\s+", " ", ln).strip()
        if collapsed:
            out.append(collapsed)
    return out


class GitlabMirrorExistsTestCase(unittest.TestCase):
    def test_canonical_gitlab_reference_exists(self) -> None:
        self.assertTrue(
            CANON_GITLAB.is_file(),
            f"canonical GitLab adapter reference missing: {CANON_GITLAB}",
        )

    def test_mirror_gitlab_reference_exists(self) -> None:
        self.assertTrue(
            MIRROR_GITLAB.is_file(),
            "canonical references/gitlab.md was not mirrored into codex/ - "
            "run `bash scripts/sync-codex.sh`",
        )


class GitlabMirrorContentParityTestCase(unittest.TestCase):
    def test_mirror_adds_no_fabricated_content(self) -> None:
        """Every mirror content line traces back to the canonical.

        The sync only transforms whitespace and drops the Codex-meta note. It
        never INVENTS content. So (whitespace-collapsed) the mirror's content-line
        set must be a subset of the canonical's. A mirror line with no canonical
        origin means the sync corrupted the file.
        """
        canon = set(_normalize(CANON_GITLAB.read_text(encoding="utf-8")))
        mirror = _normalize(MIRROR_GITLAB.read_text(encoding="utf-8"))
        orphans = [ln for ln in mirror if ln not in canon]
        self.assertEqual(
            [],
            orphans,
            "codex/ gitlab.md has content lines with no canonical origin "
            f"(sync corruption?): {orphans[:5]}",
        )

    def test_mirror_preserves_bulk_of_canonical(self) -> None:
        """Nearly all canonical content survives into the mirror.

        Only the single trailing Codex-meta bullet is deliberately stripped, so the
        mirror must retain the overwhelming bulk of canonical content. A large drop
        means the sync silently lost adapter prose: a real parity failure.
        """
        canon = _normalize(CANON_GITLAB.read_text(encoding="utf-8"))
        mirror = set(_normalize(MIRROR_GITLAB.read_text(encoding="utf-8")))
        missing = [ln for ln in canon if ln not in mirror]
        # The Codex-meta note spans ~2 collapsed lines; allow a tiny slack only.
        self.assertLessEqual(
            len(missing),
            4,
            f"codex/ gitlab.md dropped {len(missing)} canonical content lines "
            f"(stale mirror - run sync-codex.sh): e.g. {missing[:5]}",
        )

class JiraMirrorExistsTestCase(unittest.TestCase):
    def test_canonical_jira_reference_exists(self) -> None:
        self.assertTrue(
            CANON_JIRA.is_file(),
            f"canonical Jira adapter reference missing: {CANON_JIRA}",
        )

    def test_mirror_jira_reference_exists(self) -> None:
        self.assertTrue(
            MIRROR_JIRA.is_file(),
            "canonical references/jira.md was not mirrored into codex/ - "
            "run `bash scripts/sync-codex.sh`",
        )


class JiraMirrorContentParityTestCase(unittest.TestCase):
    def test_mirror_adds_no_fabricated_content(self) -> None:
        """Every mirror content line traces back to the canonical jira.md."""
        canon = set(_normalize(CANON_JIRA.read_text(encoding="utf-8")))
        mirror = _normalize(MIRROR_JIRA.read_text(encoding="utf-8"))
        orphans = [ln for ln in mirror if ln not in canon]
        self.assertEqual(
            [],
            orphans,
            "codex/ jira.md has content lines with no canonical origin "
            f"(sync corruption?): {orphans[:5]}",
        )

    def test_mirror_preserves_bulk_of_canonical(self) -> None:
        """Nearly all canonical jira.md content survives into the mirror."""
        canon = _normalize(CANON_JIRA.read_text(encoding="utf-8"))
        mirror = set(_normalize(MIRROR_JIRA.read_text(encoding="utf-8")))
        missing = [ln for ln in canon if ln not in mirror]
        # The Codex-meta note spans ~2 collapsed lines; allow a tiny slack only.
        self.assertLessEqual(
            len(missing),
            4,
            f"codex/ jira.md dropped {len(missing)} canonical content lines "
            f"(stale mirror - run sync-codex.sh): e.g. {missing[:5]}",
        )


if __name__ == "__main__":
    unittest.main()
