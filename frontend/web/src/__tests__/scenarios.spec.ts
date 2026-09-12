import { mount, RouterLinkStub } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import PortalScenarios from "@/views/portal/scenarios/index.vue";

describe("scenario gallery", () => {
  it("shows six bounded food-industry demo scenarios", () => {
    const wrapper = mount(PortalScenarios, {
      global: { stubs: { RouterLink: RouterLinkStub } },
    });

    expect(wrapper.findAll('[data-testid="scenario-card"]')).toHaveLength(6);
    expect(wrapper.text()).toContain("AI+通用办公");
    expect(wrapper.text()).toContain("AI+研发");
    expect(wrapper.text()).toContain("AI+制造");
    expect(wrapper.text()).toContain("AI+质量");
    expect(wrapper.text()).toContain("AI+营销出海");
    expect(wrapper.text()).toContain("AI+经营");

    for (const card of wrapper.findAll('[data-testid="scenario-card"]')) {
      expect(card.text()).toMatch(/Demo|模拟|规划/);
    }
  });
});
