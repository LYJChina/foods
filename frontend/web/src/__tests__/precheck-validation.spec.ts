import { describe, expect, it } from "vitest";

import { createEmptyPrecheckDraft, validatePrecheckStep } from "@/views/portal/precheck/validation";

describe("precheck step validation", () => {
  it("reports field-specific errors for incomplete product information", () => {
    expect(validatePrecheckStep(1, createEmptyPrecheckDraft())).toEqual({
      product_name: "请输入产品名称",
      product_category: "请选择产品类别",
      target_market: "请选择目标市场",
    });
  });

  it("requires at least one low-sensitivity material description", () => {
    const draft = createEmptyPrecheckDraft();
    draft.product_name = "潮州糖果示例产品";
    draft.product_category = "candy";
    draft.target_market = "EU";

    expect(validatePrecheckStep(2, draft)).toEqual({
      materials: "请至少选择一种低敏材料",
    });
  });

  it("requires both boundary confirmations before submission", () => {
    const draft = createEmptyPrecheckDraft();
    draft.confirmed_low_sensitivity = false;
    draft.accepts_disclaimer = false;

    expect(validatePrecheckStep(3, draft)).toEqual({
      confirmed_low_sensitivity: "请确认未提交企业核心数据",
      accepts_disclaimer: "请确认理解预检结果的辅助性质",
    });
  });
});
