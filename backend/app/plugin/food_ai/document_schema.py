from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DocumentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class DocumentRecord(BaseModel):
    document_id: str = Field(min_length=1, max_length=128)
    original_filename: str = Field(min_length=1, max_length=255)
    storage_path: str = Field(min_length=1, max_length=1024)
    content_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(ge=0)
    sha256: str = Field(min_length=1, max_length=128)
    status: DocumentStatus = DocumentStatus.PENDING
    document_parser_task_id: str | None = Field(default=None, max_length=255)
    error_message: str | None = Field(default=None, max_length=2000)
    created_at: datetime
    updated_at: datetime
    expires_at: datetime


class DocumentChunk(BaseModel):
    document_id: str = Field(min_length=1, max_length=128)
    chunk_index: int = Field(ge=0)
    content: str = Field(min_length=1)
    page_number: int | None = Field(default=None, ge=1)
    heading: str | None = Field(default=None, max_length=500)


class Citation(BaseModel):
    document_id: str = Field(min_length=1, max_length=128)
    chunk_index: int = Field(ge=0)
    original_filename: str = Field(min_length=1, max_length=255)
    excerpt: str = Field(min_length=1)
    page_number: int | None = Field(default=None, ge=1)
    heading: str | None = None


class QuestionResult(BaseModel):
    question_id: str = Field(min_length=1, max_length=128)
    document_id: str = Field(min_length=1, max_length=128)
    question: str = Field(min_length=1, max_length=4000)
    answer: str = Field(min_length=1)
    citations: list[Citation] = Field(default_factory=list)
    created_at: datetime
