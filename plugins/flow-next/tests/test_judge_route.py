"""Live route facts and explain output, using observed PR and task fixtures."""
import importlib.util
import io
from contextlib import redirect_stdout
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
spec = importlib.util.spec_from_file_location("flowctl_judge_route_test", SCRIPTS / "flowctl.py")
f = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = f
spec.loader.exec_module(f)


def route_matrix_rows():
    """Route-matrix rows keyed by starting-state prefix, across both matrix files."""
    refs = SCRIPTS.parent / "skills/flow-next-flow/references"
    rows = [
        [cell.strip() for cell in line.split("|")[1:-1]]
        for name in ("route-matrix.md", "route-matrix-more.md")
        for line in (refs / name).read_text(encoding="utf-8").splitlines()
        if line.startswith("| ") and not line.startswith("| Starting state")
    ]

    class _Rows:
        def __getitem__(self, prefix):
            hits = [row for row in rows if row[0].startswith(prefix)]
            assert len(hits) == 1, f"{len(hits)} route-matrix rows start with {prefix!r}"
            return hits[0]

    return _Rows()


class JudgeRouteTests(unittest.TestCase):
    def live(self, **overrides):
        return dict(view="live", spec_body="Build a bounded feature", ready=True,
                    tasks_total=0, tasks_done=0, pr_exists=False, pr_ref=None,
                    **overrides)

    def test_live_precedence(self):
        cases = [
            ({"pr_exists": None}, "host"),
            ({"pr_exists": True, "tasks_total": 2, "tasks_done": 2}, "existing_pr_tail"),
            ({"tasks_total": 2, "tasks_done": 2}, "all_done_make_pr"),
            ({"tasks_total": 2}, "work_planned"),
            ({"tasks_total": 1, "no_plan": True}, "work_planned"),
            ({}, "work_no_plan_default"),
            ({"no_plan": False}, "work_no_plan_default"),
            ({"no_plan": True, "spec_body": "task plan"}, "work_no_plan_default"),
            ({"spec_body": "Please plan this out"}, "plan"),
            ({"spec_body": "Separate owners implement each part"}, "plan"),
            ({"spec_body": "Ship in two PRs"}, "plan"),
            ({"spec_body": "Please decompose this into tasks"}, "plan"),
            # Isolated vocabulary and negated requests are not plan signals.
            ({"spec_body": "Implement a decompose() helper for matrix factorization."}, "work_no_plan_default"),
            ({"spec_body": "Do not decompose this into tasks; deliver one PR."}, "work_no_plan_default"),
            ({"spec_body": "Don't plan this out; never break it down into tasks."}, "work_no_plan_default"),
            ({"ready": False}, "host"),
        ]
        for overrides, expected in cases:
            with self.subTest(overrides=overrides):
                state = self.live()
                state.update(overrides)
                self.assertEqual(f.judge_route_lifecycle(state)["value"], expected)
        self.assertIsNone(f.judge_route_lifecycle({"view": "intent"}))

    def test_probe_observations_and_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            body = repo / "spec.md"
            body.write_text("Implement feature", encoding="utf-8")
            spec_data = {"title": "Feature", "status": "open", "branch_name": "fn-1-feature"}
            for status in ("OPEN", "MERGED", "CLOSED", "absent", "failed", "truncated", "ambiguous"):
                with self.subTest(status=status):
                    rows = [] if status == "absent" else [{"number": 1, "state": status, "url": "https://example.test/pr/1"}]
                    if status in {"truncated", "ambiguous"}:
                        rows = [{"number": i, "state": "OPEN" if status == "ambiguous" else "CLOSED", "url": f"pr/{i}"}
                                for i in range(100 if status == "truncated" else 2)]
                    probe = SimpleNamespace(returncode=int(status == "failed"), stdout=json.dumps(rows))
                    with patch.dict(f.os.environ, {"TYPESAFE_API_KEY": "test-key"}), patch.object(f, "get_config", return_value=True), patch.object(f, "get_repo_root", return_value=repo), patch.object(f, "get_flow_dir", return_value=repo), patch.object(f, "resolve_spec_id_arg", return_value="fn-1-feature"), patch.object(f, "load_json_or_exit", return_value=spec_data), patch.object(f, "normalize_epic", side_effect=lambda x: x), patch.object(f, "find_spec_md_path", return_value=body), patch.object(f.TaskInventory, "load", return_value=SimpleNamespace(by_spec={})), patch.object(f.subprocess, "run", return_value=probe) as run:
                        state = f.judge_route_state({}, "fn-1-feature")
                    self.assertIn("--state", run.call_args.args[0])
                    self.assertIn("all", run.call_args.args[0])
                    self.assertEqual(state["pr_exists"], None if status in {"failed", "truncated", "ambiguous"} else status != "absent")
                    if status in {"OPEN", "MERGED", "CLOSED"}:
                        self.assertEqual(state["pr_ref"]["state"], status)
                        self.assertEqual(f.judge_route_lifecycle(state)["value"], "existing_pr_tail")
                        # make-pr now closes the spec before opening its PR. Keep
                        # every observed PR on the tail route so the host can land,
                        # end after merge, or stop on an unmerged closure.
                        state["status"] = "done"
                        self.assertEqual(f.judge_route_lifecycle(state)["value"], "existing_pr_tail")
                    self.assertFalse(state["no_plan"])

    def test_closed_spec_without_observed_pr_never_routes_to_replacement(self):
        scratch = SCRIPTS.parents[2] / ".flow" / "tmp"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as tmp:
            repo = Path(tmp)
            body = repo / "spec.md"
            body.write_text("Implement feature", encoding="utf-8")
            spec_path = repo / "spec.json"
            # This is the persisted status written by spec close. Exercise the
            # real JSON reader and normalizer rather than inventing route facts.
            spec_path.write_text(json.dumps({
                "id": "fn-1-feature", "title": "Feature", "status": "done",
                "branch_name": "fn-1-feature", "ready": True,
            }), encoding="utf-8")
            probe = SimpleNamespace(returncode=0, stdout="[]")
            with patch.dict(f.os.environ, {"TYPESAFE_API_KEY": "test-key"}), patch.object(f, "get_config", return_value=True), patch.object(f, "get_repo_root", return_value=repo), patch.object(f, "get_flow_dir", return_value=repo), patch.object(f, "resolve_spec_id_arg", return_value="fn-1-feature"), patch.object(f, "find_spec_json_path", return_value=spec_path), patch.object(f, "find_spec_md_path", return_value=body), patch.object(f.TaskInventory, "load", return_value=SimpleNamespace(by_spec={"fn-1-feature": [{"status": "done"}]})), patch.object(f.subprocess, "run", return_value=probe):
                state = f.judge_route_state({}, "fn-1-feature")
            self.assertEqual(state["status"], "done")
            self.assertEqual((state["tasks_total"], state["tasks_done"]), (1, 1))
            self.assertIs(state["pr_exists"], False)
            route = f.judge_route_lifecycle(state)
            self.assertEqual(route["value"], "host")
            self.assertEqual(route["rule"], "closed spec without observed PR")
            lines = f.judge_route_explain({"available": True, "decision": route}, state)
            presentation = f.JUDGE_ROUTE_PRESENTATION["closed_spec_no_pr"]
            self.assertEqual(lines[0], f"Next: {presentation[0]}")
            self.assertEqual(lines[3], f"Skip/narrow: {presentation[1]}")

    def test_missing_branch_is_nothing_to_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            body = repo / "spec.md"
            body.write_text("Implement feature", encoding="utf-8")
            planned = [{"status": "todo"}, {"status": "done"}]
            for branch, tasks, expected in ((None, planned, "work_planned"), ("", [], "work_no_plan_default")):
                with self.subTest(branch=branch):
                    spec_data = {"title": "Feature", "status": "open", "ready": True, "branch_name": branch}
                    with patch.dict(f.os.environ, {"TYPESAFE_API_KEY": "test-key"}), patch.object(f, "get_config", return_value=True), patch.object(f, "get_repo_root", return_value=repo), patch.object(f, "get_flow_dir", return_value=repo), patch.object(f, "resolve_spec_id_arg", return_value="fn-1-feature"), patch.object(f, "load_json_or_exit", return_value=spec_data), patch.object(f, "normalize_epic", side_effect=lambda x: x), patch.object(f, "find_spec_md_path", return_value=body), patch.object(f.TaskInventory, "load", return_value=SimpleNamespace(by_spec={"fn-1-feature": tasks})), patch.object(f.subprocess, "run") as run:
                        state = f.judge_route_state({}, "fn-1-feature")
                        with patch.object(f, "judge_questions", return_value=[]), patch.object(f, "judge_decide", return_value={}):
                            result = f.judge_evaluate("route", state)
                    run.assert_not_called()
                    self.assertIs(state["pr_exists"], False)
                    self.assertIsNone(state["pr_ref"])
                    self.assertEqual(f.judge_route_lifecycle(state)["value"], expected)
                    self.assertTrue(result["available"])
                    self.assertNotEqual(result.get("reason"), "transport")
                    self.assertNotIn("pr_probe_failed", result)

    def test_scanners_skip_non_utf8_files_and_explain_completes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "README.md").write_bytes("Dev server: `pnpm dev`\nCaf\xe9\n".encode("latin-1"))
            (repo / "AGENTS.md").write_text("Launch command: `make serve`\n", encoding="utf-8")
            (repo / "requirements.txt").write_bytes(b"caf\xe9lib\n")
            (repo / "legacy.py").write_bytes(b"# caf\xe9\nimport sqlite3\n")
            (repo / "app.py").write_text("import requests\n", encoding="utf-8")
            self.assertEqual(f.judge_startable_target(repo), "make serve")
            with patch.object(f, "get_repo_root", return_value=repo), patch.object(f.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="legacy.py\napp.py\n")):
                tokens = f.judge_dependency_tokens({"intent": "`import requests`, `import sqlite3`, `pip install newlib`"})
            self.assertEqual(tokens, ["newlib", "sqlite3"])
            state = repo / "state.json"
            state.write_text(json.dumps({
                "view": "intent", "view_meaning": "An intent at intake", "repo": tmp,
                "intent": "`pip install newlib` for the crash on save", "status": None, "ready": False,
                "no_plan": False, "tasks_total": 0, "tasks_done": 0, "pr_exists": False, "pr_ref": None,
                "startable_target_fact": None,
            }), encoding="utf-8")
            args = SimpleNamespace(preset="route", spec=None, state_file=str(state), explain=True, json=False)
            out = io.StringIO()
            with patch.object(f, "get_repo_root", return_value=repo), patch.object(f, "judge_evaluate", return_value={"available": False, "reason": "no_key"}), patch.object(f.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="legacy.py\napp.py\n")), redirect_stdout(out):
                f.cmd_judge(args)
            self.assertIn("Route: host (jev-unavailable(no_key))", out.getvalue())

    def test_standalone_qa_assembles_target_without_pr_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            body = repo / "spec.md"
            body.write_text("Acceptance: the modal opens.\nDev server: `pnpm dev`\n")
            args = SimpleNamespace(preset="qa-gate", spec="fn-1", state_file=None, explain=False, json=True)
            with patch.object(f, "get_repo_root", return_value=repo), patch.object(f, "get_flow_dir", return_value=repo), patch.object(f, "resolve_spec_id_arg", return_value="fn-1"), patch.object(f, "find_spec_md_path", return_value=body), patch.object(f, "judge_evaluate", return_value={"available": False, "reason": "no_key"}) as evaluate, patch.object(f.subprocess, "run") as process, redirect_stdout(io.StringIO()):
                f.cmd_judge(args)
            self.assertEqual(evaluate.call_args.args[0], "qa-gate")
            self.assertEqual(evaluate.call_args.args[1]["startable_target_fact"], "pnpm dev")
            self.assertEqual(evaluate.call_args.args[1]["acceptance"], body.read_text())
            process.assert_not_called()

    def test_dependency_scan_names_only_unrecorded_mentions(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "package.json").write_text('{"dependencies":{"react":"1"}}')
            (repo / "app.py").write_text("import sqlite3\n")
            with patch.object(f, "get_repo_root", return_value=repo), patch.object(f.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="app.py\n")):
                tokens = f.judge_dependency_tokens({"intent": "Use the react library, `import sqlite3`, run `npm install newlib` and `pip install typesafe`; keep `flowctl` unchanged"})
            self.assertEqual(tokens, ["newlib", "typesafe"])

    def test_presentation_skip_cells_match_matrix(self):
        rows = route_matrix_rows()
        states = {"discovery": "No written direction", "theme": "A theme or direction",
                  "build": "One meaningful idea", "capture_brief": "Existing structured brief",
                  "defect": "A reported defect", "cleanup": "A structural change",
                  "slowness": "A measured slowness", "hillclimb": "One metric to improve",
                  "question": "A read-only question", "fork": "A design or behaviour fork",
                  "tiny": "Tiny, local", "refine": "A valid spec with unresolved",
                  "plan_review": "A spec whose design needs",
                  "work_no_plan_default": "A ready spec with no tasks", "plan": "A ready spec with no tasks",
                  "work_planned": "A spec with an intentional plan",
                  "all_done_make_pr": "A spec whose tasks are all done",
                  "existing_pr_tail": "A spec with an existing PR",
                  "closed_spec_no_pr": "A closed spec with no observed PR"}
        for kind, prefix in states.items():
            self.assertEqual(f.JUDGE_ROUTE_PRESENTATION[kind][1], rows[prefix][3])

    def test_target_and_trimming(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.assertIsNone(f.judge_startable_target(repo, "UI acceptance only"))
            (repo / "README.md").write_text("```sh\npnpm dev\n```", encoding="utf-8")
            self.assertEqual(f.judge_startable_target(repo), "pnpm dev")
            self.assertEqual(f.judge_startable_target(repo, "Deploy URL: https://example.test/app"), "https://example.test/app")
            with patch.object(f, "get_repo_root", return_value=repo):
                state = f.judge_route_state({"view": "brief", "spec_body": "x" * 100001})
            self.assertEqual(len(state["spec_body"]), 100000)
            self.assertTrue(state["spec_body_truncated"])
            self.assertEqual(state["startable_target_fact"], "pnpm dev")

    def test_target_preserves_documented_commands_and_rejects_placeholders(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cases = [
                ("Start command: make dev", "make dev"),
                ("Start command: pnpm dev:web", "pnpm dev:web"),
                ("run `pnpm dev:web` locally", "pnpm dev:web"),
                ("- Launch target: `http://127.0.0.1:<port>` on a port this run owns.", None),
                ("- Start command: `npm run dev -- --port <port> --host 127.0.0.1`.", None),
                ("Launch target: `http://127.0.0.1:8787`.", "http://127.0.0.1:8787"),
            ]
            for text, expected in cases:
                with self.subTest(text=text):
                    self.assertEqual(f.judge_startable_target(repo, text), expected)

    def test_explain_json_keeps_structured_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.json"
            state.write_text(json.dumps({
                "view": "intent", "view_meaning": "An intent at intake", "repo": tmp, "intent": "Fix the crash on save",
                "status": None, "ready": False, "no_plan": False, "tasks_total": 0, "tasks_done": 0,
                "pr_exists": False, "pr_ref": None, "startable_target_fact": None,
            }), encoding="utf-8")
            args = SimpleNamespace(preset="route", spec=None, state_file=str(state), explain=True, json=True)
            out = io.StringIO()
            with patch.object(f, "get_repo_root", return_value=Path(tmp)), patch.object(f, "judge_evaluate", return_value={"available": False, "reason": "no_key"}), redirect_stdout(out):
                f.cmd_judge(args)
            result = json.loads(out.getvalue())
            self.assertFalse(result["available"])
            self.assertEqual(result["reason"], "no_key")
            self.assertEqual(result["explain"][1], "Route: host (jev-unavailable(no_key))")
            self.assertEqual([line.split(":", 1)[0] for line in result["explain"]], ["Next", "Route", "Signal", "Skip/narrow", "Why not the alternatives"])

    def test_explain_uses_same_answers(self):
        result = {"available": True, "decision": {"value": "defect", "candidates": [["defect", .91], ["build", .06], ["tiny", .02]]}, "answers": {"kind": {"confidence": .91}, "reports_defect": {"type": "noul", "noul": .94}, "tiny_one_context_change": {"type": "noul", "noul": .99}}}
        lines = f.judge_route_explain(result, {"view": "intent"})
        self.assertEqual([line.split(":", 1)[0] for line in lines], ["Next", "Route", "Signal", "Skip/narrow", "Why not the alternatives"])
        self.assertIn("reports_defect (jev 0.94)", lines[2])
        self.assertNotIn("tiny_one_context_change", lines[2])
        self.assertIn("build 0.06, tiny 0.02", lines[4])
        unavailable = f.judge_route_explain({"available": False, "reason": "timeout"}, {"view": "intent"})
        self.assertEqual(unavailable[1], "Route: host (jev-unavailable(timeout))")


if __name__ == "__main__":
    unittest.main()
