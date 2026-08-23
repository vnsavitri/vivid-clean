"""Stdlib-only checks for deterministic marks in documents and media."""

from __future__ import annotations

import re
import struct
import unicodedata
import zipfile
from pathlib import Path
from typing import Any

SEVERITY = {"info": 0, "low": 1, "medium": 2, "high": 3}
AI_VENDORS = (
    "chatgpt",
    "openai",
    "claude",
    "anthropic",
    "copilot",
    "gemini",
    "deepseek",
    "kimi",
    "qwen",
    "mistral",
)
GENERATORS = AI_VENDORS + ("pandoc", "markitdown", "python-docx", "python-pptx")

ALWAYS_SUSPICIOUS = {
    "U+200B ZERO WIDTH SPACE": "\u200b",
    "U+2060 WORD JOINER": "\u2060",
    "U+FEFF ZERO WIDTH NO-BREAK SPACE": "\ufeff",
    "U+00AD SOFT HYPHEN": "\u00ad",
    "U+180E MONGOLIAN VOWEL SEPARATOR": "\u180e",
}
TYPOGRAPHIC_SPACES = {
    "U+00A0 NO-BREAK SPACE": "\u00a0",
    "U+202F NARROW NO-BREAK SPACE": "\u202f",
    "U+205F MEDIUM MATHEMATICAL SPACE": "\u205f",
    "U+3000 IDEOGRAPHIC SPACE": "\u3000",
}
TAG_RANGE = (0xE0020, 0xE007F)
BIDI_CONTROLS = (
    {0x061C, 0x200E, 0x200F} | set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A))
)
RTL_RANGES = ((0x0590, 0x08FF), (0xFB1D, 0xFDFF), (0xFE70, 0xFEFF))
JOINING_RANGES = RTL_RANGES + (
    (0x0900, 0x0DFF),
    (0x0F00, 0x109F),
    (0x1780, 0x17FF),
)
MONGOLIAN_RANGE = (0x1800, 0x18AF)

CORE_FIELDS = (
    "dc:creator",
    "cp:lastModifiedBy",
    "cp:revision",
    "dcterms:created",
    "dcterms:modified",
    "dc:title",
    "cp:keywords",
    "dc:description",
)
APP_FIELDS = ("Application", "Company", "Manager", "TotalTime", "AppVersion")

Finding = dict[str, Any]


class VerificationError(RuntimeError):
    """The verifier couldn't complete its checks."""


def _finding(category: str, location: str, detail: str, severity: str) -> Finding:
    return {
        "category": category,
        "location": location,
        "detail": detail,
        "severity": severity,
    }


def _in_ranges(char: str, ranges: tuple[tuple[int, int], ...]) -> bool:
    return any(lo <= ord(char) <= hi for lo, hi in ranges)


def _emoji_like(char: str) -> bool:
    cp = ord(char)
    return (
        0x1F000 <= cp <= 0x1FAFF
        or 0x2600 <= cp <= 0x27BF
        or unicodedata.category(char) == "So"
    )


def _context_char(text: str, index: int, direction: int) -> str:
    pos = index + direction
    while 0 <= pos < len(text) and ord(text[pos]) in BIDI_CONTROLS:
        pos += direction
    return text[pos] if 0 <= pos < len(text) else ""


def _joiner_is_expected(text: str, index: int, char: str) -> bool:
    before = _context_char(text, index, -1)
    after = _context_char(text, index, 1)
    if not before or not after:
        return False
    if char == "\u200d" and (_emoji_like(before) or _emoji_like(after)):
        return True
    return _in_ranges(before, JOINING_RANGES) and _in_ranges(after, JOINING_RANGES)


def _variation_is_expected(text: str, index: int) -> bool:
    before = _context_char(text, index, -1)
    cp = ord(text[index])
    if not before:
        return False
    if 0x180B <= cp <= 0x180D:
        return MONGOLIAN_RANGE[0] <= ord(before) <= MONGOLIAN_RANGE[1]
    return _emoji_like(before) or ord(before) > 0x2FFF


def _bidi_is_expected(text: str, index: int) -> bool:
    window = text[max(0, index - 8) : index] + text[index + 1 : index + 9]
    return any(_in_ranges(char, RTL_RANGES) for char in window)


def _unexpected_tag_count(text: str) -> int:
    """Count Unicode tags, preserving valid subdivision-flag emoji sequences."""
    unexpected = 0
    index = 0
    while index < len(text):
        if not (TAG_RANGE[0] <= ord(text[index]) <= TAG_RANGE[1]):
            index += 1
            continue
        start = index
        while index < len(text) and TAG_RANGE[0] <= ord(text[index]) <= TAG_RANGE[1]:
            index += 1
        valid_flag = (
            start > 0
            and ord(text[start - 1]) == 0x1F3F4
            and ord(text[index - 1]) == 0xE007F
            and index - start >= 2
        )
        if not valid_flag:
            unexpected += index - start
    return unexpected


def scan_invisible(text: str, location: str) -> list[Finding]:
    findings: list[Finding] = []
    for name, char in ALWAYS_SUSPICIOUS.items():
        count = text.count(char)
        if count:
            findings.append(
                _finding("invisible_unicode", location, f"{name} x{count}", "high")
            )

    for name, char in TYPOGRAPHIC_SPACES.items():
        count = text.count(char)
        if count:
            findings.append(
                _finding("typographic_space", location, f"{name} x{count}", "low")
            )

    suspicious: dict[str, int] = {
        "joiner": 0,
        "variation selector": 0,
        "bidi control": 0,
    }
    for index, char in enumerate(text):
        cp = ord(char)
        if char in ("\u200c", "\u200d") and not _joiner_is_expected(text, index, char):
            suspicious["joiner"] += 1
        elif (
            (0xFE00 <= cp <= 0xFE0F)
            or (0xE0100 <= cp <= 0xE01EF)
            or (0x180B <= cp <= 0x180D)
        ):
            if not _variation_is_expected(text, index):
                suspicious["variation selector"] += 1
        elif cp in BIDI_CONTROLS and not _bidi_is_expected(text, index):
            suspicious["bidi control"] += 1

    for label, count in suspicious.items():
        if count:
            findings.append(
                _finding(
                    "invisible_unicode",
                    location,
                    f"unexpected {label} x{count}",
                    "high",
                )
            )

    tags = _unexpected_tag_count(text)
    if tags:
        findings.append(
            _finding(
                "invisible_unicode", location, f"Unicode tag characters x{tags}", "high"
            )
        )
    return findings


def _severity_for_value(value: str) -> str:
    lower = value.lower()
    if any(vendor in lower for vendor in AI_VENDORS):
        return "high"
    if any(generator in lower for generator in GENERATORS):
        return "medium"
    return "low"


def scan_ooxml(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise VerificationError(
            f"{path.name} has a ZIP signature but isn't a readable OOXML file"
        ) from exc
    with archive:
        names = set(archive.namelist())
        if "[Content_Types].xml" not in names:
            raise VerificationError(
                f"{path.name} is a ZIP file, but it isn't a recognised OOXML document"
            )
        try:
            damaged = archive.testzip()
        except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
            raise VerificationError(
                f"{path.name} contains an unreadable ZIP entry"
            ) from exc
        if damaged:
            raise VerificationError(
                f"{path.name} contains a damaged ZIP entry: {damaged}"
            )
        provenance_parts = [
            name for name in names if "c2pa" in name.lower() or "jumbf" in name.lower()
        ]
        for part in provenance_parts:
            findings.append(
                _finding("c2pa_provenance", part, "C2PA/JUMBF package part", "high")
            )
        if "docProps/core.xml" in names:
            xml = archive.read("docProps/core.xml").decode("utf-8", "ignore")
            for field in CORE_FIELDS:
                match = re.search(
                    r"<" + field + r"[^>]*>(.*?)</" + field + r">", xml, re.DOTALL
                )
                if match and match.group(1).strip():
                    value = match.group(1).strip()
                    severity = (
                        _severity_for_value(value)
                        if field in ("dc:creator", "cp:lastModifiedBy")
                        else "medium"
                    )
                    findings.append(
                        _finding(
                            "document_metadata",
                            f"docProps/core.xml:{field}",
                            value[:80],
                            severity,
                        )
                    )
        if "docProps/app.xml" in names:
            xml = archive.read("docProps/app.xml").decode("utf-8", "ignore")
            for field in APP_FIELDS:
                match = re.search(
                    r"<" + field + r"[^>]*>(.*?)</" + field + r">", xml, re.DOTALL
                )
                if match and match.group(1).strip():
                    value = match.group(1).strip()
                    severity = (
                        _severity_for_value(value)
                        if field == "Application"
                        else "medium"
                    )
                    category = (
                        "producer_hint"
                        if field == "Application"
                        else "document_metadata"
                    )
                    findings.append(
                        _finding(
                            category, f"docProps/app.xml:{field}", value[:80], severity
                        )
                    )
        if "docProps/custom.xml" in names:
            xml = archive.read("docProps/custom.xml").decode("utf-8", "ignore")
            for match in re.finditer(r'property[^>]*name="([^"]+)"', xml):
                findings.append(
                    _finding(
                        "document_metadata",
                        f"docProps/custom.xml:{match.group(1)}",
                        "custom property present",
                        "medium",
                    )
                )
        for part in sorted(names):
            if part.endswith(".xml"):
                findings.extend(
                    scan_invisible(archive.read(part).decode("utf-8", "ignore"), part)
                )
        for part in (
            "word/document.xml",
            *sorted(
                n
                for n in names
                if n.startswith("ppt/slides/slide") and n.endswith(".xml")
            ),
        ):
            if part not in names:
                continue
            data = archive.read(part)
            for tag, label in ((b"<w:ins ", "w:ins"), (b"<w:del ", "w:del")):
                if tag in data:
                    authors = re.findall(rb'w:author="([^"]*)"', data)
                    ai_author = any(
                        any(v.encode() in author.lower() for v in AI_VENDORS)
                        for author in authors
                    )
                    detail = "tracked changes present" + (
                        " (AI-vendor author)" if ai_author else ""
                    )
                    findings.append(
                        _finding(
                            "tracked_changes",
                            f"{part}:{label}",
                            detail,
                            "high" if ai_author else "medium",
                        )
                    )
            if b"w:rsidR" in data:
                findings.append(
                    _finding(
                        "editing_identifiers",
                        part,
                        "RSID editing-session identifiers present",
                        "low",
                    )
                )
        comment_parts = (
            ("word/comments.xml", rb"<w:comment\b"),
            ("word/people.xml", rb"<w:person\b"),
        )
        for part, marker in comment_parts:
            if part in names and re.search(marker, archive.read(part)):
                content = archive.read(part)
                ai_author = any(
                    vendor.encode() in content.lower() for vendor in AI_VENDORS
                )
                findings.append(
                    _finding(
                        "comments",
                        part,
                        "comment or people records present"
                        + (" (AI-vendor author)" if ai_author else ""),
                        "high" if ai_author else "medium",
                    )
                )
    return findings


def scan_png(data: bytes) -> list[Finding]:
    findings: list[Finding] = []
    offset = 8
    flagged = {
        b"tEXt": "text chunk",
        b"zTXt": "compressed text chunk",
        b"iTXt": "international text chunk",
        b"eXIf": "EXIF chunk",
        b"caBX": "C2PA manifest chunk",
    }
    while offset + 12 <= len(data):
        length, chunk = struct.unpack(">I4s", data[offset : offset + 8])
        if length > len(data) - offset - 12:
            raise VerificationError("PNG contains a truncated chunk")
        if chunk in flagged:
            category = "c2pa_provenance" if chunk == b"caBX" else "image_metadata"
            findings.append(
                _finding(
                    category,
                    f"PNG chunk {chunk.decode()}",
                    flagged[chunk],
                    "high" if chunk == b"caBX" else "medium",
                )
            )
        offset += length + 12
        if chunk == b"IEND":
            return findings
    raise VerificationError("PNG is truncated or missing its IEND chunk")


def scan_jpeg(data: bytes) -> list[Finding]:
    if data.rfind(b"\xff\xd9") < 2:
        raise VerificationError("JPEG is truncated or missing its end marker")
    findings: list[Finding] = []
    offset = 2
    while offset + 2 <= len(data):
        if data[offset] != 0xFF:
            raise VerificationError("JPEG contains an invalid marker")
        marker = data[offset + 1]
        if marker == 0xD9:
            return findings
        if marker in (0xD8,) or 0xD0 <= marker <= 0xD7:
            offset += 2
            continue
        if offset + 4 > len(data):
            raise VerificationError("JPEG contains a truncated segment")
        length = struct.unpack(">H", data[offset + 2 : offset + 4])[0]
        if length < 2 or offset + 2 + length > len(data):
            raise VerificationError("JPEG contains an invalid segment length")
        segment = data[offset + 4 : offset + 2 + length]
        if marker == 0xE1 and segment.startswith(b"Exif\x00\x00"):
            findings.append(
                _finding("image_metadata", "JPEG APP1", "EXIF segment", "medium")
            )
        elif marker == 0xE1 and b"xap/1.0" in segment[:80]:
            findings.append(
                _finding("image_metadata", "JPEG APP1", "XMP packet", "medium")
            )
        elif marker == 0xEB and segment[:2] == b"JP":
            findings.append(
                _finding("c2pa_provenance", "JPEG APP11", "JUMBF/C2PA segment", "high")
            )
        elif marker == 0xED:
            findings.append(
                _finding("image_metadata", "JPEG APP13", "IPTC segment", "medium")
            )
        elif marker == 0xFE:
            findings.append(
                _finding("image_metadata", "JPEG COM", "comment segment", "medium")
            )
        if marker == 0xDA:
            return findings
        offset += length + 2
    raise VerificationError("JPEG is truncated")


def scan_webp(data: bytes) -> list[Finding]:
    if len(data) < 12:
        raise VerificationError("WebP is truncated")
    declared = struct.unpack("<I", data[4:8])[0] + 8
    if declared > len(data):
        raise VerificationError("WebP is truncated")
    findings: list[Finding] = []
    offset = 12
    while offset + 8 <= declared:
        chunk, length = struct.unpack("<4sI", data[offset : offset + 8])
        end = offset + 8 + length
        if end > declared:
            raise VerificationError("WebP contains a truncated chunk")
        if chunk in (b"EXIF", b"XMP "):
            findings.append(
                _finding(
                    "image_metadata",
                    f"WebP chunk {chunk.decode().strip()}",
                    "embedded metadata",
                    "medium",
                )
            )
        elif chunk in (b"C2PA", b"JUMB"):
            findings.append(
                _finding(
                    "c2pa_provenance",
                    f"WebP chunk {chunk.decode()}",
                    "C2PA/JUMBF data",
                    "high",
                )
            )
        offset = end + (length % 2)
    return findings


def scan_pdf(data: bytes) -> list[Finding]:
    if b"%%EOF" not in data[-2048:]:
        raise VerificationError("PDF is truncated or missing its EOF marker")
    findings: list[Finding] = []
    for key in (
        b"/Title",
        b"/Author",
        b"/Creator",
        b"/Producer",
        b"/CreationDate",
        b"/ModDate",
        b"/Keywords",
        b"/Subject",
    ):
        match = re.search(re.escape(key) + rb"\s*\((.*?)\)", data, re.DOTALL)
        if match:
            value = match.group(1).decode("utf-8", "ignore")[:80]
            severity = (
                _severity_for_value(value)
                if key in (b"/Author", b"/Creator", b"/Producer")
                else "medium"
            )
            findings.append(_finding("pdf_metadata", key.decode(), value, severity))
    if b"<x:xmpmeta" in data or b"<?xpacket" in data:
        findings.append(
            _finding("pdf_metadata", "XMP", "XMP metadata packet", "medium")
        )
    if b"application/c2pa" in data.lower() or b"c2pa_manifest" in data.lower():
        findings.append(
            _finding("c2pa_provenance", "<raw>", "C2PA/JUMBF marker bytes", "high")
        )
    findings.extend(scan_invisible(data.decode("utf-8", "ignore"), "<raw-bytes>"))
    return findings


def scan(path: str | Path) -> list[Finding]:
    file_path = Path(path)
    try:
        data = file_path.read_bytes()
    except OSError as exc:
        raise VerificationError(str(exc)) from exc
    if not data:
        raise VerificationError(f"{file_path.name} is empty")
    if data.startswith(b"PK\x03\x04"):
        return scan_ooxml(file_path)
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return scan_png(data)
    if data.startswith(b"\xff\xd8"):
        return scan_jpeg(data)
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return scan_webp(data)
    if data.startswith(b"%PDF"):
        return scan_pdf(data)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise VerificationError(
            f"{file_path.name} is an unsupported or unreadable binary format"
        ) from exc
    if "\x00" in text:
        raise VerificationError(f"{file_path.name} is an unsupported binary format")
    return scan_invisible(text, "<text>")


def diff(original: str | Path, cleaned: str | Path) -> dict[str, Any]:
    before, after = scan(original), scan(cleaned)
    before_map = {(item["category"], item["location"]): item for item in before}
    after_map = {(item["category"], item["location"]): item for item in after}
    residual: list[Finding] = []
    for item in after:
        key = (item["category"], item["location"])
        if key in before_map:
            prior = before_map[key]
            detail = item["detail"]
            if detail != prior["detail"]:
                detail = f"{detail} (was: {prior['detail'][:60]})"
            residual.append({**item, "detail": detail})
    return {
        "removed": [
            item
            for item in before
            if (item["category"], item["location"]) not in after_map
        ],
        "residual": residual,
        "introduced": [
            item
            for item in after
            if (item["category"], item["location"]) not in before_map
        ],
    }


def failing_findings(
    result: dict[str, Any], threshold: str = "medium"
) -> list[Finding]:
    minimum = SEVERITY[threshold]
    return [
        item
        for key in ("residual", "introduced")
        for item in result[key]
        if SEVERITY[item["severity"]] >= minimum
    ]
