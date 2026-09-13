import { describe, expect, it } from "vitest";
import { DashboardAPI } from "@/api/module_food_ai/dashboard";

describe("dashboard data adapter", () => {
  it("returns a complete sample snapshot behind an async API", async () => {
    const data = await DashboardAPI.getSnapshot();
    expect(DashboardAPI.dataMode).toBe("sample");
    expect(data.summary).toMatchObject({
      total_handled: expect.any(Number),
      knowledge_documents: expect.any(Number),
      today_users: expect.any(Number),
      active_agents: expect.any(Number),
    });
    expect(data.trend).toHaveLength(7);
    expect(data.distribution.length).toBeGreaterThan(0);
    expect(data.recent_cases.length).toBeGreaterThan(0);
  });
});
