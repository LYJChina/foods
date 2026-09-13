"""Application service for the isolated DocumentParser document workflow."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile, status

from app.config.setting import settings
from app.core.exceptions import CustomException

from .document_answerer import AnswererUnavailable, DocumentAnswerer
from .document_parser_client import DocumentParserClient, DocumentParserInvalidResponse, DocumentParserUnavailable
from .document_processing import count_pdf_pages, extract_chunks, sanitize_file_name, validate_upload
from .document_repository import DocumentRepository
from .document_schema import DocumentRecord, DocumentStatus


class DocumentService:
    def __init__(self, repository: DocumentRepository, document_parser: DocumentParserClient, storage_dir: Path | None = None, answerer: DocumentAnswerer | None = None) -> None:
        self.repository = repository
        self.document_parser = document_parser
        self.storage_dir = storage_dir or settings.DOCUMENT_STORAGE_DIR
        self.answerer = answerer

    async def create(self, file: UploadFile, confirmed_low_sensitivity: bool) -> DocumentRecord:
        content = await self._read_limited(file)
        try:
            suffix = validate_upload(file.filename or "", file.content_type, content, len(content), confirmed_low_sensitivity)
            if suffix == ".pdf":
                count_pdf_pages(content)
        except ValueError as exc:
            message = str(exc)
            raise CustomException(msg=message, status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE if "大小" in message else status.HTTP_400_BAD_REQUEST) from None
        document_id = uuid4().hex
        path = self.storage_dir / sanitize_file_name(file.filename or "", suffix)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        now = datetime.now(UTC)
        record = DocumentRecord(document_id=document_id, original_filename=Path(file.filename or "document").name, storage_path=str(path), content_type=file.content_type or "application/octet-stream", size_bytes=len(content), sha256=hashlib.sha256(content).hexdigest(), created_at=now, updated_at=now, expires_at=now + timedelta(days=settings.DOCUMENT_RETENTION_DAYS))
        self.repository.create_document(record)
        try:
            task = await self.document_parser.submit(path.name, content, record.content_type)
        except DocumentParserUnavailable:
            self.repository.update_status(document_id, DocumentStatus.FAILED, error_message="文档解析服务暂不可用，请稍后重试。")
            raise CustomException(msg="文档解析服务暂不可用，请稍后重试。", status_code=status.HTTP_503_SERVICE_UNAVAILABLE) from None
        except DocumentParserInvalidResponse:
            self.repository.update_status(document_id, DocumentStatus.FAILED, error_message="文档解析服务返回的数据无效。")
            raise CustomException(msg="文档解析服务返回的数据无效。", status_code=status.HTTP_502_BAD_GATEWAY) from None
        return self.repository.update_status(document_id, DocumentStatus.PENDING, document_parser_task_id=str(task["task_id"])) or record

    async def refresh_status(self, document_id: str) -> tuple[DocumentRecord, str]:
        record = self._require_document(document_id)
        if record.status in {DocumentStatus.READY, DocumentStatus.FAILED}:
            return record, "ready" if record.status is DocumentStatus.READY else "failed"
        if not record.document_parser_task_id:
            return record, "queued"
        try:
            upstream = await self.document_parser.get_status(record.document_parser_task_id)
        except DocumentParserUnavailable:
            raise CustomException(msg="文档解析服务暂不可用，请稍后重试。", status_code=status.HTTP_503_SERVICE_UNAVAILABLE) from None
        except DocumentParserInvalidResponse:
            raise CustomException(msg="文档解析服务返回的数据无效。", status_code=status.HTTP_502_BAD_GATEWAY) from None
        upstream_status = str(upstream.get("status", "")).lower()
        if upstream_status in {"failed", "error"}:
            record = self.repository.update_status(document_id, DocumentStatus.FAILED, error_message="文档解析失败，请更换文件后重试。") or record
            return record, "failed"
        if upstream_status not in {"done", "completed", "success", "finished"}:
            record = self.repository.update_status(document_id, DocumentStatus.PROCESSING) or record
            return record, "parsing"
        try:
            result = await self.document_parser.get_result(record.document_parser_task_id)
            chunks = [chunk.model_copy(update={"document_id": document_id}) for chunk in extract_chunks(result)]
            if not chunks:
                raise ValueError("解析结果没有可预览文本")
            self.repository.replace_chunks(document_id, chunks)
        except DocumentParserUnavailable:
            raise CustomException(msg="文档解析服务暂不可用，请稍后重试。", status_code=status.HTTP_503_SERVICE_UNAVAILABLE) from None
        except (DocumentParserInvalidResponse, ValueError):
            record = self.repository.update_status(document_id, DocumentStatus.FAILED, error_message="文档解析结果无效。") or record
            return record, "failed"
        record = self.repository.update_status(document_id, DocumentStatus.READY) or record
        return record, "indexing"

    async def get_content(self, document_id: str, offset: int, limit: int) -> dict[str, object]:
        self._require_document(document_id)
        chunks = self.repository.list_chunks(document_id)
        return {"items": chunks[offset : offset + limit], "offset": offset, "limit": limit, "total": len(chunks)}

    async def delete(self, document_id: str) -> None:
        record = self._require_document(document_id)
        self.repository.delete_document(document_id)
        Path(record.storage_path).unlink(missing_ok=True)

    async def question(self, document_id: str, question: str):
        record = self._require_document(document_id)
        if record.status is not DocumentStatus.READY:
            raise CustomException(msg="文档尚未解析完成，暂不可问答。", status_code=status.HTTP_409_CONFLICT)
        if not question.strip():
            raise CustomException(msg="问题不能为空。", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        if self.answerer is None:
            raise CustomException(msg="问答模型服务未配置或暂不可用。", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
        chunks = self.repository.search_chunks(document_id, question, limit=5)
        try:
            result = await self.answerer.answer(document_id, record.original_filename, question.strip(), chunks)
        except AnswererUnavailable:
            raise CustomException(msg="问答模型服务未配置或暂不可用。", status_code=status.HTTP_503_SERVICE_UNAVAILABLE) from None
        return self.repository.save_question(result)

    async def _read_limited(self, file: UploadFile) -> bytes:
        chunks: list[bytes] = []
        total = 0
        while data := await file.read(1024 * 1024):
            total += len(data)
            if total > settings.DOCUMENT_MAX_UPLOAD_BYTES:
                raise CustomException(msg="文件大小超过限制，最大允许 20MB。", status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
            chunks.append(data)
        return b"".join(chunks)

    def _require_document(self, document_id: str) -> DocumentRecord:
        record = self.repository.get_document(document_id)
        if record is None:
            raise CustomException(msg="文档不存在或已删除。", status_code=status.HTTP_404_NOT_FOUND)
        return record
