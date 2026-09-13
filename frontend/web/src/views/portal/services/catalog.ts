/** A filterable service-hall category. */
export interface ServiceCategory {
  id: "documents" | "policy" | "enterprise" | "diagnosis";
  name: string;
}

export type ServiceStatus = "available" | "planned";

export interface PublicService {
  id:
    | "documents"
    | "precheck"
    | "diagnosis"
    | "scenarios"
    | "policy-reading"
    | "label-check"
    | "application-materials";
  categoryId: ServiceCategory["id"];
  name: string;
  description: string;
  method: string;
  materials: string[];
  status: ServiceStatus;
  route?: string;
  keywords?: string[];
}

export interface QuickAssistantCase {
  id: string;
  prompt: string;
  serviceId: PublicService["id"];
  keywords: string[];
}

export const serviceCategories: ServiceCategory[] = [
  { id: "documents", name: "文档与知识" },
  { id: "policy", name: "政策与合规" },
  { id: "enterprise", name: "企业服务" },
  { id: "diagnosis", name: "诊断与评估" },
];

export const publicServices: PublicService[] = [
  {
    id: "documents",
    categoryId: "documents",
    name: "智能文档解析",
    description: "上传公开或低敏文档，解析结构并基于原文引用进行问答。",
    method: "在线上传与问答",
    materials: ["公开或低敏 PDF、Word 文档"],
    status: "available",
    route: "/portal/documents",
    keywords: ["政策", "业务文件", "文档", "重点", "条款", "解析"],
  },
  {
    id: "precheck",
    categoryId: "policy",
    name: "出口合规预检",
    description: "围绕产品、目标市场和低敏材料，生成结构化辅助预检结果。",
    method: "在线填写与规则预检",
    materials: ["产品类别", "目标市场", "低敏材料说明"],
    status: "available",
    route: "/portal/precheck",
    keywords: ["出口", "合规", "海外", "预检"],
  },
  {
    id: "diagnosis",
    categoryId: "diagnosis",
    name: "企业数智化诊断",
    description: "评估企业数字化基础、AI Ready 程度与治理需求，输出分层建议。",
    method: "在线问卷评估",
    materials: ["企业基本情况", "数字化基础问卷"],
    status: "available",
    route: "/portal/diagnosis",
    keywords: ["诊断", "企业", "数智化", "AI Ready"],
  },
  {
    id: "scenarios",
    categoryId: "diagnosis",
    name: "AI 场景匹配",
    description: "通过食品行业场景示例，匹配适合企业验证的 AI 应用方向。",
    method: "场景浏览与匹配",
    materials: ["企业应用需求概述"],
    status: "available",
    route: "/portal/scenarios",
    keywords: ["场景", "AI 场景", "匹配", "适合"],
  },
  {
    id: "policy-reading",
    categoryId: "documents",
    name: "政策文件解读",
    description: "面向公开政策文件的重点提炼与条款解读服务。",
    method: "规划中的在线服务",
    materials: ["公开政策文件"],
    status: "planned",
  },
  {
    id: "label-check",
    categoryId: "policy",
    name: "食品标签辅助检查",
    description: "面向食品标签内容的辅助检查与问题提示服务。",
    method: "规划中的在线服务",
    materials: ["食品标签材料"],
    status: "planned",
  },
  {
    id: "application-materials",
    categoryId: "enterprise",
    name: "申报材料整理",
    description: "面向企业申报事项的材料归集与整理服务。",
    method: "规划中的在线服务",
    materials: ["申报事项相关公开材料"],
    status: "planned",
  },
];

export const quickAssistantCases: QuickAssistantCase[] = [
  {
    id: "document-parse",
    prompt: "帮我解析一份政策或业务文件。",
    serviceId: "documents",
    keywords: ["解析", "政策", "业务文件"],
  },
  {
    id: "document-summary",
    prompt: "帮我提炼文档重点和条款。",
    serviceId: "documents",
    keywords: ["提炼", "文档", "重点", "条款"],
  },
  {
    id: "export-precheck",
    prompt: "我想进行出口合规预检。",
    serviceId: "precheck",
    keywords: ["出口", "合规", "预检"],
  },
  {
    id: "scenario-match",
    prompt: "帮我判断企业适合哪些 AI 场景。",
    serviceId: "scenarios",
    keywords: ["企业", "适合", "AI 场景"],
  },
];
