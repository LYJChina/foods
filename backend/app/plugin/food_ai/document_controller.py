"""Public platform endpoints; browsers never call MinerU directly."""

from typing import Annotated

from fastapi import APIRouter, File, Form, Path, Query, UploadFile, status
from fastapi.responses import JSONResponse

from app.common.response import SuccessResponse
from app.config.setting import settings

from .document_repository import DocumentRepository
from .document_service import DocumentService
from .mineru_client import MinerUClient

DocumentRouter = APIRouter(prefix="/food-ai/documents", tags=["食品行业 AI 文档解析 Demo"])
_repository = DocumentRepository(settings.DOCUMENT_STORAGE_DIR / "documents.db")
_mineru = MinerUClient(settings.MINERU_URL, settings.MINERU_TOKEN, settings.DOCUMENT_LLM_TIMEOUT_SECONDS)
document_service = DocumentService(_repository, _mineru)


def _payload(record, public_status: str) -> dict[str, object]:
    return {"document_id": record.document_id, "file_name": record.original_filename, "status": public_status, "expires_at": record.expires_at, "can_ask": record.status.value == "ready", "is_demo": True}


@DocumentRouter.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_document(file: Annotated[UploadFile, File()], confirmed_low_sensitivity: Annotated[bool, Form()]) -> JSONResponse:
    record = await document_service.create(file, confirmed_low_sensitivity)
    return SuccessResponse(data=_payload(record, "queued"), msg="文档已进入解析队列", status_code=status.HTTP_202_ACCEPTED)


@DocumentRouter.get("/{document_id}")
async def get_document(document_id: Annotated[str, Path(min_length=1, max_length=128)]) -> JSONResponse:
    record, public_status = await document_service.refresh_status(document_id)
    return SuccessResponse(data=_payload(record, public_status), msg="获取文档状态成功")


@DocumentRouter.get("/{document_id}/content")
async def get_content(document_id: Annotated[str, Path(min_length=1, max_length=128)], offset: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 50) -> JSONResponse:
    return SuccessResponse(data=await document_service.get_content(document_id, offset, limit), msg="获取解析内容成功")


@DocumentRouter.delete("/{document_id}")
async def delete_document(document_id: Annotated[str, Path(min_length=1, max_length=128)]) -> JSONResponse:
    await document_service.delete(document_id)
    return SuccessResponse(data={"document_id": document_id}, msg="文档已删除")
