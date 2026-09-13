<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { DashboardAPI, type DashboardSnapshot } from "@/api/module_food_ai/dashboard";

const snapshot = ref<DashboardSnapshot | null>(null);
const isLoading = ref(true);
const loadError = ref(false);

const statusLabels = {
  completed: "已完成",
  processing: "办理中",
  failed: "未完成",
} as const;

const formattedUpdatedAt = computed(() => {
  if (!snapshot.value) return "—";
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(snapshot.value.summary.updated_at)
  );
});

const formattedSubmittedAt = (value: string) =>
  new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));

onMounted(async () => {
  try {
    snapshot.value = await DashboardAPI.getSnapshot();
  } catch {
    loadError.value = true;
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <main class="portal-page">
    <div class="portal-container">
      <header class="portal-page__intro">
        <span class="portal-section__kicker">公共服务办理信息</span>
        <h1>办理记录</h1>
        <p>以下为平台样例数据，用于说明公共服务办理流程，不对应真实企业或个人事项。</p>
      </header>

      <p v-if="isLoading" class="portal-records-empty" role="status">正在加载示例办理记录…</p>
      <p v-else-if="loadError" class="portal-records-empty" role="alert">示例办理记录暂时无法加载，请稍后重试。</p>
      <template v-else-if="snapshot">
        <section class="portal-records-summary" aria-label="示例数据概览">
          <article><strong>{{ snapshot.summary.total_handled }}</strong><span>累计办理（示例数据）</span></article>
          <article><strong>{{ snapshot.summary.today_users }}</strong><span>今日服务用户（示例数据）</span></article>
          <article><strong>{{ formattedUpdatedAt }}</strong><span>数据更新时间（示例数据）</span></article>
        </section>

        <section class="portal-records-table-wrap" aria-label="示例办理记录">
          <table class="portal-records-table">
            <thead><tr><th scope="col">事项名称</th><th scope="col">服务类型</th><th scope="col">提交时间</th><th scope="col">状态</th><th scope="col">数据说明</th></tr></thead>
            <tbody>
              <tr v-for="record in snapshot.recent_cases" :key="record.id">
                <td class="portal-records-table__title">{{ record.title }}</td>
                <td>{{ record.service_name }}</td>
                <td class="portal-records-table__muted">{{ formattedSubmittedAt(record.submitted_at) }}</td>
                <td><span class="portal-records-status" :class="`portal-records-status--${record.status}`">{{ statusLabels[record.status] }}</span></td>
                <td><span class="portal-data-label">示例数据</span></td>
              </tr>
            </tbody>
          </table>
        </section>
      </template>
    </div>
  </main>
</template>
