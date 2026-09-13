import { describe, expect, it } from "vitest";

import { PortalContentAPI } from "@/api/module_food_ai/content";

describe("portal content adapter", () => {
  it("labels every news and notice item as sample data", async () => {
    const content = await PortalContentAPI.getHomeContent();
    const items = [...content.news, ...content.notices];

    expect(content.dataMode).toBe("sample");
    expect(items.length).toBeGreaterThan(0);
    expect(items.every((item) => item.dataMode === "sample")).toBe(true);
  });

  it("uses only valid internal targets", async () => {
    const content = await PortalContentAPI.getHomeContent();

    expect(content.quickActions.every((item) => item.to.startsWith("/portal/"))).toBe(true);
    expect(
      content.serviceZones.every((item) => item.to.startsWith("/portal/services?category="))
    ).toBe(true);
  });

  it("returns an isolated copy for each request", async () => {
    const first = await PortalContentAPI.getHomeContent();
    const second = await PortalContentAPI.getHomeContent();
    const firstNews = first.news[0];
    const secondNews = second.news[0];

    expect(firstNews).toBeDefined();
    expect(secondNews).toBeDefined();
    if (!firstNews || !secondNews) return;
    firstNews.title = "已被调用方修改";
    expect(secondNews.title).not.toBe("已被调用方修改");
  });
});
