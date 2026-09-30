"""The judge's HTTPS connection honours HTTPS_PROXY / NO_PROXY (http.client ignores them on its own)."""
import importlib.util
import os
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "flowctl.py"
_spec = importlib.util.spec_from_file_location("flowctl_judge_proxy", SCRIPT)
flowctl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(flowctl)

PROXY_VARS = ("HTTPS_PROXY", "https_proxy", "NO_PROXY", "no_proxy")


class JudgeProxyTests(unittest.TestCase):
    def connect(self, **env):
        clean = {k: v for k, v in os.environ.items() if k not in PROXY_VARS}
        with mock.patch.dict(os.environ, {**clean, **env}, clear=True):
            return flowctl.judge_https_connection("api.typesafe.ai", 10)

    def test_direct_without_proxy(self):
        c = self.connect()
        self.assertEqual((c.host, c.port), ("api.typesafe.ai", 443))
        self.assertIsNone(c._tunnel_host)

    def test_tunnels_through_https_proxy(self):
        c = self.connect(HTTPS_PROXY="http://127.0.0.1:3128")
        self.assertEqual((c.host, c.port), ("127.0.0.1", 3128))
        self.assertEqual((c._tunnel_host, c._tunnel_port), ("api.typesafe.ai", 443))

    def test_proxy_credentials_become_proxy_authorization(self):
        c = self.connect(https_proxy="http://user:p%40ss@proxy.local:8080")
        self.assertEqual(c.host, "proxy.local")
        self.assertTrue(c._tunnel_headers["Proxy-Authorization"].startswith("Basic "))

    def test_no_proxy_excludes_the_host(self):
        for entry in (".typesafe.ai", "typesafe.ai", "api.typesafe.ai", "*"):
            with self.subTest(entry=entry):
                c = self.connect(HTTPS_PROXY="http://127.0.0.1:3128", NO_PROXY=f"localhost,{entry}")
                self.assertEqual(c.host, "api.typesafe.ai")
                self.assertIsNone(c._tunnel_host)


if __name__ == "__main__":
    unittest.main()
