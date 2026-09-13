# Government Portal AI Search Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有食品行业运行看板首页重构为政务公共服务门户，并新增一个由后端安全调用国产大模型的独立智能问答页。

**Architecture:** Vue 3 公共门户继续使用现有 `/portal` 匿名壳层，首页内容由前端样例适配器提供并明确标注“示例信息”，AI 搜索只负责路由到独立问答页。FastAPI 新增公共助手边界，复用现有 OpenAI-compatible 服务端配置，前端永不接触 API key；具体文档解析、预检、诊断和场景流程不改。

**Tech Stack:** Vue 3、TypeScript、Vue Router、SCSS、Vitest、Vue Test Utils、FastAPI、Pydantic、httpx、pytest

**Spec:** `docs/superpowers/specs/2026-09-14-government-portal-ai-search-redesign.md`

## Global Constraints

- 主色为政府深蓝 `#174B82`，功能蓝为 `#2F6FB2`，背景使用白色和浅灰蓝。
- 红色仅作为栏目标题下划线或少量当前导航提示。
- 容器使用直角或 2px 微圆角；禁止胶囊卡片、大面积阴影、玻璃效果、渐变和紫色 AI 风格。
- 不使用政府机关名称、国徽、公章、官方 Logo 或仿官方认证图形。
- 首页新闻、通知和统计必须显式标注“示例信息”，不得伪装成真实政府发布。
- 首页搜索不会自动调用模型；查询参数只预填智能问答输入框，由用户再次发送。
- 前端只调用平台 FastAPI；模型地址、模型名称和 API key 仅从后端环境变量读取。
- 模型未配置或不可用时明确返回 503，不生成伪造答案。
- 用户可见文案不得出现上游文档解析工具名称，统一使用“公共服务平台智能体”。
- `backend/data/documents/` 是运行数据，不提交、不删除、不改写。
- 375px、768px、1024px、1440px 视口不得产生横向滚动。

---

### Task 1: 固化政务门户壳层与视觉 Token

**Files:**
- Modify: `frontend/web/src/layouts/portal/index.vue`
- Modify: `frontend/web/src/styles/portal.scss`
- Modify: `frontend/web/src/__tests__/portal-home.spec.ts`

**Interfaces:**
- Consumes: 现有 `PortalLayout`、`RouterView` 和 `/portal/*` 匿名路由。
- Produces: 四项一级导航、三层页头、统一 `.portal-*` 政务视觉 token，供后续首页与问答页复用。

- [ ] **Step 1: 把壳层验收改写为失败测试**

  在 `portal-home.spec.ts` 中将壳层断言改为：

  ```ts
  it("renders the neutral government-service shell", () => {
    const wrapper = mount(PortalLayout, {
      global: { stubs: { RouterView: true, RouterLink: RouterLinkStub } },
    });

    expect(wrapper.text()).toContain("食品行业 AI 公共服务平台");
    expect(wrapper.text()).toContain("首页");
    expect(wrapper.text()).toContain("智能服务");
    expect(wrapper.text()).toContain("办理记录");
    expect(wrapper.text()).toContain("使用指南");
    expect(wrapper.text()).not.toContain("潮州市");
    expect(wrapper.text()).not.toMatch(/DEMO|演示原型|MinerU/i);
  });
  ```

- [ ] **Step 2: 运行测试并确认旧页头不满足新文案**

  Run: `cd frontend/web && pnpm vitest run src/__tests__/portal-home.spec.ts`

  Expected: FAIL，原因包含仍显示“潮州市”或“中台首页”。

- [ ] **Step 3: 实现中性平台页头与四项导航**

  在 `layouts/portal/index.vue` 中保留跳转主内容链接，把用户可见结构改为：辅助栏（公共服务平台、无障碍浏览、使用帮助）、品牌栏（食品行业 AI 公共服务平台）、主导航（首页、智能服务、办理记录、使用指南）。无障碍和帮助入口使用站内锚点或现有 `/portal/guide`，不制造外部政府链接。

  在 `portal.scss` 中将全局 token 固定为：

  ```scss
  :root {
    --portal-navy: #174b82;
    --portal-navy-deep: #123d6b;
    --portal-blue: #2f6fb2;
    --portal-red: #b4232b;
    --portal-bg: #f4f7fa;
    --portal-card: #fff;
    --portal-text: #172b3f;
    --portal-muted: #526477;
    --portal-border: #d6e0e9;
    --portal-radius: 2px;
  }
  ```

  清除公共门户范围内的 `linear-gradient`、`radial-gradient`、`border-radius: 999px` 和明显悬浮阴影；按钮、表单与卡片统一 `var(--portal-radius)`。保留圆形进度或状态图形时必须是数据表达而非装饰卡片。

- [ ] **Step 4: 运行壳层测试与样式静态扫描**

  Run: `cd frontend/web && pnpm vitest run src/__tests__/portal-home.spec.ts && ! rg -n "gradient|border-radius:\s*(999px|1[024]px)" src/layouts/portal src/views/portal/home src/views/portal/assistant src/styles/portal.scss`

  Expected: PASS；扫描无匹配。问答目录尚未创建时 `rg` 可忽略不存在路径，但实施完成后的全量验收必须无匹配。

- [ ] **Step 5: 提交门户壳层**

  Run: `git add frontend/web/src/layouts/portal/index.vue frontend/web/src/styles/portal.scss frontend/web/src/__tests__/portal-home.spec.ts && git commit -m "feat: refresh public portal shell"`

---

### Task 2: 建立首页样例内容适配层

**Files:**
- Create: `frontend/web/src/api/module_food_ai/content.ts`
- Create: `frontend/web/src/__tests__/portal-content.spec.ts`

**Interfaces:**
- Consumes: `ServiceCategory["id"]` 和现有站内路由。
- Produces: `PortalContentAPI.getHomeContent(): Promise<PortalHomeContent>`；新闻、通知、热点词、快捷入口和服务专区均由同一类型化数据源输出。

- [ ] **Step 1: 写适配层契约测试**

  ```ts
  import { describe, expect, it } from "vitest";
  import { PortalContentAPI } from "@/api/module_food_ai/content";

  describe("portal content adapter", () => {
    it("labels every news and notice item as sample data", async () => {
      const content = await PortalContentAPI.getHomeContent();
      expect(content.dataMode).toBe("sample");
      expect([...content.news, ...content.notices].length).toBeGreaterThan(0);
      expect([...content.news, ...content.notices].every((item) => item.dataMode === "sample")).toBe(true);
    });

    it("uses only valid internal targets", async () => {
      const content = await PortalContentAPI.getHomeContent();
      expect(content.quickActions.every((item) => item.to.startsWith("/portal/"))).toBe(true);
      expect(content.serviceZones.every((item) => item.to.startsWith("/portal/services?category="))).toBe(true);
    });
  });
  ```

- [ ] **Step 2: 运行测试并确认模块不存在**

  Run: `cd frontend/web && pnpm vitest run src/__tests__/portal-content.spec.ts`

  Expected: FAIL，提示无法解析 `module_food_ai/content`。

- [ ] **Step 3: 实现类型化样例适配器**

  定义 `PortalContentItem`、`PortalQuickAction`、`PortalServiceZone`、`PortalHomeContent`。每条新闻与通知都包含 `id`、`title`、`date`、`kind`、`dataMode: "sample"`；适配器返回 `Promise.resolve(structuredClone(sampleHomeContent))`，避免组件修改共享常量。

  快捷入口固定映射：

  ```ts
  const quickActions = [
    { id: "query", label: "我要查", icon: "ri:search-line", to: "/portal/services?focus=search" },
    { id: "handle", label: "我要办", icon: "ri:file-list-3-line", to: "/portal/services?status=available" },
    { id: "assistant", label: "智能问答", icon: "ri:chat-3-line", to: "/portal/assistant" },
    { id: "documents", label: "文档解析", icon: "ri:file-text-line", to: "/portal/documents" },
  ] as const;
  ```

  服务专区 category 使用 `policy`、`enterprise`、`documents`、`diagnosis`，不得创建服务大厅无法识别的参数。

- [ ] **Step 4: 运行内容契约测试**

  Run: `cd frontend/web && pnpm vitest run src/__tests__/portal-content.spec.ts`

  Expected: PASS。

- [ ] **Step 5: 提交内容适配层**

  Run: `git add frontend/web/src/api/module_food_ai/content.ts frontend/web/src/__tests__/portal-content.spec.ts && git commit -m "feat: add sample portal content adapter"`

---

### Task 3: 重构首页为新闻与公共服务门户

**Files:**
- Modify: `frontend/web/src/views/portal/home/index.vue`
- Modify: `frontend/web/src/__tests__/portal-home.spec.ts`
- Modify: `frontend/web/src/styles/portal.scss`

**Interfaces:**
- Consumes: `PortalContentAPI.getHomeContent()`；Vue Router `push()`；站内 `/portal/assistant`、`/portal/services` 和 `/portal/documents`。
- Produces: 首页 AI 搜索跳转、四个快捷入口、四个服务专区、工作动态和通知公告双列列表。

- [ ] **Step 1: 写首页结构和跳转失败测试**

  使用内存路由挂载首页，至少覆盖：栏目存在、示例标签存在、空搜索点击、带问题提交。

  ```ts
  it("routes AI search to the assistant without sending automatically", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/portal/home", component: PortalHome },
        { path: "/portal/assistant", component: { template: "<div />" } },
      ],
    });
    await router.push("/portal/home");
    const wrapper = mount(PortalHome, { global: { plugins: [router] } });
    await flushPromises();

    expect(wrapper.text()).toContain("工作动态");
    expect(wrapper.text()).toContain("通知公告");
    expect(wrapper.text()).toContain("示例信息");
    await wrapper.get("[data-testid='ai-search-input']").setValue("出口合规需要哪些材料？");
    await wrapper.get("[data-testid='ai-search-form']").trigger("submit");
    await flushPromises();
    expect(router.currentRoute.value.fullPath).toBe("/portal/assistant?q=%E5%87%BA%E5%8F%A3%E5%90%88%E8%A7%84%E9%9C%80%E8%A6%81%E5%93%AA%E4%BA%9B%E6%9D%90%E6%96%99%EF%BC%9F");
  });
  ```

- [ ] **Step 2: 运行测试确认旧运行看板失败**

  Run: `cd frontend/web && pnpm vitest run src/__tests__/portal-home.spec.ts`

  Expected: FAIL，旧首页仍包含运行概况且没有新闻通知结构。

- [ ] **Step 3: 实现新首页**

  删除首页对 `DashboardAPI`、运行图表、最近办理和内嵌助手的依赖。建立 `query`、`content`、`loading`、`loadError` 状态；搜索提交规则为：

  ```ts
  const openAssistant = () => {
    const normalized = query.value.trim();
    return router.push({
      path: "/portal/assistant",
      query: normalized ? { q: normalized } : undefined,
    });
  };
  ```

  首页 DOM 顺序固定为：AI 搜索首屏、热门问题、快捷入口、服务专区、工作动态/通知公告。信息列表标题旁显示“示例信息”，加载失败只替换信息列表并提供重试，不阻断搜索与服务入口。

- [ ] **Step 4: 实现首页响应式样式**

  1440px 使用四列入口与双列新闻，1024px 服务专区降为两列，768px 新闻通知改单列，375px 快捷入口两列且搜索按钮高度至少 44px。所有卡片使用 0–2px 圆角，无渐变和重阴影。

- [ ] **Step 5: 运行首页和内容测试**

  Run: `cd frontend/web && pnpm vitest run src/__tests__/portal-home.spec.ts src/__tests__/portal-content.spec.ts`

  Expected: PASS。

- [ ] **Step 6: 提交首页**

  Run: `git add frontend/web/src/views/portal/home/index.vue frontend/web/src/styles/portal.scss frontend/web/src/__tests__/portal-home.spec.ts && git commit -m "feat: rebuild portal homepage around public services"`

---

### Task 4: 新增后端公共智能问答边界

**Files:**
- Create: `backend/app/plugin/food_ai/assistant.py`
- Modify: `backend/app/plugin/food_ai/schema.py`
- Modify: `backend/app/plugin/food_ai/controller.py`
- Create: `backend/tests/plugin/food_ai/test_assistant.py`

**Interfaces:**
- Consumes: `settings.DOCUMENT_LLM_BASE_URL`、`settings.DOCUMENT_LLM_MODEL`、`settings.DOCUMENT_LLM_API_KEY`、`settings.DOCUMENT_LLM_TIMEOUT_SECONDS`；OpenAI-compatible `/chat/completions` 协议。
- Produces: `POST /food-ai/assistant/questions`，输入 `AssistantQuestionRequest`，输出 `AssistantQuestionResult`。

- [ ] **Step 1: 写 schema 和控制器失败测试**

  ```py
  def test_assistant_rejects_blank_question(test_client):
      response = test_client.post("/food-ai/assistant/questions", json={"question": "   "})
      assert response.status_code == 422


  def test_assistant_returns_recommendations_and_disclaimer(test_client, monkeypatch):
      async def fake_answer(question: str, conversation_id: str | None = None):
          return AssistantQuestionResult(
              answer="可先使用出口合规预检服务整理材料。",
              conversation_id="conversation-1",
              recommended_services=[AssistantServiceRecommendation(name="出口合规预检", route="/portal/precheck")],
              sources=[],
          )
      monkeypatch.setattr(food_ai_service.assistant, "answer", fake_answer)
      response = test_client.post("/food-ai/assistant/questions", json={"question": "出口材料有哪些？"})
      assert response.status_code == 200
      assert response.json()["data"]["disclaimer"] == "AI 生成，仅供辅助参考"
  ```

  同一文件补充：未配置模型返回 503、httpx 超时返回 503、无可靠来源时 `sources == []`。

- [ ] **Step 2: 运行后端测试确认端点不存在**

  Run: `cd backend && .venv/bin/pytest tests/plugin/food_ai/test_assistant.py -q`

  Expected: FAIL，端点返回 404 或导入的新类型不存在。

- [ ] **Step 3: 定义请求响应类型**

  在 `schema.py` 新增：

  ```py
  class AssistantQuestionRequest(BaseModel):
      question: str = Field(min_length=1, max_length=2000)
      conversation_id: str | None = Field(default=None, max_length=128)

      @field_validator("question")
      @classmethod
      def strip_question(cls, value: str) -> str:
          value = value.strip()
          if not value:
              raise ValueError("问题不能为空")
          return value


  class AssistantServiceRecommendation(BaseModel):
      name: str
      route: str


  class AssistantQuestionResult(BaseModel):
      answer: str
      conversation_id: str
      recommended_services: list[AssistantServiceRecommendation] = Field(default_factory=list)
      sources: list[str] = Field(default_factory=list)
      disclaimer: Literal["AI 生成，仅供辅助参考"] = "AI 生成，仅供辅助参考"
  ```

- [ ] **Step 4: 实现服务端模型适配器**

  `assistant.py` 定义 `AssistantUnavailable`、`PublicAssistant` protocol、`OpenAICompatiblePublicAssistant`。系统提示词只允许平台服务导航和辅助性解释，明确禁止正式审批/认证/监管/法律结论，并将四项现有可用服务名称与路由写入后端白名单。模型只输出 JSON；Pydantic 校验失败、HTTP 错误、超时或缺少配置均抛出 `AssistantUnavailable`。

  客户端使用 `httpx.AsyncClient(timeout=min(configured_timeout, 30), trust_env=False)`，网络超时最多重试一次；401、403、422 等非瞬时错误不重试。返回的推荐路由必须经过白名单过滤，来源在没有已配置可靠材料时固定为空数组。

- [ ] **Step 5: 注册控制器端点并映射 503**

  在 `controller.py` 增加 `POST /assistant/questions`。捕获 `AssistantUnavailable` 后抛出 `CustomException(msg="问答模型服务未配置或暂不可用", status_code=503)`；不得把底层响应体、模型地址或密钥写入错误消息。

- [ ] **Step 6: 运行问答测试和 food_ai 全量测试**

  Run: `cd backend && .venv/bin/pytest tests/plugin/food_ai -q`

  Expected: PASS。

- [ ] **Step 7: 提交后端问答边界**

  Run: `git add backend/app/plugin/food_ai/assistant.py backend/app/plugin/food_ai/schema.py backend/app/plugin/food_ai/controller.py backend/tests/plugin/food_ai/test_assistant.py && git commit -m "feat: add public service assistant endpoint"`

---

### Task 5: 新增独立智能问答页

**Files:**
- Create: `frontend/web/src/api/module_food_ai/assistant.ts`
- Create: `frontend/web/src/views/portal/assistant/index.vue`
- Create: `frontend/web/src/views/portal/assistant/components/AssistantSidebar.vue`
- Create: `frontend/web/src/views/portal/assistant/components/QuickQuestions.vue`
- Create: `frontend/web/src/views/portal/assistant/components/MessageList.vue`
- Create: `frontend/web/src/views/portal/assistant/components/QuestionComposer.vue`
- Modify: `frontend/web/src/router/routes.ts`
- Modify: `frontend/web/src/styles/portal.scss`
- Create: `frontend/web/src/__tests__/portal-assistant.spec.ts`
- Modify: `frontend/web/src/__tests__/portal-routes.spec.ts`

**Interfaces:**
- Consumes: `POST /food-ai/assistant/questions`；路由查询参数 `q`；`recommended_services[].route`。
- Produces: `/portal/assistant` 页面状态 `idle | submitting | answered | unavailable`；`AssistantAPI.ask(body)`。

- [ ] **Step 1: 写路由、预填和发送行为失败测试**

  ```ts
  it("prefills q without automatically calling the API", async () => {
    await router.push("/portal/assistant?q=%E5%A6%82%E4%BD%95%E8%A7%A3%E6%9E%90%E6%94%BF%E7%AD%96%E6%96%87%E4%BB%B6%EF%BC%9F");
    const wrapper = mount(PortalAssistant, { global: { plugins: [router] } });
    expect(wrapper.get("textarea").element.value).toBe("如何解析政策文件？");
    expect(askSpy).not.toHaveBeenCalled();
  });

  it("sends only after explicit submit and renders the disclaimer", async () => {
    const wrapper = mount(PortalAssistant, { global: { plugins: [router] } });
    await wrapper.get("textarea").setValue("出口合规需要哪些材料？");
    await wrapper.get("form").trigger("submit");
    await flushPromises();
    expect(askSpy).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain("AI 生成，仅供辅助参考");
  });
  ```

  `portal-routes.spec.ts` 的路由集合必须增加 `assistant`。

- [ ] **Step 2: 运行测试确认页面和路由不存在**

  Run: `cd frontend/web && pnpm vitest run src/__tests__/portal-assistant.spec.ts src/__tests__/portal-routes.spec.ts`

  Expected: FAIL。

- [ ] **Step 3: 实现 API 类型和调用**

  `assistant.ts` 导出 `AssistantQuestionRequest`、`AssistantServiceRecommendation`、`AssistantQuestionResult` 和：

  ```ts
  export const AssistantAPI = {
    async ask(body: AssistantQuestionRequest): Promise<AssistantQuestionResult> {
      const response = await request<ApiResponse<AssistantQuestionResult>>({
        url: "/food-ai/assistant/questions",
        method: "post",
        data: body,
        headers: { Authorization: NO_AUTH_FLAG },
        timeout: 30_000,
      });
      return response.data.data;
    },
  };
  ```

- [ ] **Step 4: 实现页面状态机和组件**

  `index.vue` 初始化时只读取 `route.query.q` 并预填。快捷问题只设置 `draft`。发送时 trim 并校验 1–2000 字，追加用户消息，切换 `submitting`，收到结果后追加助手消息并保存 `conversation_id`；503/网络失败切换 `unavailable`，保留草稿并提供“重新发送”。发送中禁用输入与按钮，避免重复请求。

  `MessageList` 用 `aria-live="polite"`，错误区域用 `role="alert"`。推荐服务只渲染 `/portal/` 开头的站内路由。欢迎态展示四个已确认快捷问题，底部固定显示“AI 生成，仅供辅助参考”。

- [ ] **Step 5: 实现问答页政务布局与响应式**

  桌面端为 240px 左侧辅助导航 + 主对话区；768px 以下改为顶部横向辅助标签；375px 输入区仍保持按钮 44px、无横向滚动。消息气泡仅使用 0–2px 圆角，用户消息使用浅蓝底，助手消息白底边框。

- [ ] **Step 6: 运行问答页、路由和类型检查**

  Run: `cd frontend/web && pnpm vitest run src/__tests__/portal-assistant.spec.ts src/__tests__/portal-routes.spec.ts && pnpm type-check`

  Expected: PASS。

- [ ] **Step 7: 提交独立问答页**

  Run: `git add frontend/web/src/api/module_food_ai/assistant.ts frontend/web/src/views/portal/assistant frontend/web/src/router/routes.ts frontend/web/src/styles/portal.scss frontend/web/src/__tests__/portal-assistant.spec.ts frontend/web/src/__tests__/portal-routes.spec.ts && git commit -m "feat: add public service assistant page"`

---

### Task 6: 让服务大厅响应首页筛选参数

**Files:**
- Modify: `frontend/web/src/views/portal/services/index.vue`
- Modify: `frontend/web/src/__tests__/service-hall.spec.ts`

**Interfaces:**
- Consumes: `route.query.category`、`route.query.status`、`route.query.focus`；`serviceCategories` 与 `publicServices`。
- Produces: 首页“我要查”“我要办”和服务专区可直接落到正确的服务大厅状态。

- [ ] **Step 1: 写 URL 参数同步失败测试**

  ```ts
  it("applies supported category and availability query parameters", async () => {
    await router.push("/portal/services?category=policy&status=available");
    const wrapper = mount(PortalServices, { global: { plugins: [router] } });
    expect(wrapper.text()).toContain("出口合规预检");
    expect(wrapper.text()).not.toContain("政策文件解读");
  });
  ```

  再增加非法 `category` 回落到 `all`、`focus=search` 时搜索框获得焦点的测试。

- [ ] **Step 2: 运行测试确认旧页面忽略 URL 参数**

  Run: `cd frontend/web && pnpm vitest run src/__tests__/service-hall.spec.ts`

  Expected: FAIL。

- [ ] **Step 3: 实现参数白名单和状态同步**

  使用 `serviceCategories.some()` 验证 category；status 只接受 `available`；watch 路由参数并同步筛选。筛选变化时使用 `router.replace()` 写回 URL，避免浏览器历史堆积。`focus=search` 在 `nextTick` 后聚焦搜索输入并删除一次性 focus 参数。

- [ ] **Step 4: 运行服务大厅测试**

  Run: `cd frontend/web && pnpm vitest run src/__tests__/service-hall.spec.ts`

  Expected: PASS。

- [ ] **Step 5: 提交筛选联动**

  Run: `git add frontend/web/src/views/portal/services/index.vue frontend/web/src/__tests__/service-hall.spec.ts && git commit -m "feat: link portal shortcuts to service filters"`

---

### Task 7: 清理旧助手、统一剩余公共页面并完成回归验收

**Files:**
- Delete: `frontend/web/src/views/portal/components/PortalAssistant.vue`
- Modify: `frontend/web/src/styles/portal.scss`
- Modify: `frontend/web/src/views/portal/documents/index.vue`
- Modify: `frontend/web/src/views/portal/precheck/index.vue`
- Modify: `frontend/web/src/views/portal/precheck/result.vue`
- Modify: `frontend/web/src/views/portal/diagnosis/index.vue`
- Modify: `frontend/web/src/views/portal/scenarios/index.vue`
- Modify: `frontend/web/src/views/portal/records/index.vue`
- Modify: `frontend/web/src/views/portal/guide/index.vue`
- Modify: `README.md`

**Interfaces:**
- Consumes: Task 1 的视觉 token 与 Task 5 的唯一问答入口。
- Produces: 全站一致的政务公共服务视觉；不再存在旧浮动助手和旧工具品牌文案；可复现的启动与配置说明。

- [ ] **Step 1: 写静态守卫测试**

  在现有 `smoke.spec.ts` 或新建 `portal-copy.spec.ts` 读取公共门户源文件，断言用户可见源码不包含 `MinerU`、`DEMO`、`演示原型`，并断言旧 `PortalAssistant.vue` 不再被引用。样例数据的“示例信息”不属于禁止项。

- [ ] **Step 2: 运行静态守卫并确认旧代码失败**

  Run: `cd frontend/web && pnpm vitest run src/__tests__/smoke.spec.ts`

  Expected: FAIL，旧组件或旧文案仍存在。

- [ ] **Step 3: 删除旧助手并统一公共页面样式**

  删除未使用的浮动助手组件及 `.portal-assistant*` 样式。把剩余公共页面的 8–14px 卡片圆角、胶囊按钮和重阴影替换为 0–2px 圆角、边框与栏目分隔线；不改变文档上传/解析/问答、预检、诊断和场景匹配业务逻辑。

- [ ] **Step 4: 更新 README**

  README 增加：前端 5180、平台 FastAPI 8001、文档解析服务 8002 的启动顺序；智能问答后端环境变量名称；API key 仅放 `backend/env/.env.dev` 且该文件不得提交；新闻通知是样例信息；文档解析上游在用户文案中统一称“公共服务平台智能体”。不得写入真实 key、模型价格或未核验能力。

- [ ] **Step 5: 运行前后端自动化验证**

  Run: `cd frontend/web && pnpm test && pnpm type-check && pnpm build`

  Expected: Vitest、Vue TypeScript 与 Vite build 全部成功。

  Run: `cd backend && .venv/bin/pytest tests/plugin/food_ai -q`

  Expected: PASS。

- [ ] **Step 6: 启动服务做四档视觉验收**

  分别启动 8002 文档解析服务、8001 FastAPI 和 5180 Vite；在 1440×900、1024×768、768×1024、375×812 检查 `/web/#/portal/home`、`/web/#/portal/assistant`、`/web/#/portal/services`。确认无横向滚动、搜索可键盘操作、问答失败有 503 提示、样例信息标签清晰、无旧浮动助手和无未经授权政府标识。

- [ ] **Step 7: 检查敏感信息与运行数据没有进入提交**

  Run: `git status --short && git diff --cached --check && git diff --check && ! git diff -- . ':!backend/data/documents/**' | rg -n "sk-[A-Za-z0-9_-]{16,}|API_KEY\s*=\s*[^\"']+"`

  Expected: `backend/data/documents/` 仍只显示为未跟踪运行数据；无密钥样式匹配；diff check 无错误。

- [ ] **Step 8: 提交收尾改造**

  Run: `git add frontend/web/src frontend/web/README.md README.md && git status --short`

  确认暂存区不含 `backend/data/documents/` 后运行：`git commit -m "feat: complete government public service portal redesign"`

