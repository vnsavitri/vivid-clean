"""Install pinned engines and assistant skill copies for packaged installs."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from .runtime import runtime_root, skill_source_root
from .workflow import ANTHROPIES_REF, WATERMARKS_REMOVER_REF, WorkflowError

WATERMARKS_REMOVER_URL = "https://github.com/guillaumemeyer/watermarks-remover.git"
ANTHROPIES_URL = "https://github.com/CharlesHoskinson/anthropies.git"


def _run(command: list[str], *, cwd: Path | None = None) -> None:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise WorkflowError(f"couldn't run {command[0]}: {exc}") from exc
    if result.returncode:
        message = (result.stderr or result.stdout).strip()[:800]
        raise WorkflowError(f"{command[0]} failed: {message}")


def _checkout_pinned(name: str, url: str, ref: str, vendor: Path) -> Path:
    target = vendor / name
    vendor.mkdir(parents=True, exist_ok=True)
    if not (target / ".git").is_dir():
        _run(["git", "clone", "--filter=blob:none", "--no-checkout", url, str(target)])
    origin = subprocess.run(
        ["git", "-C", str(target), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=False,
    )
    if origin.returncode or origin.stdout.strip() != url:
        raise WorkflowError(f"{target} has an unexpected origin; refusing to update it")
    _run(["git", "-C", str(target), "fetch", "--depth", "1", "origin", ref])
    _run(["git", "-C", str(target), "checkout", "--detach", "--force", "FETCH_HEAD"])
    actual = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if actual.returncode or actual.stdout.strip() != ref:
        raise WorkflowError(f"{name} didn't resolve to the audited commit")
    return target


def _state_root(home: Path) -> Path:
    override = os.environ.get("VIVID_CLEAN_STATE_HOME")
    if override:
        return Path(override).expanduser().resolve()
    xdg_state = os.environ.get("XDG_STATE_HOME")
    if xdg_state:
        return Path(xdg_state).expanduser().resolve()
    return home / ".local" / "state"


def _skill_targets(home: Path) -> tuple[tuple[str, Path], ...]:
    codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex")).expanduser()
    return (
        ("agents", home / ".agents" / "skills" / "vivid-clean"),
        ("cursor", home / ".cursor" / "skills" / "vivid-clean"),
        ("claude", home / ".claude" / "skills" / "vivid-clean"),
        ("codex", codex_home / "skills" / "vivid-clean"),
    )


def _install_skill_copy(source: Path, target: Path, backup_root: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    backup_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    for legacy in target.parent.glob("vivid-clean.backup.*"):
        archive = Path(tempfile.mkdtemp(prefix=f"legacy.{timestamp}.", dir=backup_root))
        shutil.move(str(legacy), archive / legacy.name)
    stage = Path(tempfile.mkdtemp(prefix=".vivid-clean.stage.", dir=target.parent))
    backup: Path | None = None
    try:
        shutil.copy2(source / "SKILL.md", stage / "SKILL.md")
        shutil.copy2(source / "PROMPT.md", stage / "PROMPT.md")
        if target.exists() or target.is_symlink():
            current = Path(
                tempfile.mkdtemp(prefix=f"current.{timestamp}.", dir=backup_root)
            )
            backup = current / "vivid-clean"
            shutil.move(str(target), backup)
        shutil.move(str(stage), target)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        if backup is not None and backup.exists() and not target.exists():
            shutil.move(str(backup), target)
        raise


def install_skills() -> list[Path]:
    """Install the packaged skill in supported assistant locations."""
    home = Path(os.environ.get("VIVID_CLEAN_USER_HOME", Path.home())).expanduser()
    source = skill_source_root()
    backup_base = _state_root(home) / "vivid-clean" / "skill-backups"
    installed: list[Path] = []
    for label, target in _skill_targets(home):
        _install_skill_copy(source, target, backup_base / label)
        installed.append(target)
    return installed


def _node_is_supported() -> bool:
    node = shutil.which("node")
    if not node:
        return False
    result = subprocess.run(
        [
            node,
            "-e",
            'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)',
        ],
        check=False,
    )
    return result.returncode == 0


def setup_runtime(*, skills_only: bool = False, with_anthropies: bool = True) -> dict:
    """Install the audited engine checkout and assistant skill copies."""
    if not skills_only and not shutil.which("git"):
        raise WorkflowError("git is required for setup but wasn't found")
    root = runtime_root()
    installed_skills = install_skills()
    result: dict[str, object] = {
        "runtime_root": str(root),
        "skills": [str(path) for path in installed_skills],
        "watermarks_remover": "skipped",
        "anthropies": "disabled" if not with_anthropies else "unavailable",
    }
    if skills_only:
        return result
    vendor = root / "vendor"
    _checkout_pinned(
        "watermarks-remover",
        WATERMARKS_REMOVER_URL,
        WATERMARKS_REMOVER_REF,
        vendor,
    )
    result["watermarks_remover"] = WATERMARKS_REMOVER_REF
    if with_anthropies and _node_is_supported() and shutil.which("pnpm"):
        target = _checkout_pinned("anthropies", ANTHROPIES_URL, ANTHROPIES_REF, vendor)
        _run(["pnpm", "install", "--frozen-lockfile"], cwd=target)
        _run(["pnpm", "build"], cwd=target)
        result["anthropies"] = ANTHROPIES_REF
    return result
