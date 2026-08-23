from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from vivid_clean import __version__
from vivid_clean.bootstrap import setup_runtime
from vivid_clean.runtime import data_root, runtime_root


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
        bootstrap = (
            Path(__file__).parents[1] / "src/vivid_clean/bootstrap.py"
        ).read_text(encoding="utf-8")
        workflow = (
            Path(__file__).parents[1] / "src/vivid_clean/workflow.py"
        ).read_text(encoding="utf-8")
        for ref in (
            "104aacd212d7a262c32bd7f1f4aa380c26a5d4b5",
            "6d1dba6870b9a01a1c088e18d8eed44366bbbe36",
        ):
            self.assertIn(ref, workflow)
        self.assertIn("WATERMARKS_REMOVER_REF", bootstrap)
        self.assertIn("ANTHROPIES_REF", bootstrap)

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
            self.assertEqual(
                list((codex_home / "skills").glob("vivid-clean.backup.*")), []
            )
            state_backups = user_home / ".local" / "state" / "vivid-clean"
            stale_copies = list(state_backups.rglob("stale.txt"))
            self.assertEqual(len(stale_copies), 1)
            self.assertEqual(stale_copies[0].read_text(encoding="utf-8"), "old")
            self.assertFalse((user_home / ".codex" / "skills" / "vivid-clean").exists())

    def test_skills_only_install_moves_discoverable_legacy_backups(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            user_home = root / "user"
            skills_home = user_home / ".agents" / "skills"
            legacy_backup = skills_home / "vivid-clean.backup.20260823T000000Z.1"
            legacy_backup.mkdir(parents=True)
            (legacy_backup / "SKILL.md").write_text(
                "---\nname: vivid-clean\n---\n", encoding="utf-8"
            )
            environment = os.environ.copy()
            environment["VIVID_CLEAN_USER_HOME"] = str(user_home)
            environment["CODEX_HOME"] = str(user_home / ".codex")
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
            discoverable = list(skills_home.glob("vivid-clean*/SKILL.md"))
            self.assertEqual(discoverable, [skills_home / "vivid-clean" / "SKILL.md"])
            migrated = list(
                (user_home / ".local" / "state" / "vivid-clean").rglob("SKILL.md")
            )
            self.assertEqual(len(migrated), 1)

    def test_skill_backup_state_directory_precedence(self) -> None:
        cases = (
            ("xdg", False),
            ("vivid-clean", True),
        )
        for expected_name, use_project_override in cases:
            with (
                self.subTest(expected_name=expected_name),
                tempfile.TemporaryDirectory() as temp,
            ):
                root = Path(temp)
                user_home = root / "user"
                codex_home = root / "codex"
                old_install = codex_home / "skills" / "vivid-clean"
                old_install.mkdir(parents=True)
                (old_install / "stale.txt").write_text("old", encoding="utf-8")
                xdg_state = root / "xdg"
                project_state = root / "vivid-clean"
                environment = os.environ.copy()
                environment["VIVID_CLEAN_USER_HOME"] = str(user_home)
                environment["CODEX_HOME"] = str(codex_home)
                environment["XDG_STATE_HOME"] = str(xdg_state)
                if use_project_override:
                    environment["VIVID_CLEAN_STATE_HOME"] = str(project_state)
                else:
                    environment.pop("VIVID_CLEAN_STATE_HOME", None)

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
                expected_root = project_state if use_project_override else xdg_state
                self.assertEqual(len(list(expected_root.rglob("stale.txt"))), 1)
                other_root = xdg_state if use_project_override else project_state
                self.assertEqual(list(other_root.rglob("stale.txt")), [])

    def test_release_version_is_consistent(self) -> None:
        root = Path(__file__).parents[1]
        metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        expected = metadata["project"]["version"]

        self.assertEqual(__version__, expected)
        self.assertIn(
            f"## {expected} - 2026-08-23", (root / "CHANGELOG.md").read_text()
        )
        result = subprocess.run(
            [sys.executable, "-m", "vivid_clean.cli", "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), f"vivid-clean {expected}")

    def test_packaged_runtime_uses_xdg_data_home(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            xdg_data = Path(temp) / "data"
            with patch.dict(
                os.environ,
                {"XDG_DATA_HOME": str(xdg_data)},
                clear=False,
            ):
                os.environ.pop("VIVID_CLEAN_DATA_HOME", None)
                self.assertEqual(data_root(), (xdg_data / "vivid-clean").resolve())

    def test_explicit_runtime_home_takes_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            expected = Path(temp) / "runtime"
            with patch.dict(
                os.environ,
                {"VIVID_CLEAN_DATA_HOME": str(expected)},
                clear=False,
            ):
                self.assertEqual(runtime_root(), expected.resolve())

    def test_packaged_setup_can_install_only_the_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            user_home = root / "user"
            codex_home = root / "codex"
            environment = {
                "VIVID_CLEAN_USER_HOME": str(user_home),
                "VIVID_CLEAN_DATA_HOME": str(root / "runtime"),
                "VIVID_CLEAN_STATE_HOME": str(root / "state"),
                "CODEX_HOME": str(codex_home),
            }
            with patch.dict(os.environ, environment, clear=False):
                result = setup_runtime(skills_only=True)

            self.assertEqual(result["watermarks_remover"], "skipped")
            for target in (
                user_home / ".agents" / "skills" / "vivid-clean",
                user_home / ".cursor" / "skills" / "vivid-clean",
                user_home / ".claude" / "skills" / "vivid-clean",
                codex_home / "skills" / "vivid-clean",
            ):
                self.assertTrue((target / "SKILL.md").is_file())
                self.assertTrue((target / "PROMPT.md").is_file())
