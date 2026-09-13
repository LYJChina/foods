"""Safe validation and deterministic MinerU-result chunking for document QA."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.config.setting import settings
from app.plugin.food_ai.document_schema import DocumentChunk

MAX_CHUNK_CHARACTERS = 1200
CHUNK_OVERLAP_CHARACTERS = 80

_PAGE_MARKER = re.compile(r"^(?:第\s*\d+\s*页|page\s*\d+)$", re.IGNORECASE)
_PAGE_FURNITURE_TYPES = {"header", "footer", "page_header", "page_footer"}
_SUPPORTED_TYPES = {
    ".pdf": ("application/pdf", (b"%PDF-",)),
    ".docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        (b"PK\x03\x04",),
    ),
    ".pptx": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        (b"PK\x03\x04",),
    ),
    ".jpg": ("image/jpeg", (b"\xff\xd8\xff",)),
    ".jpeg": ("image/jpeg", (b"\xff\xd8\xff",)),
    ".png": ("image/png", (b"\x89PNG\r\n\x1a\n",)),
}
_DISK_SUFFIXES = {".pdf", ".docx", ".pptx", ".jpg", ".png"}


def validate_upload(
    file_name: str,
    content_type: str | None,
    header: bytes,
    size: int,
    confirmed_low_sensitivity: bool,
) -> str:
    """Validate untrusted upload metadata and return its safe disk suffix."""
    if not confirmed_low_sensitivity:
        raise ValueError("仅允许已确认的低敏公开资料，不得上传配方、工艺、成本、客户、订单或生产经营数据。")
    if not isinstance(size, int) or size < 0 or size > settings.DOCUMENT_MAX_UPLOAD_BYTES:
        raise ValueError("文件大小超过限制，最大允许 20MB。")

    suffix = Path(file_name or "").suffix.lower()
    type_definition = _SUPPORTED_TYPES.get(suffix)
    if type_definition is None or (content_type or "").lower().split(";", 1)[0].strip() != type_definition[0]:
        raise ValueError("文件类型与扩展名不匹配或不受支持。")
    if not isinstance(header, bytes) or not any(header.startswith(signature) for signature in type_definition[1]):
        raise ValueError("文件内容与声明的类型不匹配。")
    if suffix in {".docx", ".pptx"} and not _is_expected_ooxml(header, suffix):
        raise ValueError("文件内容与声明的类型不匹配。")
    return ".jpg" if suffix == ".jpeg" else suffix


def sanitize_file_name(file_name: str, approved_suffix: str | None = None) -> str:
    """Create a disk name independent of an untrusted client path or filename."""
    suffix = (approved_suffix or Path(file_name or "").suffix).lower()
    if suffix == ".jpeg":
        suffix = ".jpg"
    if suffix not in _DISK_SUFFIXES:
        raise ValueError("文件类型不受支持。")
    return f"{uuid4().hex}{suffix}"


def count_pdf_pages(pdf: bytes | BinaryIO) -> int:
    """Return a PDF page count and enforce the configured upper boundary."""
    try:
        stream = BytesIO(pdf) if isinstance(pdf, bytes) else pdf
        page_count = len(PdfReader(stream).pages)
    except (OSError, PdfReadError, TypeError, ValueError) as exc:
        raise ValueError("PDF 文件无效或无法读取。") from exc
    if page_count > settings.DOCUMENT_MAX_PAGES:
        raise ValueError(f"PDF 页数超过限制，最大允许 {settings.DOCUMENT_MAX_PAGES} 页。")
    return page_count


def extract_chunks(mineru_result: Mapping[str, Any]) -> list[DocumentChunk]:
    """Turn MinerU content-list data into bounded, source-attributed document chunks."""
    document_id = str(mineru_result.get("document_id") or "document")
    content_list = _find_content_list(mineru_result)
    entries = _text_entries(content_list)

    chunks: list[DocumentChunk] = []
    heading_levels: dict[int, str] = {}
    for entry in entries:
        text = entry["text"]
        if _is_title(entry["type"]):
            level = _heading_level(entry["level"])
            heading_levels[level] = text
            for obsolete_level in tuple(heading_levels):
                if obsolete_level > level:
                    del heading_levels[obsolete_level]
            continue
        if _is_page_furniture(entry["type"], text):
            continue
        heading = _heading_path(heading_levels)
        page_number = entry["page"] + 1 if entry["page"] is not None else None
        for part in _split_text(text):
            if len(chunks) >= settings.DOCUMENT_MAX_CHUNKS:
                raise ValueError("解析结果无效。")
            chunks.append(
                DocumentChunk(
                    document_id=document_id,
                    chunk_index=len(chunks),
                    content=part,
                    page_number=page_number,
                    heading=heading,
                )
            )
    return chunks


def _is_expected_ooxml(content: bytes, suffix: str) -> bool:
    required_part = "word/document.xml" if suffix == ".docx" else "ppt/presentation.xml"
    try:
        with ZipFile(BytesIO(content)) as archive:
            members = set(archive.namelist())
    except (BadZipFile, OSError):
        return False
    return "[Content_Types].xml" in members and required_part in members


def _find_content_list(result: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    direct = result.get("content_list")
    if isinstance(direct, Sequence) and not isinstance(direct, (str, bytes)):
        return [item for item in direct if isinstance(item, Mapping)]
    results = result.get("results")
    if isinstance(results, Mapping):
        for parsed in results.values():
            if isinstance(parsed, Mapping):
                nested = parsed.get("content_list")
                if isinstance(nested, Sequence) and not isinstance(nested, (str, bytes)):
                    return [item for item in nested if isinstance(item, Mapping)]
    return []


def _text_entries(content_list: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for item in content_list:
        text = item.get("text")
        if not isinstance(text, str) or not (cleaned := " ".join(text.split())):
            continue
        raw_page = item.get("page_idx")
        page = raw_page if isinstance(raw_page, int) and raw_page >= 0 else None
        entries.append({"type": str(item.get("type") or "text").lower(), "text": cleaned, "level": item.get("text_level"), "page": page})
    return entries


def _is_page_furniture(item_type: str, text: str) -> bool:
    return item_type in _PAGE_FURNITURE_TYPES or bool(_PAGE_MARKER.fullmatch(text))


def _is_title(item_type: str) -> bool:
    return item_type in {"title", "heading"}


def _heading_level(value: object) -> int:
    return value if isinstance(value, int) and value > 0 else 1


def _heading_path(heading_levels: Mapping[int, str]) -> str | None:
    heading = " / ".join(heading_levels[level] for level in sorted(heading_levels))
    return heading[:500] or None


def _split_text(text: str) -> list[str]:
    if len(text) <= MAX_CHUNK_CHARACTERS:
        return [text]
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + MAX_CHUNK_CHARACTERS, len(text))
        parts.append(text[start:end])
        if end == len(text):
            break
        start = end - CHUNK_OVERLAP_CHARACTERS
    return parts
