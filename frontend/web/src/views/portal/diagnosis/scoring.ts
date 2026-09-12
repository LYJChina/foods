import type { DiagnosisAnswers, DiagnosisResult } from "@/types/food-ai";

export function scoreDiagnosis(answers: DiagnosisAnswers): DiagnosisResult {
  const score =
    answers.digital_foundation +
    answers.data_readiness +
    answers.ai_experience +
    answers.governance_readiness +
    answers.export_need;
  const maturity = score <= 3 ? "start" : score <= 7 ? "prepare" : "advance";

  return {
    score,
    maturity,
    recommendations: {
      public_platform: [
        "先体验公共知识、出口合规预检和通用 AI 能力",
        "不提交配方、工艺、成本、客户、订单等核心数据",
      ],
      light_poc: [
        "选择一个边界清晰、可使用低敏样本的场景开展轻量验证",
        "预先约定成功指标、数据留存和退出机制",
      ],
      enterprise_project: [
        "涉及生产经营系统或核心数据的能力应在企业侧专项建设",
        "同步规划身份权限、审计和外部模型调用边界",
      ],
    },
    disclaimer: "本诊断基于简化问卷和演示规则，仅用于讨论下一步路径。",
    is_demo: true,
  };
}
