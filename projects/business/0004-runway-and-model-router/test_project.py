"""표준 시험: (1) 스크립트가 직접 실행되어 '성공'을 출력하는지 (2) 웹 서버와 JSON API가 동작하는지."""
import json
import os
import subprocess
import sys
import threading
import unittest
import urllib.request
from http.server import HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
CFG = json.load(open(os.path.join(HERE, "project.json"), encoding="utf-8"))


class ProjectTest(unittest.TestCase):
    def test_script_runs(self):
        r = subprocess.run([sys.executable, CFG["script"]], cwd=HERE, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("성공", r.stdout)

    def test_api_function(self):
        import importlib
        mod, fn = CFG["entry"].split(":")
        result = getattr(importlib.import_module(mod), fn)({})
        self.assertTrue(result.get("ok"), result)

    def test_http(self):
        import server
        httpd = HTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{httpd.server_port}"
        try:
            self.assertTrue(json.load(urllib.request.urlopen(base + "/health"))["ok"])
            self.assertTrue(json.load(urllib.request.urlopen(base + "/api/run"))["ok"])
            self.assertIn("<button", urllib.request.urlopen(base + "/").read().decode("utf-8"))
        finally:
            httpd.shutdown()


if __name__ == "__main__":
    unittest.main()
