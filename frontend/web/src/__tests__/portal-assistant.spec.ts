import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import PortalAssistant from "@/views/portal/assistant/index.vue";

const { askSpy } = vi.hoisted(() => ({
  askSpy: vi.fn(),
}));

vi.mock("@/api/module_food_ai/assistant", () => ({
  AssistantAPI: { ask: askSpy },
}));

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/portal/assistant", component: PortalAssistant },
      { path: "/portal/precheck", component: { template: "<div>预检</div>" } },
    ],
  });
}

describe("public service assistant", () => {
  beforeEach(() => {
    askSpy.mockReset();
    askSpy.mockResolvedValue({
      answer: "可先使用出口合规预检服务整理材料。",
      conversation_id: "conversation-1",
      recommended_services: [{ name: "出口合规预检", route: "/portal/precheck" }],
      sources: [],
      disclaimer: "AI 生成，仅供辅助参考",
    });
  });

  it("prefills q without automatically calling the model API", async () => {
    const router = makeRouter();
    await router.push("/portal/assistant?q=%E5%A6%82%E4%BD%95%E8%A7%A3%E6%9E%90%E6%94%BF%E7%AD%96%E6%96%87%E4%BB%B6%EF%BC%9F");
    await router.isReady();
    const wrapper = mount(PortalAssistant, { global: { plugins: [router] } });

    expect((wrapper.get("textarea").element as HTMLTextAreaElement).value).toBe("如何解析政策文件？");
    expect(askSpy).not.toHaveBeenCalled();
  });

  it("sends only after explicit submit and renders the result", async () => {
    const router = makeRouter();
    await router.push("/portal/assistant");
    await router.isReady();
    const wrapper = mount(PortalAssistant, { global: { plugins: [router] } });

    await wrapper.get("textarea").setValue("出口合规需要哪些材料？");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(wrapper.text()).toContain("可先使用出口合规预检服务整理材料。");
    expect(wrapper.text()).toContain("出口合规预检");
    expect(wrapper.text()).toContain("AI 生成，仅供辅助参考");
  });

  it("keeps the question and offers retry when the service is unavailable", async () => {
    askSpy.mockRejectedValueOnce(new Error("503"));
    const router = makeRouter();
    await router.push("/portal/assistant");
    await router.isReady();
    const wrapper = mount(PortalAssistant, { global: { plugins: [router] } });

    await wrapper.get("textarea").setValue("如何办理？");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(wrapper.get("[role='alert']").text()).toContain("暂不可用");
    expect((wrapper.get("textarea").element as HTMLTextAreaElement).value).toBe("如何办理？");
    expect(wrapper.text()).toContain("重新发送");
  });
});
