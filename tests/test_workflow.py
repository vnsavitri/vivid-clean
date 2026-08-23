from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from vivid_clean.workflow import WorkflowError, _default_output, finish, prepare

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"


def make_styled_docx(path: Path) -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
    relationships = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    document_relationships = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://example.com" TargetMode="External"/>
</Relationships>"""
    document = f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="{W}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:rPr><w:b/></w:rPr><w:t>Original heading</w:t></w:r></w:p>
    <w:p><w:r><w:t>Keep this </w:t></w:r><w:hyperlink r:id="rId5"><w:r><w:rPr><w:u w:val="single"/></w:rPr><w:t>linked phrase</w:t></w:r></w:hyperlink></w:p>
    <w:tbl><w:tr><w:tc><w:p><w:r><w:t>Table value 42</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
  </w:body>
</w:document>"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("word/document.xml", document)
        archive.writestr("word/_rels/document.xml.rels", document_relationships)


def make_styled_pptx(path: Path) -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
<Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
<Override PartName="/ppt/notesSlides/notesSlide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>
</Types>"""
    root_relationships = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>"""
    presentation = f"""<p:presentation xmlns:p="{P}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst></p:presentation>"""
    slide = f"""<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree><p:sp><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr b="1"/><a:t>AAAA</a:t></a:r><a:r><a:rPr i="1"/><a:t>BBBB</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>"""
    notes = f"""<?xml version="1.0" encoding="UTF-8"?>
<p:notes xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree><p:sp><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>Speaker note</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:notes>"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_relationships)
        archive.writestr("ppt/presentation.xml", presentation)
        archive.writestr("ppt/slides/slide1.xml", slide)
        archive.writestr("ppt/notesSlides/notesSlide1.xml", notes)


class CopyingClient:
    def clean(self, source: Path) -> tuple[bytes, dict]:
        return source.read_bytes(), {"kind": "docx", "actions": []}


@contextmanager
def copying_client(_repo: Path):
    yield (
        CopyingClient(),
        {
            "name": "test-cleaner",
            "ref": "fixture",
            "capabilities": {"formats": ["docx", "pptx", "text"]},
        },
    )


class WorkflowSafetyTests(unittest.TestCase):
    def test_default_output_keeps_source_directory(self) -> None:
        source = Path("/tmp/Draft.docx")
        self.assertEqual(
            _default_output(source, "_reviewed"), Path("/tmp/Draft_reviewed.docx")
        )

    def test_pdf_default_keeps_source_format(self) -> None:
        self.assertEqual(
            _default_output(Path("/tmp/Paper.pdf"), "_vivid"),
            Path("/tmp/Paper_vivid.pdf"),
        )

    def test_suffix_cannot_escape_the_source_directory(self) -> None:
        for suffix in ("", "../elsewhere", "folder/name", "folder\\name"):
            with self.assertRaises(WorkflowError):
                _default_output(Path("/tmp/Draft.docx"), suffix)

    def test_docx_text_is_edited_without_rebuilding_the_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "Draft.docx"
            make_styled_docx(source)
            with (
                patch("vivid_clean.workflow.managed_watermarks_client", copying_client),
                patch("vivid_clean.workflow.find_tool", return_value=None),
            ):
                session = prepare(source, root)
                draft = session / "draft.md"
                draft.write_text(
                    draft.read_text(encoding="utf-8").replace(
                        "Original heading", "A revised heading"
                    ),
                    encoding="utf-8",
                )
                output, _report, status = finish(session, "_reviewed", None, None)

            self.assertEqual(status, "checks_passed")
            with zipfile.ZipFile(source) as before, zipfile.ZipFile(output) as after:
                self.assertEqual(set(before.namelist()), set(after.namelist()))
                self.assertEqual(
                    before.read("word/_rels/document.xml.rels"),
                    after.read("word/_rels/document.xml.rels"),
                )
                before_xml = ET.fromstring(before.read("word/document.xml"))
                after_xml = ET.fromstring(after.read("word/document.xml"))
                for query in (".//w:p", ".//w:r", ".//w:tbl", ".//w:hyperlink"):
                    self.assertEqual(
                        len(before_xml.findall(query, {"w": W})),
                        len(after_xml.findall(query, {"w": W})),
                    )
                self.assertIsNotNone(after_xml.find(".//w:b", {"w": W}))
                output_text = "".join(
                    node.text or "" for node in after_xml.findall(".//w:t", {"w": W})
                )
                self.assertIn("A revised heading", output_text)
                self.assertIn("Table value 42", output_text)

    def test_pptx_keeps_styled_runs_and_speaker_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "Slides.pptx"
            make_styled_pptx(source)
            with patch(
                "vivid_clean.workflow.managed_watermarks_client", copying_client
            ):
                session = prepare(source, root)
                draft = session / "draft.md"
                draft.write_text(
                    draft.read_text(encoding="utf-8")
                    .replace("AAAABBBB", "ZZZZYYYY")
                    .replace("Speaker note", "Revised speaker note"),
                    encoding="utf-8",
                )
                output, _report, status = finish(session, "_reviewed", None, None)

            self.assertEqual(status, "checks_passed")
            with zipfile.ZipFile(source) as before, zipfile.ZipFile(output) as after:
                self.assertEqual(set(before.namelist()), set(after.namelist()))
                slide = ET.fromstring(after.read("ppt/slides/slide1.xml"))
                runs = slide.findall(".//a:r", {"a": A})
                self.assertEqual(len(runs), 2)
                self.assertTrue(
                    all(
                        "".join(node.text or "" for node in run.iter(f"{{{A}}}t"))
                        for run in runs
                    )
                )
                self.assertEqual(runs[0].find("a:rPr", {"a": A}).get("b"), "1")
                self.assertEqual(runs[1].find("a:rPr", {"a": A}).get("i"), "1")
                notes = ET.fromstring(after.read("ppt/notesSlides/notesSlide1.xml"))
                note_text = "".join(
                    node.text or "" for node in notes.findall(".//a:t", {"a": A})
                )
                self.assertIn("Revised speaker note", note_text)

    def test_finish_refuses_a_changed_protected_number(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "Draft.docx"
            make_styled_docx(source)
            with patch(
                "vivid_clean.workflow.managed_watermarks_client", copying_client
            ):
                session = prepare(source, root)
                draft = session / "draft.md"
                draft.write_text(
                    draft.read_text(encoding="utf-8").replace(
                        "Table value 42", "Table value 43"
                    ),
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(WorkflowError, "protected values changed"):
                    finish(session, "_reviewed", None, None)

            report = root / "Draft_reviewed.docx.vivid-clean-report.md"
            self.assertTrue(report.is_file())
            self.assertIn("incomplete", report.read_text(encoding="utf-8"))
            self.assertTrue(session.is_dir())

    def test_json_report_keeps_engine_evidence_and_scoped_channels(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "Draft.docx"
            make_styled_docx(source)
            json_report = root / "report.json"
            with patch(
                "vivid_clean.workflow.managed_watermarks_client", copying_client
            ):
                session = prepare(source, root)
                _output, _report, status = finish(
                    session,
                    "_reviewed",
                    None,
                    json_report,
                    "manual edit",
                    "human",
                    "voice-preserving",
                )

            self.assertEqual(status, "checks_passed")
            record = __import__("json").loads(json_report.read_text(encoding="utf-8"))
            self.assertEqual(record["engine"]["report"]["kind"], "docx")
            self.assertEqual(
                record["engine"]["capabilities"]["formats"],
                ["docx", "pptx", "text"],
            )
            self.assertEqual(
                record["channels"]["package_structure"]["status"], "passed"
            )
            self.assertEqual(record["channels"]["protected_values"]["status"], "passed")
            self.assertEqual(record["channels"]["statistical"]["status"], "not_checked")
            self.assertEqual(record["channels"]["proprietary"]["status"], "not_checked")
            self.assertEqual(record["writing_pass"]["backend"], "manual edit")
            self.assertEqual(record["writing_pass"]["backend_kind"], "human")
            self.assertEqual(
                record["writing_pass"]["rewrite_evidence"]["status"], "insufficient"
            )

    def test_finish_refuses_hosted_statistical_rewrite_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "Draft.docx"
            make_styled_docx(source)
            with patch(
                "vivid_clean.workflow.managed_watermarks_client", copying_client
            ):
                session = prepare(source, root)
                with self.assertRaisesRegex(
                    WorkflowError, "origin or unknown hosted model"
                ):
                    finish(
                        session,
                        "_reviewed",
                        None,
                        None,
                        "Claude",
                        "hosted",
                        "statistical-risk-reduction",
                    )

            report = root / "Draft_reviewed.docx.vivid-clean-report.md"
            report_text = report.read_text(encoding="utf-8")
            self.assertIn("Backend: `Claude`", report_text)
            self.assertIn("Result: **incomplete**", report_text)
            self.assertTrue(session.is_dir())

    def test_cleanup_removes_only_valid_vivid_clean_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            session = root / "vivid-clean-owned-session"
            session.mkdir()
            (session / "session.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "/tmp/source.docx",
                        "cleaned": str(session / "cleaned.docx"),
                    }
                ),
                encoding="utf-8",
            )
            lookalike = root / "vivid-clean-personal-notes"
            lookalike.mkdir()
            (lookalike / "keep.txt").write_text("keep", encoding="utf-8")
            environment = os.environ.copy()
            environment["TMPDIR"] = str(root)
            environment["PYTHONPATH"] = str(Path(__file__).parents[1] / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "vivid_clean.cli",
                    "cleanup",
                    "--older-than",
                    "0",
                    "--json",
                ],
                cwd=Path(__file__).parents[1],
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            expected_session = str(session.resolve())
            self.assertFalse(session.exists())
            self.assertTrue(lookalike.is_dir())
            self.assertEqual(json.loads(result.stdout)["removed"], [expected_session])
