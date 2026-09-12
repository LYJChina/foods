export type MaterialKind =
  | "label_image"
  | "packaging_image"
  | "product_spec"
  | "public_document";

export interface PrecheckCreate {
  product_name: string;
  product_category: string;
  target_market: string;
  materials: MaterialKind[];
  contains_core_data: boolean;
  notes?: string;
}

export interface RiskItem {
  code: string;
  title: string;
  level: "info" | "attention";
  summary: string;
  next_step: string;
}

export interface PrecheckResult {
  overall: "needs_review" | "insufficient_materials";
  risks: RiskItem[];
  missing_materials: string[];
  source_labels: string[];
  next_steps: string[];
  disclaimer: string;
  is_demo: true;
}

export interface PrecheckTask {
  task_id: string;
  status: "completed";
  submitted_at: string;
  request: PrecheckCreate;
  result: PrecheckResult;
}
