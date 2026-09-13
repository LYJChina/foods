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
    { service_id: "food-safety", service_name: "食品安全问答", handled: 412 },
    { service_id: "nutrition-analysis", service_name: "营养成分分析", handled: 338 },
    { service_id: "recipe-generation", service_name: "食谱生成", handled: 297 },
    { service_id: "ingredient-check", service_name: "食材信息核验", handled: 239 },
  ],
  recent_cases: [
    {
      id: "SAMPLE-0001",
      title: "帮我分析这份早餐的营养成分",
      service_name: "营养成分分析",
      submitted_at: "2026-09-13T19:42:00+08:00",
      status: "completed",
    },
    {
      id: "SAMPLE-0002",
      title: "生成一份低盐家常晚餐食谱",
      service_name: "食谱生成",
      submitted_at: "2026-09-13T19:36:00+08:00",
      status: "processing",
    },
    {
      id: "SAMPLE-0003",
      title: "核验这批食材的保质期信息",
      service_name: "食材信息核验",
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
