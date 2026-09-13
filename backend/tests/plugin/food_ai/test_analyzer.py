import pytest

from app.plugin.food_ai.analyzer import CoreDataRejectedError, DemoComplianceAnalyzer
from app.plugin.food_ai.schema import MaterialKind, PrecheckCreate


def build_request(**overrides) -> PrecheckCreate:
    payload = {
        "product_name": "潮州糖果示例产品",
        "product_category": "candy",
        "target_market": "EU",
        "materials": [MaterialKind.LABEL_IMAGE, MaterialKind.PRODUCT_SPEC],
        "contains_core_data": False,
    }
    payload.update(overrides)
    return PrecheckCreate(**payload)


def test_valid_sample_returns_structured_demo_result() -> None:
    result = DemoComplianceAnalyzer().analyze(build_request())

    assert result.overall == "needs_review"
    assert result.is_demo is True
    assert result.source_labels == ["辅助规则集（非实时法规库）"]
    assert result.disclaimer == "仅用于辅助预检，不替代专业认证、检验或法律判断。"
    assert len(result.risks) >= 1


def test_missing_low_sensitivity_materials_are_reported() -> None:
    result = DemoComplianceAnalyzer().analyze(build_request(materials=[]))

    assert result.overall == "insufficient_materials"
    assert result.missing_materials == ["包装或标签图片", "产品规格说明"]


def test_core_enterprise_data_is_refused() -> None:
    with pytest.raises(CoreDataRejectedError, match="核心数据"):
        DemoComplianceAnalyzer().analyze(build_request(contains_core_data=True))
