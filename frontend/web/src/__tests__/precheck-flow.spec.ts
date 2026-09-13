import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { describe, expect, it, vi } from "vitest";

import { FoodAIPortalAPI } from "@/api/module_food_ai/portal";
import PortalPrecheck from "@/views/portal/precheck/index.vue";

vi.mock("@/api/module_food_ai/portal", () => ({
  FoodAIPortalAPI: {
    createPrecheck: vi.fn(),
  },
}));

describe("precheck flow", () => {
  it("validates each step, submits low-sensitivity data and opens the result", async () => {
    vi.mocked(FoodAIPortalAPI.createPrecheck).mockResolvedValue({
      task_id: "demo-task-1",
      status: "completed",
      submitted_at: "2026-09-13T00:00:00Z",
      request: {
        product_name: "潮州糖果示例产品",
        product_category: "candy",
        target_market: "EU",
        materials: ["label_image"],
        contains_core_data: false,
      },
      result: {
        overall: "needs_review",
        risks: [],
        missing_materials: [],
        source_labels: ["Demo 规则集（非实时法规库）"],
        next_steps: [],
        disclaimer: "仅用于辅助预检。",
        is_demo: true,
      },
    });

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/portal/precheck", component: PortalPrecheck },
        { path: "/portal/precheck/:taskId", component: { template: "<div>result</div>" } },
      ],
    });
    await router.push("/portal/precheck");
    await router.isReady();

    const wrapper = mount(PortalPrecheck, {
      global: { plugins: [router] },
    });

    expect(wrapper.text()).not.toMatch(/Demo|DEMO|演示原型|模拟回复/i);

    await wrapper.get('[data-testid="next-step"]').trigger("click");
    expect(wrapper.text()).toContain("请输入产品名称");

    await wrapper.get("#product-name").setValue("潮州糖果示例产品");
    await wrapper.get("#product-category").setValue("candy");
    await wrapper.get("#target-market").setValue("EU");
    await wrapper.get('[data-testid="next-step"]').trigger("click");

    await wrapper.get('input[value="label_image"]').setValue(true);
    await wrapper.get('[data-testid="next-step"]').trigger("click");

    await wrapper.get("#confirm-low-sensitivity").setValue(true);
    await wrapper.get("#accept-disclaimer").setValue(true);
    wrapper.get('[data-testid="submit-precheck"]');
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(router.currentRoute.value.fullPath).toBe("/portal/precheck/demo-task-1");
  });
});
