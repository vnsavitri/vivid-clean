#!/usr/bin/env python3
"""Remove DOCX properties without changing the document body."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vivid_clean.docx import scrub_docx

parser = argparse.ArgumentParser()
parser.add_argument("source")
parser.add_argument("destination", nargs="?")
args = parser.parse_args()
scrub_docx(args.source, args.destination)
