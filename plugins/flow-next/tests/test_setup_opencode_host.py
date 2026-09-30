"""OpenCode-host setup detection, run as the executable Step-0 bash.

PLUGIN_ROOT carrying .flow-next-opencode-manifest classifies as opencode;
GROK_AGENT still wins; absence of the file is not an OpenCode signal.

Run:
    cd plugins/flow-next/tests && python3 -m unittest test_setup_opencode_host -q
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve()
PLUGIN = HERE.parent.parent
WORKFLOW = PLUGIN / "skills" / "flow-next-setup" / "workflow.md"

HOST_ENV_KEYS = (
    "DROID_PLUGIN_ROOT",
    "CLAUDE_PLUGIN_ROOT",
    "CURSOR_AGENT",
    "GROK_AGENT",
    "CLAUDECODE",
    "CURSOR_TRACE_ID",
    "CODEX_HOME",
)

_BASH = shutil.which("bash")

_STEP0_HEADING = re.compile(
    r"(?m)^## Step 0: Resolve plugin path and detect platform\s*$"
)
_FIRST_BASH_FENCE = re.compile(r"(?ms)^```bash\n(.*?)(?:^```\s*$)", re.MULTILINE)

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")


def _extract_step0_detection_bash(text: str) -> str:
    heads = list(_STEP0_HEADING.finditer(text))
    if len(heads) != 1:
        raise AssertionError(
            f"expected exactly one Step-0 heading, found {len(heads)}"
        )
    after = text[heads[0].end() :]
    next_h2 = re.search(r"(?m)^## ", after)
    step0 = after[: next_h2.start()] if next_h2 else after
    fences = list(_FIRST_BASH_FENCE.finditer(step0))
    if len(fences) != 1:
        raise AssertionError(
            f"expected exactly one ```bash fence under Step 0, found {len(fences)}"
        )
    return fences[0].group(1)


@unittest.skipUnless(_BASH, "bash required to execute the Step-0 detection fence")
class TestOpencodeDetectionExecutable(unittest.TestCase):
    """Run the actual canonical Step-0 bash under OpenCode fixtures."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.bash = _extract_step0_detection_bash(_read(WORKFLOW))

    def _run(self, plugin_root: Path, home: Path, **host_env: str) -> str:
        env = {
            k: v for k, v in os.environ.items() if k not in HOST_ENV_KEYS
        }
        env["HOME"] = str(home)
        env["PLUGIN_ROOT"] = str(plugin_root)
        for k in HOST_ENV_KEYS:
            env.pop(k, None)
        env.update(host_env)
        script = f"set -eu\n{self.bash}\nprintf '%s\\n' \"$PLATFORM\"\n"
        proc = subprocess.run(
            [_BASH, "-c", script],
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode != 0:
            raise AssertionError(
                f"detection bash failed (rc={proc.returncode}):\n"
                f"stdout={proc.stdout!r}\nstderr={proc.stderr!r}"
            )
        return proc.stdout.strip()

    def test_manifest_at_plugin_root_is_opencode(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            root = home / "opencode"
            root.mkdir()
            (root / ".flow-next-opencode-manifest").write_text(
                "skills/flow-next-setup/SKILL.md\n", encoding="utf-8"
            )
            self.assertEqual(self._run(root, home), "opencode")

    def test_plain_plugin_root_without_manifest_is_codex(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            root = home / "plugin"
            root.mkdir()
            self.assertEqual(self._run(root, home), "codex")

    def test_grok_wins_over_opencode_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            root = home / "opencode"
            root.mkdir()
            (root / ".flow-next-opencode-manifest").write_text(
                "skills/flow-next-setup/SKILL.md\n", encoding="utf-8"
            )
            self.assertEqual(
                self._run(root, home, GROK_AGENT="1"), "grok"
            )

    def test_inherited_claudecode_without_claude_manifest_is_opencode(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            root = home / "opencode"
            root.mkdir()
            (root / ".flow-next-opencode-manifest").write_text(
                "skills/flow-next-setup/SKILL.md\n", encoding="utf-8"
            )
            self.assertEqual(
                self._run(root, home, CLAUDECODE="1"), "opencode"
            )


if __name__ == "__main__":
    unittest.main()
