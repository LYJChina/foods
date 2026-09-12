from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class MaterialKind(StrEnum):
    LABEL_IMAGE = "label_image"
    PACKAGING_IMAGE = "packaging_image"
    PRODUCT_SPEC = "product_spec"
    PUBLIC_DOCUMENT = "public_document"


class PrecheckCreate(BaseModel):
    product_name: str = Field(min_length=2, max_length=100)
    product_category: str = Field(min_length=2, max_length=50)
    target_market: str = Field(min_length=2, max_length=50)
    materials: list[MaterialKind] = Field(default_factory=list, max_length=8)
    contains_core_data: bool = False
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("product_name", "product_category", "target_market")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value


class RiskItem(BaseModel):
    code: str
    title: str
    level: Literal["info", "attention"]
    summary: str
    next_step: str


class PrecheckResult(BaseModel):
    overall: Literal["needs_review", "insufficient_materials"]
    risks: list[RiskItem]
    missing_materials: list[str]
    source_labels: list[str]
    next_steps: list[str]
    disclaimer: str
    is_demo: Literal[True] = True


class PrecheckTask(BaseModel):
    task_id: str
    status: Literal["completed"]
    submitted_at: datetime
    request: PrecheckCreate
    result: PrecheckResult


class PortalSummary(BaseModel):
    service_count: Literal[4] = 4
    scenario_count: Literal[6] = 6
    output_mode_count: Literal[2] = 2
    diagnosis_class_count: Literal[3] = 3
    is_demo: Literal[True] = True
    data_label: str = "演示数据，非实时统计"


class DiagnosisCreate(BaseModel):
    digital_foundation: int = Field(ge=0, le=2)
    data_readiness: int = Field(ge=0, le=2)
    ai_experience: int = Field(ge=0, le=2)
    governance_readiness: int = Field(ge=0, le=2)
    export_need: int = Field(ge=0, le=2)


class DiagnosisResult(BaseModel):
    score: int = Field(ge=0, le=10)
    maturity: Literal["start", "prepare", "advance"]
    recommendations: dict[
        Literal["public_platform", "light_poc", "enterprise_project"],
        list[str],
    ]
    disclaimer: str
    is_demo: Literal[True] = True
