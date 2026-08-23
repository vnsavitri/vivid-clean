from __future__ import annotations

import base64
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import ClassVar

from vivid_clean.service import ServiceError, WatermarksClient


class Handler(BaseHTTPRequestHandler):
    response: ClassVar[dict[str, object]] = {"ok": True}
    status = 200

    def do_GET(self) -> None:
        self._send()

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        self._send()

    def _send(self) -> None:
        data = json.dumps(type(self).response).encode()
        self.send_response(type(self).status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_args) -> None:
        pass


class ServiceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.client = WatermarksClient(f"http://127.0.0.1:{cls.server.server_port}")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self) -> None:
        Handler.status = 200
        Handler.response = {"ok": True}

    def test_valid_clean_contract(self) -> None:
        with TemporaryDirectory() as temp:
            source = Path(temp) / "a.txt"
            source.write_text("hello")
            Handler.response = {
                "ok": True,
                "kind": "text",
                "cleaned": base64.b64encode(b"hello").decode(),
                "report": {"removed": 0},
            }
            cleaned, report = self.client.clean(source)
        self.assertEqual(cleaned, b"hello")
        self.assertEqual(report["kind"], "text")

    def test_error_payload_is_never_success(self) -> None:
        Handler.response = {"ok": False, "error": "detector failed"}
        with self.assertRaises(ServiceError):
            self.client.health()

    def test_missing_report_empty_and_invalid_base64_fail(self) -> None:
        with TemporaryDirectory() as temp:
            source = Path(temp) / "a.txt"
            source.write_text("hello")
            for response in (
                {"ok": True, "cleaned": "", "report": {}},
                {"ok": True, "cleaned": "%%%", "report": {}},
                {"ok": True, "cleaned": base64.b64encode(b"hello").decode()},
            ):
                Handler.response = response
                with self.assertRaises(ServiceError):
                    self.client.clean(source)

    def test_http_failure_is_never_success(self) -> None:
        Handler.status = 500
        Handler.response = {"ok": False, "error": "partial evidence"}
        with self.assertRaises(ServiceError):
            self.client.health()

    def test_remote_service_urls_are_rejected(self) -> None:
        for url in (
            "https://example.com",
            "http://192.0.2.1:8765",
            "file:///tmp/service",
        ):
            with self.assertRaises(ServiceError):
                WatermarksClient(url)


if __name__ == "__main__":
    unittest.main()
