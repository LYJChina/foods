import { describe, expect, it } from "vitest";
import { publicServices, quickAssistantCases } from "@/views/portal/services/catalog";

describe("public service catalog", () => {
  it("keeps available services routable and planned services disabled", () => {
    expect(publicServices.find((item) => item.id === "documents")).toMatchObject({
      status: "available",
      route: "/portal/documents",
    });
    expect(publicServices.filter((item) => item.status === "planned").every((item) => !item.route)).toBe(true);
  });

  it("maps every quick case to an available service", () => {
    const available = new Set(publicServices.filter((item) => item.status === "available").map((item) => item.id));
    expect(quickAssistantCases.every((item) => available.has(item.serviceId))).toBe(true);
  });
});
