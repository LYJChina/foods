import json
import re
import sqlite3
import unicodedata
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from app.plugin.food_ai.document_schema import DocumentChunk, DocumentRecord, DocumentStatus, QuestionResult


class DocumentRepository:
    """SQLite persistence for document parsing and grounded question answering."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._fts_available = False
        self._initialize()

    def create_document(self, document: DocumentRecord) -> DocumentRecord:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    document_id, original_filename, storage_path, content_type, size_bytes, sha256,
                    status, document_parser_task_id, error_message, created_at, updated_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._document_values(document),
            )
        return document

    def update_status(
        self,
        document_id: str,
        status: DocumentStatus,
        *,
        document_parser_task_id: str | None = None,
        error_message: str | None = None,
    ) -> DocumentRecord | None:
        updated_at = datetime.now(UTC)
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE documents
                SET status = ?, document_parser_task_id = COALESCE(?, document_parser_task_id),
                    error_message = ?, updated_at = ?
                WHERE document_id = ?
                """,
                (status.value, document_parser_task_id, error_message, self._serialize_datetime(updated_at), document_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_document(document_id)

    def replace_chunks(self, document_id: str, chunks: Iterable[DocumentChunk]) -> list[DocumentChunk]:
        ordered_chunks = sorted(chunks, key=lambda chunk: chunk.chunk_index)
        if any(chunk.document_id != document_id for chunk in ordered_chunks):
            raise ValueError("所有内容块必须属于同一文档")
        if len({chunk.chunk_index for chunk in ordered_chunks}) != len(ordered_chunks):
            raise ValueError("内容块序号不能重复")

        with self._connect() as connection:
            if not self._document_exists(connection, document_id):
                raise KeyError(f"文档不存在: {document_id}")
            connection.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))
            if self._fts_available:
                connection.execute("DELETE FROM document_chunks_fts WHERE document_id = ?", (document_id,))
            for chunk in ordered_chunks:
                connection.execute(
                    """
                    INSERT INTO document_chunks (document_id, chunk_index, content, page_number, heading)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (chunk.document_id, chunk.chunk_index, chunk.content, chunk.page_number, chunk.heading),
                )
                if self._fts_available:
                    connection.execute(
                        "INSERT INTO document_chunks_fts (document_id, chunk_index, content) VALUES (?, ?, ?)",
                        (chunk.document_id, chunk.chunk_index, chunk.content),
                    )
        return ordered_chunks

    def get_document(self, document_id: str) -> DocumentRecord | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,)).fetchone()
        return self._record_from_row(row) if row else None

    def list_chunks(self, document_id: str) -> list[DocumentChunk]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT document_id, chunk_index, content, page_number, heading FROM document_chunks WHERE document_id = ? ORDER BY chunk_index ASC",
                (document_id,),
            ).fetchall()
        return [DocumentChunk.model_validate(dict(row)) for row in rows]

    def search_chunks(self, document_id: str, query: str, *, limit: int = 5) -> list[DocumentChunk]:
        if limit <= 0 or not query.strip():
            return []
        if self._fts_available:
            chunks = self._search_fts(document_id, query, limit)
            if chunks:
                return chunks
        return self._search_keywords(document_id, query, limit)

    def save_question(self, result: QuestionResult) -> QuestionResult:
        citations_json = json.dumps([citation.model_dump(mode="json") for citation in result.citations], ensure_ascii=False)
        with self._connect() as connection:
            if not self._document_exists(connection, result.document_id):
                raise KeyError(f"文档不存在: {result.document_id}")
            connection.execute(
                """
                INSERT INTO document_questions (question_id, document_id, question, answer, citations_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (result.question_id, result.document_id, result.question, result.answer, citations_json, self._serialize_datetime(result.created_at)),
            )
        return result

    def delete_document(self, document_id: str) -> bool:
        with self._connect() as connection:
            if self._fts_available:
                connection.execute("DELETE FROM document_chunks_fts WHERE document_id = ?", (document_id,))
            cursor = connection.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
        return cursor.rowcount == 1

    def delete_expired(self, now: datetime | None = None) -> int:
        cutoff = self._serialize_datetime(now or datetime.now(UTC))
        with self._connect() as connection:
            rows = connection.execute("SELECT document_id FROM documents WHERE expires_at <= ?", (cutoff,)).fetchall()
            document_ids = [row["document_id"] for row in rows]
            if self._fts_available:
                connection.executemany("DELETE FROM document_chunks_fts WHERE document_id = ?", ((document_id,) for document_id in document_ids))
            deleted_count = sum(
                connection.execute("DELETE FROM documents WHERE document_id = ?", (document_id,)).rowcount for document_id in document_ids
            )
        return deleted_count

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    original_filename TEXT NOT NULL,
                    storage_path TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    status TEXT NOT NULL,
                    document_parser_task_id TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS document_chunks (
                    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    page_number INTEGER,
                    heading TEXT,
                    PRIMARY KEY (document_id, chunk_index)
                );
                CREATE TABLE IF NOT EXISTS document_questions (
                    question_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    citations_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_documents_expires_at ON documents(expires_at);
                CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks(document_id, chunk_index);
                """
            )
            try:
                connection.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS document_chunks_fts USING fts5(document_id UNINDEXED, chunk_index UNINDEXED, content)"
                )
            except sqlite3.OperationalError:
                self._fts_available = False
            else:
                self._fts_available = True

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _search_fts(self, document_id: str, query: str, limit: int) -> list[DocumentChunk]:
        tokens = self._tokens(query)
        if not tokens:
            return []
        fts_query = " OR ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT chunks.document_id, chunks.chunk_index, chunks.content, chunks.page_number, chunks.heading
                FROM document_chunks_fts
                JOIN document_chunks AS chunks
                  ON chunks.document_id = document_chunks_fts.document_id
                 AND chunks.chunk_index = document_chunks_fts.chunk_index
                WHERE document_chunks_fts.content MATCH ? AND document_chunks_fts.document_id = ?
                ORDER BY bm25(document_chunks_fts), chunks.chunk_index ASC
                LIMIT ?
                """,
                (fts_query, document_id, limit),
            ).fetchall()
        return [DocumentChunk.model_validate(dict(row)) for row in rows]

    def _search_keywords(self, document_id: str, query: str, limit: int) -> list[DocumentChunk]:
        query_tokens = set(self._tokens(query))
        if not query_tokens:
            return []
        candidates = self.list_chunks(document_id)
        ranked = [
            (len(query_tokens.intersection(self._tokens(chunk.content))), chunk.chunk_index, chunk)
            for chunk in candidates
        ]
        return [chunk for score, _, chunk in sorted(ranked, key=lambda item: (-item[0], item[1])) if score > 0][:limit]

    @staticmethod
    def _tokens(value: str) -> list[str]:
        normalized = unicodedata.normalize("NFKC", value).lower()
        words = re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]", normalized)
        return words

    @staticmethod
    def _document_exists(connection: sqlite3.Connection, document_id: str) -> bool:
        return connection.execute("SELECT 1 FROM documents WHERE document_id = ?", (document_id,)).fetchone() is not None

    @staticmethod
    def _serialize_datetime(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat()

    @classmethod
    def _document_values(cls, document: DocumentRecord) -> tuple[object, ...]:
        return (
            document.document_id,
            document.original_filename,
            document.storage_path,
            document.content_type,
            document.size_bytes,
            document.sha256,
            document.status.value,
            document.document_parser_task_id,
            document.error_message,
            cls._serialize_datetime(document.created_at),
            cls._serialize_datetime(document.updated_at),
            cls._serialize_datetime(document.expires_at),
        )

    @staticmethod
    def _record_from_row(row: sqlite3.Row) -> DocumentRecord:
        values = dict(row)
        values["status"] = DocumentStatus(values["status"])
        for field in ("created_at", "updated_at", "expires_at"):
            values[field] = datetime.fromisoformat(values[field])
        return DocumentRecord.model_validate(values)
