import { beforeEach, describe, expect, it, vi } from "vitest";

const initSiteConfig = vi.fn();

vi.mock("@/hooks/core/useSiteConfig", () => ({
  useSiteConfig: () => ({ initSiteConfig }),
}));

vi.mock("@utils", () => ({
  checkStorageCompatibility: vi.fn(),
  startVersionPolling: vi.fn(),
  toggleTransition: vi.fn(),
  systemUpgrade: vi.fn(),
}));

import { useAppBootstrap } from "@/hooks/core/useAppBootstrap";

describe("useAppBootstrap", () => {
  beforeEach(() => {
    initSiteConfig.mockClear();
  });

  it("does not request admin site configuration on anonymous portal routes", () => {
    useAppBootstrap().bootstrap("/portal/home");

    expect(initSiteConfig).not.toHaveBeenCalled();
  });

  it("still initializes admin site configuration outside the portal", () => {
    useAppBootstrap().bootstrap("/login");

    expect(initSiteConfig).toHaveBeenCalledOnce();
  });
});
