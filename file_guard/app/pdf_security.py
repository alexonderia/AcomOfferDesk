from __future__ import annotations

import zlib

from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, NameObject, StreamObject


_ACTIVE_NAMES = frozenset({"/JavaScript", "/JS", "/OpenAction", "/AA", "/Launch", "/RichMedia", "/XFA"})
_C2PA_MIME_TYPES = frozenset({"application/c2pa", "application/x-c2pa-manifest-store"})
_C2PA_STORE_UUID = bytes.fromhex("6332706100110010800000aa00389b71")
_C2PA_MANIFEST_UUIDS = frozenset(
    bytes.fromhex(value)
    for value in (
        "63326d6100110010800000aa00389b71",  # Standard manifest (c2ma).
        "6332636d00110010800000aa00389b71",  # Compressed manifest (c2cm).
        "6332756d00110010800000aa00389b71",  # Update manifest (c2um).
    )
)
_MAX_PDF_OBJECTS = 100_000
_MAX_JUMBF_BOXES = 4096
_MAX_JUMBF_DEPTH = 32


def inspect_pdf_metadata(reader: PdfReader, *, max_metadata_bytes: int) -> list[bytes]:
    """Allow only framed C2PA metadata, returning decoded bytes for antivirus scanning.

    This checks the passive container, not the authenticity of C2PA signatures. An
    attachment name or MIME label alone must never exempt arbitrary embedded files.
    """
    embedded_streams: dict[int, StreamObject] = {}
    declared_streams: set[int] = set()
    for obj in _pdf_objects(reader):
        if isinstance(obj, NameObject) and obj in _ACTIVE_NAMES:
            raise ValueError("PDF contains active content")
        if not isinstance(obj, DictionaryObject):
            continue
        if obj.get("/Type") == "/EmbeddedFile":
            if not isinstance(obj, StreamObject):
                raise ValueError("Invalid embedded file stream")
            embedded_streams[id(obj)] = obj
        if "/EF" not in obj:
            continue
        if obj.get("/Type") != "/Filespec" or obj.get("/AFRelationship") != "/C2PA_Manifest":
            raise ValueError("PDF contains a non-metadata attachment")
        # Older C2PA producers put the MIME type on the stream only.
        if "/Subtype" in obj and str(obj["/Subtype"]).lstrip("/") not in _C2PA_MIME_TYPES:
            raise ValueError("Unsupported metadata MIME type")
        files = obj["/EF"]
        if not isinstance(files, DictionaryObject) or not files or set(files) - {"/F", "/UF"}:
            raise ValueError("Invalid metadata file specification")
        for reference in files.values():
            stream = reference.get_object()
            if not isinstance(stream, StreamObject) or stream.get("/Type") != "/EmbeddedFile":
                raise ValueError("Invalid metadata stream")
            declared_streams.add(id(stream))

    if set(embedded_streams) != declared_streams:
        raise ValueError("PDF contains an undeclared attachment")

    metadata: list[bytes] = []
    remaining = max_metadata_bytes
    for stream in embedded_streams.values():
        if str(stream.get("/Subtype", "")).lstrip("/") not in _C2PA_MIME_TYPES:
            raise ValueError("Unsupported embedded file MIME type")
        data = _metadata_bytes(stream, limit=remaining)
        _validate_c2pa_store(data)
        metadata.append(data)
        remaining -= len(data)
    return metadata


def _pdf_objects(reader: PdfReader):
    # Include xref and object-stream entries: Names/EmbeddedFiles alone misses
    # associated files, annotation attachments and otherwise unreferenced objects.
    pending = [reader.trailer]
    for generation, entries in reader.xref.items():
        if generation == 65535:
            continue
        for number in entries:
            if number:
                pending.append(IndirectObject(number, generation, reader))
                if len(pending) > _MAX_PDF_OBJECTS:
                    raise ValueError("PDF object limit exceeded")
    for number in reader.xref_objStm:
        pending.append(IndirectObject(number, 0, reader))
        if len(pending) > _MAX_PDF_OBJECTS:
            raise ValueError("PDF object limit exceeded")

    visited: set[int] = set()
    references: set[tuple[int, int]] = set()
    examined = 0
    while pending:
        examined += 1
        if examined > _MAX_PDF_OBJECTS:
            raise ValueError("PDF object limit exceeded")
        obj = pending.pop()
        if isinstance(obj, IndirectObject):
            reference = (obj.idnum, obj.generation)
            if reference in references:
                continue
            references.add(reference)
            obj = obj.get_object()
            if obj is None:
                raise ValueError("Unresolved PDF object")
        if id(obj) in visited:
            continue
        visited.add(id(obj))
        yield obj
        if isinstance(obj, DictionaryObject):
            pending.extend(obj.keys())
            pending.extend(obj.values())
        elif isinstance(obj, ArrayObject):
            pending.extend(obj)
        if len(pending) > _MAX_PDF_OBJECTS:
            raise ValueError("PDF object limit exceeded")


def _metadata_bytes(stream: StreamObject, *, limit: int) -> bytes:
    # Avoid get_data() on compressed, untrusted metadata: it can allocate the
    # entire inflated stream before a size check. PDF streams retain encoded _data.
    data = stream._data
    filters = stream.get("/Filter")
    if isinstance(filters, ArrayObject) and len(filters) == 1:
        filters = filters[0]
    if filters is None:
        if len(data) > limit:
            raise ValueError("PDF metadata size limit exceeded")
        return data
    if filters not in ("/FlateDecode", "/Fl") or stream.get("/DecodeParms"):
        raise ValueError("Unsupported PDF metadata encoding")
    inflater = zlib.decompressobj()
    decoded = inflater.decompress(data, limit + 1)
    if len(decoded) > limit or not inflater.eof or inflater.unused_data:
        raise ValueError("Invalid or oversized PDF metadata")
    return decoded


def _boxes(data: memoryview):
    offset = 0
    count = 0
    while offset < len(data):
        count += 1
        if count > _MAX_JUMBF_BOXES:
            raise ValueError("C2PA box limit exceeded")
        if len(data) - offset < 8:
            raise ValueError("Truncated JUMBF box")
        size = int.from_bytes(data[offset : offset + 4], "big")
        kind = bytes(data[offset + 4 : offset + 8])
        header = 8
        if size == 1:
            if len(data) - offset < 16:
                raise ValueError("Truncated JUMBF box")
            size = int.from_bytes(data[offset + 8 : offset + 16], "big")
            header = 16
        if size < header or offset + size > len(data):
            raise ValueError("Invalid JUMBF box size")
        yield kind, data[offset + header : offset + size]
        offset += size


def _validate_c2pa_store(data: bytes) -> None:
    boxes = list(_boxes(memoryview(data)))
    if len(boxes) != 1 or boxes[0][0] != b"jumb":
        raise ValueError("Attachment is not a C2PA manifest store")
    store = list(_boxes(boxes[0][1]))
    if not store or store[0][0] != b"jumd":
        raise ValueError("Missing C2PA store description")
    description = bytes(store[0][1])
    if (
        len(description) < 22
        or description[:16] != _C2PA_STORE_UUID
        or not description[16] & 2
        or description[17:].split(b"\x00", 1)[0] != b"c2pa"
    ):
        raise ValueError("Invalid C2PA store description")

    pending = [(boxes[0][1], 0)]
    count = 0
    has_manifest = False
    while pending:
        payload, depth = pending.pop()
        if depth > _MAX_JUMBF_DEPTH:
            raise ValueError("C2PA nesting limit exceeded")
        for kind, content in _boxes(payload):
            count += 1
            if count > _MAX_JUMBF_BOXES:
                raise ValueError("C2PA box limit exceeded")
            if kind == b"jumb":
                children = iter(_boxes(content))
                first = next(children, None)
                if first is None or first[0] != b"jumd" or len(first[1]) < 17:
                    raise ValueError("Invalid C2PA superbox")
                if depth == 0 and bytes(first[1][:16]) in _C2PA_MANIFEST_UUIDS:
                    has_manifest = True
                pending.append((content, depth + 1))
    if not has_manifest:
        raise ValueError("C2PA store has no manifest")
