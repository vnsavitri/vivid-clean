"""Command-line interface for vivid-clean."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__
from .service import ServiceError, WatermarksClient
from .verify import SEVERITY, VerificationError, diff, failing_findings, scan
from .workflow import WorkflowError, cleanup_sessions, find_tool, finish, prepare


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _print_findings(result: dict) -> None:
    for label in ("removed", "residual", "introduced"):
        for item in result[label]:
            print(
                f"[{label:>10}] [{item['severity']:>6}] {item['category']}: {item['location']} - {item['detail']}"
            )
    print(
        f"removed={len(result['removed'])} residual={len(result['residual'])} introduced={len(result['introduced'])}"
    )


def _doctor() -> int:
    print(f"vivid-clean {__version__}")
    print(f"Python: {sys.version.split()[0]}")
    tools = {command: find_tool(command) for command in ("git",)}
    for command, location in tools.items():
        print(f"{command}: {location or 'not found'}")
    repo = _repo_root()
    wm = repo / "vendor" / "watermarks-remover"
    anthropies = repo / "vendor" / "anthropies" / "dist" / "cli.js"
    print(
        f"watermarks-remover checkout: {'available' if wm.is_dir() else 'not installed'}"
    )
    print(
        f"anthropies fallback: {'available' if anthropies.is_file() else 'not installed'}"
    )
    try:
        client = WatermarksClient(timeout=3)
        health = client.health()
        capabilities = client.capabilities()
        print(
            f"cleaning service: available ({health.get('version', 'unknown version')})"
        )
        print("service capabilities:")
        print(json.dumps(capabilities, indent=2))
        return 0
    except ServiceError as exc:
        if os.environ.get("WATERMARKS_SERVICE_URL"):
            print(f"configured cleaning service: unavailable ({exc})")
            return 1
        if wm.is_dir():
            print(
                "persistent cleaning service: not running (a private one will start when needed)"
            )
        else:
            print(f"cleaning service: unavailable ({exc})")
        return 0 if wm.is_dir() else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vivid-clean",
        description="Prepare, preserve and check a cleaned copy of a file",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="clean and extract a file for humanising")
    prep.add_argument("input", type=Path)
    done = sub.add_parser("finish", help="apply edits and check a prepared session")
    done.add_argument("session", type=Path)
    done.add_argument("--suffix", default="_vivid")
    done.add_argument("--output", type=Path)
    done.add_argument("--report-json", type=Path)
    check = sub.add_parser("verify", help="compare an original with an output")
    check.add_argument("original", type=Path)
    check.add_argument("output", type=Path)
    check.add_argument("--fail-on", choices=("low", "medium", "high"), default="medium")
    check.add_argument("--json", action="store_true")
    scan_parser = sub.add_parser("scan", help="inspect one file")
    scan_parser.add_argument("file", type=Path)
    scan_parser.add_argument("--json", action="store_true")
    cleanup = sub.add_parser("cleanup", help="remove abandoned restricted sessions")
    cleanup.add_argument(
        "--older-than",
        type=float,
        default=24,
        metavar="HOURS",
        help="remove sessions at least this old (default: 24)",
    )
    cleanup.add_argument("--dry-run", action="store_true")
    cleanup.add_argument("--json", action="store_true")
    sub.add_parser("doctor", help="show installed and missing capabilities")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "prepare":
            session = prepare(args.input, _repo_root())
            print(session)
            draft = session / "draft.md"
            if draft.exists():
                print(f"Edit {draft}, then run: vivid-clean finish {session}")
            else:
                print(
                    f"This format doesn't have a text rewrite step. Run: vivid-clean finish {session}"
                )
            return 0
        if args.command == "finish":
            output, report, status = finish(
                args.session, args.suffix, args.output, args.report_json
            )
            print(f"Output: {output}")
            print(f"Report: {report}")
            return 0 if status == "checks_passed" else 1
        if args.command == "verify":
            result = diff(args.original, args.output)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                _print_findings(result)
            return 1 if failing_findings(result, args.fail_on) else 0
        if args.command == "scan":
            findings = scan(args.file)
            if args.json:
                print(
                    json.dumps({"file": args.file.name, "findings": findings}, indent=2)
                )
            else:
                for item in findings:
                    print(
                        f"[{item['severity']:>6}] {item['category']}: {item['location']} - {item['detail']}"
                    )
            return (
                1
                if any(
                    SEVERITY[item["severity"]] >= SEVERITY["medium"]
                    for item in findings
                )
                else 0
            )
        if args.command == "cleanup":
            removed = cleanup_sessions(args.older_than, args.dry_run)
            if args.json:
                print(
                    json.dumps(
                        {
                            "dry_run": args.dry_run,
                            "removed": [str(path) for path in removed],
                        },
                        indent=2,
                    )
                )
            else:
                action = "Would remove" if args.dry_run else "Removed"
                if removed:
                    for path in removed:
                        print(f"{action}: {path}")
                else:
                    print("No expired vivid-clean sessions found.")
            return 0
        return _doctor()
    except (WorkflowError, VerificationError, ServiceError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
