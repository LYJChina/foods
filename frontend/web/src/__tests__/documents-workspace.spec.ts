import { mount, RouterLinkStub } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import PortalDocuments from "@/views/portal/documents/index.vue";

vi.mock("@/api/module_food_ai/documents", () => ({
  DocumentAPI: {
    create: vi.fn(),
    status: vi.fn(),
    content: vi.fn(),
    question: vi.fn(),
    remove: vi.fn(),
  },
}));

describe("document parsing workspace", () => {
  it("presents a bounded upload flow with clear service constraints", () => {
    const wrapper = mount(PortalDocuments, {
      global: {
        stubs: {
          ElUpload: { template: "<div><slot /><slot name='tip' /></div>" },
          ElButton: { template: "<button><slot /></button>" },
          ElCheckbox: { template: "<label><input type='checkbox' /><slot /></label>" },
          ElInput: { template: "<textarea />" },
          RouterLink: RouterLinkStub,
        },
      },
    });

    expect(wrapper.get("h1").text()).toContain("智能文档解析与问答");
    expect(wrapper.text()).toContain("公共服务平台智能体");
    expect(wrapper.text()).toContain("20MB");
    expect(wrapper.text()).toContain("24 小时自动删除");
    expect(wrapper.text()).toContain("禁止上传配方、工艺、成本、客户、订单和生产经营数据");
    expect(wrapper.text()).not.toMatch(/DEMO|原型|模拟结果/i);
    expect(wrapper.find('[data-testid="document-stepper"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="document-upload-card"]').exists()).toBe(true);
    expect(wrapper.text()).not.toContain("RAG 数据库");
    expect(wrapper.text()).not.toContain("MCP 管理");
  });
});
