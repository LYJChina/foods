from typing import Protocol

from .schema import MaterialKind, PrecheckCreate, PrecheckResult, RiskItem


class CoreDataRejectedError(ValueError):
    """提交内容明确包含企业核心数据时拒绝处理。"""


class ComplianceAnalyzer(Protocol):
    def analyze(self, request: PrecheckCreate) -> PrecheckResult: ...


class DemoComplianceAnalyzer:
    """确定性 Demo 分析器，不连接法规库、OCR 或大模型。"""

    def analyze(self, request: PrecheckCreate) -> PrecheckResult:
        if request.contains_core_data:
            raise CoreDataRejectedError("检测到企业核心数据声明，本平台拒绝接收和处理。")

        missing_materials: list[str] = []
        if not ({MaterialKind.LABEL_IMAGE, MaterialKind.PACKAGING_IMAGE} & set(request.materials)):
            missing_materials.append("包装或标签图片")
        if MaterialKind.PRODUCT_SPEC not in request.materials:
            missing_materials.append("产品规格说明")

        risks = [
            RiskItem(
                code="AUX-LABEL-001",
                title="标签与强制标识需人工复核",
                level="attention",
                summary=f"目标市场为 {request.target_market}。当前服务未连接实时法规库，不能确认具体标签要求。",
                next_step="由合规人员依据目标市场现行官方规则核验语言、配料、过敏原和营养标识。",
            ),
            RiskItem(
                code="AUX-CERT-001",
                title="认证与验厂条件待确认",
                level="info",
                summary="认证要求通常取决于产品、市场和客户约定，本结果不作认证适用性判断。",
                next_step="结合客户合同与认证机构公开材料形成核验清单。",
            ),
        ]

        return PrecheckResult(
            overall="insufficient_materials" if missing_materials else "needs_review",
            risks=risks,
            missing_materials=missing_materials,
            source_labels=["辅助规则集（非实时法规库）"],
            next_steps=[
                "补充或复核低敏材料",
                "核对目标市场现行公开规则",
                "必要时咨询认证、检验或法律专业人员",
            ],
            disclaimer="仅用于辅助预检，不替代专业认证、检验或法律判断。",
        )
