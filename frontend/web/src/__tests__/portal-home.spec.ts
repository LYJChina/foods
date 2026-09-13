import { flushPromises, mount, RouterLinkStub } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import PortalLayout from "@/layouts/portal/index.vue";
import PortalHome from "@/views/portal/home/index.vue";
import PortalServices from "@/views/portal/services/index.vue";

describe("portal homepage", () => {
  it("presents the operations overview and sample data disclosure", async () => {
    const wrapper = mount(PortalHome, {
      global: { stubs: { RouterLink: RouterLinkStub } },
    });
    await flushPromises();

    expect(wrapper.get("h1").text()).toContain("运行概况");
    expect(wrapper.text()).toContain("累计办理事项");
    expect(wrapper.text()).toContain("示例数据");
    expect(wrapper.text()).toContain("公共服务助手");
    expect(wrapper.text()).toContain("最近办理事项");
    expect(
      wrapper
        .findAllComponents(RouterLinkStub)
        .some((link) => link.props("to") === "/portal/documents")
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

  it("provides the public service center primary navigation", () => {
    const wrapper = mount(PortalLayout, {
      global: { stubs: { RouterView: true, RouterLink: RouterLinkStub } },
    });

    const navigation = wrapper.get('nav[aria-label="主导航"]');
    expect(navigation.text()).toContain("中台首页");
    expect(navigation.text()).toContain("智能服务大厅");
    expect(navigation.text()).toContain("办理记录");
    expect(navigation.text()).toContain("使用指南");
  });

  it("lists the canonical public service catalog with its real availability state", () => {
    const wrapper = mount(PortalServices, {
      global: { stubs: { RouterLink: RouterLinkStub } },
    });

    expect(wrapper.text()).toContain("智能文档解析");
    expect(wrapper.text()).toContain("出口合规预检");
    expect(wrapper.text()).toContain("可办理");
    expect(wrapper.text()).toContain("规划中");
  });
});
