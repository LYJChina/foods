<script setup lang="ts">
import { computed, ref } from "vue";
import { Icon } from "@iconify/vue";
import { useRoute } from "vue-router";

import { AssistantAPI } from "@/api/module_food_ai/assistant";
import AssistantSidebar from "./components/AssistantSidebar.vue";
import MessageList, { type AssistantMessage } from "./components/MessageList.vue";
import QuestionComposer from "./components/QuestionComposer.vue";
import QuickQuestions from "./components/QuickQuestions.vue";

type AssistantState = "idle" | "submitting" | "answered" | "unavailable";

const route = useRoute();
const incomingQuestion = Array.isArray(route.query.q) ? route.query.q[0] : route.query.q;
const draft = ref((incomingQuestion ?? "").slice(0, 2000));
const state = ref<AssistantState>("idle");
const conversationId = ref<string>();
const messages = ref<AssistantMessage[]>([]);
const errorMessage = ref("");
const quickQuestions = [
  "如何解析政策文件？",
  "出口合规需要哪些材料？",
  "如何开展企业数智化诊断？",
  "怎样选择合适的 AI 场景？",
];
const isSubmitting = computed(() => state.value === "submitting");

function fillQuestion(question: string) {
  draft.value = question;
  errorMessage.value = "";
  state.value = messages.value.length ? "answered" : "idle";
}

async function submitQuestion() {
  const question = draft.value.trim();
  if (!question || question.length > 2000 || isSubmitting.value) return;

  errorMessage.value = "";
  state.value = "submitting";
  messages.value.push({ id: `user-${Date.now()}`, role: "user", content: question });
  try {
    const result = await AssistantAPI.ask({
      question,
      conversation_id: conversationId.value,
    });
    conversationId.value = result.conversation_id;
    messages.value.push({
      id: `assistant-${Date.now()}`,
      role: "assistant",
      content: result.answer,
      recommendations: result.recommended_services,
    });
    state.value = "answered";
  } catch {
    messages.value.pop();
    errorMessage.value = "问答模型服务暂不可用，您的问题已保留，请稍后重新发送。";
    state.value = "unavailable";
  }
}
</script>

<template>
  <main class="portal-page public-assistant-page">
    <div class="portal-container">
      <nav class="public-assistant-breadcrumb" aria-label="面包屑">
        <RouterLink to="/portal/home">首页</RouterLink><span>/</span><span>公共服务智能问答</span>
      </nav>
      <header class="public-assistant-title">
        <span aria-hidden="true"><Icon icon="ri:chat-smile-3-line" /></span>
        <div><h1>公共服务智能问答</h1><p>围绕平台服务、办事入口和公开材料提供辅助咨询。</p></div>
      </header>

      <div class="public-assistant-layout">
        <AssistantSidebar />
        <section id="assistant-conversation" class="public-assistant-conversation">
          <div v-if="messages.length === 0" class="public-assistant-welcome">
            <Icon icon="ri:customer-service-2-line" aria-hidden="true" />
            <h2>您好，我是公共服务助手</h2>
            <p>请选择常见问题，或在下方输入您想咨询、查询或办理的事项。</p>
            <QuickQuestions :questions="quickQuestions" @select="fillQuestion" />
          </div>
          <MessageList v-else :messages="messages" :submitting="isSubmitting" />
          <div v-if="errorMessage" class="public-assistant-error" role="alert">
            <Icon icon="ri:error-warning-line" aria-hidden="true" />{{ errorMessage }}
          </div>
          <QuestionComposer
            v-model="draft"
            :submitting="isSubmitting"
            :retry="state === 'unavailable'"
            @submit="submitQuestion"
          />
          <p class="public-assistant-disclaimer">AI 生成，仅供辅助参考</p>
        </section>
      </div>
    </div>
  </main>
</template>

<style scoped lang="scss">
.public-assistant-page { padding-top: 24px; }
.public-assistant-breadcrumb { display: flex; gap: 8px; margin-bottom: 14px; color: var(--portal-muted); font-size: 13px; }
.public-assistant-breadcrumb a { color: var(--portal-blue); }
.public-assistant-title { min-height: 90px; display: flex; align-items: center; gap: 18px; padding: 18px 22px; color: #fff; background: var(--portal-navy); }
.public-assistant-title > span { width: 48px; height: 48px; display: grid; place-items: center; border: 1px solid rgba(255, 255, 255, .55); }
.public-assistant-title svg { width: 28px; height: 28px; }
.public-assistant-title h1 { margin: 0; font-size: 26px; }
.public-assistant-title p { margin: 2px 0 0; color: #dbe9f5; font-size: 14px; }
.public-assistant-layout { display: grid; grid-template-columns: 240px minmax(0, 1fr); gap: 18px; margin-top: 18px; }
:deep(.public-assistant-sidebar), .public-assistant-conversation { border: 1px solid var(--portal-border); background: #fff; }
:deep(.public-assistant-sidebar) { align-self: start; }
:deep(.public-assistant-sidebar h2) { margin: 0; padding: 15px 18px; color: var(--portal-navy-deep); border-bottom: 1px solid var(--portal-border); font-size: 17px; }
:deep(.public-assistant-sidebar nav) { display: grid; }
:deep(.public-assistant-sidebar nav a) { min-height: 48px; display: flex; align-items: center; gap: 10px; padding: 10px 18px; border-bottom: 1px solid #e6ebf0; }
:deep(.public-assistant-sidebar nav a:first-child) { color: var(--portal-blue); border-left: 3px solid var(--portal-red); background: #f1f6fb; }
:deep(.public-assistant-sidebar__tip) { padding: 16px 18px; color: var(--portal-muted); font-size: 12px; }
:deep(.public-assistant-sidebar__tip strong) { color: var(--portal-text); }
:deep(.public-assistant-sidebar__tip p) { margin: 5px 0 0; }
.public-assistant-conversation { min-height: 560px; display: flex; flex-direction: column; padding: 24px; }
.public-assistant-welcome { display: grid; justify-items: center; padding: 44px 20px 34px; text-align: center; }
.public-assistant-welcome > svg { width: 52px; height: 52px; color: var(--portal-blue); }
.public-assistant-welcome h2 { margin: 12px 0 5px; color: var(--portal-navy-deep); font-size: 23px; }
.public-assistant-welcome p { margin: 0; color: var(--portal-muted); }
:deep(.public-assistant-quick) { width: min(720px, 100%); display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 26px; }
:deep(.public-assistant-quick button) { min-height: 48px; padding: 9px 14px; cursor: pointer; color: var(--portal-navy); text-align: left; border: 1px solid #c8d6e4; background: #f8fafc; }
:deep(.public-assistant-quick button:hover) { border-color: var(--portal-blue); background: #eef5fb; }
:deep(.public-assistant-messages) { display: grid; gap: 14px; margin-bottom: 22px; }
:deep(.public-assistant-messages article) { max-width: 82%; padding: 13px 15px; border: 1px solid var(--portal-border); background: #fff; }
:deep(.public-assistant-messages article.is-user) { margin-left: auto; border-color: #b8d0e5; background: #edf5fb; }
:deep(.public-assistant-messages strong) { color: var(--portal-navy); font-size: 13px; }
:deep(.public-assistant-messages p) { margin: 4px 0 0; white-space: pre-wrap; }
:deep(.public-assistant-recommendations) { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; padding-top: 10px; margin-top: 10px; border-top: 1px solid var(--portal-border); }
:deep(.public-assistant-recommendations span) { color: var(--portal-muted); font-size: 12px; }
:deep(.public-assistant-recommendations a) { padding: 5px 9px; color: var(--portal-blue); border: 1px solid #bcd0e1; font-size: 13px; }
.public-assistant-error { display: flex; align-items: center; gap: 8px; padding: 10px 12px; margin-top: auto; color: #9b1c24; border: 1px solid #e7b9bd; background: #fff5f5; }
:deep(.public-assistant-composer) { margin-top: auto; padding-top: 18px; border-top: 1px solid var(--portal-border); }
:deep(.public-assistant-composer label) { display: block; margin-bottom: 7px; color: var(--portal-text); font-weight: 700; }
:deep(.public-assistant-composer > div) { display: grid; grid-template-columns: minmax(0, 1fr) 126px; gap: 10px; }
:deep(.public-assistant-composer textarea) { width: 100%; min-height: 80px; resize: vertical; padding: 10px 12px; color: var(--portal-text); border: 1px solid #aebfd0; border-radius: var(--portal-radius); }
:deep(.public-assistant-composer button) { min-height: 48px; align-self: end; display: inline-flex; align-items: center; justify-content: center; gap: 7px; padding: 10px 14px; cursor: pointer; color: #fff; border: 0; background: var(--portal-navy); font-weight: 700; }
:deep(.public-assistant-composer button:disabled) { cursor: not-allowed; opacity: .55; }
:deep(.public-assistant-composer small) { display: block; margin-top: 5px; color: var(--portal-muted); }
.public-assistant-disclaimer { margin: 10px 0 0; color: var(--portal-muted); text-align: center; font-size: 12px; }
@media (max-width: 768px) {
  .public-assistant-layout { grid-template-columns: 1fr; }
  :deep(.public-assistant-sidebar h2), :deep(.public-assistant-sidebar__tip) { display: none; }
  :deep(.public-assistant-sidebar nav) { display: flex; overflow-x: auto; }
  :deep(.public-assistant-sidebar nav a) { min-width: 120px; justify-content: center; flex: 1  0 auto; border-bottom: 0; border-right: 1px solid var(--portal-border); }
  :deep(.public-assistant-sidebar nav a:first-child) { border-left: 0; border-bottom: 3px solid var(--portal-red); }
  .public-assistant-conversation { min-height: 520px; padding: 18px; }
}
@media (max-width: 520px) {
  .public-assistant-title { padding-inline: 14px; }
  .public-assistant-title > span { display: none; }
  .public-assistant-title h1 { font-size: 22px; }
  :deep(.public-assistant-quick) { grid-template-columns: 1fr; }
  :deep(.public-assistant-messages article) { max-width: 94%; }
  :deep(.public-assistant-composer > div) { grid-template-columns: 1fr; }
  :deep(.public-assistant-composer button) { min-height: 44px; }
}
</style>
