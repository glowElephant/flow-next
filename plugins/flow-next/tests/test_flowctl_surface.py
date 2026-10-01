"""Post-refactor production-surface and live workflow command contracts."""

from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling test helpers
from flowctl_test_support import FLOWCTL_CMD


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN = REPO_ROOT / "plugins" / "flow-next"
FLOWCTL_PY = PLUGIN / "scripts" / "flowctl.py"
SCRIPTS_DIR = FLOWCTL_PY.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import flowctl  # noqa: E402


PLAN_INVOCATION_MANIFEST = (
    ("preflight",),
    ("init",),
    ("cat",),
    ("show",),
    ("specs",),
    ("spec", "ready"),
    ("strategy", "read"),
    ("spec", "set-plan"),
    ("task", "set-spec"),
    ("spec", "create"),
    ("spec", "add-dep"),
    ("task", "create"),
    ("dep", "add"),
    ("validate",),
)

FLOWCTL_INVOCATION = re.compile(
    r'(?<![A-Za-z0-9_])"?\$FLOWCTL"?\s+'
    r"([a-z][a-z0-9-]*)(?:\s+([a-z][a-z0-9-]*))?"
)

ACTIVE_REFERENCE_ROOTS = (
    REPO_ROOT / "README.md",
    PLUGIN / "docs",
    PLUGIN / "skills",
    PLUGIN / "agents",
    PLUGIN / "codex" / "skills",
    PLUGIN / "codex" / "agents",
    REPO_ROOT / "agent_docs",
)
ACTIVE_REFERENCE_EXCLUDES = (
    "agent_docs/guidance-eval/",
    "agent_docs/optimization-log.md",
)
SHELL_FENCE_LANGUAGES = {"", "bash", "sh", "shell", "zsh", "powershell"}
EXECUTABLE_FLOWCTL_INVOCATION = re.compile(
    r'(?m)^\s*(?:"?\$FLOWCTL"?|(?:\.flow/bin/|scripts/)?flowctl)'
    r'(?![.A-Za-z0-9_-])\s+'
    r"([a-z][a-z0-9-]*)(?:\s+([a-z][a-z0-9-]*))?"
)


def _active_reference_files() -> list[Path]:
    paths: list[Path] = []
    for root in ACTIVE_REFERENCE_ROOTS:
        candidates = (
            [root]
            if root.is_file()
            else (
                path
                for path in root.rglob("*")
                if path.suffix in {".md", ".toml"}
            )
        )
        for path in candidates:
            relative = path.relative_to(REPO_ROOT).as_posix()
            if any(relative.startswith(prefix) for prefix in ACTIVE_REFERENCE_EXCLUDES):
                continue
            paths.append(path)
    return sorted(set(paths))


def _shell_fence_bodies(text: str) -> list[tuple[str, bool]]:
    bodies: list[tuple[str, bool]] = []
    open_language: str | None = None
    body: list[str] = []
    for line in text.splitlines():
        if open_language is None:
            match = re.match(r"^\s*```([^\s`]*)\s*$", line)
            if match and match.group(1).lower() in SHELL_FENCE_LANGUAGES:
                open_language = match.group(1).lower()
                body = []
            continue
        if re.match(r"^\s*```\s*$", line):
            bodies.append(("\n".join(body), bool(open_language)))
            open_language = None
            body = []
            continue
        body.append(line)
    return bodies


class _ParserCaptured(Exception):
    pass


def _built_parser() -> argparse.ArgumentParser:
    captured: dict[str, argparse.ArgumentParser] = {}

    def capture(parser, *_args, **_kwargs):
        captured["parser"] = parser
        raise _ParserCaptured

    with mock.patch.object(argparse.ArgumentParser, "parse_args", capture):
        with unittest.TestCase().assertRaises(_ParserCaptured):
            flowctl.main()
    return captured["parser"]


def _leaf_parsers(parser: argparse.ArgumentParser, prefix=()):
    subparser_actions = [
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]
    if not subparser_actions:
        yield prefix, parser
        return
    for action in subparser_actions:
        seen: set[int] = set()
        for name, child in action.choices.items():
            if id(child) in seen:
                continue
            seen.add(id(child))
            yield from _leaf_parsers(child, prefix + (name,))


LEAF_PATHS = frozenset(" ".join(path) for path, _parser in _leaf_parsers(_built_parser()))
TOP_LEVEL_COMMANDS = {path.split(" ", 1)[0] for path in LEAF_PATHS}
GROUPED_COMMANDS = {path.split(" ", 1)[0] for path in LEAF_PATHS if " " in path}


class CliSurfaceContractTest(unittest.TestCase):
    def test_every_registered_leaf_has_a_callable_handler(self) -> None:
        leaves = list(_leaf_parsers(_built_parser()))
        missing = [
            " ".join(path)
            for path, parser in leaves
            if not callable(parser.get_default("func"))
        ]
        self.assertEqual(missing, [])

    def test_live_plan_invocation_manifest_exists_and_parses(self) -> None:
        # Branch-disclosure refactor: plan's gated bash moved verbatim into
        # references/ (readiness-warn, route-a-refine, tracker-first-mint,
        # setup-questions, strategy-alignment, next-steps-menu). The reached
        # paths still invoke the same flowctl verbs, so the manifest is checked
        # against the skill files PLUS every reference they disclose.
        plan_skill = PLUGIN / "skills" / "flow-next-plan"
        plan_files = [plan_skill / "SKILL.md", plan_skill / "steps.md"]
        plan_files += sorted((plan_skill / "references").glob("*.md"))
        gating_text = "\n".join(
            f.read_text(encoding="utf-8")
            for f in (plan_skill / "SKILL.md", plan_skill / "steps.md")
        )
        for reference in sorted((plan_skill / "references").glob("*.md")):
            # Every reference whose verbs count toward the manifest must be
            # reachable: a gating file has to name it.
            self.assertIn(f"references/{reference.name}", gating_text)
        plan_text = "\n".join(
            f.read_text(encoding="utf-8") for f in plan_files
        )
        invocations = set()
        for match in FLOWCTL_INVOCATION.finditer(plan_text):
            top, child = match.groups()
            invocations.add(
                (top, child) if top in GROUPED_COMMANDS and child else (top,)
            )
        for path in PLAN_INVOCATION_MANIFEST:
            self.assertIn(path, invocations, " ".join(path))
            result = subprocess.run(
                [*FLOWCTL_CMD, *path, "--help"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, (path, result.stderr))


class ActiveReferenceContractTest(unittest.TestCase):
    def test_active_shell_snippets_only_invoke_registered_commands(self) -> None:
        failures: list[str] = []
        for path in _active_reference_files():
            text = path.read_text(encoding="utf-8")
            for body, strict in _shell_fence_bodies(text):
                for match in EXECUTABLE_FLOWCTL_INVOCATION.finditer(body):
                    top, child = match.groups()
                    if top not in TOP_LEVEL_COMMANDS:
                        if strict:
                            failures.append(
                                f"{path.relative_to(REPO_ROOT)}: {top}"
                            )
                        # Unlabelled fences also carry prose and diagrams. The
                        # removed-surface test below guards historical command
                        # names even there; language-tagged shell fences are
                        # strict and reject every unknown top-level command.
                        continue
                    if top in GROUPED_COMMANDS and child:
                        command = f"{top} {child}"
                        if (
                            command not in LEAF_PATHS
                            and not any(
                                leaf.startswith(f"{command} ")
                                for leaf in LEAF_PATHS
                            )
                        ):
                            failures.append(
                                f"{path.relative_to(REPO_ROOT)}: {command}"
                            )
        self.assertEqual(failures, [])

    def test_strategy_commands_use_the_resolved_flowctl_path(self) -> None:
        strategy = PLUGIN / "skills" / "flow-next-strategy"
        for path in strategy.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(
                text,
                r'(?<!\$)(?<!["/])\bflowctl\s+(?:strategy|specs)\b',
                path.relative_to(REPO_ROOT).as_posix(),
            )

class CompletionReviewStateTest(unittest.TestCase):
    def test_completion_review_status_persists_all_authoritative_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            flow_dir = Path(tmp) / ".flow"
            specs = flow_dir / "specs"
            specs.mkdir(parents=True)
            path = specs / "fn-1.json"
            path.write_text(
                json.dumps(
                    {
                        "id": "fn-1",
                        "title": "One",
                        "status": "open",
                        "created_at": "2026-01-01T00:00:00Z",
                    }
                ),
                encoding="utf-8",
            )
            args = argparse.Namespace(id="fn-1", status="ship", json=True)
            output = io.StringIO()
            timestamps = iter(
                ["2026-07-21T23:00:00Z", "2026-07-21T23:00:01Z"]
            )
            with mock.patch.object(flowctl, "ensure_flow_exists", return_value=True):
                with mock.patch.object(flowctl, "get_flow_dir", return_value=flow_dir):
                    with mock.patch.object(flowctl, "now_iso", side_effect=timestamps):
                        with redirect_stdout(output):
                            flowctl.cmd_spec_set_completion_review_status(args)

            stored = json.loads(path.read_text(encoding="utf-8"))
            payload = json.loads(output.getvalue())
            self.assertEqual(stored["completion_review_status"], "ship")
            self.assertEqual(
                stored["completion_reviewed_at"], "2026-07-21T23:00:00Z"
            )
            self.assertEqual(stored["updated_at"], "2026-07-21T23:00:01Z")
            self.assertEqual(stored["created_at"], "2026-01-01T00:00:00Z")
            self.assertEqual(payload["completion_review_status"], "ship")
            self.assertEqual(
                payload["completion_reviewed_at"], stored["completion_reviewed_at"]
            )


if __name__ == "__main__":
    unittest.main()
