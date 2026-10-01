"""Review-prompt loading and rendering behaviour.

``flowctl`` ships FALLBACK constants that must be byte-identical to the
skill-owned ``references/*.md`` templates: an install where the plugin root is
unavailable renders the fallback, and it must send reviewers the same prompt
every other install sends. Edit one, edit the other.

Rendering is checked for substitution only: every identity slot and shared
block lands where the builder puts it, optional slots drop out when empty, and
no placeholder survives. What the prompts say is not pinned here.

Run:
    python3 -m unittest plugins.flow-next.tests.test_review_prompt_template_parity -v
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path
from typing import Any

# The tracker package sits beside flowctl.py; under a test module sys.path[0]
# is THIS directory, not scripts/, so it would not import.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def _load_flowctl() -> Any:
    here = Path(__file__).resolve()
    flowctl_path = here.parent.parent / "scripts" / "flowctl.py"
    if not flowctl_path.is_file():
        raise RuntimeError(f"flowctl.py not found at {flowctl_path}")
    spec = importlib.util.spec_from_file_location(
        "flowctl_review_prompt_parity", flowctl_path
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


flowctl = _load_flowctl()

HERE = Path(__file__).resolve()
PLUGIN_DIR = HERE.parent.parent  # plugins/flow-next
REPO_ROOT = PLUGIN_DIR.parent.parent

# (embedded FALLBACK constant, on-disk template relative to repo root)
PARITY_PAIRS = [
    (
        "IMPL_REVIEW_PROMPT_FALLBACK",
        "plugins/flow-next/skills/flow-next-impl-review/references/impl-review-prompt.md",
    ),
    (
        "STANDALONE_REVIEW_PROMPT_FALLBACK",
        "plugins/flow-next/skills/flow-next-impl-review/references/standalone-review-prompt.md",
    ),
    (
        "PLAN_REVIEW_PROMPT_FALLBACK",
        "plugins/flow-next/skills/flow-next-plan-review/references/plan-review-prompt.md",
    ),
    (
        "COMPLETION_REVIEW_PROMPT_FALLBACK",
        "plugins/flow-next/skills/flow-next-spec-completion-review/references/completion-review-prompt.md",
    ),
]

# NOT in PARITY_PAIRS, deliberately: VALIDATOR_TEMPLATE_FALLBACK and
# DEEP_PASSES_FALLBACK are hand-written CONDENSATIONS of their templates, not
# byte-identical mirrors like the four above. Do not "fix" the difference.

_HINTS = "hint-a\nhint-b"
_DSUM = " 3 files changed, 10 insertions(+), 2 deletions(-)"
_TASKS = (".flow/tasks/fn-parity.1.md", ".flow/tasks/fn-parity.2.md")
_SPEC = ".flow/specs/fn-parity.md"
_RANGE = "aaaaaaa..bbbbbbb"
_BASE = "main"
_FOCUS = "auth and sessions"

# A `{name}` left behind means a template placeholder was never substituted.
_UNSUBSTITUTED = re.compile(r"\{[a-z_]+_(?:block|section|guidance|files|branch)\}")
_VERDICT_TAG = re.compile(r"<verdict>([A-Z_]+)</verdict>")


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n")


def _slots(prompt: str) -> str:
    """The identity slots the builder renders ahead of the instructions."""
    return prompt.split("<review_instructions>", 1)[0]


class TestReviewPromptTemplateParity(unittest.TestCase):
    def test_fallbacks_match_template_files(self) -> None:
        for const_name, rel in PARITY_PAIRS:
            with self.subTest(template=rel):
                fallback = getattr(flowctl, const_name)
                path = REPO_ROOT / rel
                self.assertTrue(path.is_file(), f"template missing: {rel}")
                self.assertEqual(
                    _normalize(fallback),
                    _normalize(path.read_text(encoding="utf-8")),
                    f"{const_name} drifted from {rel} - keep FALLBACK byte-identical "
                    f"to the skill template.",
                )


class _HermeticCriteria(unittest.TestCase):
    """Renders must not absorb the host repo's .flow/criteria.md."""

    def setUp(self) -> None:
        super().setUp()
        import tempfile
        import unittest.mock as _mock
        self._criteria_tmp = tempfile.TemporaryDirectory()
        patcher = _mock.patch.object(
            flowctl,
            "get_criteria_path",
            lambda: Path(self._criteria_tmp.name) / "criteria.md",
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._criteria_tmp.cleanup)


class TestReviewPromptRendering(_HermeticCriteria):
    """Identity slots and shared blocks are substituted; empty slots drop out."""

    def _assert_rendered(self, prompt: str) -> None:
        self.assertEqual(_UNSUBSTITUTED.findall(prompt), [])
        self.assertNotIn("<!-- placeholders:", prompt)
        self.assertIn(flowctl.CONFIDENCE_RUBRIC_BLOCK, prompt)
        self.assertIn(flowctl.PROTECTED_ARTIFACTS_BLOCK, prompt)
        self.assertIn(flowctl.REVIEW_JSON_TALLY_BLOCK, prompt)

    def test_impl_review_prompt(self) -> None:
        prompt = flowctl.build_review_prompt(
            "impl", context_hints=_HINTS, review_scope=_DSUM,
            diff_range=_RANGE, spec_path=_SPEC,
        )
        self._assert_rendered(prompt)
        self.assertIn(f"<context_hints>\n{_HINTS}\n</context_hints>", prompt)
        self.assertIn(f"<changed_files>\n{_DSUM}\n</changed_files>", prompt)
        self.assertIn(f"git diff {_RANGE}", prompt)
        self.assertIn(f"<spec>\n{_SPEC}\n</spec>", prompt)
        self.assertIn(flowctl.SMELL_BASELINE_BLOCK, prompt)
        self.assertIn(flowctl.R_ID_COVERAGE_BLOCK, prompt)
        self.assertIn(flowctl.CLASSIFICATION_RUBRIC_BLOCK, prompt)
        self.assertTrue(prompt.rstrip().endswith("</review_instructions>"))

    def test_impl_review_prompt_empty_optionals(self) -> None:
        prompt = flowctl.build_review_prompt("impl", spec_path=_SPEC)
        self._assert_rendered(prompt)
        for absent in ("<context_hints>", "<changed_files>", "<diff_range>", "<task_specs>"):
            with self.subTest(absent=absent):
                self.assertNotIn(absent, _slots(prompt))
        self.assertTrue(prompt.startswith(f"<spec>\n{_SPEC}\n</spec>"))

    def test_plan_review_prompt(self) -> None:
        prompt = flowctl.build_review_prompt(
            "plan", context_hints=_HINTS, spec_path=_SPEC, task_spec_paths=_TASKS,
        )
        self._assert_rendered(prompt)
        self.assertIn(flowctl.PLAN_QUALITY_BLOCK, prompt)
        self.assertIn("<task_specs>\n" + "\n".join(_TASKS) + "\n</task_specs>", prompt)
        self.assertNotIn("<diff_range>", _slots(prompt))

    def test_plan_review_prompt_no_tasks(self) -> None:
        prompt = flowctl.build_review_prompt("plan", context_hints=_HINTS, spec_path=_SPEC)
        self._assert_rendered(prompt)
        self.assertNotIn("<task_specs>", _slots(prompt))

    def test_standalone_review_prompt(self) -> None:
        prompt = flowctl.build_standalone_review_prompt(_BASE, _FOCUS, _DSUM, _RANGE)
        self._assert_rendered(prompt)
        self.assertIn(_BASE, prompt)
        self.assertIn(_FOCUS, prompt)
        self.assertIn(_DSUM, prompt)
        self.assertIn(f"git diff {_RANGE}", prompt)

    def test_standalone_review_prompt_no_focus(self) -> None:
        prompt = flowctl.build_standalone_review_prompt(_BASE, None, _DSUM, _RANGE)
        self._assert_rendered(prompt)
        self.assertNotIn(_FOCUS, prompt)

    def test_completion_review_prompt(self) -> None:
        prompt = flowctl.build_completion_review_prompt(_SPEC, _TASKS, _DSUM, _RANGE)
        self._assert_rendered(prompt)
        self.assertIn(f"<spec>\n{_SPEC}\n</spec>", prompt)
        self.assertIn("<task_specs>\n" + "\n".join(_TASKS) + "\n</task_specs>", prompt)
        self.assertIn(f"git diff {_RANGE}", prompt)

    def test_completion_review_prompt_no_tasks(self) -> None:
        prompt = flowctl.build_completion_review_prompt(_SPEC, (), _DSUM, _RANGE)
        self._assert_rendered(prompt)
        self.assertNotIn("<task_specs>", _slots(prompt))


class TestReviewPromptVerdictGrammar(unittest.TestCase):
    """Every verdict a prompt offers is one the verdict parser accepts."""

    def test_verdict_tags_are_parser_grammar(self) -> None:
        for _, rel in PARITY_PAIRS:
            with self.subTest(template=rel):
                text = (REPO_ROOT / rel).read_text(encoding="utf-8")
                offered = set(_VERDICT_TAG.findall(text))
                self.assertLessEqual({"SHIP", "NEEDS_WORK", "NEEDS_HUMAN"}, offered)
                for verdict in offered:
                    self.assertEqual(
                        flowctl.parse_codex_verdict(f"<verdict>{verdict}</verdict>"),
                        verdict,
                    )


class TestDeepPassFallbackCoverage(unittest.TestCase):
    """Structural checks only - deliberately NOT a content comparison.

    A declared pass with no fallback entry is a KeyError on exactly the
    stripped installs the fallback exists for, and a missing template file
    breaks the normal path for everyone else.
    """

    def test_fallback_covers_every_declared_pass(self) -> None:
        self.assertEqual(
            sorted(flowctl.DEEP_PASSES), sorted(flowctl.DEEP_PASSES_FALLBACK)
        )

    def test_rel_constant_points_at_a_real_template(self) -> None:
        path = REPO_ROOT / flowctl.DEEP_PASSES_TEMPLATE_REL
        self.assertTrue(
            path.is_file(), f"DEEP_PASSES_TEMPLATE_REL missing on disk: {path}"
        )

    def test_every_pass_parses_out_of_the_template(self) -> None:
        """A sentinel in the fallback slot proves extraction reached the file."""
        for pass_name in flowctl.DEEP_PASSES:
            with self.subTest(deep_pass=pass_name):
                sentinel = f"<<DEEP-PASS-FALLBACK-USED:{pass_name}>>"
                real = flowctl.DEEP_PASSES_FALLBACK[pass_name]
                flowctl.DEEP_PASSES_FALLBACK[pass_name] = sentinel
                try:
                    got = flowctl.load_deep_pass_template(pass_name)
                finally:
                    flowctl.DEEP_PASSES_FALLBACK[pass_name] = real
                self.assertNotEqual(
                    got, sentinel,
                    f"load_deep_pass_template({pass_name!r}) fell back instead of "
                    f"parsing {flowctl.DEEP_PASSES_TEMPLATE_REL} - the "
                    f"<!-- {pass_name.upper()}_TEMPLATE --> marker or its "
                    f"```markdown fence is missing or renamed.",
                )


class TestValidatorTemplateRepoRootPath(unittest.TestCase):
    """Regression: the repo-root branch of ``load_validator_template`` was dead."""

    def test_rel_constant_points_at_a_real_template(self) -> None:
        path = REPO_ROOT / flowctl.VALIDATOR_TEMPLATE_REL
        self.assertTrue(
            path.is_file(), f"VALIDATOR_TEMPLATE_REL missing on disk: {path}"
        )

    def test_repo_root_branch_is_reachable(self) -> None:
        """Patch the repo root and assert the on-disk copy wins over the fallback."""
        import tempfile

        marker = "# MARKER validate-pass\n\n<!-- FINDINGS_BLOCK -->\n"
        original = flowctl.get_repo_root
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / flowctl.VALIDATOR_TEMPLATE_REL
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(marker, encoding="utf-8")
            flowctl.get_repo_root = lambda: root
            try:
                got = flowctl.load_validator_template()
            finally:
                flowctl.get_repo_root = original
        self.assertEqual(got, marker)


if __name__ == "__main__":
    unittest.main()
