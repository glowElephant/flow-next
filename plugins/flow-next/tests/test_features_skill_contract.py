"""Behavioral contract for /flow-next:features (fn-211.1).

Extracts and EXECUTES the two skill predicates shipped as bash fences in
SKILL.md (autonomy-namespace scan; state-resolved seed/maintain routing)
and the maintain PR create fence, and asserts the FEATURES_VERDICT terminal
grammar is stated.

Behavior only: no prose-string pins beyond the structural greps needed to
extract fences and headings (G2).

Run:
    cd plugins/flow-next/tests && python3 -m unittest test_features_skill_contract -q
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN = REPO_ROOT / "plugins" / "flow-next"
SKILL_DIR = PLUGIN / "skills" / "flow-next-features"
SKILL_MD = SKILL_DIR / "SKILL.md"
MAINTAIN_MD = SKILL_DIR / "maintain.md"

_BASH = shutil.which("bash")

VERDICT_GRAMMAR = (
    "FEATURES_VERDICT=<SEEDED|CLEAN|CHANGED|BLOCKED|REFUSED> "
    'features=<n> reason="<one line>"'
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")


def _bash_fences(text: str) -> list[str]:
    return re.findall(r"```bash\n(.*?)```", text, re.DOTALL)


def _autonomy_fence(text: str) -> str:
    for body in _bash_fences(text):
        if "FEATURES_VERDICT=REFUSED" in body and "env" in body and "grep" in body:
            return body
    raise AssertionError("autonomy-refusal bash fence not found in SKILL.md")


def _mode_fence(text: str) -> str:
    for body in _bash_fences(text):
        if ".flow/features" in body and "MODE=" in body:
            return body
    raise AssertionError("mode-detection bash fence not found in SKILL.md")


def _run_bash(script: str, *, env: dict[str, str], cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    assert _BASH, "bash required to execute skill fences"
    return subprocess.run(
        [_BASH],
        input=script,
        env=env,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def _clean_env(**extra: str) -> dict[str, str]:
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    env.update(extra)
    return env


class AutonomyNamespaceScan(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fence = _autonomy_fence(_read(SKILL_MD))

    @unittest.skipUnless(_BASH, "bash required to execute the autonomy fence")
    def test_novel_marker_outside_any_written_list_refuses(self) -> None:
        # FLOW_AUTONOMOUS_FUTURE is deliberately not a name written in the
        # fence. A fixed check of FLOW_AUTONOMOUS alone would miss it.
        proc = _run_bash(
            self.fence,
            env=_clean_env(FLOW_AUTONOMOUS_FUTURE="1"),
        )
        output = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, f"novel marker must refuse: {output}")
        self.assertIn("FEATURES_VERDICT=REFUSED", output)

    @unittest.skipUnless(_BASH, "bash required to execute the autonomy fence")
    def test_clean_env_does_not_refuse(self) -> None:
        proc = _run_bash(self.fence, env=_clean_env())
        output = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, f"clean env must pass: {output}")
        self.assertNotIn("FEATURES_VERDICT=REFUSED", output)


class ModeDetectionStateRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fence = _mode_fence(_read(SKILL_MD))

    def _mode_in(self, tmp: str, arguments: str = "") -> str:
        proc = _run_bash(
            self.fence,
            env=_clean_env(ARGUMENTS=arguments),
            cwd=tmp,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        match = re.search(r"^MODE=(\S+)", proc.stdout, re.M)
        self.assertIsNotNone(match, f"no MODE= line in stdout: {proc.stdout!r}")
        return match.group(1)

    @unittest.skipUnless(_BASH, "bash required to execute the mode fence")
    def test_absent_features_dir_routes_to_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self._mode_in(tmp), "seed")

    @unittest.skipUnless(_BASH, "bash required to execute the mode fence")
    def test_present_features_dir_routes_to_maintain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".flow", "features").mkdir(parents=True)
            self.assertEqual(self._mode_in(tmp), "maintain")

    @unittest.skipUnless(_BASH, "bash required to execute the mode fence")
    def test_present_plus_init_intent_routes_to_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".flow", "features").mkdir(parents=True)
            self.assertEqual(self._mode_in(tmp, arguments="--init"), "seed")


class TerminalGrammar(unittest.TestCase):
    def test_features_verdict_grammar_stated(self) -> None:
        skill = _read(SKILL_MD)
        self.assertIn(VERDICT_GRAMMAR, skill)
        self.assertIn("FEATURES_VERDICT=", skill)
        for token in ("SEEDED", "CLEAN", "CHANGED", "BLOCKED", "REFUSED"):
            self.assertIn(token, skill)


class MaintainShipStep(unittest.TestCase):
    """#495: the PR create fence honours the create seam."""

    @unittest.skipUnless(_BASH, "bash required to execute the create fence")
    def test_pr_create_fence_honours_the_create_seam(self) -> None:
        text = _read(MAINTAIN_MD)
        fence = next(
            (body for body in _bash_fences(text) if "--body-file" in body), None
        )
        self.assertIsNotNone(fence, "PR create fence not found in maintain.md")
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "args"
            stub = Path(tmp) / "create"
            stub.write_text(f'#!/bin/sh\nprintf "%s\\n" "$@" > "{log}"\n', encoding="utf-8")
            stub.chmod(0o755)
            env = _clean_env(FLOW_PR_CREATE_CMD=str(stub), PR_BODY=str(Path(tmp) / "body.md"))
            res = _run_bash(fence, env=env, cwd=tmp)
            self.assertEqual(res.returncode, 0, res.stderr)
            args = log.read_text(encoding="utf-8").splitlines()
        self.assertIn("--title", args)
        self.assertIn("--body-file", args)


if __name__ == "__main__":
    unittest.main()
