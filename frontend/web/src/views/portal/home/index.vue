<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { Icon } from "@iconify/vue";
import { DashboardAPI, type DashboardSnapshot } from "@/api/module_food_ai/dashboard";
import { publicServices, quickAssistantCases } from "@/views/portal/services/catalog";

const snapshot = ref<DashboardSnapshot | null>(null),
  loading = ref(true),
  error = ref("");
const selectedCase = ref(quickAssistantCases[0]),
  query = ref(""),
  recommendation = ref("");
const range = ref<"7d" | "30d">("7d");
const selectedService = computed(() =>
  publicServices.find((item) => item.id === selectedCase.value?.serviceId)
);
const maxTrend = computed(() =>
  Math.max(...(snapshot.value?.trend.map((item) => item.handled) ?? [1]))
);
const maxDistribution = computed(() =>
  Math.max(...(snapshot.value?.distribution.map((item) => item.handled) ?? [1]))
);
const metrics = computed(() => {
  const summary = snapshot.value?.summary;
  return [
    { label: "累计办理事项", value: summary?.total_handled ?? 0, unit: "件", icon: "ri:task-line" },
    {
      label: "知识库收录文档",
      value: summary?.knowledge_documents ?? 0,
      unit: "份",
      icon: "ri:book-3-line",
    },
    { label: "今日服务人数", value: summary?.today_users ?? 0, unit: "人", icon: "ri:user-3-line" },
    {
      label: "当前开放智能服务",
      value: summary?.active_agents ?? 0,
      unit: "个",
      icon: "ri:apps-2-line",
    },
  ];
});
async function load() {
  loading.value = true;
  error.value = "";
  try {
    snapshot.value = await DashboardAPI.getSnapshot();
  } catch {
    error.value = "运行概况暂时无法加载，请稍后重试。";
  } finally {
    loading.value = false;
  }
}
function selectCase(item: (typeof quickAssistantCases)[number]) {
  selectedCase.value = item;
  query.value = item.prompt;
  recommendation.value = "";
}
function recommend() {
  const text = query.value.trim().toLowerCase();
  const match = quickAssistantCases.find((item) =>
    item.keywords.some((word) => text.includes(word.toLowerCase()))
  );
  recommendation.value = match
    ? `为你推荐：${publicServices.find((service) => service.id === match.serviceId)?.name ?? "智能服务"}`
    : "暂未找到对应服务，请前往智能服务大厅选择。";
  if (match) selectedCase.value = match;
}
onMounted(load);
</script>

<template>
  <main class="portal-page portal-dashboard-home portal-container">
    <header class="dashboard-heading">
      <div>
        <h1>运行概况</h1>
      </div>
      <div class="dashboard-heading__meta">
        <span class="sample-badge">示例数据</span
        ><small>数据更新时间：{{ snapshot?.summary.updated_at ?? "—" }}</small
        ><span class="service-health"><i></i>服务运行正常</span>
      </div>
    </header>
    <div v-if="error" class="dashboard-inline-error" role="alert">
      <Icon icon="ri:error-warning-line" />{{ error
      }}<button type="button" @click="load">重试</button>
    </div>
    <section v-if="!loading" class="dashboard-metrics" aria-label="运行指标">
      <article v-for="metric in metrics" :key="metric.label" class="dashboard-metric">
        <span class="dashboard-metric__icon"><Icon :icon="metric.icon" /></span>
        <div>
          <small>{{ metric.label }}</small
          ><strong
            >{{ metric.value.toLocaleString("zh-CN") }}<em>{{ metric.unit }}</em></strong
          >
        </div>
      </article>
    </section>
    <div v-else class="dashboard-loading">正在加载运行概况…</div>
    <section v-if="snapshot" class="dashboard-main-grid">
      <div class="dashboard-visuals">
        <article class="dashboard-panel dashboard-trend">
          <header>
            <div>
              <span>服务趋势</span>
              <h2>近 7 日办理情况</h2>
            </div>
            <div class="dashboard-range">
              <button :class="{ active: range === '7d' }" type="button" @click="range = '7d'">
                近 7 日</button
              ><button :class="{ active: range === '30d' }" type="button" @click="range = '30d'">
                近 30 日
              </button>
            </div>
          </header>
          <div class="trend-chart" role="img" aria-label="近七日服务办理趋势">
            <div v-for="point in snapshot.trend" :key="point.date" class="trend-column">
              <strong>{{ point.handled }}</strong
              ><i :style="{ height: `${Math.max(8, (point.handled / maxTrend) * 100)}%` }"></i
              ><small>{{ point.date.slice(5) }}</small>
            </div>
          </div>
          <p class="chart-note">数据为首页展示样例，正式接入后将由统计接口提供。</p>
        </article>
        <article class="dashboard-panel">
          <header>
            <div>
              <span>服务分布</span>
              <h2>各智能服务办理量</h2>
            </div>
            <span class="panel-unit">办理量</span>
          </header>
          <ul class="distribution-list">
            <li v-for="item in snapshot.distribution" :key="item.service_id">
              <div>
                <span>{{ item.service_name }}</span
                ><strong>{{ item.handled }}</strong>
              </div>
              <span class="distribution-track"
                ><i :style="{ width: `${(item.handled / maxDistribution) * 100}%` }"></i
              ></span>
            </li>
          </ul>
        </article>
      </div>
      <aside class="dashboard-assistant dashboard-panel">
        <header>
          <div class="assistant-title">
            <span><Icon icon="ri:customer-service-2-line" /></span>
            <div>
              <span>公共服务助手</span>
              <h2>从这里开始办理</h2>
            </div>
          </div>
          <small>服务导航</small>
        </header>
        <p class="assistant-welcome">你好，我可以根据你的需求推荐合适的公共服务。</p>
        <div class="assistant-cases">
          <button
            v-for="item in quickAssistantCases"
            :key="item.id"
            type="button"
            :class="{ active: selectedCase?.id === item.id }"
            @click="selectCase(item)"
          >
            {{ item.prompt }}
          </button>
        </div>
        <label for="assistant-query">描述你的需求</label>
        <div class="assistant-input">
          <input
            id="assistant-query"
            v-model="query"
            placeholder="例如：我想解析一份政策文件"
            @keyup.enter="recommend"
          /><button type="button" aria-label="查找服务" @click="recommend">
            <Icon icon="ri:arrow-right-line" />
          </button>
        </div>
        <p v-if="recommendation" class="assistant-recommendation">
          <Icon icon="ri:lightbulb-line" />{{ recommendation }}
        </p>
        <div v-if="selectedService" class="assistant-result">
          <small>推荐服务</small><strong>{{ selectedService.name }}</strong
          ><span>{{ selectedService.description }}</span
          ><RouterLink
            v-if="selectedService.route"
            class="portal-button portal-button--primary"
            :to="selectedService.route"
            >立即办理 <Icon icon="ri:arrow-right-line"
          /></RouterLink>
        </div>
      </aside>
    </section>
    <section v-if="snapshot" class="dashboard-recent dashboard-panel">
      <header>
        <div>
          <span>办理动态</span>
          <h2>最近办理事项</h2>
        </div>
        <span class="sample-badge">示例数据</span>
      </header>
      <div class="recent-table" role="table" aria-label="最近办理事项">
        <div class="recent-row recent-row--head" role="row">
          <span>事项名称</span><span>使用服务</span><span>提交时间</span><span>状态</span>
        </div>
        <div v-for="item in snapshot.recent_cases" :key="item.id" class="recent-row" role="row">
          <strong>{{ item.title }}</strong
          ><span>{{ item.service_name }}</span
          ><span>{{ item.submitted_at.replace("T", " ").slice(0, 16) }}</span
          ><span class="case-status" :class="`is-${item.status}`">{{
            item.status === "completed"
              ? "已完成"
              : item.status === "processing"
                ? "处理中"
                : "处理失败"
          }}</span>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped lang="scss">
.portal-dashboard-home {
  padding-top: 26px;
  padding-bottom: 56px;
}
.dashboard-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
  padding-bottom: 14px;
  border-bottom: 2px solid var(--portal-navy);
}
.dashboard-heading h1 {
  margin: 0;
  font-size: 32px;
  color: var(--portal-navy);
}
.dashboard-heading p {
  margin: 0;
  color: var(--portal-muted);
}
.dashboard-heading__meta {
  display: grid;
  justify-items: end;
  gap: 6px;
  color: #64748b;
  font-size: 13px;
}
.sample-badge {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 2px 9px;
  color: #52667b;
  border: 1px solid #b9c7d5;
  background: #f3f6f9;
  font-size: 12px;
  font-weight: 700;
}
.service-health {
  display: flex;
  align-items: center;
  gap: 6px;
}
.service-health i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #1b9b78;
}
.dashboard-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin: 16px 0;
}
.dashboard-metric {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  border: 1px solid var(--portal-border);
  border-top: 3px solid var(--portal-blue);
  background: #fff;
}
.dashboard-metric__icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  color: var(--portal-blue);
  background: #edf5fb;
}
.dashboard-metric__icon svg {
  width: 20px;
}
.dashboard-metric small,
.dashboard-metric strong {
  display: block;
}
.dashboard-metric small {
  color: var(--portal-muted);
  font-size: 13px;
}
.dashboard-metric strong {
  color: var(--portal-navy);
  font-size: 26px;
  line-height: 1.25;
}
.dashboard-metric em {
  margin-left: 3px;
  color: var(--portal-muted);
  font-size: 13px;
  font-style: normal;
  font-weight: 500;
}
.dashboard-main-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 14px;
}
.dashboard-visuals {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 14px;
}
.dashboard-panel {
  border: 1px solid var(--portal-border);
  background: #fff;
}
.dashboard-panel header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 18px;
  border-bottom: 1px solid var(--portal-border);
}
.dashboard-panel header span {
  color: var(--portal-blue);
  font-size: 12px;
  font-weight: 750;
}
.dashboard-panel h2 {
  margin: 2px 0 0;
  color: var(--portal-navy);
  font-size: 18px;
}
.dashboard-range {
  display: flex;
  gap: 0;
}
.dashboard-range button {
  min-height: 30px;
  padding: 3px 9px;
  cursor: pointer;
  color: #64748b;
  border: 1px solid #c7d3df;
  background: #fff;
  font-size: 12px;
}
.dashboard-range button + button {
  border-left: 0;
}
.dashboard-range button.active {
  color: #fff;
  border-color: var(--portal-blue);
  background: var(--portal-blue);
}
.trend-chart {
  height: 236px;
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 22px 18px 0;
  border-bottom: 1px solid #e6ecf2;
}
.trend-column {
  height: 100%;
  display: grid;
  flex: 1;
  grid-template-rows: 18px 1fr 22px;
  justify-items: center;
  align-items: end;
  color: #64748b;
  font-size: 11px;
}
.trend-column strong {
  color: var(--portal-blue);
  font-size: 11px;
}
.trend-column i {
  width: min(26px, 60%);
  display: block;
  background: var(--portal-blue);
}
.trend-column:nth-child(2n) i {
  background: #3a91b2;
}
.trend-column small {
  align-self: end;
}
.chart-note {
  padding: 0 18px 13px;
  margin: 0;
  color: #8291a2;
  font-size: 11px;
}
.panel-unit {
  padding-top: 4px;
  color: #64748b !important;
  font-weight: 500 !important;
}
.distribution-list {
  display: grid;
  gap: 17px;
  margin: 0;
  padding: 21px 18px;
  list-style: none;
}
.distribution-list li > div {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
  color: #334155;
  font-size: 13px;
}
.distribution-list strong {
  color: var(--portal-navy);
}
.distribution-track {
  height: 10px;
  display: block;
  overflow: hidden;
  background: #e8eef4;
}
.distribution-track i {
  height: 100%;
  display: block;
  background: var(--portal-green);
}
.dashboard-assistant {
  min-height: 100%;
  background: #fbfdff;
}
.dashboard-assistant header {
  align-items: center;
}
.assistant-title {
  display: flex;
  align-items: center;
  gap: 9px;
}
.assistant-title > span {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  color: #fff;
  background: var(--portal-navy);
}
.assistant-title svg {
  width: 18px;
}
.assistant-title h2 {
  font-size: 17px;
}
.dashboard-assistant header > small {
  padding-top: 4px;
  color: #64748b;
}
.assistant-welcome {
  padding: 15px 18px;
  margin: 0;
  color: #475569;
  line-height: 1.55;
  background: #f1f6fa;
  font-size: 13px;
}
.assistant-cases {
  display: grid;
  gap: 7px;
  padding: 14px 18px 12px;
}
.assistant-cases button {
  padding: 8px 10px;
  cursor: pointer;
  text-align: left;
  color: #334155;
  border: 1px solid #d2dce6;
  background: #fff;
  font-size: 13px;
  line-height: 1.45;
}
.assistant-cases button:hover,
.assistant-cases button.active {
  color: var(--portal-blue);
  border-color: var(--portal-blue);
  background: #f3f9fd;
}
.dashboard-assistant label {
  display: block;
  padding: 0 18px 6px;
  color: #334155;
  font-size: 13px;
  font-weight: 700;
}
.assistant-input {
  display: grid;
  grid-template-columns: 1fr 38px;
  gap: 6px;
  padding: 0 18px;
}
.assistant-input input {
  width: 100%;
  min-height: 38px;
  padding: 7px 9px;
  border: 1px solid #afc0d1;
  font: inherit;
  font-size: 13px;
}
.assistant-input button {
  width: 38px;
  min-height: 38px;
  cursor: pointer;
  color: #fff;
  border: 0;
  background: var(--portal-blue);
}
.assistant-recommendation {
  display: flex;
  gap: 5px;
  padding: 8px 18px 0;
  margin: 0;
  color: #805b00;
  font-size: 12px;
}
.assistant-result {
  display: grid;
  gap: 5px;
  padding: 14px 18px 18px;
  margin-top: 14px;
  border-top: 1px solid var(--portal-border);
}
.assistant-result small {
  color: var(--portal-blue);
}
.assistant-result strong {
  color: var(--portal-navy);
}
.assistant-result span {
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}
.assistant-result .portal-button {
  min-height: 38px;
  margin-top: 4px;
  padding: 6px 12px;
  font-size: 13px;
}
.dashboard-recent {
  margin-top: 14px;
}
.dashboard-recent header {
  align-items: center;
}
.recent-table {
  width: 100%;
  overflow-x: auto;
}
.recent-row {
  min-width: 680px;
  display: grid;
  grid-template-columns: 2fr 1.15fr 1.1fr 80px;
  gap: 12px;
  align-items: center;
  padding: 12px 18px;
  border-bottom: 1px solid #e8edf2;
  color: #475569;
  font-size: 13px;
}
.recent-row:last-child {
  border-bottom: 0;
}
.recent-row--head {
  color: #64748b;
  background: #f7f9fb;
  font-size: 12px;
}
.recent-row strong {
  color: #24364b;
  font-weight: 650;
}
.case-status {
  font-weight: 700;
}
.case-status.is-completed {
  color: var(--portal-green);
}
.case-status.is-processing {
  color: var(--portal-amber);
}
.case-status.is-failed {
  color: var(--portal-red);
}
.dashboard-inline-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  margin: 16px 0;
  color: #8f171e;
  border: 1px solid #efc4c7;
  background: #fff5f5;
}
.dashboard-inline-error button {
  margin-left: auto;
  min-height: 34px;
  padding: 3px 11px;
  cursor: pointer;
  color: #8f171e;
  border: 1px solid #d99ca0;
  background: #fff;
}
.dashboard-loading {
  padding: 32px;
  text-align: center;
  color: #64748b;
  border: 1px solid var(--portal-border);
  background: #fff;
}
@media (max-width: 1100px) {
  .dashboard-main-grid {
    grid-template-columns: 1fr;
  }
  .dashboard-assistant {
    min-height: 0;
  }
  .dashboard-visuals {
    grid-template-columns: 1.2fr 1fr;
  }
}
@media (max-width: 768px) {
  .dashboard-heading {
    align-items: flex-start;
    flex-direction: column;
  }
  .dashboard-heading__meta {
    justify-items: start;
  }
  .dashboard-metrics {
    grid-template-columns: repeat(2, 1fr);
  }
  .dashboard-visuals {
    grid-template-columns: 1fr;
  }
  .dashboard-main-grid {
    gap: 12px;
  }
}
@media (max-width: 560px) {
  .portal-dashboard-home {
    padding-top: 22px;
  }
  .dashboard-heading h1 {
    font-size: 28px;
  }
  .dashboard-metrics {
    gap: 8px;
  }
  .dashboard-metric {
    align-items: flex-start;
    flex-direction: column;
    padding: 12px;
  }
  .dashboard-metric strong {
    font-size: 22px;
  }
  .dashboard-metric__icon {
    width: 34px;
    height: 34px;
  }
  .dashboard-panel header {
    padding: 14px;
  }
  .trend-chart {
    height: 210px;
    padding-inline: 10px;
    gap: 4px;
  }
  .trend-column i {
    width: 18px;
  }
  .dashboard-range button {
    padding-inline: 6px;
  }
  .recent-row {
    padding-inline: 14px;
  }
}
</style>
