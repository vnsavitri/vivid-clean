#!/usr/bin/env python3
"""Compatibility entry point for vivid-clean verification."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vivid_clean.cli import main

if __name__ == "__main__":
    arguments = sys.argv[1:]
    if arguments and arguments[0] == "diff":
        arguments = ["verify", *arguments[1:]]
    elif arguments and arguments[0] == "scan":
        arguments = ["scan", *arguments[1:]]
    else:
        arguments = ["verify", *arguments]
    raise SystemExit(main(arguments))
