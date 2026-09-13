import { flushPromises, mount, RouterLinkStub } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import PortalLayout from "@/layouts/portal/index.vue";
import PortalHome from "@/views/portal/home/index.vue";
import PortalServices from "@/views/portal/services/index.vue";

describe("portal homepage", () => {
  it("renders the neutral government-service shell", () => {
    const wrapper = mount(PortalLayout, {
      global: { stubs: { RouterView: true, RouterLink: RouterLinkStub } },
    });

    expect(wrapper.text()).toContain("食品行业 AI 公共服务平台");
    const navigation = wrapper.get('nav[aria-label="主导航"]');
    expect(navigation.text()).toContain("首页");
    expect(navigation.text()).toContain("智能服务");
    expect(navigation.text()).toContain("办理记录");
    expect(navigation.text()).toContain("使用指南");
    expect(wrapper.text()).not.toContain("潮州市");
    expect(wrapper.text()).not.toMatch(/DEMO|演示原型|MinerU/i);
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
