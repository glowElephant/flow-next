"""Skill call-site diet: flowctl invocation shapes and routed references.

Pins what the fences run (config snapshot counts, the bulk task create, the
impl-review flag parse, per-backend plan-review dispatch) and that gated
references stay reachable. Canonical files and, where the check survives the
sync rewrite, the codex mirror copies.
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PLUGIN = REPO / "plugins" / "flow-next"
SKILLS = PLUGIN / "skills"
MIRROR_SKILLS = PLUGIN / "codex" / "skills"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "plan_invocation_counts"

# Matches an actual `config get` INVOCATION ($FLOWCTL-prefixed, quoted or not),
# never a prose mention of the words "config get".
CONFIG_GET = re.compile(r'\$FLOWCTL"?\s+config get')


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str, start: str, end: str) -> str:
    """Slice of text from the line starting `start` up to the line starting `end`."""
    lines = text.splitlines(keepends=True)
    out, active = [], False
    for line in lines:
        if line.startswith(start):
            active = True
        elif active and line.startswith(end):
            break
        if active:
            out.append(line)
    joined = "".join(out)
    assert joined, f"section {start!r}..{end!r} not found"
    return joined


def both_copies(rel: str):
    """Canonical file + its codex-mirror copy (mirror must exist)."""
    canonical = SKILLS / rel
    mirrored = MIRROR_SKILLS / rel
    assert canonical.exists(), f"missing canonical file: {rel}"
    assert mirrored.exists(), f"missing codex mirror copy: {rel}"
    return [canonical, mirrored]


class PlanDietTestCase(unittest.TestCase):
    def steps(self):
        return both_copies("flow-next-plan/steps.md")

    def test_plan_uses_preflight_config(self):
        for path in both_copies("flow-next-plan/SKILL.md"):
            self.assertIn("preflight --json", read(path))
        for path in self.steps():
            self.assertEqual(CONFIG_GET.findall(read(path)), [])

    def test_route_b_create_path_has_no_set_branch_or_set_spec(self):
        for path in self.steps():
            route_b = section(read(path), "**Route B", "## Step 6")
            self.assertNotIn("$FLOWCTL spec set-branch", route_b,
                             f"{path}: set-branch reintroduced on the create path")
            self.assertNotIn("$FLOWCTL task set-spec", route_b,
                             f"{path}: per-task set-spec reintroduced on the create path")
            # Tasks are created in one bulk call whose JSON carries the
            # create-time fields.
            self.assertIn("$FLOWCTL task create --spec", route_b)
            self.assertIn("--from-json", route_b)
            for field in ("description_file", "acceptance_file", "satisfies"):
                self.assertIn(field, route_b, f"{path}: task create lost {field}")

    def test_fixture_shows_at_least_40_percent_fewer_invocations(self):
        def count(name):
            lines = read(FIXTURES / name).splitlines()
            return len([ln for ln in lines if ln.strip() and not ln.startswith("#")])

        before, after = count("before.txt"), count("after.txt")
        self.assertGreater(before, after)
        # Integer math: (before - after) / before >= 0.40
        self.assertGreaterEqual(
            (before - after) * 100, 40 * before,
            f"plan fixture reduction below 40% ({before} -> {after})",
        )

    def test_plan_optional_routes_load_one_level_references_after_gates(self):
        steps = read(SKILLS / "flow-next-plan/steps.md")
        cases = (
            ("## Step 6.5", "## Step 7", "tracker.perEvent.plan",
             "references/tracker-projection.md"),
            ("## Step 7", "## Step 8", "review mode is `none`",
             "references/selected-review.md"),
        )
        for start, end, gate, reference in cases:
            body = section(steps, start, end) if end else steps[steps.index(start):]
            self.assertIn(gate, body)
            self.assertIn(reference, body)
            self.assertLess(body.index(gate), body.index(reference),
                            f"{reference}: reference must follow its route gate")
            root = SKILLS / "flow-next-plan"
            path = root / reference
            self.assertTrue(path.is_file(), f"missing routed reference: {path}")
            # References remain exactly one directory level under the skill root.
            self.assertEqual(len(path.relative_to(root).parts), 2)

    def test_plan_holdout_keeps_subject_and_answer_key_separate(self):
        holdout = REPO / "optimization" / "plan" / "holdout"
        subject = read(holdout / "input.md")
        oracle = read(holdout / "oracle.md")
        self.assertIn("no-code permit-intake architecture", subject)
        self.assertIn("H10 — review route", oracle)
        self.assertNotIn("H1 — no implementation leakage", subject)


class PilotSnapshotTestCase(unittest.TestCase):
    """The unattended driver (`flow --auto`, formerly pilot). `auto.md` is the
    single always-loaded-under---auto file, so the ONE root config snapshot
    call lives there; the gated references derive every later read via jq."""

    def test_hop_uses_snapshot_instead_of_config_calls(self):
        for path in both_copies("flow-next-flow/auto.md"):
            text = read(path)
            self.assertIn("pilot snapshot", text)
            self.assertEqual(CONFIG_GET.findall(text), [])

    def test_no_config_scratch_ceremony(self):
        for path in both_copies("flow-next-flow/auto.md"):
            self.assertNotIn("flow-pilot-config-", read(path))

    def test_backlog_mode_has_zero_flowctl_config_calls(self):
        for path in both_copies("flow-next-flow/references/backlog-mode.md"):
            self.assertNotRegex(read(path), r'\$FLOWCTL"?\s+config\b',
                                f"{path}: backlog-mode.md must be config-call-free")

    def test_consumers_use_snapshot_payload(self):
        for rel in ("auto.md", "references/backlog-mode.md"):
            for path in both_copies(f"flow-next-flow/{rel}"):
                self.assertIn("PILOT_SNAPSHOT", read(path))
                self.assertNotIn("PILOT_CFG_SNAPSHOT", read(path))


class MakePrFenceTestCase(unittest.TestCase):
    def test_phase0_reaches_bundled_preflight(self):
        script = read(SKILLS.parent / "scripts/make-pr-preflight.sh")
        for path in both_copies("flow-next-make-pr/workflow.md"):
            phase0 = section(read(path), "## Phase 0", "## Phase 1")
            self.assertIn('source "$(dirname "$FLOWCTL")/make-pr-preflight.sh"', phase0)
        self.assertIn('SPEC_JSON=$("$FLOWCTL" show "$SPEC_ID" --json', script)
        self.assertIn("# fence:spec-close", script)
        self.assertIn("NEED_INPUT:", script)


class ImplReviewArgFenceTestCase(unittest.TestCase):
    def test_single_argument_parse_fence(self):
        # The flag parse runs only on the opt-in path, which SKILL.md routes
        # to other-paths.md.
        for path in both_copies("flow-next-impl-review/SKILL.md"):
            self.assertIn("[other-paths.md](other-paths.md)", read(path))
        for path in both_copies("flow-next-impl-review/other-paths.md"):
            text = read(path)
            self.assertEqual(
                text.count("for arg in $(printf "), 1,
                f"{path}: impl-review must parse $ARGUMENTS in exactly ONE fence",
            )
            # The merged fence still covers all three opt-in flags.
            for needle in ("--validate) VALIDATE=true", "--deep) DEEP=true",
                           "--interactive) INTERACTIVE=true"):
                self.assertIn(needle, text, f"{path}: merged arg fence lost {needle!r}")


class PlanReviewSingleSourceTestCase(unittest.TestCase):
    INVOKE = re.compile(r"^\$FLOWCTL (codex|copilot|cursor) plan-review", re.M)
    BACKENDS = ("claude", "codex", "copilot", "cursor", "host", "rp")

    def test_backend_blocks_live_only_in_selected_workflows(self):
        skill_dir = SKILLS / "flow-next-plan-review"
        self.assertEqual(self.INVOKE.findall(read(skill_dir / "SKILL.md")), [])
        self.assertEqual(self.INVOKE.findall(read(skill_dir / "workflow.md")), [])
        for backend in ("codex", "copilot", "cursor"):
            path = skill_dir / f"workflow-{backend}.md"
            self.assertEqual(
                self.INVOKE.findall(read(path)),
                [backend],
                f"{path}: must contain exactly its selected backend dispatch",
            )

    def test_router_lists_every_backend_once(self):
        skill = read(SKILLS / "flow-next-plan-review/SKILL.md")
        for backend in self.BACKENDS:
            link = f"[workflow-{backend}.md](workflow-{backend}.md)"
            self.assertEqual(skill.count(link), 1, f"router drift for {backend}")

    def test_codex_mirror_is_b1_or_regenerated_split(self):
        """Parallel workers defer mirror regen; integrated tree must be split."""
        mirror = MIRROR_SKILLS / "flow-next-plan-review"
        if (mirror / "workflow-codex.md").exists():
            for backend in self.BACKENDS:
                self.assertTrue((mirror / f"workflow-{backend}.md").is_file())
            self.assertEqual(self.INVOKE.findall(read(mirror / "workflow.md")), [])
        else:
            # The conductor owns the combined sync. Before that sync, the
            # isolated worker must leave the known B1 monolith untouched.
            self.assertEqual(
                set(self.INVOKE.findall(read(mirror / "workflow.md"))),
                {"codex", "copilot", "cursor"},
            )

    def test_subprocess_fences_redeclare_spec_id(self):
        for backend in ("codex", "copilot", "cursor", "claude"):
            path = SKILLS / "flow-next-plan-review" / f"workflow-{backend}.md"
            text = read(path)
            self.assertIn('SPEC_ID="<', text)
            # fn-257 R1: a Bash-tool call leaves $1 empty; the id is literal.
            self.assertNotIn("${1:-}", text)
            self.assertIn(f"$FLOWCTL {backend} plan-review", text)


class RoutedReferencesAndVerdictsTestCase(unittest.TestCase):
    """Gated references stay reachable; machine-read verdict lines remain."""

    def test_auto_reaches_its_gated_references(self):
        for path in both_copies("flow-next-flow/auto.md"):
            text = read(path)
            self.assertIn("(references/backlog-mode.md)", text)
            self.assertIn("(references/qa-stage.md)", text)
            self.assertIn("config.pipeline.qa", text)

    def test_verdict_lines_remain(self):
        for path in both_copies("flow-next-plan-review/SKILL.md"):
            self.assertIn("BLOCKED: DESIGN_CONFLICT", read(path))
        for path in both_copies("flow-next-flow/auto.md"):
            self.assertIn("PILOT_VERDICT=<ADVANCED|NO_WORK|", read(path))
        for path in both_copies("flow-next-land/SKILL.md"):
            self.assertIn("LAND_VERDICT=<verdict|NO_WORK>", read(path))


if __name__ == "__main__":
    unittest.main()
