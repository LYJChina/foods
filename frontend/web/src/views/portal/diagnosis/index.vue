<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { Icon } from "@iconify/vue";

import { FoodAIPortalAPI } from "@/api/module_food_ai/portal";
import type {
  DiagnosisAnswers,
  DiagnosisRecommendationKey,
  DiagnosisResult,
} from "@/types/food-ai";
import { scoreDiagnosis } from "./scoring";

const questions: Array<{
  key: keyof DiagnosisAnswers;
  title: string;
  help: string;
}> = [
  { key: "digital_foundation", title: "数字化基础", help: "ERP、WMS、MES、QMS 等系统和设备联网基础" },
  { key: "data_readiness", title: "数据可用程度", help: "数据质量、口径、权限与可连接程度" },
  { key: "ai_experience", title: "AI 应用经验", help: "通用工具、知识库、Agent 或场景验证经验" },
  { key: "governance_readiness", title: "AI 安全治理准备", help: "数据分级、权限继承、调用审计与模型边界" },
  { key: "export_need", title: "出口合规需求", help: "海外法规、标签、认证验厂与客户文件需求" },
];
const options = [
  { value: 0, label: "尚未开展" },
  { value: 1, label: "已有基础" },
  { value: 2, label: "较为成熟" },
];
const recommendationMeta: Record<DiagnosisRecommendationKey, { title: string; icon: string }> = {
  public_platform: { title: "公共平台直接解决", icon: "ri:government-line" },
  light_poc: { title: "开展轻量 POC", icon: "ri:test-tube-line" },
  enterprise_project: { title: "企业专项建设", icon: "ri:building-2-line" },
};
const maturityLabels = {
  start: "起步探索",
  prepare: "准备验证",
  advance: "深化应用",
};

const answers = reactive<DiagnosisAnswers>({
  digital_foundation: 0,
  data_readiness: 0,
  ai_experience: 0,
  governance_readiness: 0,
  export_need: 0,
});
const result = ref<DiagnosisResult | null>(null);
const isSubmitting = ref(false);
const usedLocalFallback = ref(false);
const scorePercent = computed(() => ((result.value?.score ?? 0) / 10) * 100);

async function submitDiagnosis(): Promise<void> {
  isSubmitting.value = true;
  usedLocalFallback.value = false;
  try {
    result.value = await FoodAIPortalAPI.createDiagnosis({ ...answers });
  } catch {
    result.value = scoreDiagnosis(answers);
    usedLocalFallback.value = true;
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <main class="portal-page portal-container">
    <header class="portal-page__intro">
      <span class="portal-section__kicker">下一步路径判断</span>
      <h1>企业数智化轻量诊断</h1>
      <p>用 5 个基础问题形成辅助建议，并将需求分为公共平台、轻量 POC 和企业专项建设三类。</p>
    </header>

    <div class="portal-diagnosis-layout">
      <form class="portal-diagnosis-form" @submit.prevent="submitDiagnosis">
        <fieldset v-for="(question, index) in questions" :key="question.key" class="portal-question">
          <legend><span>{{ index + 1 }}</span>{{ question.title }}</legend>
          <p>{{ question.help }}</p>
          <div class="portal-scale">
            <label v-for="option in options" :key="option.value">
              <input v-model.number="answers[question.key]" type="radio" :name="question.key" :value="option.value" />
              <span>{{ option.label }}</span>
            </label>
          </div>
        </fieldset>
        <button type="submit" class="portal-button portal-button--primary portal-diagnosis-submit" :disabled="isSubmitting">
          {{ isSubmitting ? "正在生成诊断…" : "生成诊断建议" }}
        </button>
      </form>

      <aside class="portal-diagnosis-note">
        <Icon icon="ri:information-line" aria-hidden="true" />
        <h2>诊断范围</h2>
        <p>仅使用当前选择的 0—2 分答案，不采集企业名称、经营指标、客户、订单、配方或生产数据。</p>
        <p>评分用于辅助判断需求分流，不构成项目评估或采购依据。</p>
      </aside>
    </div>

    <section v-if="result" class="portal-diagnosis-result" aria-live="polite">
      <div class="portal-diagnosis-result__heading">
        <div><span class="portal-data-label">简化辅助规则</span><h2>{{ maturityLabels[result.maturity] }}</h2></div>
        <div class="portal-score"><strong>{{ result.score }}</strong><span>/ 10 分</span></div>
      </div>
      <div class="portal-score-track" aria-hidden="true"><i :style="{ width: scorePercent + '%' }"></i></div>
      <p v-if="usedLocalFallback" class="portal-local-fallback">后端暂不可用，当前显示浏览器本地确定性辅助规则结果。</p>
      <div class="portal-recommendations">
        <article v-for="(items, key) in result.recommendations" :key="key">
          <Icon :icon="recommendationMeta[key].icon" aria-hidden="true" />
          <h3>{{ recommendationMeta[key].title }}</h3>
          <ul><li v-for="item in items" :key="item">{{ item }}</li></ul>
        </article>
      </div>
      <p class="portal-result__disclaimer"><strong>边界声明：</strong>{{ result.disclaimer }}</p>
    </section>
  </main>
</template>
