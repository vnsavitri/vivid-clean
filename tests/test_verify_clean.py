from __future__ import annotations

import struct
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

from vivid_clean.docx import scrub_docx
from vivid_clean.verify import (
    VerificationError,
    diff,
    failing_findings,
    scan,
    scan_invisible,
)

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""
RELATIONSHIPS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""
DOCUMENT = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>{}</w:t></w:r></w:p></w:body></w:document>"""
CORE = """<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:creator>ChatGPT</dc:creator></cp:coreProperties>"""
APP = """<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>pandoc</Application></Properties>"""


def make_docx(path: Path, dirty: bool, application: str = "pandoc") -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("_rels/.rels", RELATIONSHIPS)
        archive.writestr(
            "word/document.xml",
            DOCUMENT.format("Hello\u200b world" if dirty else "Hello world"),
        )
        if dirty:
            archive.writestr("docProps/core.xml", CORE)
            archive.writestr("docProps/app.xml", APP.replace("pandoc", application))


def chunk(name: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + name
        + data
        + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)
    )


class VerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_docx_diff_detects_and_removes_seeded_marks(self) -> None:
        dirty, clean = self.root / "dirty.docx", self.root / "clean.docx"
        make_docx(dirty, True)
        make_docx(clean, False)
        result = diff(dirty, clean)
        self.assertGreaterEqual(len(result["removed"]), 3)
        self.assertFalse(failing_findings(result))

    def test_changed_producer_is_residual(self) -> None:
        original, output = self.root / "original.docx", self.root / "output.docx"
        make_docx(original, True)
        make_docx(output, True, "markitdown")
        result = diff(original, output)
        self.assertTrue(any("was:" in item["detail"] for item in result["residual"]))

    def test_producer_hints_cover_multiple_model_vendors(self) -> None:
        for index, producer in enumerate(
            (
                "Anthropic Claude",
                "OpenAI Codex",
                "Google Gemini",
                "Microsoft Copilot",
                "xAI Grok",
                "Kimi",
                "Qwen",
                "DeepSeek",
                "Mistral",
            )
        ):
            with self.subTest(producer=producer):
                path = self.root / f"producer-{index}.docx"
                make_docx(path, True, producer)
                hints = [
                    item for item in scan(path) if item["category"] == "producer_hint"
                ]
                self.assertTrue(hints)
                self.assertEqual(hints[0]["severity"], "high")

    def test_scrubber_removes_properties_and_keeps_body(self) -> None:
        path = self.root / "document.docx"
        make_docx(path, True)
        before = zipfile.ZipFile(path).read("word/document.xml")
        scrub_docx(path)
        with zipfile.ZipFile(path) as archive:
            self.assertNotIn("docProps/core.xml", archive.namelist())
            self.assertNotIn("docProps/app.xml", archive.namelist())
            self.assertEqual(before, archive.read("word/document.xml"))
            self.assertNotIn(b"docProps", archive.read("_rels/.rels"))
            self.assertNotIn(b"docProps", archive.read("[Content_Types].xml"))

    def test_empty_comments_part_is_not_a_finding(self) -> None:
        path = self.root / "document.docx"
        make_docx(path, False)
        with zipfile.ZipFile(path, "a") as archive:
            archive.writestr(
                "word/comments.xml",
                '<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>',
            )
        self.assertFalse(any(item["category"] == "comments" for item in scan(path)))

    def test_contextual_unicode_preserves_real_language_and_emoji(self) -> None:
        text = "Family 👩‍👩‍👧‍👦, Persian می‌روم, Devanagari क्‍ष, emoji ❤️, العربية \u200f\u202bمرحبا\u202c, flag 🏴\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f"
        self.assertFalse(
            [
                item
                for item in scan_invisible(text, "text")
                if item["severity"] == "high"
            ]
        )

    def test_contextual_unicode_flags_out_of_context_controls(self) -> None:
        findings = scan_invisible(
            "plain\u200dtext \ufe0f watermark\u2060 \u200f\U000e0061\U000e007f", "text"
        )
        self.assertGreaterEqual(
            len([item for item in findings if item["severity"] == "high"]), 3
        )

    def test_typographic_spaces_are_low_severity(self) -> None:
        findings = scan_invisible("10\u00a0000 € and 中文\u3000空格", "text")
        self.assertTrue(findings)
        self.assertTrue(all(item["severity"] == "low" for item in findings))

    def test_png_metadata_and_truncation(self) -> None:
        dirty = self.root / "dirty.png"
        dirty.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + chunk(b"caBX", b"c2pa")
            + chunk(b"IEND", b"")
        )
        self.assertTrue(
            any(item["category"] == "c2pa_provenance" for item in scan(dirty))
        )
        truncated = self.root / "bad.png"
        truncated.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I4s", 99, b"tEXt"))
        with self.assertRaises(VerificationError):
            scan(truncated)

    def test_provenance_words_in_plain_text_are_not_metadata(self) -> None:
        path = self.root / "report.md"
        path.write_text("This report discusses C2PA and JUMBF metadata.")
        self.assertEqual(scan(path), [])

    def test_unknown_binary_is_incomplete(self) -> None:
        path = self.root / "unknown.bin"
        path.write_bytes(b"\x00\x01\xff\x02")
        with self.assertRaises(VerificationError):
            scan(path)

    def test_webp_metadata_and_truncation(self) -> None:
        path = self.root / "dirty.webp"
        payload = b"test"
        body = b"WEBP" + b"EXIF" + struct.pack("<I", len(payload)) + payload
        path.write_bytes(b"RIFF" + struct.pack("<I", len(body)) + body)
        self.assertTrue(
            any(item["category"] == "image_metadata" for item in scan(path))
        )
        path.write_bytes(b"RIFF" + struct.pack("<I", 99) + body)
        with self.assertRaises(VerificationError):
            scan(path)

    def test_truncated_pdf_is_incomplete(self) -> None:
        path = self.root / "bad.pdf"
        path.write_bytes(b"%PDF-1.4\n1 0 obj")
        with self.assertRaises(VerificationError):
            scan(path)


if __name__ == "__main__":
    unittest.main()
