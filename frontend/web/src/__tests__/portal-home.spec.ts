import { mount, RouterLinkStub } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import PortalLayout from "@/layouts/portal/index.vue";
import PortalHome from "@/views/portal/home/index.vue";

describe("portal homepage", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("presents the four public service entrances and demo data disclosure", () => {
    const wrapper = mount(PortalHome, {
      global: { stubs: { RouterLink: RouterLinkStub } },
    });

    expect(wrapper.get("h1").text()).toContain("看得见 AI");
    expect(wrapper.findAll('[data-testid="service-card"]')).toHaveLength(4);
    expect(wrapper.text()).toContain("出口合规与海外服务");
    expect(wrapper.text()).toContain("演示数据，非实时统计");
    expect(wrapper.findAllComponents(RouterLinkStub).some((link) => link.props("to") === "/portal/precheck")).toBe(true);
  });

  it("labels assistant replies as simulated and supports collapsing", async () => {
    const wrapper = mount(PortalLayout, {
      global: { stubs: { RouterView: true, RouterLink: RouterLinkStub } },
    });

    expect(wrapper.text()).toContain("模拟回复");
    expect(wrapper.text()).toContain("未连接实时大模型");

    await wrapper.get('button[aria-label="收起 AI 助手"]').trigger("click");
    expect(wrapper.find('button[aria-label="展开 AI 助手"]').exists()).toBe(true);
  });

  it("starts collapsed on narrow screens so content remains unobscured", () => {
    vi.stubGlobal("matchMedia", vi.fn().mockReturnValue({ matches: true }));

    const wrapper = mount(PortalLayout, {
      global: { stubs: { RouterView: true, RouterLink: RouterLinkStub } },
    });

    expect(wrapper.find('button[aria-label="展开 AI 助手"]').exists()).toBe(true);
  });

  it("starts collapsed at standard desktop widths so cards remain unobscured", () => {
    vi.stubGlobal(
      "matchMedia",
      vi.fn().mockImplementation((query: string) => ({ matches: query === "(max-width: 1599px)" }))
    );

    const wrapper = mount(PortalLayout, {
      global: { stubs: { RouterView: true, RouterLink: RouterLinkStub } },
    });

    expect(wrapper.find('button[aria-label="展开 AI 助手"]').exists()).toBe(true);
  });
});
