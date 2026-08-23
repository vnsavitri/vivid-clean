"""Resolve vivid-clean's source checkout and per-user runtime files."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def source_root() -> Path:
    """Return the repository root when running from a source checkout."""
    return Path(__file__).resolve().parents[2]


def data_root() -> Path:
    """Return the writable directory used by packaged installations."""
    override = os.environ.get("VIVID_CLEAN_DATA_HOME")
    if override:
        return Path(override).expanduser().resolve()
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        return Path(xdg_data).expanduser().resolve() / "vivid-clean"
    return Path.home() / ".local" / "share" / "vivid-clean"


def runtime_root() -> Path:
    """Use an explicit data home, a source checkout, or the user data directory."""
    if os.environ.get("VIVID_CLEAN_DATA_HOME"):
        return data_root()
    root = source_root()
    if (root / "install.sh").is_file():
        return root
    return data_root()


def skill_source_root() -> Path:
    """Find the skill files in a checkout or an installed wheel."""
    root = source_root()
    if (root / "SKILL.md").is_file() and (root / "PROMPT.md").is_file():
        return root
    packaged = Path(sys.prefix) / "share" / "vivid-clean"
    if (packaged / "SKILL.md").is_file() and (packaged / "PROMPT.md").is_file():
        return packaged
    raise FileNotFoundError("the packaged vivid-clean skill files weren't found")
