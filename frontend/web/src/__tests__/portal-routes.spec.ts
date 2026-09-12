import { describe, expect, it, vi } from "vitest";
import type { RouteRecordRaw } from "vue-router";

vi.mock("@stores", () => ({
  useWorktabStore: () => ({ keepAliveExclude: [] }),
}));
vi.mock("@/locales", () => ({ $t: (key: string) => key }));
vi.mock("@/layouts/index.vue", () => ({ default: { name: "AdminLayoutStub" } }));
vi.mock("@views/dashboard/workplace/index.vue", () => ({ default: {} }));
vi.mock("@views/dashboard/analysis/index.vue", () => ({ default: {} }));
vi.mock("@views/redirect/index.vue", () => ({ default: {} }));
vi.mock("@views/module_system/auth/login/index.vue", () => ({ default: {} }));
vi.mock("@views/exception/401/index.vue", () => ({ default: {} }));
vi.mock("@views/exception/403/index.vue", () => ({ default: {} }));
vi.mock("@views/exception/404/index.vue", () => ({ default: {} }));
vi.mock("@views/exception/500/index.vue", () => ({ default: {} }));
vi.mock("@views/dashboard/home/index.vue", () => ({ default: {} }));
vi.mock("@views/fastlink/current/profile.vue", () => ({ default: {} }));
vi.mock("@views/fastlink/changelog/index.vue", () => ({ default: {} }));
vi.mock("@views/fastlink/pricing/index.vue", () => ({ default: {} }));
vi.mock("@views/fastlink/tutorial/index.vue", () => ({ default: {} }));
vi.mock("@views/fastlink/fachat/index.vue", () => ({ default: {} }));

import { staticRoutes } from "@/router/routes";

describe("public portal routes", () => {
  it("registers the complete anonymous portal flow", () => {
    const portalRoute = staticRoutes.find((route) => route.path === "/portal");

    expect(portalRoute).toBeDefined();
    expect(portalRoute?.meta?.public).toBe(true);

    const children = (portalRoute?.children ?? []) as RouteRecordRaw[];
    expect(children.map((route) => route.path)).toEqual([
      "home",
      "precheck",
      "precheck/:taskId",
      "scenarios",
      "diagnosis",
    ]);
    expect(children.every((route) => route.meta?.public === true)).toBe(true);
  });
});
