<script setup lang="ts">
import { ref } from "vue";
import { Icon } from "@iconify/vue";

import { assistantPrompts } from "../content";

const isOpen = ref(
  typeof window === "undefined" || typeof window.matchMedia !== "function"
    ? true
    : !window.matchMedia("(max-width: 1599px)").matches
);
const input = ref("");
const answer = ref("您可以从出口预检、场景体验或数智化诊断开始。");

function reply(question: string): void {
  const normalized = question.trim();
  if (!normalized) return;
  answer.value = `已记录问题“${normalized}”。Demo 阶段仅展示交互，请通过页面功能继续体验。`;
  input.value = "";
}
</script>

<template>
  <aside v-if="isOpen" class="portal-assistant" aria-label="食品行业 AI 助手">
    <header class="portal-assistant__header">
      <span class="portal-assistant__avatar" aria-hidden="true">
        <Icon icon="ri:robot-2-line" />
      </span>
      <span><strong>食品行业 AI 助手</strong><small>公共知识问答·Demo</small></span>
      <button type="button" aria-label="收起 AI 助手" @click="isOpen = false">
        <Icon icon="ri:subtract-line" aria-hidden="true" />
      </button>
    </header>
    <div class="portal-assistant__body">
      <div class="portal-assistant__answer" aria-live="polite">
        <p>{{ answer }}</p>
        <small>模拟回复·未连接实时大模型</small>
      </div>
      <div class="portal-assistant__prompts" aria-label="示例问题">
        <button v-for="prompt in assistantPrompts" :key="prompt" type="button" @click="reply(prompt)">
          {{ prompt }}
        </button>
      </div>
      <form class="portal-assistant__form" @submit.prevent="reply(input)">
        <label class="sr-only" for="portal-assistant-input">输入问题</label>
        <input id="portal-assistant-input" v-model="input" type="text" placeholder="输入您的问题…" />
        <button type="submit" aria-label="发送问题">
          <Icon icon="ri:send-plane-fill" aria-hidden="true" />
        </button>
      </form>
      <p class="portal-assistant__notice">输出仅用于功能演示，不替代专业认证、检验或法律判断。</p>
    </div>
  </aside>
  <button v-else class="portal-assistant-launcher" type="button" aria-label="展开 AI 助手" @click="isOpen = true">
    <Icon icon="ri:robot-2-line" aria-hidden="true" />
    <span>AI 助手</span>
  </button>
</template>
