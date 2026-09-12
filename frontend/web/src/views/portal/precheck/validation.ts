import type { MaterialKind } from "@/types/food-ai";

export interface PrecheckFormDraft {
  product_name: string;
  product_category: string;
  target_market: string;
  materials: MaterialKind[];
  notes: string;
  confirmed_low_sensitivity: boolean;
  accepts_disclaimer: boolean;
}

export type PrecheckFieldErrors = Partial<Record<keyof PrecheckFormDraft, string>>;

export function createEmptyPrecheckDraft(): PrecheckFormDraft {
  return {
    product_name: "",
    product_category: "",
    target_market: "",
    materials: [],
    notes: "",
    confirmed_low_sensitivity: false,
    accepts_disclaimer: false,
  };
}

export function validatePrecheckStep(
  step: 1 | 2 | 3,
  draft: PrecheckFormDraft
): PrecheckFieldErrors {
  const errors: PrecheckFieldErrors = {};

  if (step === 1) {
    if (!draft.product_name.trim()) errors.product_name = "请输入产品名称";
    if (!draft.product_category) errors.product_category = "请选择产品类别";
    if (!draft.target_market) errors.target_market = "请选择目标市场";
  }

  if (step === 2 && draft.materials.length === 0) {
    errors.materials = "请至少选择一种低敏材料";
  }

  if (step === 3) {
    if (!draft.confirmed_low_sensitivity) {
      errors.confirmed_low_sensitivity = "请确认未提交企业核心数据";
    }
    if (!draft.accepts_disclaimer) {
      errors.accepts_disclaimer = "请确认理解预检结果的辅助性质";
    }
  }

  return errors;
}
