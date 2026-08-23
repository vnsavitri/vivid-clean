"""Small contract check against the exact upstream commit used by CI."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from vivid_clean.service import ServiceError, WatermarksClient


@unittest.skipUnless(
    os.environ.get("WATERMARKS_SERVICE_URL"), "live service URL wasn't provided"
)
class LiveServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = WatermarksClient(os.environ["WATERMARKS_SERVICE_URL"])

    def test_health_and_capabilities_contract(self) -> None:
        self.assertTrue(self.client.health()["ok"])
        capabilities = self.client.capabilities()
        self.assertIn("tools", capabilities)
        self.assertIn("text_detectors", capabilities)

    def test_clean_removes_seeded_invisible_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "seed.txt"
            source.write_text("hello\u200b world", encoding="utf-8")
            cleaned, report = self.client.clean(source)
        self.assertEqual(cleaned.decode("utf-8"), "hello world")
        self.assertEqual(report["kind"], "text")

    def test_corrupt_container_is_not_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "broken.docx"
            source.write_bytes(b"PK\x03\x04truncated")
            with self.assertRaises(ServiceError):
                self.client.clean(source)


if __name__ == "__main__":
    unittest.main()
