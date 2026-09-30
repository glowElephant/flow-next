"""The RP plan-review setup fence stops at the cap and finalizes a failed setup."""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "flow-next"


def bash_fences(text: str) -> list[str]:
    return re.findall(r"```bash\n(.*?)```", text, flags=re.DOTALL)


class RepoPromptSetupWorkflowContractTest(unittest.TestCase):

    @unittest.skipIf(
        os.name == "nt",
        "nested bash -c exit propagation is covered by the Unix matrices",
    )
    def test_plan_setup_fence_stops_at_cap_and_finalizes_setup_failure(self) -> None:
        path = (
            PLUGIN_ROOT
            / "skills/flow-next-plan-review/workflow-rp.md"
        )
        fence = next(
            block for block in bash_fences(path.read_text(encoding="utf-8"))
            if "rp setup-review" in block and "--response-type review" in block
        ).replace("<spec-id>", "fn-1-demo").replace("<suffix>", "test")
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            log = temp / "calls.log"
            stub = temp / "flowctl_stub.py"
            stub.write_text(
                "import json\n"
                "import os\n"
                "import sys\n"
                "args = sys.argv[1:]\n"
                "with open(os.environ['CALL_LOG'], 'a', encoding='utf-8') as handle:\n"
                "    handle.write(' '.join(args) + '\\n')\n"
                "pair = ' '.join(args[:2])\n"
                # The fence probes RP mode before setup. Answer 'ce': the
                # reservation legs this test exists to pin (pre-dispatch
                # increment, and the record that finalizes a failed setup) are
                # the CE path. Classic defers reservation until its final
                # prompt exists, so it would exercise neither.
                "if pair == 'rp mode-probe':\n"
                "    print(json.dumps({'mode': 'ce'}))\n"
                "    raise SystemExit(0)\n"
                "if pair == 'review-rounds increment':\n"
                "    print(json.dumps("
                "{'round': 1, 'cap': 4, 'reservation_id': 'res-1'}))\n"
                "    raise SystemExit(4 if os.environ.get('FAIL_CAP') == '1' else 0)\n"
                "if pair == 'rp setup-review':\n"
                "    if os.environ.get('FAIL_SETUP') == '1':\n"
                "        raise SystemExit(2)\n"
                "    print('RP_MODE=ce W=2 T=ctx CHAT_ID=chat')\n"
                "elif pair == 'review-rounds record':\n"
                "    print(json.dumps({'recorded': True}))\n"
                "elif args[:1] == ['cat']:\n"
                "    print('# Demo spec')\n",
                encoding="utf-8",
            )
            prefix = (
                "FLOWCTL='python flowctl_stub.py'\n"
                "REPO_ROOT=.\n"
                "SPEC_ID=fn-1-demo\n"
                "CALL_LOG=calls.log\n"
                "export CALL_LOG FAIL_CAP FAIL_SETUP\n"
            )
            capped = subprocess.run(
                ["bash", "-c", prefix + fence],
                cwd=temp,
                env={**os.environ, "FAIL_CAP": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(capped.returncode, 4, capped.stderr)
            self.assertNotIn("rp setup-review", log.read_text(encoding="utf-8"))

            log.write_text("", encoding="utf-8")
            failed = subprocess.run(
                ["bash", "-c", prefix + fence],
                cwd=temp,
                env={**os.environ, "FAIL_SETUP": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            calls = log.read_text(encoding="utf-8")
            self.assertEqual(
                failed.returncode,
                2,
                f"stdout={failed.stdout!r} stderr={failed.stderr!r} calls={calls!r}",
            )
            self.assertIn("rp setup-review", calls)
            self.assertIn("review-rounds record", calls)


if __name__ == "__main__":
    unittest.main()
