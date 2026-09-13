from __future__ import annotations

from io import BytesIO

import pytest
from pypdf import PdfWriter

from app.plugin.food_ai.document_processing import (
    MAX_CHUNK_CHARACTERS,
    count_pdf_pages,
    extract_chunks,
    sanitize_file_name,
    validate_upload,
)

PDF_HEADER = b"%PDF-1.7\n"
DOCX_HEADER = b"PK\x03\x04\x14\x00\x06\x00"
JPEG_HEADER = b"\xff\xd8\xff\xe0\x00\x10JFIF"
PNG_HEADER = b"\x89PNG\r\n\x1a\n"


@pytest.mark.parametrize(
    ("file_name", "content_type", "header", "expected_suffix"),
    [
        ("标签.pdf", "application/pdf", PDF_HEADER, ".pdf"),
        ("标签.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", DOCX_HEADER, ".docx"),
        ("标签.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation", DOCX_HEADER, ".pptx"),
        ("标签.jpeg", "image/jpeg", JPEG_HEADER, ".jpg"),
        ("标签.png", "image/png", PNG_HEADER, ".png"),
    ],
)
def test_validate_upload_accepts_only_supported_extension_mime_and_signature(
    file_name: str, content_type: str, header: bytes, expected_suffix: str
) -> None:
    assert validate_upload(file_name, content_type, header, 20 * 1024 * 1024, True) == expected_suffix


def test_validate_upload_rejects_mismatched_extension_mime_or_signature() -> None:
    with pytest.raises(ValueError, match="文件类型"):
        validate_upload("标签.pdf", "image/png", PNG_HEADER, 1, True)

    with pytest.raises(ValueError, match="文件内容"):
        validate_upload("标签.pdf", "application/pdf", PNG_HEADER, 1, True)


def test_validate_upload_enforces_size_boundary_and_low_sensitivity_declaration() -> None:
    assert validate_upload("标签.pdf", "application/pdf", PDF_HEADER, 20 * 1024 * 1024, True) == ".pdf"

    with pytest.raises(ValueError, match="20MB"):
        validate_upload("标签.pdf", "application/pdf", PDF_HEADER, 20 * 1024 * 1024 + 1, True)
    with pytest.raises(ValueError, match="低敏"):
        validate_upload("标签.pdf", "application/pdf", PDF_HEADER, 1, False)


def test_sanitize_file_name_never_preserves_user_supplied_path() -> None:
    disk_name = sanitize_file_name("../../配方.pdf", ".pdf")

    assert disk_name.endswith(".pdf")
    assert "/" not in disk_name
    assert "\\" not in disk_name
    assert "配方" not in disk_name


def test_count_pdf_pages_rejects_document_over_one_hundred_pages() -> None:
    writer = PdfWriter()
    for _ in range(101):
        writer.add_blank_page(width=72, height=72)
    document = BytesIO()
    writer.write(document)

    with pytest.raises(ValueError, match="100"):
        count_pdf_pages(document.getvalue())


def test_extract_chunks_removes_repeated_headers_and_footers_and_preserves_context() -> None:
    mineru_result = {
        "document_id": "doc-001",
        "content_list": [
            {"type": "title", "text": "食品标签", "text_level": 1, "page_idx": 0},
            {"type": "text", "text": "机密页眉", "page_idx": 0},
            {"type": "text", "text": "过敏原应明确标示。", "page_idx": 0},
            {"type": "text", "text": "第 1 页", "page_idx": 0},
            {"type": "title", "text": "配料", "text_level": 2, "page_idx": 1},
            {"type": "text", "text": "机密页眉", "page_idx": 1},
            {"type": "text", "text": "配料应按含量递减顺序列出。", "page_idx": 1},
            {"type": "text", "text": "第 2 页", "page_idx": 1},
        ],
    }

    chunks = extract_chunks(mineru_result)

    assert [(chunk.document_id, chunk.chunk_index, chunk.page_number, chunk.heading) for chunk in chunks] == [
        ("doc-001", 0, 1, "食品标签"),
        ("doc-001", 1, 2, "食品标签 / 配料"),
    ]
    assert [chunk.content for chunk in chunks] == ["过敏原应明确标示。", "配料应按含量递减顺序列出。"]


def test_extract_chunks_uses_stable_indices_and_bounded_overlapping_content() -> None:
    paragraph = "标签信息" * (MAX_CHUNK_CHARACTERS // 4 + 80)
    mineru_result = {
        "document_id": "doc-002",
        "content_list": [
            {"type": "title", "text": "通则", "text_level": 1, "page_idx": 2},
            {"type": "text", "text": paragraph, "page_idx": 2},
        ],
    }

    first = extract_chunks(mineru_result)
    second = extract_chunks(mineru_result)

    assert [chunk.chunk_index for chunk in first] == list(range(len(first)))
    assert first == second
    assert all(len(chunk.content) <= MAX_CHUNK_CHARACTERS for chunk in first)
    assert first[0].page_number == 3
    assert first[0].heading == "通则"
    assert first[0].content[-80:] == first[1].content[:80]
