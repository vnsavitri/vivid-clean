from __future__ import annotations

import unittest
from pathlib import Path


class InstallerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = (Path(__file__).parents[1] / "install.sh").read_text(
            encoding="utf-8"
        )

    def test_upstream_refs_are_exact_commits(self) -> None:
        self.assertIn(
            'WATERMARKS_REMOVER_REF="104aacd212d7a262c32bd7f1f4aa380c26a5d4b5"',
            self.script,
        )
        self.assertIn(
            'ANTHROPIES_REF="6d1dba6870b9a01a1c088e18d8eed44366bbbe36"', self.script
        )
        self.assertNotIn("git pull", self.script)

    def test_supported_skill_locations_are_installed(self) -> None:
        for location in (
            ".agents/skills",
            ".cursor/skills",
            ".claude/skills",
            ".codex/skills",
        ):
            self.assertIn(location, self.script)

    def test_installer_uses_repo_virtualenv(self) -> None:
        self.assertIn('VENV_DIR="${REPO_DIR}/.venv"', self.script)
        self.assertNotIn("pip3 install", self.script)
