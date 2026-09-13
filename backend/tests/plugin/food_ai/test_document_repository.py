from datetime import UTC, datetime, timedelta

import pytest

from app.config.setting import Settings
from app.plugin.food_ai.document_repository import DocumentRepository
from app.plugin.food_ai.document_schema import DocumentChunk, DocumentRecord, DocumentStatus, QuestionResult


def build_document(**overrides: object) -> DocumentRecord:
    values: dict[str, object] = {
        "document_id": "doc-001",
        "original_filename": "欧盟食品标签指引.pdf",
        "storage_path": "documents/doc-001.pdf",
        "content_type": "application/pdf",
        "size_bytes": 1024,
        "sha256": "a" * 64,
        "status": DocumentStatus.PENDING,
        "created_at": datetime(2026, 9, 13, 8, tzinfo=UTC),
        "updated_at": datetime(2026, 9, 13, 8, tzinfo=UTC),
        "expires_at": datetime(2026, 9, 20, 8, tzinfo=UTC),
    }
    values.update(overrides)
    return DocumentRecord(**values)


def build_chunk(index: int, content: str) -> DocumentChunk:
    return DocumentChunk(
        document_id="doc-001",
        chunk_index=index,
        content=content,
        page_number=index + 1,
        heading=f"第 {index + 1} 节",
    )


def test_create_read_and_update_status(tmp_path) -> None:
    repository = DocumentRepository(tmp_path / "documents.db")
    created = repository.create_document(build_document())

    assert created.document_id == "doc-001"
    assert created.status is DocumentStatus.PENDING
    assert repository.get_document("missing") is None

    updated = repository.update_status("doc-001", DocumentStatus.PROCESSING, mineru_task_id="task-100")

    assert updated is not None
    assert updated.status is DocumentStatus.PROCESSING
    assert updated.mineru_task_id == "task-100"
    assert repository.get_document("doc-001") == updated


def test_chunk_order_search_ranking_and_question_persistence(tmp_path) -> None:
    repository = DocumentRepository(tmp_path / "documents.db")
    repository.create_document(build_document())
    repository.replace_chunks(
        "doc-001",
        [
            build_chunk(2, "标签应当标示食品名称。"),
            build_chunk(0, "欧盟食品标签需要列明过敏原和配料表。"),
            build_chunk(1, "欧盟食品出口还应核验认证材料。"),
        ],
    )

    assert [chunk.chunk_index for chunk in repository.list_chunks("doc-001")] == [0, 1, 2]
    assert [chunk.chunk_index for chunk in repository.search_chunks("doc-001", "欧盟食品标签", limit=3)] == [0, 1, 2]

    question = QuestionResult(
        question_id="question-001",
        document_id="doc-001",
        question="标签需要什么？",
        answer="应列明过敏原和配料表。",
        citations=[],
        created_at=datetime(2026, 9, 13, 9, tzinfo=UTC),
    )
    assert repository.save_question(question) == question


def test_delete_cascades_chunks_questions_and_expired_documents(tmp_path) -> None:
    repository = DocumentRepository(tmp_path / "documents.db")
    repository.create_document(build_document())
    repository.replace_chunks("doc-001", [build_chunk(0, "待删除的食品标签内容")])
    repository.save_question(
        QuestionResult(
            question_id="question-001",
            document_id="doc-001",
            question="示例问题",
            answer="示例回答",
            citations=[],
            created_at=datetime(2026, 9, 13, 9, tzinfo=UTC),
        )
    )

    assert repository.delete_document("doc-001") is True
    assert repository.get_document("doc-001") is None
    assert repository.list_chunks("doc-001") == []

    repository.create_document(
        build_document(
            document_id="doc-expired",
            storage_path="documents/doc-expired.pdf",
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
    )
    repository.create_document(
        build_document(
            document_id="doc-retained",
            storage_path="documents/doc-retained.pdf",
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
    )

    assert repository.delete_expired(datetime.now(UTC)) == 1
    assert repository.get_document("doc-expired") is None
    assert repository.get_document("doc-retained") is not None


def test_document_settings_default_to_one_day_retention_and_page_limit() -> None:
    settings = Settings(_env_file=None)

    assert settings.DOCUMENT_RETENTION_DAYS == 1
    assert settings.DOCUMENT_MAX_PAGES == 100


def test_delete_expired_removes_fts_entries_when_fts5_is_available(tmp_path) -> None:
    repository = DocumentRepository(tmp_path / "documents.db")
    if not repository._fts_available:
        pytest.skip("SQLite 构建未提供 FTS5")
    repository.create_document(
        build_document(
            document_id="doc-expired",
            storage_path="documents/doc-expired.pdf",
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
    )
    repository.replace_chunks(
        "doc-expired",
        [
            DocumentChunk(
                document_id="doc-expired",
                chunk_index=0,
                content="过期文档的食品标签内容",
            )
        ],
    )

    assert repository.delete_expired(datetime.now(UTC)) == 1
    with repository._connect() as connection:
        fts_rows = connection.execute(
            "SELECT document_id FROM document_chunks_fts WHERE document_id = ?",
            ("doc-expired",),
        ).fetchall()
    assert fts_rows == []
