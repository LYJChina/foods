export interface PortalService {
  title: string;
  description: string;
  action: string;
  to: string;
  icon: string;
  tone: "blue" | "cyan" | "green" | "amber";
}

export const portalServices: PortalService[] = [
  {
    title: "智能文档解析与问答",
    description: "上传公开或低敏文档，由公共服务平台智能体解析并基于原文引用进行问答。",
    action: "上传文档",
    to: "/portal/documents",
    icon: "ri:sparkling-2-line",
    tone: "blue",
  },
  {
    title: "出口合规与海外服务",
    description: "围绕产品、目标市场和低敏材料，形成结构化辅助预检。",
    action: "立即预检",
    to: "/portal/precheck",
    icon: "ri:shield-check-line",
    tone: "cyan",
  },
  {
    title: "AI 场景体验与验证",
    description: "通过 6 个食品行业场景 Demo，说明实施条件、价值与边界。",
    action: "体验场景",
    to: "/portal/scenarios",
    icon: "ri:apps-2-line",
    tone: "green",
  },
  {
    title: "数智化诊断与服务对接",
    description: "评估数字化基础、AI Ready 程度与治理需求，输出三类建议。",
    action: "开始诊断",
    to: "/portal/diagnosis",
    icon: "ri:pulse-line",
    tone: "amber",
  },
];

export const portalMetrics = [
  { value: "4 类", label: "一期公共服务" },
  { value: "6 个", label: "食品行业场景方向" },
  { value: "2 种", label: "直接使用与开放调用" },
  { value: "3 类", label: "数智化诊断建议" },
];

export const coverageItems = [
  { label: "糖果", value: 92, level: "高" },
  { label: "休闲食品", value: 84, level: "高" },
  { label: "卤制品", value: 63, level: "中" },
  { label: "保健食品", value: 51, level: "中" },
];

export const assistantPrompts = [
  "出口预检需准备什么？",
  "哪些材料不建议上传？",
  "如何选择 AI 场景？",
];
