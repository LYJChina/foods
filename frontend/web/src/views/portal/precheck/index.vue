<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { Icon } from "@iconify/vue";
import { useRouter } from "vue-router";

import { FoodAIPortalAPI } from "@/api/module_food_ai/portal";
import type { MaterialKind, PrecheckCreate } from "@/types/food-ai";
import {
  createEmptyPrecheckDraft,
  type PrecheckFieldErrors,
  validatePrecheckStep,
} from "./validation";

const router = useRouter();
const step = ref<1 | 2 | 3>(1);
const draft = reactive(createEmptyPrecheckDraft());
const errors = ref<PrecheckFieldErrors>({});
const isSubmitting = ref(false);
const submitError = ref("");

const steps = ["产品信息", "低敏材料", "范围确认"];
const productCategories = [
  { value: "candy", label: "糖果" },
  { value: "snack", label: "休闲食品" },
  { value: "braised_food", label: "卤制品" },
  { value: "health_food", label: "保健食品" },
  { value: "other", label: "其他食品" },
];
const targetMarkets = [
  { value: "EU", label: "欧盟" },
  { value: "US", label: "美国" },
  { value: "SEA", label: "东南亚" },
  { value: "JP", label: "日本" },
  { value: "OTHER", label: "其他市场" },
];
const materialOptions: Array<{ value: MaterialKind; label: string; help: string }> = [
  { value: "label_image", label: "标签图片", help: "产品正背面标签或设计稿" },
  { value: "packaging_image", label: "包装图片", help: "不含客户与订单信息的包装资料" },
  { value: "product_spec", label: "产品规格说明", help: "不含配方比例和工艺参数" },
  { value: "public_document", label: "公开资料", help: "公开可查或获授权提交的文件" },
];

const progress = computed(() => step.value + " / 3");

function nextStep(): void {
  const stepErrors = validatePrecheckStep(step.value, draft);
  errors.value = stepErrors;
  if (Object.keys(stepErrors).length === 0 && step.value < 3) {
    step.value = (step.value + 1) as 2 | 3;
  }
}

function previousStep(): void {
  errors.value = {};
  if (step.value > 1) step.value = (step.value - 1) as 1 | 2;
}

async function submitPrecheck(): Promise<void> {
  const stepErrors = validatePrecheckStep(3, draft);
  errors.value = stepErrors;
  if (Object.keys(stepErrors).length > 0) return;

  const payload: PrecheckCreate = {
    product_name: draft.product_name.trim(),
    product_category: draft.product_category,
    target_market: draft.target_market,
    materials: [...draft.materials],
    contains_core_data: false,
    notes: draft.notes.trim() || undefined,
  };

  isSubmitting.value = true;
  submitError.value = "";
  try {
    const task = await FoodAIPortalAPI.createPrecheck(payload);
    await router.push("/portal/precheck/" + task.task_id);
  } catch {
    submitError.value = "提交失败，请检查后端服务后重试。";
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <main class="portal-page portal-container">
    <header class="portal-page__intro">
      <span class="portal-section__kicker">标志性服务 Demo</span>
      <h1>产品出口合规 AI 预检</h1>
      <p>选择产品类型和目标市场，提交低敏材料描述，获得结构化的演示风险提示。</p>
    </header>

    <div class="portal-precheck-layout">
      <section class="portal-form-card" aria-labelledby="precheck-form-title">
        <div class="portal-form-card__top">
          <div>
            <p class="portal-form-card__progress">步骤 {{ progress }}</p>
            <h2 id="precheck-form-title">{{ steps[step - 1] }}</h2>
          </div>
          <ol class="portal-stepper" aria-label="预检步骤">
            <li v-for="(label, index) in steps" :key="label" :class="{ 'is-active': index + 1 === step, 'is-done': index + 1 < step }">
              <span>{{ index + 1 }}</span><small>{{ label }}</small>
            </li>
          </ol>
        </div>

        <form @submit.prevent="submitPrecheck">
          <div v-if="step === 1" class="portal-form-grid">
            <div class="portal-field portal-field--wide">
              <label for="product-name">产品名称 <em>必填</em></label>
              <input id="product-name" v-model="draft.product_name" type="text" :aria-invalid="Boolean(errors.product_name)" aria-describedby="product-name-error" placeholder="例如：潮州糖果示例产品" />
              <p v-if="errors.product_name" id="product-name-error" class="portal-field__error">{{ errors.product_name }}</p>
            </div>
            <div class="portal-field">
              <label for="product-category">产品类别 <em>必填</em></label>
              <select id="product-category" v-model="draft.product_category" :aria-invalid="Boolean(errors.product_category)" aria-describedby="product-category-error">
                <option value="">请选择</option>
                <option v-for="option in productCategories" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
              <p v-if="errors.product_category" id="product-category-error" class="portal-field__error">{{ errors.product_category }}</p>
            </div>
            <div class="portal-field">
              <label for="target-market">目标市场 <em>必填</em></label>
              <select id="target-market" v-model="draft.target_market" :aria-invalid="Boolean(errors.target_market)" aria-describedby="target-market-error">
                <option value="">请选择</option>
                <option v-for="option in targetMarkets" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
              <p v-if="errors.target_market" id="target-market-error" class="portal-field__error">{{ errors.target_market }}</p>
            </div>
          </div>

          <div v-else-if="step === 2">
            <p class="portal-form-help">本 Demo 不上传文件，仅选择拟提交的材料类型。正式建设时应采用最小必要、按次处理和可配置不留存策略。</p>
            <fieldset class="portal-materials">
              <legend>选择低敏材料 <em>至少一项</em></legend>
              <label v-for="option in materialOptions" :key="option.value">
                <input v-model="draft.materials" type="checkbox" :value="option.value" />
                <span><strong>{{ option.label }}</strong><small>{{ option.help }}</small></span>
              </label>
            </fieldset>
            <p v-if="errors.materials" class="portal-field__error">{{ errors.materials }}</p>
            <div class="portal-field">
              <label for="precheck-notes">补充说明 <span>选填</span></label>
              <textarea id="precheck-notes" v-model="draft.notes" maxlength="500" rows="4" placeholder="请勿填写配方、工艺、成本、客户、订单或生产经营数据"></textarea>
            </div>
          </div>

          <div v-else class="portal-confirmation">
            <div class="portal-boundary-list">
              <h3>提交前请确认数据边界</h3>
              <ul>
                <li><Icon icon="ri:close-circle-line" aria-hidden="true" /> 不提交配方比例、工艺参数、成本、客户、订单和生产经营数据</li>
                <li><Icon icon="ri:check-line" aria-hidden="true" /> 仅提交标签、包装、规格说明或公开资料等低敏信息</li>
                <li><Icon icon="ri:information-line" aria-hidden="true" /> Demo 使用固定规则，不调用 OCR、实时法规库或真实大模型</li>
              </ul>
            </div>
            <label class="portal-confirm-check">
              <input id="confirm-low-sensitivity" v-model="draft.confirmed_low_sensitivity" type="checkbox" />
              <span>我确认提交内容不含企业核心数据</span>
            </label>
            <p v-if="errors.confirmed_low_sensitivity" class="portal-field__error">{{ errors.confirmed_low_sensitivity }}</p>
            <label class="portal-confirm-check">
              <input id="accept-disclaimer" v-model="draft.accepts_disclaimer" type="checkbox" />
              <span>我理解结果仅用于辅助预检，不替代专业认证、检验或法律判断</span>
            </label>
            <p v-if="errors.accepts_disclaimer" class="portal-field__error">{{ errors.accepts_disclaimer }}</p>
          </div>

          <p v-if="submitError" class="portal-submit-error" role="alert">{{ submitError }}</p>
          <div class="portal-form-actions">
            <button v-if="step > 1" type="button" class="portal-button portal-button--secondary" @click="previousStep">上一步</button>
            <button v-if="step < 3" type="button" class="portal-button portal-button--primary" data-testid="next-step" @click="nextStep">下一步</button>
            <button v-else type="submit" class="portal-button portal-button--primary" data-testid="submit-precheck" :disabled="isSubmitting">
              {{ isSubmitting ? "正在生成 Demo 结果…" : "提交并生成预检结果" }}
            </button>
          </div>
        </form>
      </section>

      <aside class="portal-side-note">
        <Icon icon="ri:shield-check-line" aria-hidden="true" />
        <h2>本轮会做什么</h2>
        <p>根据产品类别、目标市场和材料类型运行确定性的 Demo 规则，返回风险条目、缺失材料和下一步建议。</p>
        <h3>本轮不会做什么</h3>
        <p>不会上传或解析真实文件，不会查询政府后台接口，也不会调用真实法规库或大模型。</p>
      </aside>
    </div>
  </main>
</template>
