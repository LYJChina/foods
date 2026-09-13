import { mount, RouterLinkStub } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import PortalLayout from "@/layouts/portal/index.vue";
import PortalHome from "@/views/portal/home/index.vue";

describe("portal homepage", () => {
  it("presents the four public service entrances and demo data disclosure", () => {
    const wrapper = mount(PortalHome, {
      global: { stubs: { RouterLink: RouterLinkStub } },
    });

    expect(wrapper.get("h1").text()).toContain("看得见 AI");
    expect(wrapper.findAll('[data-testid="service-card"]')).toHaveLength(4);
    expect(wrapper.text()).toContain("出口合规与海外服务");
    expect(wrapper.text()).toContain("演示数据，非实时统计");
    expect(
      wrapper
        .findAllComponents(RouterLinkStub)
        .some((link) => link.props("to") === "/portal/precheck")
    ).toBe(true);
  });

  it("uses production-facing portal branding without a simulated assistant", () => {
    const wrapper = mount(PortalLayout, {
      global: { stubs: { RouterView: true, RouterLink: RouterLinkStub } },
    });

    expect(wrapper.text()).not.toMatch(/DEMO|演示原型|模拟回复/i);
    expect(wrapper.find('button[aria-label="展开 AI 助手"]').exists()).toBe(false);
    expect(wrapper.text()).toContain("食品行业·政务公共服务");
  });
});
