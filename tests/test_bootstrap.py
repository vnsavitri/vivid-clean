from __future__ import annotations

import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from vivid_clean import bootstrap, cli, runtime
from vivid_clean.workflow import WorkflowError


class BootstrapTests(unittest.TestCase):
    def test_run_reports_process_and_launch_failures(self) -> None:
        failed = subprocess.CompletedProcess(["git"], 2, "", "bad ref")
        with (
            patch("vivid_clean.bootstrap.subprocess.run", return_value=failed),
            self.assertRaisesRegex(WorkflowError, "git failed: bad ref"),
        ):
            bootstrap._run(["git", "fetch"])

        with (
            patch(
                "vivid_clean.bootstrap.subprocess.run",
                side_effect=OSError("missing"),
            ),
            self.assertRaisesRegex(WorkflowError, "couldn't run git: missing"),
        ):
            bootstrap._run(["git", "fetch"])

    def test_checkout_refuses_an_unexpected_origin(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "vendor" / "cleaner"
            (target / ".git").mkdir(parents=True)
            wrong_origin = subprocess.CompletedProcess(
                ["git"], 0, "https://example.com/wrong.git\n", ""
            )
            with (
                patch(
                    "vivid_clean.bootstrap.subprocess.run",
                    return_value=wrong_origin,
                ),
                self.assertRaisesRegex(WorkflowError, "unexpected origin"),
            ):
                bootstrap._checkout_pinned(
                    "cleaner",
                    "https://example.com/right.git",
                    "a" * 40,
                    target.parent,
                )

    def test_checkout_refuses_a_commit_other_than_the_audited_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            vendor = Path(temp) / "vendor"
            target = vendor / "cleaner"
            (target / ".git").mkdir(parents=True)
            expected = "a" * 40
            responses = (
                subprocess.CompletedProcess(
                    ["git"], 0, "https://example.com/cleaner.git\n", ""
                ),
                subprocess.CompletedProcess(["git"], 0, f"{'b' * 40}\n", ""),
            )
            with (
                patch("vivid_clean.bootstrap._run"),
                patch(
                    "vivid_clean.bootstrap.subprocess.run",
                    side_effect=responses,
                ),
                self.assertRaisesRegex(WorkflowError, "audited commit"),
            ):
                bootstrap._checkout_pinned(
                    "cleaner",
                    "https://example.com/cleaner.git",
                    expected,
                    vendor,
                )

    def test_skill_install_replaces_current_and_archives_legacy_copies(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = root / "skills" / "vivid-clean"
            backups = root / "state"
            source.mkdir()
            (source / "SKILL.md").write_text("new skill", encoding="utf-8")
            (source / "PROMPT.md").write_text("new prompt", encoding="utf-8")
            target.mkdir(parents=True)
            (target / "old.txt").write_text("current", encoding="utf-8")
            for number in (1, 2):
                legacy = target.parent / f"vivid-clean.backup.old.{number}"
                legacy.mkdir()
                (legacy / "old.txt").write_text(f"legacy {number}", encoding="utf-8")

            bootstrap._install_skill_copy(source, target, backups)

            self.assertEqual(
                (target / "SKILL.md").read_text(encoding="utf-8"), "new skill"
            )
            self.assertEqual(list(target.parent.glob("vivid-clean.backup.*")), [])
            archived = sorted(
                path.read_text(encoding="utf-8") for path in backups.rglob("old.txt")
            )
            self.assertEqual(archived, ["current", "legacy 1", "legacy 2"])

    def test_skill_install_restores_current_copy_when_final_move_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            target = root / "skills" / "vivid-clean"
            backups = root / "state"
            source.mkdir()
            (source / "SKILL.md").write_text("new skill", encoding="utf-8")
            (source / "PROMPT.md").write_text("new prompt", encoding="utf-8")
            target.mkdir(parents=True)
            (target / "old.txt").write_text("current", encoding="utf-8")
            real_move = bootstrap.shutil.move

            def fail_final_move(source_path: str, destination_path: Path) -> object:
                if ".vivid-clean.stage." in source_path:
                    raise OSError("simulated final move failure")
                return real_move(source_path, destination_path)

            with (
                patch(
                    "vivid_clean.bootstrap.shutil.move",
                    side_effect=fail_final_move,
                ),
                self.assertRaisesRegex(OSError, "simulated final move failure"),
            ):
                bootstrap._install_skill_copy(source, target, backups)

            self.assertEqual(
                (target / "old.txt").read_text(encoding="utf-8"), "current"
            )

    def test_setup_requires_git_for_the_cleaner(self) -> None:
        with (
            patch("vivid_clean.bootstrap.shutil.which", return_value=None),
            self.assertRaisesRegex(WorkflowError, "git is required"),
        ):
            bootstrap.setup_runtime()

    def test_setup_can_skip_the_optional_anthropies_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with (
                patch("vivid_clean.bootstrap.runtime_root", return_value=root),
                patch("vivid_clean.bootstrap.install_skills", return_value=[]),
                patch(
                    "vivid_clean.bootstrap.shutil.which", return_value="/usr/bin/git"
                ),
                patch(
                    "vivid_clean.bootstrap._checkout_pinned",
                    return_value=root / "vendor" / "watermarks-remover",
                ) as checkout,
            ):
                result = bootstrap.setup_runtime(with_anthropies=False)

            self.assertEqual(result["anthropies"], "disabled")
            self.assertEqual(
                result["watermarks_remover"], bootstrap.WATERMARKS_REMOVER_REF
            )
            checkout.assert_called_once()

    def test_node_support_check_handles_missing_old_and_supported_node(self) -> None:
        with patch("vivid_clean.bootstrap.shutil.which", return_value=None):
            self.assertFalse(bootstrap._node_is_supported())
        with (
            patch("vivid_clean.bootstrap.shutil.which", return_value="node"),
            patch(
                "vivid_clean.bootstrap.subprocess.run",
                side_effect=(
                    subprocess.CompletedProcess(["node"], 1),
                    subprocess.CompletedProcess(["node"], 0),
                ),
            ),
        ):
            self.assertFalse(bootstrap._node_is_supported())
            self.assertTrue(bootstrap._node_is_supported())


class RuntimeTests(unittest.TestCase):
    def test_data_root_falls_back_to_the_user_data_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            environment = os.environ.copy()
            environment.pop("VIVID_CLEAN_DATA_HOME", None)
            environment.pop("XDG_DATA_HOME", None)
            with (
                patch.dict(os.environ, environment, clear=True),
                patch("vivid_clean.runtime.Path.home", return_value=Path(temp)),
            ):
                self.assertEqual(
                    runtime.data_root(),
                    Path(temp) / ".local" / "share" / "vivid-clean",
                )

    def test_runtime_root_uses_checkout_then_packaged_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            checkout = root / "checkout"
            checkout.mkdir()
            (checkout / "install.sh").touch()
            with (
                patch.dict(os.environ, {}, clear=True),
                patch("vivid_clean.runtime.source_root", return_value=checkout),
            ):
                self.assertEqual(runtime.runtime_root(), checkout)
            (checkout / "install.sh").unlink()
            with (
                patch.dict(os.environ, {}, clear=True),
                patch("vivid_clean.runtime.source_root", return_value=checkout),
                patch("vivid_clean.runtime.data_root", return_value=root / "data"),
            ):
                self.assertEqual(runtime.runtime_root(), root / "data")

    def test_skill_source_uses_packaged_files_and_reports_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            checkout = root / "checkout"
            packaged = root / "prefix" / "share" / "vivid-clean"
            checkout.mkdir()
            packaged.mkdir(parents=True)
            (packaged / "SKILL.md").touch()
            (packaged / "PROMPT.md").touch()
            with (
                patch("vivid_clean.runtime.source_root", return_value=checkout),
                patch("vivid_clean.runtime.sys.prefix", str(root / "prefix")),
            ):
                self.assertEqual(runtime.skill_source_root(), packaged)
            (packaged / "PROMPT.md").unlink()
            with (
                patch("vivid_clean.runtime.source_root", return_value=checkout),
                patch("vivid_clean.runtime.sys.prefix", str(root / "prefix")),
                self.assertRaisesRegex(FileNotFoundError, "weren't found"),
            ):
                runtime.skill_source_root()


class SetupCliTests(unittest.TestCase):
    def test_setup_json_forwards_both_switches(self) -> None:
        result = {
            "runtime_root": "/tmp/runtime",
            "watermarks_remover": "skipped",
            "anthropies": "disabled",
            "skills": [],
        }
        stdout = io.StringIO()
        with (
            patch("vivid_clean.cli.setup_runtime", return_value=result) as setup,
            redirect_stdout(stdout),
        ):
            status = cli.main(["setup", "--skills-only", "--no-anthropies", "--json"])

        self.assertEqual(status, 0)
        setup.assert_called_once_with(skills_only=True, with_anthropies=False)
        self.assertIn('"watermarks_remover": "skipped"', stdout.getvalue())

    def test_setup_text_output_names_the_installed_components(self) -> None:
        result = {
            "runtime_root": "/tmp/runtime",
            "watermarks_remover": "abc123",
            "anthropies": "unavailable",
            "skills": [],
        }
        stdout = io.StringIO()
        with (
            patch("vivid_clean.cli.setup_runtime", return_value=result),
            redirect_stdout(stdout),
        ):
            status = cli.main(["setup"])

        self.assertEqual(status, 0)
        self.assertIn("Runtime files: /tmp/runtime", stdout.getvalue())
        self.assertIn("watermarks-remover: abc123", stdout.getvalue())

    def test_setup_errors_return_status_two(self) -> None:
        stderr = io.StringIO()
        with (
            patch(
                "vivid_clean.cli.setup_runtime",
                side_effect=WorkflowError("setup failed"),
            ),
            redirect_stderr(stderr),
        ):
            status = cli.main(["setup"])

        self.assertEqual(status, 2)
        self.assertIn("error: setup failed", stderr.getvalue())
