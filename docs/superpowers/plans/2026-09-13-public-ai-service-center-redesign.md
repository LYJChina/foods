# Public AI Service Center Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the marketing-style portal with a government-oriented AI service center containing a sample-data dashboard, navigation assistant, intelligent service hall, records page, and usage guide while preserving existing service workflows.

**Architecture:** Keep the anonymous `/portal` shell and existing service routes. Add an asynchronous front-end Dashboard adapter that currently returns sample data with contracts reserved for future FastAPI endpoints. Add a service catalog as the single source of truth for the service hall, assistant recommendations, and popular-service links.

**Tech Stack:** Vue 3 Composition API, TypeScript, Vue Router, Element Plus, ECharts 6, Iconify Remix Icon, Vitest, Vue Test Utils, SCSS.

**Spec:** `docs/superpowers/specs/2026-09-13-public-ai-service-center-redesign.md`

## Global Constraints

- Do not implement a real statistics backend, RAG database query, MCP management, or general-purpose RAG assistant in this phase.
- Sample statistics and records must be marked `示例数据`; do not display fabricated growth rates, rankings, or real-time claims.
- Keep the existing `/portal/documents` FastAPI → DocumentParser → LLM workflow unchanged.
- Planned services must be marked `规划中` and must not navigate into fake workflows.
- Use government blue, white, light gray, and restrained gold; no gradients, glass effects, large shadows, purple/pink AI styling, or obvious rounded cards.
- Use square corners or at most `2px` radius for containers, buttons, inputs, charts, and statuses.
- Do not use an emblem, seal, or government agency mark without an authorized asset.
- Maintain visible focus, 4.5:1 text contrast, 16px body text, and 44px mobile interaction targets.
- Verify 375px, 768px, 1024px, and 1440px without horizontal scrolling.

## File Map

- `frontend/web/src/api/module_food_ai/dashboard.ts`: dashboard types and sample adapter.
- `frontend/web/src/views/portal/services/catalog.ts`: canonical service catalog and assistant mapping.
- `frontend/web/src/views/portal/home/index.vue`: dashboard data orchestration.
- `frontend/web/src/views/portal/home/components/*`: metrics, charts, assistant, and recent cases.
- `frontend/web/src/views/portal/services/index.vue`: intelligent service hall.
- `frontend/web/src/views/portal/records/index.vue`: sample record list.
- `frontend/web/src/views/portal/guide/index.vue`: service and data-boundary guidance.
- `frontend/web/src/layouts/portal/index.vue`: government portal header and navigation.
- `frontend/web/src/styles/portal.scss`: shared square visual system.
- `frontend/web/src/router/routes.ts`: public routes.
- `frontend/web/src/__tests__/*`: adapter, page, service, and route behavior.

---

### Task 1: Dashboard Data Contract and Sample Adapter

**Files:**
- Create: `frontend/web/src/api/module_food_ai/dashboard.ts`
- Test: `frontend/web/src/__tests__/dashboard-data.spec.ts`

**Interfaces:**
- Produces: `DashboardSummary`, `ServiceTrendPoint`, `ServiceDistributionItem`, `RecentCase`, `DashboardSnapshot`.
- Produces: `DashboardAPI.getSnapshot(): Promise<DashboardSnapshot>` and `DashboardAPI.dataMode`.

- [ ] **Step 1: Write the failing adapter contract test**

```ts
import { describe, expect, it } from "vitest";
import { DashboardAPI } from "@/api/module_food_ai/dashboard";

describe("dashboard data adapter", () => {
  it("returns a complete sample snapshot behind an async API", async () => {
    const data = await DashboardAPI.getSnapshot();
    expect(DashboardAPI.dataMode).toBe("sample");
    expect(data.summary).toMatchObject({
      total_handled: expect.any(Number),
      knowledge_documents: expect.any(Number),
      today_users: expect.any(Number),
      active_agents: expect.any(Number),
    });
    expect(data.trend).toHaveLength(7);
    expect(data.distribution.length).toBeGreaterThan(0);
    expect(data.recent_cases.length).toBeGreaterThan(0);
  });
});
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `cd frontend/web && npx --yes pnpm@9.15.3 test -- src/__tests__/dashboard-data.spec.ts`

Expected: FAIL because the dashboard module does not exist.

- [ ] **Step 3: Implement typed sample data behind the future API boundary**

```ts
export interface DashboardSummary {
  total_handled: number;
  knowledge_documents: number;
  today_users: number;
  active_agents: number;
  updated_at: string;
}
export interface ServiceTrendPoint { date: string; handled: number }
export interface ServiceDistributionItem { service_id: string; service_name: string; handled: number }
export interface RecentCase {
  id: string;
  title: string;
  service_name: string;
  submitted_at: string;
  status: "completed" | "processing" | "failed";
}
export interface DashboardSnapshot {
  summary: DashboardSummary;
  trend: ServiceTrendPoint[];
  distribution: ServiceDistributionItem[];
  recent_cases: RecentCase[];
}

export const DashboardAPI = {
  dataMode: "sample" as const,
  async getSnapshot(): Promise<DashboardSnapshot> {
    return structuredClone(sampleSnapshot);
  },
};
```

Populate `sampleSnapshot` with the approved summary values `1286`, `3642`, `176`, and `4`; seven dated trend points; four service distribution items; and two or more clearly synthetic recent cases whose IDs begin with `SAMPLE-`.

- [ ] **Step 4: Run the focused test**

Run: `cd frontend/web && npx --yes pnpm@9.15.3 test -- src/__tests__/dashboard-data.spec.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/web/src/api/module_food_ai/dashboard.ts frontend/web/src/__tests__/dashboard-data.spec.ts
git commit -m "feat: add dashboard sample data adapter"
```

---

### Task 2: Canonical Intelligent Service Catalog

**Files:**
- Create: `frontend/web/src/views/portal/services/catalog.ts`
- Test: `frontend/web/src/__tests__/service-hall.spec.ts`

**Interfaces:**
- Produces: `ServiceCategory`, `ServiceStatus`, `PublicService`, `QuickAssistantCase`.
- Produces: `serviceCategories`, `publicServices`, `quickAssistantCases`.
- Consumed by: dashboard assistant and service hall.

- [ ] **Step 1: Write failing catalog tests**

```ts
import { describe, expect, it } from "vitest";
import { publicServices, quickAssistantCases } from "@/views/portal/services/catalog";

describe("public service catalog", () => {
  it("keeps available services routable and planned services disabled", () => {
    expect(publicServices.find((item) => item.id === "documents")).toMatchObject({
      status: "available",
      route: "/portal/documents",
    });
    expect(publicServices.filter((item) => item.status === "planned").every((item) => !item.route)).toBe(true);
  });

  it("maps every quick case to an available service", () => {
    const available = new Set(publicServices.filter((item) => item.status === "available").map((item) => item.id));
    expect(quickAssistantCases.every((item) => available.has(item.serviceId))).toBe(true);
  });
});
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `cd frontend/web && npx --yes pnpm@9.15.3 test -- src/__tests__/service-hall.spec.ts`

Expected: FAIL because the catalog module does not exist.

- [ ] **Step 3: Implement the catalog**

Define available routes for `documents`, `precheck`, `diagnosis`, and `scenarios`. Define `policy-reading`, `label-check`, and `application-materials` as `planned` with no route. Add the four approved assistant cases, each mapped to an available service.

- [ ] **Step 4: Run tests and commit**

Run: `cd frontend/web && npx --yes pnpm@9.15.3 test -- src/__tests__/service-hall.spec.ts`

Expected: PASS.

```bash
git add frontend/web/src/views/portal/services/catalog.ts frontend/web/src/__tests__/service-hall.spec.ts
git commit -m "feat: define public intelligent service catalog"
```

---

### Task 3: Government Portal Shell and Public Routes

**Files:**
- Modify: `frontend/web/src/layouts/portal/index.vue`
- Modify: `frontend/web/src/styles/portal.scss`
- Modify: `frontend/web/src/router/routes.ts`
- Create: `frontend/web/src/views/portal/records/index.vue`
- Create: `frontend/web/src/views/portal/guide/index.vue`
- Modify: `frontend/web/src/__tests__/portal-routes.spec.ts`
- Modify: `frontend/web/src/__tests__/portal-home.spec.ts`

**Interfaces:**
- Produces routes: `/portal/home`, `/portal/services`, `/portal/records`, `/portal/guide`.
- Preserves: `/portal/documents`, `/portal/precheck`, `/portal/precheck/:taskId`, `/portal/scenarios`, `/portal/diagnosis`.

- [ ] **Step 1: Extend tests first**

Assert the primary navigation labels are `中台首页`, `智能服务大厅`, `办理记录`, and `使用指南`. Assert all new routes have `meta.public === true`; assert legacy service routes remain.

- [ ] **Step 2: Run focused tests and verify failure**

Run: `cd frontend/web && npx --yes pnpm@9.15.3 test -- src/__tests__/portal-routes.spec.ts src/__tests__/portal-home.spec.ts`

Expected: FAIL because routes and labels are absent.

- [ ] **Step 3: Add routes and shell**

Add lazy page imports. Keep `/portal/home` as redirect and preserve `/portal/documents`. Rebuild the header with a slim utility bar, brand row, and full-width primary navigation. Retain the skip link and visible focus styles. Use existing authorized project assets only.

- [ ] **Step 4: Add records and guide pages**

The records page consumes `DashboardAPI.getSnapshot()` and labels all rows `示例数据`; sample rows do not have active result links. The guide page explains scope, supported public materials, prohibited core data, and links to `/portal/services`.

- [ ] **Step 5: Run tests and commit**

Run the command from Step 2. Expected: PASS.

```bash
git add frontend/web/src/layouts/portal/index.vue frontend/web/src/styles/portal.scss frontend/web/src/router/routes.ts frontend/web/src/views/portal/records/index.vue frontend/web/src/views/portal/guide/index.vue frontend/web/src/__tests__/portal-routes.spec.ts frontend/web/src/__tests__/portal-home.spec.ts
git commit -m "feat: establish public service center shell"
```

---

### Task 4: Dashboard Metrics, Charts, and Navigation Assistant

**Files:**
- Create: `frontend/web/src/views/portal/home/components/MetricGrid.vue`
- Create: `frontend/web/src/views/portal/home/components/OperationsCharts.vue`
- Create: `frontend/web/src/views/portal/home/components/ServiceAssistant.vue`
- Create: `frontend/web/src/views/portal/home/components/RecentCases.vue`
- Replace: `frontend/web/src/views/portal/home/index.vue`
- Modify: `frontend/web/src/__tests__/portal-home.spec.ts`

**Interfaces:**
- Consumes: `DashboardAPI.getSnapshot()` from Task 1.
- Consumes: `quickAssistantCases` and `publicServices` from Task 2.
- `ServiceAssistant` emits `select-service` with an available service route.

- [ ] **Step 1: Write failing dashboard composition tests**

Mock `DashboardAPI.getSnapshot()` and mount the page with `RouterLinkStub`. Assert four metric items render, `示例数据` is visible, both chart containers have accessible names, four quick cases render, and the document case resolves to `/portal/documents`.

- [ ] **Step 2: Run the home test and verify failure**

Run: `cd frontend/web && npx --yes pnpm@9.15.3 test -- src/__tests__/portal-home.spec.ts`

Expected: FAIL because the dashboard components are absent.

- [ ] **Step 3: Implement `MetricGrid.vue`**

Accept a `DashboardSummary` prop, render the four spec metrics, and format integers with `Intl.NumberFormat("zh-CN")`. Use square white panels with a one-pixel border and a two-pixel blue top rule; do not add comparison percentages.

- [ ] **Step 4: Implement `OperationsCharts.vue`**

Accept `trend` and `distribution` props. Initialize two ECharts instances: a seven-day line chart and a horizontal service bar chart. Use `ResizeObserver` for responsive resizing, call `dispose()` on unmount, and render adjacent textual summaries so the information is not canvas-only.

```ts
onMounted(() => {
  trendChart = echarts.init(trendElement.value!);
  distributionChart = echarts.init(distributionElement.value!);
  renderCharts();
  resizeObserver = new ResizeObserver(() => {
    trendChart?.resize();
    distributionChart?.resize();
  });
  resizeObserver.observe(rootElement.value!);
});
onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  trendChart?.dispose();
  distributionChart?.dispose();
});
```

- [ ] **Step 5: Implement `ServiceAssistant.vue` as a navigator**

Render four quick cases. Selecting one resolves the corresponding available catalog service and shows its description, required materials, and a real `RouterLink` labeled `立即办理`. Free text may match catalog titles and keywords locally. An unmatched query must respond `暂未找到对应服务，请前往智能服务大厅选择`, not fabricate an LLM answer.

- [ ] **Step 6: Implement `RecentCases.vue`**

Render status labels `已完成`, `处理中`, and `处理失败`. Display `示例数据` in the heading and do not provide active result links for synthetic records.

- [ ] **Step 7: Compose the new home page**

Load the snapshot on mount. Show an in-panel loading state and an in-panel retry action if loading fails. Use the twelve-column layout: metrics above, charts in eight columns, assistant in four columns, recent cases below.

- [ ] **Step 8: Run tests and commit**

Run: `cd frontend/web && npx --yes pnpm@9.15.3 test -- src/__tests__/portal-home.spec.ts`

Expected: PASS.

```bash
git add frontend/web/src/views/portal/home frontend/web/src/__tests__/portal-home.spec.ts
git commit -m "feat: build public service operations dashboard"
```

---

### Task 5: Intelligent Service Hall

**Files:**
- Create: `frontend/web/src/views/portal/services/index.vue`
- Modify: `frontend/web/src/views/portal/services/catalog.ts`
- Modify: `frontend/web/src/__tests__/service-hall.spec.ts`
- Modify: `frontend/web/src/styles/portal.scss`

**Interfaces:**
- Consumes: `serviceCategories` and `publicServices` from Task 2.
- Renders a `RouterLink` only when `service.status === "available" && service.route`.

- [ ] **Step 1: Add failing service hall tests**

Mount the hall with `RouterLinkStub`. Assert all seven services render initially, category filtering works, text search matches title and description, the available document service points to `/portal/documents`, and planned services contain no link.

- [ ] **Step 2: Run the focused test and verify failure**

Run: `cd frontend/web && npx --yes pnpm@9.15.3 test -- src/__tests__/service-hall.spec.ts`

Expected: FAIL because the page does not exist.

- [ ] **Step 3: Implement service discovery**

Use a compact title row, labeled search input, rectangular category tabs, and a responsive three-column grid. Each item displays category, truthful status, title, description, service method, required material, and either `立即办理` or disabled `规划中`.

```ts
const filteredServices = computed(() => publicServices.filter((service) => {
  const categoryMatches = activeCategory.value === "all" || service.category === activeCategory.value;
  const text = searchText.value.trim().toLowerCase();
  const textMatches = !text || `${service.title} ${service.description} ${service.keywords.join(" ")}`.toLowerCase().includes(text);
  return categoryMatches && textMatches;
}));
```

- [ ] **Step 4: Add empty-search recovery**

Render `未找到符合条件的服务` and a keyboard-accessible button that clears the category and search value.

- [ ] **Step 5: Run tests and commit**

Run the command from Step 2. Expected: PASS.

```bash
git add frontend/web/src/views/portal/services frontend/web/src/styles/portal.scss frontend/web/src/__tests__/service-hall.spec.ts
git commit -m "feat: add intelligent public service hall"
```

---

### Task 6: Align Existing Service Pages with the Square Government System

**Files:**
- Modify: `frontend/web/src/views/portal/documents/index.vue`
- Modify: `frontend/web/src/views/portal/precheck/index.vue`
- Modify: `frontend/web/src/views/portal/precheck/result.vue`
- Modify: `frontend/web/src/views/portal/scenarios/index.vue`
- Modify: `frontend/web/src/views/portal/diagnosis/index.vue`
- Modify: `frontend/web/src/styles/portal.scss`
- Modify: affected files in `frontend/web/src/__tests__/`.

**Interfaces:**
- Preserves every existing API and form submission contract.
- Produces consistent breadcrumbs back to `/portal/services` and square page panels.

- [ ] **Step 1: Add shared-page assertions**

Retain tests for low-sensitivity confirmation, precheck validation and submission, diagnosis scoring, and scenario count. Add assertions that each service page has a breadcrumb back to `智能服务大厅` and does not render a marketing-style hero.

- [ ] **Step 2: Run affected tests before visual changes**

Run: `cd frontend/web && npx --yes pnpm@9.15.3 test -- src/__tests__/documents-workspace.spec.ts src/__tests__/precheck-flow.spec.ts src/__tests__/precheck-validation.spec.ts src/__tests__/diagnosis-scoring.spec.ts src/__tests__/scenarios.spec.ts`

Expected: new breadcrumb assertions FAIL; existing behavior assertions PASS.

- [ ] **Step 3: Replace promotional surfaces without changing logic**

Use shared square panel, header, button, form, state, and breadcrumb classes. Do not change document APIs, polling, upload validation, question submission, precheck submission, or diagnosis scoring.

- [ ] **Step 4: Remove obsolete CSS safely**

Use `rg` to confirm no component still references `.portal-demo-badge`, `.portal-assistant*`, the old marketing hero, ring chart, or old service-card classes; then remove only unused selectors.

- [ ] **Step 5: Run tests and commit**

Run the command from Step 2. Expected: PASS.

```bash
git add frontend/web/src/views/portal frontend/web/src/styles/portal.scss frontend/web/src/__tests__
git commit -m "style: align public services with government portal"
```

---

### Task 7: Full Verification and Visual QA

**Files:**
- Modify only files that verification proves require a correction.

**Interfaces:**
- Validates the complete public portal without altering backend contracts.

- [ ] **Step 1: Run static and automated verification**

```bash
cd frontend/web
npx --yes pnpm@9.15.3 type-check
npx --yes pnpm@9.15.3 test
npx --yes pnpm@9.15.3 build:dev
```

Expected: all commands exit `0` and all tests pass.

- [ ] **Step 2: Verify service routes against running local services**

Open `/portal/home`, `/portal/services`, `/portal/records`, `/portal/guide`, and `/portal/documents`. Confirm the public pages load without authentication and the document route still reaches its existing workflow.

- [ ] **Step 3: Verify responsive widths**

At 375px, 768px, 1024px, and 1440px verify `document.documentElement.scrollWidth === document.documentElement.clientWidth`, metrics remain readable, charts resize, navigation remains usable, and the assistant never covers content.

- [ ] **Step 4: Verify honesty and visual-system constraints**

Confirm sample metrics and records show `示例数据`; planned services cannot navigate; no unauthorized emblem appears; no obvious rounded cards, gradients, glass effects, or purple/pink AI styling remain; keyboard focus is visible.

- [ ] **Step 5: Commit verification fixes if any**

```bash
git add frontend/web
git commit -m "fix: complete public service center verification"
```

Do not create an empty commit when no fixes are required.
