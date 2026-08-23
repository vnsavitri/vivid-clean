from __future__ import annotations

import unittest
from pathlib import Path

from vivid_clean.workflow import WorkflowError, _default_output


class WorkflowSafetyTests(unittest.TestCase):
    def test_default_output_keeps_source_directory(self) -> None:
        source = Path("/tmp/Draft.docx")
        self.assertEqual(
            _default_output(source, "_reviewed"), Path("/tmp/Draft_reviewed.docx")
        )

    def test_pdf_default_is_docx(self) -> None:
        self.assertEqual(
            _default_output(Path("/tmp/Paper.pdf"), "_vivid"),
            Path("/tmp/Paper_vivid.docx"),
        )

    def test_suffix_cannot_escape_the_source_directory(self) -> None:
        for suffix in ("", "../elsewhere", "folder/name", "folder\\name"):
            with self.assertRaises(WorkflowError):
                _default_output(Path("/tmp/Draft.docx"), suffix)
