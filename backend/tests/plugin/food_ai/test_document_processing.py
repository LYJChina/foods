from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

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
JPEG_HEADER = b"\xff\xd8\xff\xe0\x00\x10JFIF"
PNG_HEADER = b"\x89PNG\r\n\x1a\n"


def make_ooxml(*members: str) -> bytes:
    document = BytesIO()
    with ZipFile(document, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        for member in members:
            archive.writestr(member, "<part />")
    return document.getvalue()


@pytest.mark.parametrize(
    ("file_name", "content_type", "header", "expected_suffix"),
    [
        ("标签.pdf", "application/pdf", PDF_HEADER, ".pdf"),
        (
            "标签.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            make_ooxml("word/document.xml"),
            ".docx",
        ),
        (
            "标签.pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            make_ooxml("ppt/presentation.xml"),
            ".pptx",
        ),
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


def test_validate_upload_rejects_plain_zip_and_cross_type_ooxml_disguises() -> None:
    plain_zip = BytesIO()
    with ZipFile(plain_zip, "w", ZIP_DEFLATED) as archive:
        archive.writestr("notes.txt", "not an office document")
    word_document = make_ooxml("word/document.xml")
    presentation = make_ooxml("ppt/presentation.xml")

    assert (
        validate_upload(
            "标签.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            word_document,
            len(word_document),
            True,
        )
        == ".docx"
    )
    assert (
        validate_upload(
            "标签.pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            presentation,
            len(presentation),
            True,
        )
        == ".pptx"
    )
    with pytest.raises(ValueError, match="文件内容"):
        validate_upload(
            "标签.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            plain_zip.getvalue(),
            len(plain_zip.getvalue()),
            True,
        )
    with pytest.raises(ValueError, match="文件内容"):
        validate_upload(
            "标签.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            presentation,
            len(presentation),
            True,
        )


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
            {"type": "header", "text": "机密页眉", "page_idx": 0},
            {"type": "text", "text": "过敏原应明确标示。", "page_idx": 0},
            {"type": "text", "text": "第 1 页", "page_idx": 0},
            {"type": "title", "text": "配料", "text_level": 2, "page_idx": 1},
            {"type": "header", "text": "机密页眉", "page_idx": 1},
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


def test_extract_chunks_rejects_untrusted_output_exceeding_chunk_limit() -> None:
    mineru_result = {
        "document_id": "doc-003",
        "content_list": [{"type": "text", "text": f"第 {index} 条内容", "page_idx": 0} for index in range(201)],
    }

    with pytest.raises(ValueError, match="解析结果无效"):
        extract_chunks(mineru_result)


def test_extract_chunks_truncates_untrusted_heading_path_to_schema_limit() -> None:
    mineru_result = {
        "document_id": "doc-004",
        "content_list": [
            {"type": "title", "text": "标题" * 400, "text_level": 1, "page_idx": 0},
            {"type": "text", "text": "公开标签说明。", "page_idx": 0},
        ],
    }

    chunks = extract_chunks(mineru_result)

    assert len(chunks[0].heading or "") == 500
    assert chunks[0].heading == "标题" * 250


def test_extract_chunks_preserves_repeated_body_text_across_pages() -> None:
    mineru_result = {
        "document_id": "doc-005",
        "content_list": [
            {"type": "text", "text": "本条款适用于所有产品。", "page_idx": 0},
            {"type": "text", "text": "本条款适用于所有产品。", "page_idx": 1},
        ],
    }

    chunks = extract_chunks(mineru_result)

    assert [chunk.content for chunk in chunks] == ["本条款适用于所有产品。", "本条款适用于所有产品。"]
