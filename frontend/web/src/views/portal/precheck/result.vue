<script setup lang="ts">
import { onMounted, ref } from "vue";
import { Icon } from "@iconify/vue";
import { useRoute } from "vue-router";

import { FoodAIPortalAPI } from "@/api/module_food_ai/portal";
import type { PrecheckTask } from "@/types/food-ai";

const route = useRoute();
const task = ref<PrecheckTask | null>(null);
const loading = ref(true);
const error = ref("");

async function loadResult(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    task.value = await FoodAIPortalAPI.getPrecheck(String(route.params.taskId));
  } catch {
    error.value = "结果加载失败。Demo 任务保存在后端进程内，服务重启后需重新提交。";
  } finally {
    loading.value = false;
  }
}

onMounted(loadResult);
</script>

<template>
  <main class="portal-page portal-container">
    <header class="portal-page__intro">
      <span class="portal-section__kicker">结构化 Demo 输出</span>
      <h1>出口合规预检结果</h1>
      <p>结果仅用于辅助预检和流程演示，不构成认证、检验或法律意见。</p>
    </header>

    <section v-if="loading" class="portal-state-card" aria-live="polite">
      <Icon icon="svg-spinners:ring-resize" aria-hidden="true" />
      <h2>正在加载预检结果</h2>
    </section>
    <section v-else-if="error" class="portal-state-card portal-state-card--error" role="alert">
      <Icon icon="ri:error-warning-line" aria-hidden="true" />
      <h2>暂时无法获取结果</h2>
      <p>{{ error }}</p>
      <button type="button" class="portal-button portal-button--primary" @click="loadResult">重试</button>
    </section>
    <div v-else-if="task" class="portal-result">
      <section class="portal-result__summary">
        <div>
          <span class="portal-data-label">DEMO 规则结果</span>
          <h2>{{ task.result.overall === "needs_review" ? "建议进一步人工复核" : "材料不足，建议补充后复核" }}</h2>
        </div>
        <dl>
          <div><dt>任务编号</dt><dd>{{ task.task_id }}</dd></div>
          <div><dt>目标市场</dt><dd>{{ task.request.target_market }}</dd></div>
          <div><dt>产品类别</dt><dd>{{ task.request.product_category }}</dd></div>
        </dl>
      </section>

      <section class="portal-result__section">
        <h2>风险与关注事项</h2>
        <article v-for="risk in task.result.risks" :key="risk.code" class="portal-risk-card">
          <span :class="'is-' + risk.level">{{ risk.level === "attention" ? "需关注" : "信息提示" }}</span>
          <div>
            <h3>{{ risk.title }}</h3>
            <p>{{ risk.summary }}</p>
            <p><strong>下一步：</strong>{{ risk.next_step }}</p>
          </div>
        </article>
      </section>

      <section v-if="task.result.missing_materials.length" class="portal-result__section">
        <h2>缺失材料</h2>
        <ul><li v-for="item in task.result.missing_materials" :key="item">{{ item }}</li></ul>
      </section>

      <div class="portal-result__columns">
        <section class="portal-result__section">
          <h2>演示来源</h2>
          <ul><li v-for="item in task.result.source_labels" :key="item">{{ item }}</li></ul>
        </section>
        <section class="portal-result__section">
          <h2>建议下一步</h2>
          <ol><li v-for="item in task.result.next_steps" :key="item">{{ item }}</li></ol>
        </section>
      </div>
      <p class="portal-result__disclaimer"><strong>边界声明：</strong>{{ task.result.disclaimer }}</p>
      <RouterLink class="portal-button portal-button--secondary" to="/portal/precheck">重新预检</RouterLink>
    </div>
  </main>
</template>
