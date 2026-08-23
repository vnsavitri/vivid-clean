"""Reader-friendly verification records."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DETERMINISTIC_CATEGORIES = {"invisible_unicode", "typographic_space"}


def _finding_channel_status(
    verification: dict[str, Any] | None, categories: set[str]
) -> dict[str, Any]:
    if verification is None:
        return {"status": "incomplete"}
    remaining = [
        item
        for key in ("residual", "introduced")
        for item in verification[key]
        if item["category"] in categories
    ]
    return {"status": "findings" if remaining else "passed", "findings": remaining}


def _channels(
    output: Path, verification: dict[str, Any] | None, status: str
) -> dict[str, Any]:
    all_categories = {
        item["category"]
        for key in ("removed", "residual", "introduced")
        for item in (verification or {}).get(key, [])
    }
    file_categories = all_categories - DETERMINISTIC_CATEGORIES
    package = output.suffix.lower() in {".docx", ".pptx"}
    guarded_status = "incomplete" if status == "incomplete" else "passed"
    return {
        "deterministic_text": _finding_channel_status(
            verification, DETERMINISTIC_CATEGORIES
        ),
        "file_provenance": _finding_channel_status(verification, file_categories),
        "statistical": {
            "status": "not_checked",
            "reason": "No keyed statistical detector was configured for this run.",
        },
        "proprietary": {
            "status": "not_checked",
            "reason": "No proprietary or official detector was available to this run.",
        },
        "protected_values": {"status": guarded_status if package else "not_applicable"},
        "package_structure": {
            "status": guarded_status if package else "not_applicable"
        },
    }


def build_record(
    source: Path,
    output: Path,
    engine: dict[str, Any],
    verification: dict[str, Any] | None,
    unavailable: list[str],
    status: str,
    writing_pass: dict[str, Any] | None = None,
) -> dict[str, Any]:
    engine_record = {
        key: engine[key]
        for key in ("name", "ref", "capabilities", "report", "exit_code")
        if key in engine
    }
    return {
        "schema_version": 2,
        "created_at": datetime.now(UTC).isoformat(),
        "source": source.name,
        "output": output.name,
        "status": status,
        "engine": engine_record,
        "writing_pass": writing_pass or {"status": "not_recorded"},
        "verification": verification
        or {"removed": [], "residual": [], "introduced": []},
        "channels": _channels(output, verification, status),
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
        "checks_passed": "The configured checks passed without medium or high residual findings.",
        "findings": "The output still has medium or high findings. Review it before use.",
        "incomplete": "The checks couldn't finish, so this output has an incomplete result.",
    }[record["status"]]
    writing = record["writing_pass"]
    evidence = writing.get("rewrite_evidence")
    ratio = evidence.get("surviving_ratio") if evidence else None
    ratio_text = "not available" if ratio is None else f"{ratio:.1%}"
    writing_lines = [f"- Status: `{writing.get('status', 'not_recorded')}`"]
    if writing.get("status") != "not_applicable":
        writing_lines.extend(
            [
                f"- Backend: `{writing.get('backend', 'not recorded')}`",
                f"- Backend kind: `{writing.get('backend_kind', 'unknown')}`",
                f"- Purpose: `{writing.get('purpose', 'not recorded')}`",
                "- Backend claim independently verified: `no`",
            ]
        )
    if evidence:
        writing_lines.extend(
            [
                f"- Rewrite evidence: `{evidence['status']}`",
                f"- Original five-word sequences surviving: `{ratio_text}`",
                "- This overlap measure is a rewrite-depth proxy, not a watermark detector.",
            ]
        )
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
        "## Check channels",
        "",
        *[
            f"- {name.replace('_', ' ')}: `{details['status']}`"
            for name, details in record["channels"].items()
        ],
        "",
        "## Cleaning engine",
        "",
        f"- Name: `{record['engine'].get('name', 'unknown')}`",
        f"- Engine reference: `{record['engine'].get('ref', 'not recorded')}`",
        f"- Capabilities recorded: `{'yes' if record['engine'].get('capabilities') else 'no'}`",
        f"- Engine report recorded: `{'yes' if record['engine'].get('report') else 'no'}`",
        "",
        "## Writing pass",
        "",
        *writing_lines,
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
