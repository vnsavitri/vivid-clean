"""Edit OOXML text without rebuilding the document package."""

from __future__ import annotations

import os
import re
import secrets
import tempfile
import zipfile
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PRESENTATION_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XML_NS = "http://www.w3.org/XML/1998/namespace"

ET.register_namespace("w", WORD_NS)
ET.register_namespace("a", DRAWING_NS)
ET.register_namespace("p", PRESENTATION_NS)
ET.register_namespace("r", REL_NS)


class PackageEditError(RuntimeError):
    """A package-aware edit couldn't be applied without guessing."""


PROTECTED_VALUE = re.compile(
    r"https?://[^\s<>()]+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|"
    r"(?<![\w])(?:\d{1,3}(?:[ ,]\d{3})+|\d+)(?:\.\d+)?%?(?![\w])"
)


def _protected_values(text: str) -> Counter[str]:
    return Counter(PROTECTED_VALUE.findall(text))


def _editable_parts(names: list[str], suffix: str) -> list[str]:
    if suffix == ".docx":
        candidates = [
            name
            for name in names
            if name == "word/document.xml"
            or re.fullmatch(r"word/(?:header|footer)\d+\.xml", name)
            or name in {"word/footnotes.xml", "word/endnotes.xml"}
        ]
        return sorted(candidates, key=lambda name: (name != "word/document.xml", name))
    if suffix == ".pptx":
        candidates = [
            name
            for name in names
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            or re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)
        ]
        return sorted(candidates)
    raise PackageEditError(f"package-aware editing doesn't support {suffix}")


def _paragraphs(root: ET.Element, suffix: str) -> list[ET.Element]:
    tag = f"{{{WORD_NS}}}p" if suffix == ".docx" else f"{{{DRAWING_NS}}}p"
    return list(root.iter(tag))


def _text_nodes(paragraph: ET.Element, suffix: str) -> list[ET.Element]:
    tag = f"{{{WORD_NS}}}t" if suffix == ".docx" else f"{{{DRAWING_NS}}}t"
    return list(paragraph.iter(tag))


def prepare_package_draft(source: Path, draft: Path, suffix: str) -> dict[str, Any]:
    """Extract editable paragraph blocks and return their package map."""
    token = secrets.token_hex(12)
    blocks: list[dict[str, Any]] = []
    sections: list[str] = []
    try:
        with zipfile.ZipFile(source) as archive:
            names = archive.namelist()
            for part in _editable_parts(names, suffix):
                root = ET.fromstring(archive.read(part))
                for paragraph_index, paragraph in enumerate(_paragraphs(root, suffix)):
                    nodes = _text_nodes(paragraph, suffix)
                    text = "".join(node.text or "" for node in nodes)
                    if not nodes or not text.strip():
                        continue
                    block_id = f"b{len(blocks) + 1:05d}"
                    blocks.append(
                        {
                            "id": block_id,
                            "part": part,
                            "paragraph_index": paragraph_index,
                            "original": text,
                        }
                    )
                    sections.extend(
                        [
                            f"<!-- vivid-clean:{token}:block:{block_id} -->",
                            text,
                            f"<!-- vivid-clean:{token}:endblock:{block_id} -->",
                            "",
                        ]
                    )
    except (OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        raise PackageEditError(
            f"couldn't read {source.name} as {suffix}: {exc}"
        ) from exc
    if not blocks:
        raise PackageEditError(f"{source.name} doesn't contain editable text blocks")
    draft.write_text("\n".join(sections), encoding="utf-8")
    return {"mode": "ooxml", "suffix": suffix, "token": token, "blocks": blocks}


def _read_revisions(draft: Path, editor: dict[str, Any]) -> dict[str, str]:
    try:
        text = draft.read_text(encoding="utf-8")
    except OSError as exc:
        raise PackageEditError(f"couldn't read the prepared draft: {exc}") from exc
    token = re.escape(str(editor["token"]))
    pattern = re.compile(
        rf"<!-- vivid-clean:{token}:block:(b\d{{5}}) -->\n(.*?)\n"
        rf"<!-- vivid-clean:{token}:endblock:\1 -->",
        re.DOTALL,
    )
    revisions: dict[str, str] = {}
    spans: list[tuple[int, int]] = []
    for match in pattern.finditer(text):
        block_id = match.group(1)
        if block_id in revisions:
            raise PackageEditError(f"the draft contains duplicate block {block_id}")
        revisions[block_id] = match.group(2).strip("\n")
        spans.append(match.span())
    expected = {str(block["id"]) for block in editor["blocks"]}
    if set(revisions) != expected:
        missing = sorted(expected - set(revisions))
        extra = sorted(set(revisions) - expected)
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected: {', '.join(extra)}")
        raise PackageEditError(
            "the draft's block markers changed (" + "; ".join(details) + ")"
        )
    outside = []
    cursor = 0
    for start, end in spans:
        outside.append(text[cursor:start])
        cursor = end
    outside.append(text[cursor:])
    if "".join(outside).strip():
        raise PackageEditError("the draft contains text outside its protected blocks")
    originals = {str(block["id"]): str(block["original"]) for block in editor["blocks"]}
    changed = [
        block_id
        for block_id, revised in revisions.items()
        if _protected_values(revised) != _protected_values(originals[block_id])
    ]
    if changed:
        raise PackageEditError(
            "protected values changed in "
            + ", ".join(changed)
            + "; keep numbers, URLs and email addresses unchanged"
        )
    return revisions


def _node_for_position(lengths: list[int], position: int) -> int:
    if not lengths:
        return 0
    cursor = 0
    for index, length in enumerate(lengths):
        if position < cursor + length:
            return index
        cursor += length
    return len(lengths) - 1


def _assign_across_span(
    assigned: list[list[str]],
    lengths: list[int],
    old_start: int,
    old_end: int,
    replacement: str,
) -> None:
    if not replacement:
        return
    if old_end <= old_start:
        assigned[_node_for_position(lengths, old_start)].extend(replacement)
        return
    spans: list[tuple[int, int]] = []
    cursor = 0
    for index, length in enumerate(lengths):
        overlap = max(0, min(old_end, cursor + length) - max(old_start, cursor))
        if overlap:
            spans.append((index, overlap))
        cursor += length
    if not spans:
        assigned[_node_for_position(lengths, old_start)].extend(replacement)
        return
    total = sum(weight for _index, weight in spans)
    consumed = 0
    cumulative_weight = 0
    for span_index, (node_index, weight) in enumerate(spans):
        cumulative_weight += weight
        end = (
            len(replacement)
            if span_index == len(spans) - 1
            else round(len(replacement) * cumulative_weight / total)
        )
        assigned[node_index].extend(replacement[consumed:end])
        consumed = end


def _replace_text(nodes: list[ET.Element], original: str, revised: str) -> None:
    if revised == original:
        return
    lengths = [len(node.text or "") for node in nodes]
    assigned: list[list[str]] = [[] for _ in nodes]
    matcher = SequenceMatcher(a=original, b=revised, autojunk=False)
    for operation, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if operation == "equal":
            for offset, char in enumerate(revised[new_start:new_end]):
                index = _node_for_position(lengths, old_start + offset)
                assigned[index].append(char)
        elif operation in {"replace", "insert"}:
            _assign_across_span(
                assigned,
                lengths,
                old_start,
                old_end,
                revised[new_start:new_end],
            )
    for node, characters in zip(nodes, assigned, strict=True):
        value = "".join(characters)
        node.text = value
        space = f"{{{XML_NS}}}space"
        if value[:1].isspace() or value[-1:].isspace():
            node.set(space, "preserve")
        else:
            node.attrib.pop(space, None)


def apply_package_draft(
    template: Path, draft: Path, destination: Path, editor: dict[str, Any]
) -> None:
    """Apply prepared text blocks to their original OOXML paragraphs atomically."""
    revisions = _read_revisions(draft, editor)
    suffix = str(editor["suffix"])
    blocks_by_part: dict[str, list[dict[str, Any]]] = {}
    for block in editor["blocks"]:
        blocks_by_part.setdefault(str(block["part"]), []).append(block)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        with (
            zipfile.ZipFile(template) as source,
            zipfile.ZipFile(temp_path, "w") as output,
        ):
            output.comment = source.comment
            for info in source.infolist():
                data = source.read(info.filename)
                if info.filename in blocks_by_part:
                    root = ET.fromstring(data)
                    paragraphs = _paragraphs(root, suffix)
                    for block in blocks_by_part[info.filename]:
                        index = int(block["paragraph_index"])
                        if index >= len(paragraphs):
                            raise PackageEditError(
                                f"{info.filename} lost paragraph {index} after preparation"
                            )
                        nodes = _text_nodes(paragraphs[index], suffix)
                        current = "".join(node.text or "" for node in nodes)
                        original = str(block["original"])
                        if current != original:
                            raise PackageEditError(
                                f"{info.filename} paragraph {index} changed after preparation"
                            )
                        _replace_text(nodes, original, revisions[str(block["id"])])
                    data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
                output.writestr(info, data)
        os.replace(temp_path, destination)
        _verify_package_structure(template, destination, editor)
    except (OSError, zipfile.BadZipFile, ET.ParseError, KeyError, ValueError) as exc:
        raise PackageEditError(f"couldn't apply the package-aware edit: {exc}") from exc
    finally:
        temp_path.unlink(missing_ok=True)


def _structure(element: ET.Element) -> tuple[Any, ...]:
    attributes = tuple(
        sorted(
            (name, value)
            for name, value in element.attrib.items()
            if name != f"{{{XML_NS}}}space"
        )
    )
    return (
        element.tag,
        attributes,
        tuple(_structure(child) for child in list(element)),
    )


def _verify_package_structure(
    template: Path, destination: Path, editor: dict[str, Any]
) -> None:
    """Prove that package editing changed text nodes, not document structure."""
    suffix = str(editor["suffix"])
    try:
        with zipfile.ZipFile(template) as before, zipfile.ZipFile(destination) as after:
            if before.namelist() != after.namelist():
                raise PackageEditError(
                    "package members changed during the writing pass"
                )
            editable = set(_editable_parts(before.namelist(), suffix))
            for name in before.namelist():
                before_data = before.read(name)
                after_data = after.read(name)
                if name in editable:
                    if _structure(ET.fromstring(before_data)) != _structure(
                        ET.fromstring(after_data)
                    ):
                        raise PackageEditError(
                            f"{name} structure changed during the writing pass"
                        )
                elif before_data != after_data:
                    raise PackageEditError(
                        f"{name} changed outside an editable text part"
                    )
    except (OSError, zipfile.BadZipFile, ET.ParseError) as exc:
        raise PackageEditError(f"couldn't verify the edited package: {exc}") from exc
