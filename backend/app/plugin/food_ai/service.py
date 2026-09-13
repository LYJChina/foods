from datetime import UTC, datetime
from uuid import uuid4

from fastapi import status

from app.core.exceptions import CustomException

from .analyzer import ComplianceAnalyzer, DemoComplianceAnalyzer
from .assistant import PublicAssistant, configured_public_assistant
from .schema import (
    DiagnosisCreate,
    DiagnosisResult,
    PortalSummary,
    PrecheckCreate,
    PrecheckTask,
)


class InMemoryPrecheckRepository:
    """进程内 Demo 仓库；重启后清空，不用于生产数据。"""

    def __init__(self) -> None:
        self._tasks: dict[str, PrecheckTask] = {}

    def save(self, task: PrecheckTask) -> None:
        self._tasks[task.task_id] = task

    def get(self, task_id: str) -> PrecheckTask | None:
        return self._tasks.get(task_id)


class FoodAIService:
    def __init__(
        self,
        analyzer: ComplianceAnalyzer | None = None,
        repository: InMemoryPrecheckRepository | None = None,
        assistant: PublicAssistant | None = None,
    ) -> None:
        self.analyzer = analyzer or DemoComplianceAnalyzer()
        self.repository = repository or InMemoryPrecheckRepository()
        self.assistant = assistant or configured_public_assistant()

    def create_precheck(self, request: PrecheckCreate) -> PrecheckTask:
        result = self.analyzer.analyze(request)
        task = PrecheckTask(
            task_id=f"demo-{uuid4().hex[:12]}",
            status="completed",
            submitted_at=datetime.now(UTC),
            request=request,
            result=result,
        )
        self.repository.save(task)
        return task

    def get_precheck(self, task_id: str) -> PrecheckTask:
        task = self.repository.get(task_id)
        if task is None:
            raise CustomException(
                msg="预检任务不存在",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return task

    @staticmethod
    def get_portal_summary() -> PortalSummary:
        return PortalSummary()

    @staticmethod
    def create_diagnosis(request: DiagnosisCreate) -> DiagnosisResult:
        score = sum(
            (
                request.digital_foundation,
                request.data_readiness,
                request.ai_experience,
                request.governance_readiness,
                request.export_need,
            )
        )
        maturity = "start" if score <= 3 else "prepare" if score <= 7 else "advance"
        return DiagnosisResult(
            score=score,
            maturity=maturity,
            recommendations={
                "public_platform": [
                    "先体验公共知识、出口合规预检和通用 AI 能力",
                    "不提交配方、工艺、成本、客户、订单等核心数据",
                ],
                "light_poc": [
                    "选择一个边界清晰、可使用低敏样本的场景开展轻量验证",
                    "预先约定成功指标、数据留存和退出机制",
                ],
                "enterprise_project": [
                    "涉及生产经营系统或核心数据的能力应在企业侧专项建设",
                    "同步规划身份权限、审计和外部模型调用边界",
                ],
            },
            disclaimer="本诊断基于简化问卷和演示规则，仅用于讨论下一步路径。",
        )


food_ai_service = FoodAIService()
