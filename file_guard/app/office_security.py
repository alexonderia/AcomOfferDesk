from __future__ import annotations

import io
import posixpath
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath
from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from .config import settings

_OFFICE_FORBIDDEN_EXTENSIONS = frozenset(
    {
        ".js",
        ".jse",
        ".vbs",
        ".vbe",
        ".wsf",
        ".wsh",
        ".ps1",
        ".psm1",
        ".bat",
        ".cmd",
        ".sh",
        ".py",
        ".php",
        ".pl",
        ".rb",
        ".jar",
        ".class",
        ".exe",
        ".dll",
        ".msi",
        ".com",
        ".scr",
        ".hta",
        ".html",
        ".htm",
        ".svg",
        ".bin",
    }
)

_OFFICE_XML_SCAN_PATHS = frozenset(
    {
        "[Content_Types].xml",
        "word/document.xml",
        "word/_rels/document.xml.rels",
        "word/settings.xml",
        "word/webSettings.xml",
        "xl/workbook.xml",
        "xl/_rels/workbook.xml.rels",
    }
)

_SUSPICIOUS_XML_MARKERS = (
    b"vbaProject",
    b"macros",
    b"macroEnabled",
    b"activeX",
    b"oleObject",
    b"Object",
    b"ms-its:",
    b"javascript:",
    b"vbscript:",
    b"powershell:",
    b"cmd.exe",
    b"wscript",
    b"cscript",
    b"shell",
    b"DDEAUTO",
    b"application/vnd.ms-office.vbaProject",
)

_SUSPICIOUS_EXTERNAL_TARGET_MARKERS = (
    b"javascript:",
    b"vbscript:",
    b"file:",
    b"cmd",
    b"powershell",
    b"ms-its:",
)


def validate_office_archive(
    *,
    extension: str,
    content_bytes: bytes,
) -> tuple[str, str] | None:
    required_entry = "word/document.xml" if extension == ".docx" else "xl/workbook.xml"
    if not content_bytes.startswith(b"PK\x03\x04"):
        return ("invalid_office_document", "Office document is corrupted or invalid")

    try:
        with zipfile.ZipFile(io.BytesIO(content_bytes)) as archive:
            infos = archive.infolist()
            names = {info.filename for info in infos}
    except zipfile.BadZipFile:
        return ("invalid_office_document", "Office document is corrupted or invalid")

    if "[Content_Types].xml" not in names or required_entry not in names:
        return ("invalid_office_document", "Office document is corrupted or invalid")
    if len(infos) > settings.office_max_entries:
        return ("invalid_office_document", "Office document exceeds safety limits")

    total_uncompressed = 0
    rels_to_scan: list[tuple[str, zipfile.ZipInfo]] = []

    for info in infos:
        path_failure = _validate_entry_path(info.orig_filename)
        if path_failure is not None:
            return path_failure

        suffix = Path(info.filename).suffix.lower()
        if suffix in _OFFICE_FORBIDDEN_EXTENSIONS:
            return ("invalid_office_document", "Office document contains forbidden content")
        lowered_name = info.filename.lower()
        if lowered_name.endswith("vbaproject.bin") or "/embeddings/" in lowered_name and lowered_name.endswith(".bin"):
            return ("invalid_office_document", "Office document contains forbidden content")

        if info.file_size > settings.office_max_entry_uncompressed_bytes:
            return ("invalid_office_document", "Office document exceeds safety limits")
        total_uncompressed += info.file_size
        if total_uncompressed > settings.office_max_total_uncompressed_bytes:
            return ("invalid_office_document", "Office document exceeds safety limits")
        if info.file_size > 0:
            if info.compress_size <= 0:
                return ("invalid_office_document", "Office document exceeds safety limits")
            if (info.file_size / info.compress_size) > settings.office_max_compression_ratio:
                return ("invalid_office_document", "Office document exceeds safety limits")

        if info.filename.endswith(".rels") or info.filename in _OFFICE_XML_SCAN_PATHS:
            rels_to_scan.append((info.filename, info))

    with zipfile.ZipFile(io.BytesIO(content_bytes)) as archive:
        for entry_name, info in rels_to_scan:
            content_failure = _scan_xml_entry(archive=archive, entry_name=entry_name, info=info)
            if content_failure is not None:
                return content_failure

    return None


def _validate_entry_path(name: str) -> tuple[str, str] | None:
    if not name:
        return ("invalid_office_document", "Office document is corrupted or invalid")
    if len(name) > settings.office_max_entry_name_length:
        return ("invalid_office_document", "Office document exceeds safety limits")
    if any(unicodedata.category(ch).startswith("C") for ch in name):
        return ("invalid_office_document", "Office document is corrupted or invalid")

    normalized_path = PurePosixPath(name)
    if (
        name.startswith(("/", "\\"))
        or "\\" in name
        or ".." in normalized_path.parts
    ):
        return ("invalid_office_document", "Office document is corrupted or invalid")
    return None


def _scan_xml_entry(
    *,
    archive: zipfile.ZipFile,
    entry_name: str,
    info: zipfile.ZipInfo,
) -> tuple[str, str] | None:
    if info.file_size > settings.office_max_xml_scan_bytes:
        return ("invalid_office_document", "Office document exceeds safety limits")

    try:
        with archive.open(info, "r") as entry:
            payload = entry.read(settings.office_max_xml_scan_bytes + 1)
    except (OSError, zipfile.BadZipFile, RuntimeError):
        return ("invalid_office_document", "Office document is corrupted or invalid")

    if len(payload) > settings.office_max_xml_scan_bytes:
        return ("invalid_office_document", "Office document exceeds safety limits")

    lowered = payload.lower()
    if any(marker.lower() in lowered for marker in _SUSPICIOUS_XML_MARKERS):
        return ("invalid_office_document", "Office document contains forbidden content")

    if entry_name.endswith(".rels"):
        return _scan_relationships(payload)
    try:
        root = ElementTree.fromstring(payload)
    except (ElementTree.ParseError, DefusedXmlException):
        return ("invalid_office_document", "Office document is corrupted or invalid")
    for element in root.iter():
        if "embed" in element.tag.rsplit("}", 1)[-1].casefold():
            return ("invalid_office_document", "Office document contains forbidden content")
        for attribute, reference in element.attrib.items():
            if "embed" not in attribute.rsplit("}", 1)[-1].casefold():
                continue
            if (element.tag != "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"
                    or attribute != "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
                    or not _is_internal_image(archive, entry_name, reference)):
                return ("invalid_office_document", "Office document contains forbidden content")
    return None


def _is_internal_image(archive: zipfile.ZipFile, entry_name: str, reference: str) -> bool:
    part = PurePosixPath(entry_name)
    relationships_name = str(part.parent / "_rels" / (part.name + ".rels"))
    try:
        info = archive.getinfo(relationships_name)
        if info.file_size > settings.office_max_xml_scan_bytes:
            return False
        root = ElementTree.fromstring(archive.read(info))
    except (KeyError, OSError, zipfile.BadZipFile, RuntimeError, ElementTree.ParseError, DefusedXmlException):
        return False
    relationships = [item for item in root if item.get("Id") == reference]
    if len(relationships) != 1:
        return False
    relationship = relationships[0]
    if (relationship.tag.rsplit("}", 1)[-1] != "Relationship"
            or relationship.get("Type") != "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
            or relationship.get("TargetMode", "Internal").casefold() != "internal"):
        return False
    target = relationship.get("Target", "")
    if not target or target.startswith(("/", "\\")) or "\\" in target:
        return False
    resolved = posixpath.normpath(posixpath.join(str(part.parent), target))
    if resolved.startswith("../") or Path(resolved).suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        return False
    return resolved in archive.namelist()


def _scan_relationships(payload: bytes) -> tuple[str, str] | None:
    try:
        root = ElementTree.fromstring(payload)
    except (ElementTree.ParseError, DefusedXmlException):
        return ("invalid_office_document", "Office document is corrupted or invalid")
    for relationship in root.iter():
        if relationship.tag.rsplit("}", 1)[-1] != "Relationship":
            continue
        if relationship.get("TargetMode", "").casefold() != "external":
            continue
        target = relationship.get("Target", "").casefold()
        if any(marker.decode("ascii") in target for marker in _SUSPICIOUS_EXTERNAL_TARGET_MARKERS):
            return ("invalid_office_document", "Office document contains forbidden content")
    return None
