<script setup lang="ts">
import type { AssistantServiceRecommendation } from "@/api/module_food_ai/assistant";

export interface AssistantMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  recommendations?: AssistantServiceRecommendation[];
}

defineProps<{ messages: AssistantMessage[]; submitting: boolean }>();
</script>

<template>
  <div class="public-assistant-messages" aria-live="polite">
    <article v-for="message in messages" :key="message.id" :class="`is-${message.role}`">
      <strong>{{ message.role === "assistant" ? "公共服务助手" : "您" }}</strong>
      <p>{{ message.content }}</p>
      <div v-if="message.recommendations?.length" class="public-assistant-recommendations">
        <span>推荐服务</span>
        <RouterLink
          v-for="service in message.recommendations.filter((item) => item.route.startsWith('/portal/'))"
          :key="service.route"
          :to="service.route"
        >
          {{ service.name }}
        </RouterLink>
      </div>
    </article>
    <article v-if="submitting" class="is-assistant is-loading">
      <strong>公共服务助手</strong><p>正在整理答复，请稍候…</p>
    </article>
  </div>
</template>
