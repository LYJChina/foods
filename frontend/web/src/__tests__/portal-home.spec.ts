import { flushPromises, mount, RouterLinkStub } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

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

  it("presents public-service entry points and sample information", async () => {
    const wrapper = mount(PortalHome, {
      global: { stubs: { RouterLink: RouterLinkStub } },
    });
    await flushPromises();

    expect(wrapper.get("h1").text()).toContain("AI 助手");
    expect(wrapper.text()).toContain("我要查");
    expect(wrapper.text()).toContain("我要办");
    expect(wrapper.text()).toContain("工作动态");
    expect(wrapper.text()).toContain("通知公告");
    expect(wrapper.text()).toContain("示例信息");
    expect(wrapper.text()).not.toContain("运行概况");
    expect(wrapper.text()).not.toContain("最近办理事项");
  });

  it("routes a typed AI search to the assistant without sending it", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/portal/home", component: PortalHome },
        { path: "/portal/assistant", component: { template: "<div />" } },
      ],
    });
    await router.push("/portal/home");
    await router.isReady();
    const wrapper = mount(PortalHome, { global: { plugins: [router] } });
    await flushPromises();

    await wrapper.get("[data-testid='ai-search-input']").setValue("出口合规需要哪些材料？");
    await wrapper.get("[data-testid='ai-search-form']").trigger("submit");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe("/portal/assistant");
    expect(router.currentRoute.value.query.q).toBe("出口合规需要哪些材料？");
  });

  it("opens the assistant without a query when the empty search field is activated", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/portal/home", component: PortalHome },
        { path: "/portal/assistant", component: { template: "<div />" } },
      ],
    });
    await router.push("/portal/home");
    await router.isReady();
    const wrapper = mount(PortalHome, { global: { plugins: [router] } });
    await flushPromises();

    await wrapper.get("[data-testid='ai-search-input']").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.fullPath).toBe("/portal/assistant");
  });

  it("lists the canonical public service catalog with its real availability state", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/portal/services", component: PortalServices }],
    });
    await router.push("/portal/services");
    await router.isReady();
    const wrapper = mount(PortalServices, {
      global: { plugins: [router] },
    });

    expect(wrapper.text()).toContain("智能文档解析");
    expect(wrapper.text()).toContain("出口合规预检");
    expect(wrapper.text()).toContain("可办理");
    expect(wrapper.text()).toContain("规划中");
  });
});
