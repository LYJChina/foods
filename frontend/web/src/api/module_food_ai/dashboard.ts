export interface DashboardSummary {
  total_handled: number;
  knowledge_documents: number;
  today_users: number;
  active_agents: number;
  updated_at: string;
}

export interface ServiceTrendPoint {
  date: string;
  handled: number;
}

export interface ServiceDistributionItem {
  service_id: string;
  service_name: string;
  handled: number;
}

export interface RecentCase {
  id: string;
  title: string;
  service_name: string;
  submitted_at: string;
  status: "completed" | "processing" | "failed";
}

export interface DashboardSnapshot {
  summary: DashboardSummary;
  trend: ServiceTrendPoint[];
  distribution: ServiceDistributionItem[];
  recent_cases: RecentCase[];
}

const sampleSnapshot: DashboardSnapshot = {
  summary: {
    total_handled: 1286,
    knowledge_documents: 3642,
    today_users: 176,
    active_agents: 4,
    updated_at: "2026-09-13T20:00:00+08:00",
  },
  trend: [
    { date: "2026-09-07", handled: 154 },
    { date: "2026-09-08", handled: 181 },
    { date: "2026-09-09", handled: 166 },
    { date: "2026-09-10", handled: 203 },
    { date: "2026-09-11", handled: 189 },
    { date: "2026-09-12", handled: 214 },
    { date: "2026-09-13", handled: 179 },
  ],
  distribution: [
    { service_id: "documents", service_name: "智能文档解析", handled: 412 },
    { service_id: "precheck", service_name: "出口合规预检", handled: 338 },
    { service_id: "diagnosis", service_name: "企业数智化诊断", handled: 297 },
    { service_id: "scenarios", service_name: "AI 场景匹配", handled: 239 },
  ],
  recent_cases: [
    {
      id: "SAMPLE-0001",
      title: "解析食品经营许可政策文件",
      service_name: "智能文档解析",
      submitted_at: "2026-09-13T19:42:00+08:00",
      status: "completed",
    },
    {
      id: "SAMPLE-0002",
      title: "提交出口产品合规预检",
      service_name: "出口合规预检",
      submitted_at: "2026-09-13T19:36:00+08:00",
      status: "processing",
    },
    {
      id: "SAMPLE-0003",
      title: "完成企业数智化基础评估",
      service_name: "企业数智化诊断",
      submitted_at: "2026-09-13T19:18:00+08:00",
      status: "failed",
    },
  ],
};

function cloneSampleSnapshot(): DashboardSnapshot {
  return JSON.parse(JSON.stringify(sampleSnapshot)) as DashboardSnapshot;
}

export const DashboardAPI = {
  dataMode: "sample" as const,
  async getSnapshot(): Promise<DashboardSnapshot> {
    return cloneSampleSnapshot();
  },
};
