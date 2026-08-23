from __future__ import annotations

import os
import subprocess
import tempfile
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
        ):
            self.assertIn(location, self.script)
        self.assertIn(
            'CODEX_SKILLS_HOME="${CODEX_HOME:-${INSTALL_HOME}/.codex}/skills"',
            self.script,
        )

    def test_installer_uses_repo_virtualenv(self) -> None:
        self.assertIn('VENV_DIR="${REPO_DIR}/.venv"', self.script)
        self.assertNotIn("pip3 install", self.script)
        self.assertNotIn("[documents]", self.script)
        self.assertNotIn("check_pandoc", self.script)

    def test_skills_only_install_honours_custom_codex_home(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            user_home = root / "user"
            codex_home = root / "custom-codex"
            old_install = codex_home / "skills" / "vivid-clean"
            old_install.mkdir(parents=True)
            (old_install / "stale.txt").write_text("old", encoding="utf-8")
            environment = os.environ.copy()
            environment["VIVID_CLEAN_USER_HOME"] = str(user_home)
            environment["CODEX_HOME"] = str(codex_home)
            result = subprocess.run(
                [
                    "bash",
                    str(Path(__file__).parents[1] / "install.sh"),
                    "--skills-only",
                ],
                env=environment,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(
                (codex_home / "skills" / "vivid-clean" / "SKILL.md").is_file()
            )
            self.assertFalse((old_install / "stale.txt").exists())
            backups = list((codex_home / "skills").glob("vivid-clean.backup.*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(
                (backups[0] / "stale.txt").read_text(encoding="utf-8"), "old"
            )
            self.assertFalse((user_home / ".codex" / "skills" / "vivid-clean").exists())
