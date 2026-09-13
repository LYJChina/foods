<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";
import { Icon } from "@iconify/vue";
import { ElMessage, ElMessageBox, type UploadFile } from "element-plus";
import { DocumentAPI } from "@/api/module_food_ai/documents";

type State = "idle" | "queued" | "parsing" | "indexing" | "ready" | "failed";
type Chunk = {
  chunk_index: number;
  content: string;
  page_number?: number | null;
  heading?: string | null;
};
type Citation = Chunk & { excerpt: string };
type Answer = { answer: string; citations?: Citation[] };

const selectedFile = ref<File | null>(null);
const confirmed = ref(false);
const documentId = ref("");
const fileName = ref("");
const expiresAt = ref("");
const state = ref<State>("idle");
const chunks = ref<Chunk[]>([]);
const question = ref("");
const answer = ref<Answer | null>(null);
const errorMessage = ref("");
const uploading = ref(false);
const asking = ref(false);
const activeChunk = ref<number | null>(null);
let pollTimer: ReturnType<typeof setTimeout> | undefined;

const steps = [
  { label: "上传完成", icon: "ri:upload-cloud-2-line" },
  { label: "平台智能体解析", icon: "ri:file-search-line" },
  { label: "内容整理", icon: "ri:list-check-3" },
  { label: "可预览问答", icon: "ri:question-answer-line" },
];
const stateOrder: Record<State, number> = {
  idle: -1,
  queued: 0,
  parsing: 1,
  indexing: 2,
  ready: 3,
  failed: -1,
};
const statusMeta = computed(() => {
  const map: Record<State, { label: string; detail: string; tone: string; icon: string }> = {
    idle: {
      label: "等待上传",
      detail: "选择公开或低敏文档后开始解析",
      tone: "neutral",
      icon: "ri:file-add-line",
    },
    queued: {
      label: "已提交",
      detail: "文档已进入解析队列，请稍候",
      tone: "working",
      icon: "ri:time-line",
    },
    parsing: {
      label: "正在解析",
      detail: "公共服务平台智能体正在识别文档结构与正文",
      tone: "working",
      icon: "svg-spinners:ring-resize",
    },
    indexing: {
      label: "正在整理",
      detail: "正在生成可预览、可检索的内容片段",
      tone: "working",
      icon: "svg-spinners:ring-resize",
    },
    ready: {
      label: "解析完成",
      detail: "现在可以预览内容并基于本文档提问",
      tone: "success",
      icon: "ri:checkbox-circle-line",
    },
    failed: {
      label: "解析失败",
      detail: "请检查文件后重新上传，或稍后再试",
      tone: "error",
      icon: "ri:error-warning-line",
    },
  };
  return map[state.value];
});
const canUpload = computed(() =>
  Boolean(selectedFile.value && confirmed.value && !uploading.value)
);

function handleSelect(uploadFile: UploadFile) {
  selectedFile.value = uploadFile.raw ?? null;
  errorMessage.value = "";
  return false;
}
function handleRemove() {
  selectedFile.value = null;
}
function scheduleRefresh() {
  clearTimeout(pollTimer);
  pollTimer = setTimeout(refresh, 1600);
}

async function upload() {
  if (!selectedFile.value) return ElMessage.warning("请先选择需要解析的文件");
  if (!confirmed.value) return ElMessage.warning("请先确认文档符合低敏资料边界");
  uploading.value = true;
  errorMessage.value = "";
  answer.value = null;
  chunks.value = [];
  try {
    const data = await DocumentAPI.create(selectedFile.value, confirmed.value);
    documentId.value = data.document_id;
    fileName.value = data.file_name || selectedFile.value.name;
    expiresAt.value = data.expires_at || "";
    state.value = "queued";
    await refresh();
  } catch {
    state.value = "failed";
    errorMessage.value = "文档提交失败。请确认文件格式、大小以及解析服务状态后重试。";
  } finally {
    uploading.value = false;
  }
}

async function refresh() {
  if (!documentId.value) return;
  clearTimeout(pollTimer);
  try {
    const data = await DocumentAPI.status(documentId.value);
    state.value = data.status as State;
    fileName.value = data.file_name || fileName.value;
    expiresAt.value = data.expires_at || expiresAt.value;
    errorMessage.value = "";
    if (state.value === "ready") {
      const content = await DocumentAPI.content(documentId.value);
      chunks.value = Array.isArray(content.items) ? content.items : [];
      if (!chunks.value.length) errorMessage.value = "解析已完成，但暂未生成可预览的正文内容。";
    } else if (state.value !== "failed") scheduleRefresh();
  } catch {
    errorMessage.value = "状态查询暂时失败，解析任务可能仍在继续。请稍后手动刷新。";
  }
}

async function ask() {
  if (state.value !== "ready" || !question.value.trim() || asking.value) return;
  asking.value = true;
  errorMessage.value = "";
  answer.value = null;
  try {
    answer.value = await DocumentAPI.question(documentId.value, question.value.trim());
  } catch {
    errorMessage.value = "问答服务未配置或暂不可用，文档预览不受影响。";
  } finally {
    asking.value = false;
  }
}

function resetWorkspace() {
  clearTimeout(pollTimer);
  selectedFile.value = null;
  confirmed.value = false;
  documentId.value = "";
  fileName.value = "";
  expiresAt.value = "";
  state.value = "idle";
  chunks.value = [];
  question.value = "";
  answer.value = null;
  errorMessage.value = "";
}
async function deleteDocument() {
  try {
    await ElMessageBox.confirm("删除后将无法继续预览或问答，是否确认删除？", "删除当前文档", {
      confirmButtonText: "确认删除",
      cancelButtonText: "取消",
      type: "warning",
    });
    await DocumentAPI.remove(documentId.value);
    resetWorkspace();
    ElMessage.success("文档已删除");
  } catch (error) {
    if (error !== "cancel" && error !== "close") errorMessage.value = "文档删除失败，请稍后重试。";
  }
}
function locateCitation(index: number) {
  activeChunk.value = index;
  document
    .getElementById(`chunk-${index}`)
    ?.scrollIntoView({ behavior: "smooth", block: "center" });
  window.setTimeout(() => {
    if (activeChunk.value === index) activeChunk.value = null;
  }, 1800);
}
function formatExpiry(value: string) {
  if (!value) return "上传后 24 小时";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "上传后 24 小时"
    : date.toLocaleString("zh-CN", { hour12: false });
}
onBeforeUnmount(() => clearTimeout(pollTimer));
</script>

<template>
  <main class="portal-page portal-container document-workspace">
    <nav class="document-breadcrumb" aria-label="面包屑">
      <RouterLink to="/portal/home">首页</RouterLink
      ><Icon icon="ri:arrow-right-s-line" aria-hidden="true" /><span>智能文档解析</span>
    </nav>
    <header class="document-hero">
      <div>
        <div class="document-labels"><span>公共服务平台智能体</span></div>
        <h1>智能文档解析与问答</h1>
        <p>
          文档解析使用
          上传公开或低敏文档，由公共服务平台智能体完成结构化预览，并通过后端配置的大模型进行带引用问答。
        </p>
      </div>
      <aside class="document-boundary">
        <Icon icon="ri:shield-check-line" aria-hidden="true" />
        <div>
          <strong>数据边界</strong><span>禁止上传配方、工艺、成本、客户、订单和生产经营数据</span>
        </div>
      </aside>
    </header>

    <section class="document-step-card" aria-labelledby="progress-title">
      <div class="document-status" :class="`is-${statusMeta.tone}`" aria-live="polite">
        <span class="document-status__icon"
          ><Icon :icon="statusMeta.icon" aria-hidden="true" /></span
        ><span
          ><strong id="progress-title">{{ statusMeta.label }}</strong
          ><small>{{ statusMeta.detail }}</small></span
        >
      </div>
      <ol class="document-stepper" data-testid="document-stepper">
        <li
          v-for="(step, index) in steps"
          :key="step.label"
          :class="{
            'is-done': stateOrder[state] > index,
            'is-active': stateOrder[state] === index && state !== 'failed',
          }"
        >
          <span
            ><Icon
              :icon="stateOrder[state] > index ? 'ri:check-line' : step.icon"
              aria-hidden="true" /></span
          ><small>{{ step.label }}</small>
        </li>
      </ol>
      <div v-if="documentId" class="document-task-actions">
        <button v-if="state !== 'ready'" type="button" @click="refresh">
          <Icon icon="ri:refresh-line" />刷新状态</button
        ><button type="button" @click="resetWorkspace">
          <Icon icon="ri:upload-2-line" />重新上传</button
        ><button class="is-danger" type="button" @click="deleteDocument">
          <Icon icon="ri:delete-bin-6-line" />删除文档
        </button>
      </div>
    </section>
    <div v-if="errorMessage" class="document-error" role="alert">
      <Icon icon="ri:error-warning-line" /><span>{{ errorMessage }}</span
      ><button v-if="documentId && state !== 'ready'" type="button" @click="refresh">重试</button>
    </div>

    <section v-if="!documentId" class="document-upload-layout">
      <article class="document-upload-card" data-testid="document-upload-card">
        <div class="document-card-heading">
          <span><Icon icon="ri:upload-cloud-2-line" /></span>
          <div>
            <h2>上传待解析文档</h2>
            <p>单次上传 1 个文件，解析期间请勿关闭当前页面。</p>
          </div>
        </div>
        <el-upload
          class="document-uploader"
          drag
          :auto-upload="false"
          :limit="1"
          :on-change="handleSelect"
          :on-remove="handleRemove"
          accept=".pdf,.docx,.pptx,.jpg,.jpeg,.png"
          ><Icon icon="ri:file-upload-line" /><strong>拖放文件到此处，或点击选择文件</strong
          ><span>支持 PDF、DOCX、PPTX、JPG、PNG</span></el-upload
        >
        <label class="document-confirm"
          ><el-checkbox v-model="confirmed" size="large">我确认该文档属于公开或低敏材料</el-checkbox
          ><small>点击开始解析即表示已了解并接受上方数据边界。</small></label
        >
        <button
          class="document-primary-action"
          type="button"
          :disabled="!canUpload"
          @click="upload"
        >
          <Icon :icon="uploading ? 'svg-spinners:ring-resize' : 'ri:magic-line'" />{{
            uploading ? "正在提交…" : "开始解析"
          }}
        </button>
      </article>
      <aside class="document-guide-card">
        <h2>上传说明</h2>
        <ul>
          <li>
            <Icon icon="ri:file-text-line" />
            <div><strong>常用格式</strong><small>PDF、Word、PPT 和图片文件</small></div>
          </li>
          <li>
            <Icon icon="ri:hard-drive-3-line" />
            <div><strong>文件大小</strong><small>单个文件不超过 20MB</small></div>
          </li>
          <li>
            <Icon icon="ri:pages-line" />
            <div><strong>页数限制</strong><small>PDF 最多 100 页</small></div>
          </li>
          <li>
            <Icon icon="ri:timer-2-line" />
            <div><strong>临时保留</strong><small>上传内容 24 小时自动删除</small></div>
          </li>
        </ul>
        <p>
          <Icon icon="ri:information-line" />公共服务平台智能体
          与大模型不可用时会明确提示失败，不会伪造成功结果。
        </p>
      </aside>
    </section>

    <section v-else-if="state !== 'ready'" class="document-processing-card">
      <div class="document-processing-card__visual">
        <Icon :icon="state === 'failed' ? 'ri:file-damage-line' : 'ri:file-search-line'" />
      </div>
      <div>
        <span>{{ state === "failed" ? "本次任务未完成" : "文档处理进行中" }}</span>
        <h2>{{ fileName || "当前文档" }}</h2>
        <p>
          {{
            state === "failed"
              ? "您可以重新选择文件发起解析。"
              : "系统正在执行文档识别和内容整理，完成后将自动显示预览。"
          }}
        </p>
        <small>临时文件预计删除时间：{{ formatExpiry(expiresAt) }}</small>
      </div>
    </section>

    <section v-else class="document-result-layout">
      <article class="document-preview-card">
        <header class="document-result-heading">
          <div>
            <span>解析预览</span>
            <h2>{{ fileName || "当前文档" }}</h2>
          </div>
          <span class="document-count"
            ><Icon icon="ri:file-list-3-line" />{{ chunks.length }} 个内容片段</span
          >
        </header>
        <div v-if="chunks.length" class="document-content" tabindex="0">
          <section
            v-for="chunk in chunks"
            :id="`chunk-${chunk.chunk_index}`"
            :key="chunk.chunk_index"
            class="document-chunk"
            :class="{ 'is-highlighted': activeChunk === chunk.chunk_index }"
          >
            <div class="document-chunk__meta">
              <span>#{{ chunk.chunk_index + 1 }}</span
              ><span v-if="chunk.page_number">第 {{ chunk.page_number }} 页</span>
            </div>
            <h3 v-if="chunk.heading">{{ chunk.heading }}</h3>
            <p>{{ chunk.content }}</p>
          </section>
        </div>
        <div v-else class="document-empty">
          <Icon icon="ri:file-search-line" /><strong>暂无可预览内容</strong
          ><span>请刷新状态或重新上传文档。</span>
        </div>
      </article>
      <aside class="document-qa-card">
        <header class="document-result-heading">
          <div>
            <span>文档问答</span>
            <h2>基于当前文档提问</h2>
          </div>
          <span class="document-ai-label">AI 生成</span>
        </header>
        <p class="document-qa-intro">
          回答仅基于已解析内容，并尽可能附带原文引用。仅供辅助阅读，请以原文为准。
        </p>
        <form class="document-question-form" @submit.prevent="ask">
          <label for="document-question">请输入你的问题</label
          ><el-input
            id="document-question"
            v-model="question"
            type="textarea"
            :rows="4"
            maxlength="4000"
            show-word-limit
            placeholder="例如：这份文件的主要结论是什么？"
          /><button type="submit" :disabled="!question.trim() || asking">
            <Icon :icon="asking ? 'svg-spinners:ring-resize' : 'ri:send-plane-2-line'" />{{
              asking ? "正在生成回答…" : "发送问题"
            }}
          </button>
        </form>
        <div v-if="answer" class="document-answer" aria-live="polite">
          <div class="document-answer__title">
            <Icon icon="ri:sparkling-2-line" /><strong>回答</strong>
          </div>
          <p>{{ answer.answer }}</p>
          <div v-if="answer.citations?.length" class="document-citations">
            <strong>原文引用</strong
            ><button
              v-for="citation in answer.citations"
              :key="citation.chunk_index"
              type="button"
              @click="locateCitation(citation.chunk_index)"
            >
              <span
                >[{{ citation.chunk_index + 1 }}]
                <template v-if="citation.page_number"
                  >第 {{ citation.page_number }} 页</template
                ></span
              ><small>{{ citation.excerpt }}</small
              ><Icon icon="ri:focus-3-line" />
            </button>
          </div>
          <p v-else class="document-answer__notice">
            <Icon icon="ri:information-line" />当前回答未找到足够的原文依据，请换一种问法。
          </p>
        </div>
        <div v-else class="document-qa-empty">
          <Icon icon="ri:chat-3-line" />
          <p>解析已经完成，可以开始提问。</p>
          <small>建议问题：提炼摘要、查找条款、说明某个概念。</small>
        </div>
      </aside>
    </section>
  </main>
</template>

<style scoped lang="scss">
.document-workspace {
  max-width: 1180px;
}
.document-breadcrumb {
  min-height: 32px;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 14px;
  color: #64748b;
  font-size: 14px;
}
.document-breadcrumb a {
  color: var(--portal-blue);
}
.document-breadcrumb svg {
  width: 16px;
}
.document-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 24px;
  align-items: center;
  padding: 24px 26px;
  color: #fff;
  border-radius: 2px;
  background: #edf4fa;
  box-shadow: 0 8px 24px rgba(8, 40, 79, 0.12);
}
.document-labels {
  display: flex;
  gap: 8px;
}
.document-labels span {
  padding: 3px 10px;
  border: 1px solid rgba(255, 255, 255, 0.34);
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.1);
  font-size: 13px;
  font-weight: 750;
}
.document-hero h1 {
  margin: 8px 0 6px;
  font-size: clamp(28px, 3vw, 38px);
  line-height: 1.24;
}
.document-hero p {
  margin: 0;
  color: #dce8f5;
}
.document-boundary {
  display: flex;
  gap: 13px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-left: 4px solid #70d7bd;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.09);
}
.document-boundary > svg {
  width: 26px;
  height: 26px;
  flex: none;
  color: #a7f3d0;
}
.document-boundary strong,
.document-boundary span {
  display: block;
}
.document-boundary span {
  margin-top: 3px;
  color: #e5eef8;
  font-size: 14px;
}
.document-step-card {
  display: grid;
  grid-template-columns: 220px minmax(420px, 1fr) auto;
  gap: 22px;
  align-items: center;
  padding: 16px 18px;
  margin: 16px 0;
  border: 1px solid var(--portal-border);
  border-radius: 2px;
  background: #fff;
}
.document-status {
  display: flex;
  align-items: center;
  gap: 10px;
}
.document-status__icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  flex: none;
  color: #475569;
  border-radius: 2px;
  background: #eef2f6;
}
.document-status strong,
.document-status small {
  display: block;
}
.document-status small {
  color: var(--portal-muted);
  font-size: 12px;
  line-height: 1.4;
}
.document-status.is-working .document-status__icon {
  color: var(--portal-blue);
  background: #e8f4fb;
}
.document-status.is-success .document-status__icon {
  color: var(--portal-green);
  background: #e7f7f1;
}
.document-status.is-error .document-status__icon {
  color: var(--portal-red);
  background: #fff0f1;
}
.document-stepper {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  margin: 0;
  padding: 0;
  list-style: none;
}
.document-stepper li {
  position: relative;
  display: grid;
  justify-items: center;
  gap: 4px;
  color: #64748b;
  font-size: 12px;
}
.document-stepper li:before {
  content: "";
  position: absolute;
  top: 15px;
  right: 50%;
  width: 100%;
  height: 2px;
  background: #dce4ed;
}
.document-stepper li:first-child:before {
  display: none;
}
.document-stepper li > span {
  z-index: 1;
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: 2px solid #d4dee9;
  border-radius: 50%;
  background: #fff;
}
.document-stepper .is-done:before,
.document-stepper .is-active:before {
  background: var(--portal-blue);
}
.document-stepper .is-done > span,
.document-stepper .is-active > span {
  color: #fff;
  border-color: var(--portal-blue);
  background: var(--portal-blue);
}
.document-task-actions {
  display: flex;
  gap: 5px;
}
.document-task-actions button {
  min-height: 38px;
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 9px;
  cursor: pointer;
  color: var(--portal-blue);
  border: 0;
  border-radius: 2px;
  background: transparent;
  font-weight: 650;
  white-space: nowrap;
}
.document-task-actions button:hover {
  background: #edf5fb;
}
.document-task-actions .is-danger {
  color: var(--portal-red);
}
.document-error {
  min-height: 48px;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 10px 14px;
  margin-bottom: 16px;
  color: #8f171e;
  border: 1px solid #efc4c7;
  border-radius: 2px;
  background: #fff5f5;
}
.document-error button {
  min-height: 36px;
  cursor: pointer;
  color: #8f171e;
  border: 1px solid #d99ca0;
  border-radius: 2px;
  background: #fff;
}
.document-upload-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 16px;
  align-items: start;
}
.document-upload-card,
.document-guide-card,
.document-processing-card,
.document-preview-card,
.document-qa-card {
  border: 1px solid var(--portal-border);
  border-radius: 2px;
  background: #fff;
}
.document-upload-card {
  padding: 22px;
}
.document-card-heading {
  display: flex;
  gap: 12px;
  align-items: center;
  padding-bottom: 17px;
  margin-bottom: 17px;
  border-bottom: 1px solid var(--portal-border);
}
.document-card-heading > span {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  flex: none;
  color: #fff;
  border-radius: 2px;
  background: var(--portal-blue);
}
.document-card-heading h2,
.document-card-heading p {
  margin: 0;
}
.document-card-heading h2 {
  font-size: 21px;
}
.document-card-heading p {
  color: var(--portal-muted);
  font-size: 14px;
}
.document-uploader :deep(.el-upload) {
  width: 100%;
}
.document-uploader :deep(.el-upload-dragger) {
  width: 100%;
  min-height: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  cursor: pointer;
  border: 1px dashed #8da8c3;
  border-radius: 2px;
  background: #f7fafc;
  transition: 0.2s;
}
.document-uploader :deep(.el-upload-dragger:hover) {
  border-color: var(--portal-blue);
  background: #eef6fb;
}
.document-uploader :deep(.el-upload-dragger > svg) {
  width: 42px;
  height: 42px;
  margin-bottom: 10px;
  color: var(--portal-blue);
}
.document-uploader :deep(.el-upload-dragger strong) {
  color: var(--portal-navy);
}
.document-uploader :deep(.el-upload-dragger span) {
  margin-top: 5px;
  color: #64748b;
  font-size: 13px;
}
.document-confirm {
  display: block;
  padding: 13px 14px;
  margin: 14px 0;
  border: 1px solid #d5e0eb;
  border-radius: 2px;
  background: #f8fafc;
}
.document-confirm small {
  display: block;
  padding-left: 30px;
  color: var(--portal-muted);
}
.document-primary-action {
  width: 100%;
  min-height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  color: #fff;
  border: 0;
  border-radius: 2px;
  background: var(--portal-navy);
  font-weight: 750;
}
.document-primary-action:hover:not(:disabled) {
  background: #164b86;
}
.document-primary-action:disabled {
  cursor: not-allowed;
  background: #94a3b8;
}
.document-guide-card {
  padding: 20px;
  border-top: 4px solid var(--portal-green);
}
.document-guide-card h2 {
  margin: 0 0 12px;
}
.document-guide-card ul {
  margin: 0;
  padding: 0;
  list-style: none;
}
.document-guide-card li {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #e8edf3;
}
.document-guide-card li > svg {
  width: 24px;
  color: var(--portal-blue);
}
.document-guide-card strong,
.document-guide-card small {
  display: block;
}
.document-guide-card small {
  color: var(--portal-muted);
}
.document-guide-card > p {
  display: flex;
  gap: 7px;
  padding: 11px;
  margin: 14px 0 0;
  color: #075985;
  border-radius: 2px;
  background: #eaf6fc;
  font-size: 13px;
}
.document-processing-card {
  min-height: 260px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 22px;
  padding: 34px;
}
.document-processing-card__visual {
  width: 84px;
  height: 104px;
  display: grid;
  place-items: center;
  flex: none;
  color: var(--portal-blue);
  border: 1px solid #cad9e8;
  border-radius: 2px;
  background: #f0f6fb;
  box-shadow: 8px 8px 0 #e2eaf2;
}
.document-processing-card__visual svg {
  width: 40px;
  height: 40px;
}
.document-processing-card span {
  color: var(--portal-blue);
  font-size: 14px;
  font-weight: 750;
}
.document-processing-card h2 {
  margin: 3px 0 6px;
  font-size: 24px;
  overflow-wrap: anywhere;
}
.document-processing-card p {
  margin: 0 0 9px;
  color: var(--portal-muted);
}
.document-result-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(340px, 1fr);
  gap: 16px;
  align-items: start;
}
.document-preview-card,
.document-qa-card {
  min-width: 0;
  overflow: hidden;
}
.document-qa-card {
  position: sticky;
  top: 16px;
}
.document-result-heading {
  min-height: 72px;
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid var(--portal-border);
}
.document-result-heading span {
  color: var(--portal-blue);
  font-size: 12px;
  font-weight: 750;
}
.document-result-heading h2 {
  margin: 2px 0 0;
  font-size: 19px;
  overflow-wrap: anywhere;
}
.document-result-heading .document-count,
.document-result-heading .document-ai-label {
  padding: 4px 9px;
  flex: none;
  color: #334155;
  border-radius: 2px;
  background: #edf1f5;
}
.document-result-heading .document-ai-label {
  color: #075985;
  background: #e0f2fe;
}
.document-content {
  height: min(610px, calc(100vh - 300px));
  min-height: 430px;
  overflow-y: auto;
  padding: 7px 18px 18px;
  scroll-behavior: smooth;
}
.document-chunk {
  padding: 15px 12px;
  border-bottom: 1px solid #e5ebf1;
  border-left: 3px solid transparent;
  transition: 0.2s;
}
.document-chunk.is-highlighted {
  border-left-color: var(--portal-blue);
  background: #edf7fd;
}
.document-chunk__meta {
  display: flex;
  gap: 7px;
  margin-bottom: 5px;
}
.document-chunk__meta span {
  padding: 1px 6px;
  color: #52667b;
  border-radius: 2px;
  background: #eef2f6;
  font-size: 11px;
}
.document-chunk h3 {
  margin: 0 0 5px;
  color: var(--portal-navy);
  font-size: 16px;
}
.document-chunk p {
  margin: 0;
  color: #27364a;
  line-height: 1.75;
  white-space: pre-wrap;
}
.document-empty {
  min-height: 430px;
  display: grid;
  place-content: center;
  justify-items: center;
  color: var(--portal-muted);
}
.document-empty svg {
  width: 38px;
  height: 38px;
}
.document-qa-intro {
  padding: 13px 18px;
  margin: 0;
  color: #475569;
  border-bottom: 1px solid #e5ebf1;
  background: #f8fafc;
  font-size: 13px;
}
.document-question-form {
  padding: 16px 18px;
}
.document-question-form label {
  display: block;
  margin-bottom: 7px;
  font-weight: 700;
}
.document-question-form :deep(.el-textarea__inner) {
  min-height: 100px !important;
  padding: 11px 12px;
  box-shadow: none;
}
.document-question-form button {
  width: 100%;
  min-height: 44px;
  margin-top: 12px;
  cursor: pointer;
  color: #fff;
  border: 0;
  border-radius: 2px;
  background: var(--portal-blue);
  font-weight: 750;
}
.document-question-form button:disabled {
  cursor: not-allowed;
  background: #94a3b8;
}
.document-answer {
  margin: 0 18px 18px;
  padding: 15px;
  border: 1px solid #c8dbe9;
  border-radius: 2px;
  background: #f4f9fc;
}
.document-answer__title {
  display: flex;
  gap: 8px;
  color: var(--portal-navy);
}
.document-answer > p {
  white-space: pre-wrap;
}
.document-citations {
  display: grid;
  gap: 7px;
  padding-top: 12px;
  border-top: 1px solid #d4e1eb;
}
.document-citations button {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 2px 8px;
  padding: 9px 10px;
  cursor: pointer;
  text-align: left;
  border: 1px solid #c8d8e6;
  border-radius: 2px;
  background: #fff;
}
.document-citations button span {
  color: var(--portal-blue);
  font-size: 12px;
  font-weight: 750;
}
.document-citations button small {
  grid-column: 1/-1;
  overflow: hidden;
  color: #475569;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.document-qa-empty {
  display: grid;
  justify-items: center;
  padding: 26px;
  color: #64748b;
  text-align: center;
}
.document-qa-empty svg {
  width: 34px;
  height: 34px;
}
@media (max-width: 1100px) {
  .document-step-card {
    grid-template-columns: 190px 1fr;
  }
  .document-task-actions {
    grid-column: 1/-1;
    justify-content: flex-end;
    padding-top: 8px;
    border-top: 1px solid #e5ebf1;
  }
}
@media (max-width: 1024px) {
  .document-hero {
    grid-template-columns: 1fr;
  }
  .document-result-layout {
    grid-template-columns: 1fr;
  }
  .document-qa-card {
    position: static;
  }
  .document-content {
    height: auto;
    max-height: 620px;
  }
}
@media (max-width: 768px) {
  .document-step-card {
    grid-template-columns: 1fr;
  }
  .document-task-actions {
    grid-column: 1;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
  .document-upload-layout {
    grid-template-columns: 1fr;
  }
  .document-guide-card {
    order: -1;
  }
  .document-processing-card {
    justify-content: flex-start;
  }
}
@media (max-width: 560px) {
  .document-workspace {
    padding-top: 22px;
  }
  .document-hero {
    padding: 20px;
  }
  .document-hero h1 {
    font-size: 28px;
  }
  .document-stepper small {
    max-width: 60px;
    text-align: center;
    line-height: 1.3;
  }
  .document-task-actions button {
    min-height: 44px;
  }
  .document-upload-card {
    padding: 16px;
  }
  .document-uploader :deep(.el-upload-dragger) {
    min-height: 160px;
    padding: 20px 12px;
  }
  .document-confirm small {
    padding-left: 0;
  }
  .document-processing-card {
    align-items: flex-start;
    padding: 26px 18px;
  }
  .document-processing-card__visual {
    width: 60px;
    height: 76px;
  }
  .document-result-heading {
    align-items: flex-start;
    flex-direction: column;
  }
  .document-content {
    min-height: 360px;
    padding-inline: 10px;
  }
}
</style>
