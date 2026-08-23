"""Prepare and finish an assistant-guided vivid-clean session."""

from __future__ import annotations

import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .docx import scrub_docx
from .report import build_record, write_report
from .service import ServiceError, WatermarksClient
from .verify import VerificationError, diff, failing_findings

EDITABLE = {".txt", ".md", ".docx", ".pptx", ".pdf"}
DIRECT_MEDIA = {".png", ".jpg", ".jpeg", ".webp"}
WATERMARKS_REMOVER_REF = "104aacd212d7a262c32bd7f1f4aa380c26a5d4b5"
ANTHROPIES_REF = "6d1dba6870b9a01a1c088e18d8eed44366bbbe36"


class WorkflowError(RuntimeError):
    """A workflow stage couldn't complete safely."""


def find_tool(name: str) -> str | None:
    """Find a command on PATH or beside the active virtualenv Python."""
    sibling = Path(sys.executable).with_name(name)
    if sibling.is_file() and os.access(sibling, os.X_OK):
        return str(sibling)
    return shutil.which(name)


def _free_loopback_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


@contextmanager
def managed_watermarks_client(
    repo: Path,
) -> Iterator[tuple[WatermarksClient, dict[str, str]]]:
    """Use an explicit service, or start the pinned local checkout temporarily."""
    explicit_url = os.environ.get("WATERMARKS_SERVICE_URL")
    if explicit_url:
        client = WatermarksClient(explicit_url)
        health = client.health()
        yield (
            client,
            {
                "name": "watermarks-remover",
                "ref": f"service-reported:{health.get('version', 'unknown')}",
            },
        )
        return

    server = (
        repo / "vendor" / "watermarks-remover" / "service" / "scripts" / "server.py"
    )
    if not server.is_file():
        raise ServiceError("the pinned watermarks-remover checkout isn't installed")
    port = _free_loopback_port()
    token = secrets.token_urlsafe(32)
    environment = os.environ.copy()
    environment["WATERMARKS_SERVER_API_KEY"] = token
    environment["WATERMARKS_SERVER_VERSION"] = WATERMARKS_REMOVER_REF
    process = subprocess.Popen(
        [sys.executable, str(server), "--host", "127.0.0.1", "--port", str(port)],
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    client = WatermarksClient(f"http://127.0.0.1:{port}", token=token, timeout=10)
    try:
        for _ in range(50):
            if process.poll() is not None:
                raise ServiceError("the pinned cleaning service stopped during startup")
            try:
                client.health()
                break
            except ServiceError:
                time.sleep(0.1)
        else:
            raise ServiceError("the pinned cleaning service didn't become ready")
        yield client, {"name": "watermarks-remover", "ref": WATERMARKS_REMOVER_REF}
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def _run(command: list[str]) -> None:
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise WorkflowError(f"couldn't run {command[0]}: {exc}") from exc
    if result.returncode:
        message = (result.stderr or result.stdout).strip()[:800]
        raise WorkflowError(f"{command[0]} failed: {message}")


def _fallback_anthropies(source: Path, destination: Path, repo: Path) -> dict[str, Any]:
    local_cli = repo / "vendor" / "anthropies" / "dist" / "cli.js"
    if local_cli.is_file() and shutil.which("node"):
        command = ["node", str(local_cli), "clean", str(source), "-o", str(destination)]
    elif shutil.which("anthropies"):
        command = ["anthropies", "clean", str(source), "-o", str(destination)]
    else:
        raise WorkflowError(
            "watermarks-remover isn't available and the anthropies fallback isn't installed"
        )
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if not destination.is_file() or destination.stat().st_size == 0:
        message = (result.stderr or result.stdout).strip()[:500]
        raise WorkflowError(f"anthropies didn't produce a cleaned file: {message}")
    return {"name": "anthropies", "ref": ANTHROPIES_REF, "exit_code": result.returncode}


def _extract(cleaned: Path, draft: Path, suffix: str) -> bool:
    if suffix in (".txt", ".md"):
        shutil.copyfile(cleaned, draft)
        return True
    if suffix in EDITABLE:
        executable = find_tool("markitdown")
        if not executable:
            raise WorkflowError("markitdown isn't installed; run ./install.sh")
        _run([executable, str(cleaned), "-o", str(draft)])
        return True
    if suffix in DIRECT_MEDIA:
        return False
    raise WorkflowError(f"{suffix or 'this file type'} isn't supported")


def prepare(source: Path, repo: Path) -> Path:
    source = source.expanduser().resolve()
    if not source.is_file():
        raise WorkflowError(f"input file wasn't found: {source}")
    session = Path(tempfile.mkdtemp(prefix="vivid-clean-"))
    os.chmod(session, 0o700)
    cleaned = session / f"cleaned{source.suffix.lower()}"
    engine: dict[str, Any]
    try:
        try:
            with managed_watermarks_client(repo) as (client, identity):
                cleaned_bytes, upstream_report = client.clean(source)
            cleaned.write_bytes(cleaned_bytes)
            engine = {**identity, "report": upstream_report}
        except ServiceError:
            engine = _fallback_anthropies(source, cleaned, repo)
        draft = session / "draft.md"
        editable = _extract(cleaned, draft, source.suffix.lower())
        manifest = {
            "schema_version": 1,
            "source": str(source),
            "cleaned": str(cleaned),
            "draft": str(draft) if editable else None,
            "editable": editable,
            "source_suffix": source.suffix.lower(),
            "engine": engine,
        }
        (session / "session.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        return session
    except Exception:
        shutil.rmtree(session, ignore_errors=True)
        raise


def _default_output(source: Path, suffix: str) -> Path:
    if not suffix or suffix in (".", "..") or "/" in suffix or "\\" in suffix:
        raise WorkflowError(
            "suffix must be a non-empty filename fragment without path separators"
        )
    output_suffix = ".docx" if source.suffix.lower() == ".pdf" else source.suffix
    return source.with_name(f"{source.stem}{suffix}{output_suffix}")


def finish(
    session: Path, suffix: str, output: Path | None, json_report: Path | None
) -> tuple[Path, Path, str]:
    session = session.expanduser().resolve()
    try:
        manifest = json.loads((session / "session.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        raise WorkflowError("session is missing or damaged") from exc
    source = Path(manifest["source"])
    cleaned = Path(manifest["cleaned"])
    destination = (
        output.expanduser().resolve() if output else _default_output(source, suffix)
    )
    if destination == source.resolve():
        raise WorkflowError("output must be different from the source file")
    report_path = destination.with_name(f"{destination.name}.vivid-clean-report.md")
    verification: dict[str, Any] | None = None
    unavailable = [
        "Keyed statistical watermark detectors unless configured in watermarks-remover.",
        "Pixel-level image watermarks unless an optional pixel backend is configured.",
        "Any proprietary detector that wasn't available to this run.",
    ]
    status = "incomplete"
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if manifest["editable"]:
            draft = Path(manifest["draft"])
            if not draft.is_file() or not draft.read_text(encoding="utf-8").strip():
                raise WorkflowError("draft.md is missing or empty")
            if source.suffix.lower() in (".txt", ".md"):
                shutil.copyfile(draft, destination)
            else:
                pandoc = find_tool("pandoc")
                if not pandoc:
                    raise WorkflowError(
                        "pandoc isn't installed; run vivid-clean doctor for setup help"
                    )
                _run([pandoc, "--sandbox", str(draft), "-o", str(destination)])
        else:
            shutil.copyfile(cleaned, destination)
        if destination.suffix.lower() == ".docx":
            scrub_docx(destination)
        verification = diff(source, destination)
        status = "findings" if failing_findings(verification) else "verified"
        record = build_record(
            source, destination, manifest["engine"], verification, unavailable, status
        )
        write_report(record, report_path, json_report)
        return destination, report_path, status
    except (WorkflowError, VerificationError, OSError, ValueError) as exc:
        record = build_record(
            source,
            destination,
            manifest.get("engine", {}),
            verification,
            unavailable + [f"Verification stopped: {exc}"],
            "incomplete",
        )
        write_report(record, report_path, None)
        raise WorkflowError(
            f"{exc}. An incomplete report was saved to {report_path}"
        ) from exc
    finally:
        shutil.rmtree(session, ignore_errors=True)
