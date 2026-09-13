export type PortalDataMode = "sample";

export interface PortalContentItem {
  id: string;
  title: string;
  date: string;
  kind: string;
  dataMode: PortalDataMode;
}

export interface PortalQuickAction {
  id: "query" | "handle" | "assistant" | "documents";
  label: string;
  description: string;
  icon: string;
  to: string;
}

export interface PortalServiceZone {
  id: "policy" | "enterprise" | "documents" | "diagnosis";
  title: string;
  services: string[];
  icon: string;
  to: string;
}

export interface PortalHomeContent {
  dataMode: PortalDataMode;
  hotQuestions: string[];
  quickActions: PortalQuickAction[];
  serviceZones: PortalServiceZone[];
  news: PortalContentItem[];
  notices: PortalContentItem[];
}

const sampleHomeContent: PortalHomeContent = {
  dataMode: "sample",
  hotQuestions: [
    "出口合规需要准备哪些材料？",
    "如何解析一份政策文件？",
    "企业怎样开展数智化诊断？",
    "哪些材料不建议上传？",
  ],
  quickActions: [
    {
      id: "query",
      label: "我要查",
      description: "查询平台服务与办事指引",
      icon: "ri:search-line",
      to: "/portal/services?focus=search",
    },
    {
      id: "handle",
      label: "我要办",
      description: "查看当前可在线办理事项",
      icon: "ri:file-list-3-line",
      to: "/portal/services?status=available",
    },
    {
      id: "assistant",
      label: "智能问答",
      description: "咨询食品行业公共服务问题",
      icon: "ri:chat-3-line",
      to: "/portal/assistant",
    },
    {
      id: "documents",
      label: "文档解析",
      description: "解析公开或低敏业务文档",
      icon: "ri:file-text-line",
      to: "/portal/documents",
    },
  ],
  serviceZones: [
    {
      id: "policy",
      title: "政策与合规",
      services: ["出口合规预检", "食品标签辅助检查"],
      icon: "ri:shield-check-line",
      to: "/portal/services?category=policy",
    },
    {
      id: "enterprise",
      title: "企业服务",
      services: ["申报材料整理", "服务事项导航"],
      icon: "ri:building-2-line",
      to: "/portal/services?category=enterprise",
    },
    {
      id: "documents",
      title: "文档与知识",
      services: ["智能文档解析", "政策文件解读"],
      icon: "ri:file-text-line",
      to: "/portal/services?category=documents",
    },
    {
      id: "diagnosis",
      title: "诊断与评估",
      services: ["企业数智化诊断", "AI 场景匹配"],
      icon: "ri:pulse-line",
      to: "/portal/services?category=diagnosis",
    },
  ],
  news: [
    {
      id: "news-1",
      title: "食品行业公共智能服务能力持续完善",
      date: "2026-09-12",
      kind: "平台动态",
      dataMode: "sample",
    },
    {
      id: "news-2",
      title: "企业数智化服务专题交流活动顺利开展",
      date: "2026-09-08",
      kind: "工作动态",
      dataMode: "sample",
    },
    {
      id: "news-3",
      title: "食品行业 AI 应用场景体验专区上线",
      date: "2026-09-02",
      kind: "能力更新",
      dataMode: "sample",
    },
    {
      id: "news-4",
      title: "公共服务平台完成文档解析流程优化",
      date: "2026-08-28",
      kind: "平台动态",
      dataMode: "sample",
    },
  ],
  notices: [
    {
      id: "notice-1",
      title: "关于公共服务平台功能试运行的说明",
      date: "2026-09-13",
      kind: "使用提示",
      dataMode: "sample",
    },
    {
      id: "notice-2",
      title: "智能文档解析材料范围与安全提示",
      date: "2026-09-09",
      kind: "材料要求",
      dataMode: "sample",
    },
    {
      id: "notice-3",
      title: "出口合规预检服务使用指引",
      date: "2026-09-04",
      kind: "办事指南",
      dataMode: "sample",
    },
    {
      id: "notice-4",
      title: "平台例行维护时间说明",
      date: "2026-08-30",
      kind: "维护通知",
      dataMode: "sample",
    },
  ],
};

export const PortalContentAPI = {
  async getHomeContent(): Promise<PortalHomeContent> {
    return structuredClone(sampleHomeContent);
  },
};
