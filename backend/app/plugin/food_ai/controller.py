from typing import Annotated

from fastapi import APIRouter, Body, Path, status
from fastapi.responses import JSONResponse

from app.common.response import ResponseSchema, SuccessResponse
from app.core.exceptions import CustomException

from .assistant import AssistantUnavailable
from .schema import (
    AssistantQuestionRequest,
    AssistantQuestionResult,
    DiagnosisCreate,
    DiagnosisResult,
    PortalSummary,
    PrecheckCreate,
    PrecheckTask,
)
from .service import food_ai_service

FoodAIRouter = APIRouter(prefix="/food-ai", tags=["食品行业 AI 公共服务 Demo"])


@FoodAIRouter.get(
    "/portal/summary",
    summary="获取公开门户演示概览",
    response_model=ResponseSchema[PortalSummary],
)
async def get_portal_summary() -> JSONResponse:
    return SuccessResponse(
        data=food_ai_service.get_portal_summary(),
        msg="获取演示概览成功",
    )


@FoodAIRouter.post(
    "/prechecks",
    status_code=status.HTTP_201_CREATED,
    summary="创建出口合规 Demo 预检",
    response_model=ResponseSchema[PrecheckTask],
)
async def create_precheck(
    data: Annotated[PrecheckCreate, Body(description="低敏预检信息")],
) -> JSONResponse:
    task = food_ai_service.create_precheck(data)
    return SuccessResponse(
        data=task,
        msg="Demo 预检任务已完成",
        status_code=status.HTTP_201_CREATED,
    )


@FoodAIRouter.get(
    "/prechecks/{task_id}",
    summary="查询出口合规 Demo 预检",
    response_model=ResponseSchema[PrecheckTask],
)
async def get_precheck(
    task_id: Annotated[str, Path(min_length=6, max_length=64)],
) -> JSONResponse:
    return SuccessResponse(
        data=food_ai_service.get_precheck(task_id),
        msg="获取 Demo 预检结果成功",
    )


@FoodAIRouter.post(
    "/diagnoses",
    status_code=status.HTTP_201_CREATED,
    summary="生成轻量数智化 Demo 诊断",
    response_model=ResponseSchema[DiagnosisResult],
)
async def create_diagnosis(
    data: Annotated[DiagnosisCreate, Body(description="简化诊断问卷")],
) -> JSONResponse:
    return SuccessResponse(
        data=food_ai_service.create_diagnosis(data),
        msg="Demo 诊断已生成",
        status_code=status.HTTP_201_CREATED,
    )


@FoodAIRouter.post(
    "/assistant/questions",
    summary="咨询公共服务智能助手",
    response_model=ResponseSchema[AssistantQuestionResult],
)
async def ask_public_assistant(
    data: Annotated[AssistantQuestionRequest, Body(description="公共服务咨询问题")],
) -> JSONResponse:
    try:
        result = await food_ai_service.assistant.answer(data.question, data.conversation_id)
    except AssistantUnavailable:
        raise CustomException(
            msg="问答模型服务未配置或暂不可用",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from None
    return SuccessResponse(data=result, msg="问答完成")
