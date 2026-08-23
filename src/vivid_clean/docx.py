"""Safe DOCX property removal."""

from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

PROPERTY_PARTS = {
    "docProps/core.xml",
    "docProps/app.xml",
    "docProps/custom.xml",
}
PROPERTY_TYPES = {
    "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties",
}


def _clean_relationships(data: bytes) -> bytes:
    root = ET.fromstring(data)
    for child in list(root):
        if (
            child.attrib.get("Type") in PROPERTY_TYPES
            or child.attrib.get("Target", "").lstrip("/") in PROPERTY_PARTS
        ):
            root.remove(child)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _clean_content_types(data: bytes) -> bytes:
    root = ET.fromstring(data)
    for child in list(root):
        if child.attrib.get("PartName", "").lstrip("/") in PROPERTY_PARTS:
            root.remove(child)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def scrub_docx(source: str | Path, destination: str | Path | None = None) -> Path:
    """Remove document properties and their package references atomically."""
    source_path = Path(source)
    target_path = Path(destination) if destination else source_path
    try:
        with zipfile.ZipFile(source_path, "r") as archive:
            if "[Content_Types].xml" not in archive.namelist():
                raise ValueError(f"{source_path.name} isn't a DOCX package")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            fd, temp_name = tempfile.mkstemp(
                prefix=f".{target_path.name}.", suffix=".tmp", dir=target_path.parent
            )
            os.close(fd)
            temp_path = Path(temp_name)
            try:
                with zipfile.ZipFile(temp_path, "w") as output:
                    for info in archive.infolist():
                        if info.filename in PROPERTY_PARTS:
                            continue
                        data = archive.read(info.filename)
                        if info.filename == "_rels/.rels":
                            data = _clean_relationships(data)
                        elif info.filename == "[Content_Types].xml":
                            data = _clean_content_types(data)
                        output.writestr(info, data)
                os.replace(temp_path, target_path)
            finally:
                temp_path.unlink(missing_ok=True)
    except zipfile.BadZipFile as exc:
        raise ValueError(f"{source_path.name} isn't a readable DOCX file") from exc
    return target_path
