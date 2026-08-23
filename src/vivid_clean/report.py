"""Reader-friendly verification records."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def build_record(
    source: Path,
    output: Path,
    engine: dict[str, Any],
    verification: dict[str, Any] | None,
    unavailable: list[str],
    status: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "source": source.name,
        "output": output.name,
        "status": status,
        "engine": {key: engine[key] for key in ("name", "ref") if key in engine},
        "verification": verification
        or {"removed": [], "residual": [], "introduced": []},
        "not_checked": unavailable,
    }


def _finding_lines(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return ["- None detected."]
    return [
        f"- `{item['severity']}` {item['category']} at `{item['location']}`: {item['detail']}"
        for item in items
    ]


def write_report(
    record: dict[str, Any], path: Path, json_path: Path | None = None
) -> None:
    verification = record["verification"]
    status_text = {
        "verified": "The checks that ran didn't find any medium or high residual marks.",
        "findings": "The output still has medium or high findings. Review it before use.",
        "incomplete": "Verification couldn't finish, so this output isn't verified.",
    }[record["status"]]
    lines = [
        "# vivid-clean verification record",
        "",
        f"- Source: `{record['source']}`",
        f"- Output: `{record['output']}`",
        f"- Checked: {record['created_at']}",
        f"- Result: **{record['status']}**",
        "",
        status_text,
        "",
        "This record describes the checks vivid-clean ran. It isn't proof that a person wrote the file, and it can't promise what an outside detector will decide.",
        "",
        "## Cleaning engine",
        "",
        f"- Name: `{record['engine'].get('name', 'unknown')}`",
        f"- Engine reference: `{record['engine'].get('ref', 'not recorded')}`",
        "",
        "## Removed",
        "",
        *_finding_lines(verification["removed"]),
        "",
        "## Residual",
        "",
        *_finding_lines(verification["residual"]),
        "",
        "## Introduced during conversion",
        "",
        *_finding_lines(verification["introduced"]),
        "",
        "## Not checked",
        "",
        *(
            [f"- {item}" for item in record["not_checked"]]
            or ["- All configured checks were available."]
        ),
        "",
        "The report stores filenames and detector results, not document contents or full local paths.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    if json_path:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
