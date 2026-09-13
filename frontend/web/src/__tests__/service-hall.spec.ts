import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import { publicServices, quickAssistantCases } from "@/views/portal/services/catalog";
import PortalServices from "@/views/portal/services/index.vue";

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/portal/services", component: PortalServices }],
  });
}

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

  it("applies supported category and availability query parameters", async () => {
    const router = makeRouter();
    await router.push("/portal/services?category=policy&status=available");
    await router.isReady();
    const wrapper = mount(PortalServices, { attachTo: document.body, global: { plugins: [router] } });

    expect(wrapper.text()).toContain("出口合规预检");
    expect(wrapper.text()).not.toContain("食品标签辅助检查");
    expect(wrapper.text()).not.toContain("智能文档解析");
    wrapper.unmount();
  });

  it("falls back from an unknown category and focuses search on request", async () => {
    const router = makeRouter();
    await router.push("/portal/services?category=unknown&focus=search");
    await router.isReady();
    const wrapper = mount(PortalServices, { attachTo: document.body, global: { plugins: [router] } });
    await flushPromises();

    expect(wrapper.text()).toContain("智能文档解析");
    expect(wrapper.text()).toContain("出口合规预检");
    expect(document.activeElement).toBe(wrapper.get("input[type='search']").element);
    wrapper.unmount();
  });
});
