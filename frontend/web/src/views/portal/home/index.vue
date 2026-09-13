<script setup lang="ts">
import { onMounted, ref } from "vue";
import { Icon } from "@iconify/vue";
import { useRouter } from "vue-router";

import {
  PortalContentAPI,
  type PortalHomeContent,
} from "@/api/module_food_ai/content";

const router = useRouter();
const query = ref("");
const content = ref<PortalHomeContent | null>(null);
const loading = ref(true);
const loadError = ref("");

async function loadContent() {
  loading.value = true;
  loadError.value = "";
  try {
    content.value = await PortalContentAPI.getHomeContent();
  } catch {
    loadError.value = "信息栏目暂时无法加载，请稍后重试。";
  } finally {
    loading.value = false;
  }
}

function openAssistant() {
  const normalized = query.value.trim();
  return router.push({
    path: "/portal/assistant",
    query: normalized ? { q: normalized } : undefined,
  });
}

function openHotQuestion(question: string) {
  query.value = question;
  return openAssistant();
}

function openOnEmptyClick() {
  if (!query.value.trim()) return openAssistant();
}

onMounted(loadContent);
</script>

<template>
  <main class="portal-home">
    <section class="portal-home-search" aria-labelledby="portal-search-title">
      <div class="portal-container portal-home-search__inner">
        <p class="portal-home-search__eyebrow">食品行业公共服务</p>
        <h1 id="portal-search-title">AI 助手，帮您查找公共服务</h1>
        <p class="portal-home-search__lead">政策咨询、办事导航、材料解析，一次输入直达对应服务。</p>
        <form
          data-testid="ai-search-form"
          class="portal-ai-search"
          role="search"
          @submit.prevent="openAssistant"
        >
          <label for="portal-ai-query">
            <Icon icon="ri:sparkling-2-line" aria-hidden="true" />
            <span>AI 助手</span>
          </label>
          <input
            id="portal-ai-query"
            v-model="query"
            data-testid="ai-search-input"
            type="search"
            autocomplete="off"
            placeholder="请输入您想咨询或办理的事项"
            @click="openOnEmptyClick"
          />
          <button type="submit"><Icon icon="ri:search-line" aria-hidden="true" />开始查询</button>
        </form>
        <div v-if="content" class="portal-hot-questions" aria-label="热门问题">
          <span>热门问题：</span>
          <button
            v-for="question in content.hotQuestions"
            :key="question"
            type="button"
            @click="openHotQuestion(question)"
          >
            {{ question }}
          </button>
        </div>
      </div>
    </section>

    <div class="portal-container portal-home__body">
      <section v-if="content" class="portal-quick-actions" aria-label="快捷服务">
        <RouterLink v-for="item in content.quickActions" :key="item.id" :to="item.to">
          <span class="portal-quick-actions__icon" aria-hidden="true"><Icon :icon="item.icon" /></span>
          <span><strong>{{ item.label }}</strong><small>{{ item.description }}</small></span>
          <Icon class="portal-quick-actions__arrow" icon="ri:arrow-right-s-line" aria-hidden="true" />
        </RouterLink>
      </section>

      <section v-if="content" class="portal-home-section" aria-labelledby="service-zones-title">
        <header class="portal-home-section__heading">
          <div><h2 id="service-zones-title">服务专区</h2><span></span></div>
          <RouterLink to="/portal/services">查看全部服务 <Icon icon="ri:arrow-right-line" /></RouterLink>
        </header>
        <div class="portal-service-zones">
          <RouterLink v-for="zone in content.serviceZones" :key="zone.id" :to="zone.to">
            <span class="portal-service-zones__icon" aria-hidden="true"><Icon :icon="zone.icon" /></span>
            <div>
              <h3>{{ zone.title }}</h3>
              <p>{{ zone.services.join(" · ") }}</p>
            </div>
            <Icon class="portal-service-zones__arrow" icon="ri:arrow-right-line" aria-hidden="true" />
          </RouterLink>
        </div>
      </section>

      <section class="portal-home-section" aria-label="平台信息">
        <div v-if="loading" class="portal-information-loading">正在加载平台信息…</div>
        <div v-else-if="loadError" class="portal-information-error" role="alert">
          <span>{{ loadError }}</span><button type="button" @click="loadContent">重新加载</button>
        </div>
        <div v-else-if="content" class="portal-information-grid">
          <article>
            <header class="portal-information-heading">
              <div><h2>工作动态</h2><span></span></div>
              <small>示例信息</small>
            </header>
            <ul>
              <li v-for="item in content.news" :key="item.id">
                <a href="#portal-information-note" @click.prevent>
                  <span>{{ item.title }}</span><time :datetime="item.date">{{ item.date }}</time>
                </a>
              </li>
            </ul>
          </article>
          <article>
            <header class="portal-information-heading">
              <div><h2>通知公告</h2><span></span></div>
              <small>示例信息</small>
            </header>
            <ul>
              <li v-for="item in content.notices" :key="item.id">
                <a href="#portal-information-note" @click.prevent>
                  <span>{{ item.title }}</span><time :datetime="item.date">{{ item.date }}</time>
                </a>
              </li>
            </ul>
          </article>
        </div>
        <p id="portal-information-note" class="portal-information-note">
          本栏目为页面展示样例，不代表政府部门或监管机构正式发布。
        </p>
      </section>
    </div>
  </main>
</template>

<style scoped lang="scss">
.portal-home-search { color: #17324d; border-bottom: 1px solid #cbd8e5; background: #edf4fa; }
.portal-home-search__inner { min-height: 310px; display: flex; align-items: center; flex-direction: column; justify-content: center; padding-block: 44px 38px; text-align: center; }
.portal-home-search__eyebrow { margin: 0 0 6px; color: var(--portal-blue); font-size: 15px; font-weight: 700; letter-spacing: .16em; }
.portal-home-search h1 { margin: 0; color: var(--portal-navy-deep); font-size: clamp(28px, 3.2vw, 42px); line-height: 1.3; }
.portal-home-search__lead { margin: 8px 0 22px; color: var(--portal-muted); font-size: 16px; }
.portal-ai-search { width: min(860px, 100%); min-height: 62px; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; border: 2px solid var(--portal-navy); border-radius: var(--portal-radius); background: #fff; }
.portal-ai-search label { height: 34px; display: inline-flex; align-items: center; gap: 7px; padding-inline: 18px; color: var(--portal-navy); border-right: 1px solid var(--portal-border); font-weight: 750; white-space: nowrap; }
.portal-ai-search label svg { width: 20px; height: 20px; }
.portal-ai-search input { width: 100%; height: 58px; padding: 0 18px; color: var(--portal-text); border: 0; outline: 0; background: transparent; }
.portal-ai-search button { min-width: 130px; height: 58px; display: inline-flex; align-items: center; justify-content: center; gap: 8px; cursor: pointer; color: #fff; border: 0; background: var(--portal-navy); font-weight: 700; }
.portal-ai-search button:hover { background: var(--portal-navy-deep); }
.portal-hot-questions { width: min(860px, 100%); display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 6px 16px; margin-top: 14px; color: var(--portal-muted); font-size: 13px; }
.portal-hot-questions > span { font-weight: 700; }
.portal-hot-questions button { padding: 0; cursor: pointer; color: var(--portal-blue); border: 0; background: transparent; }
.portal-hot-questions button:hover { text-decoration: underline; }
.portal-home__body { padding-block: 26px 54px; }
.portal-quick-actions { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border: 1px solid var(--portal-border); background: #fff; }
.portal-quick-actions > a { min-height: 106px; display: grid; grid-template-columns: 44px minmax(0, 1fr) 20px; gap: 13px; align-items: center; padding: 18px; border-right: 1px solid var(--portal-border); }
.portal-quick-actions > a:last-child { border-right: 0; }
.portal-quick-actions > a:hover { background: #f2f7fb; }
.portal-quick-actions__icon { width: 44px; height: 44px; display: grid; place-items: center; color: #fff; background: var(--portal-navy); }
.portal-quick-actions__icon svg { width: 23px; height: 23px; }
.portal-quick-actions strong, .portal-quick-actions small { display: block; }
.portal-quick-actions strong { color: var(--portal-navy-deep); font-size: 18px; }
.portal-quick-actions small { margin-top: 3px; color: var(--portal-muted); font-size: 12px; }
.portal-quick-actions__arrow { color: #7890a7; }
.portal-home-section { padding-top: 34px; }
.portal-home-section__heading, .portal-information-heading { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-bottom: 16px; border-bottom: 1px solid var(--portal-border); }
.portal-home-section__heading > div, .portal-information-heading > div { position: relative; }
.portal-home-section__heading h2, .portal-information-heading h2 { margin: 0; padding: 0 2px 10px; color: var(--portal-navy-deep); font-size: 23px; }
.portal-home-section__heading div > span, .portal-information-heading div > span { width: 48px; height: 3px; display: block; position: absolute; bottom: -1px; left: 0; background: var(--portal-red); }
.portal-home-section__heading > a { display: inline-flex; align-items: center; gap: 5px; color: var(--portal-blue); font-size: 14px; }
.portal-service-zones { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.portal-service-zones > a { min-height: 128px; display: grid; grid-template-columns: 42px minmax(0, 1fr) 18px; gap: 12px; align-items: center; padding: 20px 16px; border: 1px solid var(--portal-border); border-top: 3px solid var(--portal-blue); background: #fff; }
.portal-service-zones > a:hover { border-color: #9fb7ce; background: #f8fbfd; }
.portal-service-zones__icon { color: var(--portal-blue); }
.portal-service-zones__icon svg { width: 34px; height: 34px; }
.portal-service-zones h3 { margin: 0 0 6px; color: var(--portal-navy-deep); font-size: 17px; }
.portal-service-zones p { margin: 0; color: var(--portal-muted); font-size: 12px; line-height: 1.6; }
.portal-service-zones__arrow { color: #7890a7; }
.portal-information-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.portal-information-grid article { padding: 20px 22px 14px; border: 1px solid var(--portal-border); background: #fff; }
.portal-information-heading small { align-self: flex-start; padding: 3px 8px; color: #5f7081; border: 1px solid #c9d4df; background: #f5f7f9; font-size: 12px; }
.portal-information-grid ul { margin: 0; padding: 0; list-style: none; }
.portal-information-grid li { border-bottom: 1px dashed #d9e1e9; }
.portal-information-grid li:last-child { border-bottom: 0; }
.portal-information-grid li a { min-height: 45px; display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 16px; align-items: center; font-size: 14px; }
.portal-information-grid li a:hover span { color: var(--portal-blue); }
.portal-information-grid time { color: #748596; font-size: 12px; }
.portal-information-note { margin: 10px 0 0; color: #738292; font-size: 12px; }
.portal-information-loading, .portal-information-error { min-height: 190px; display: flex; align-items: center; justify-content: center; gap: 14px; color: var(--portal-muted); border: 1px solid var(--portal-border); background: #fff; }
.portal-information-error button { min-height: 36px; padding: 5px 14px; cursor: pointer; color: #fff; border: 0; background: var(--portal-navy); }
@media (max-width: 1024px) {
  .portal-quick-actions { grid-template-columns: repeat(2, 1fr); }
  .portal-quick-actions > a:nth-child(2) { border-right: 0; }
  .portal-quick-actions > a:nth-child(-n + 2) { border-bottom: 1px solid var(--portal-border); }
  .portal-service-zones { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .portal-home-search__inner { min-height: 270px; padding-block: 34px 28px; }
  .portal-ai-search { grid-template-columns: 1fr auto; }
  .portal-ai-search label { grid-column: 1 / -1; height: 34px; justify-content: center; border-right: 0; border-bottom: 1px solid var(--portal-border); }
  .portal-ai-search input, .portal-ai-search button { height: 50px; }
  .portal-information-grid { grid-template-columns: 1fr; }
}
@media (max-width: 520px) {
  .portal-home-search__lead { font-size: 14px; }
  .portal-ai-search { grid-template-columns: minmax(0, 1fr) 48px; }
  .portal-ai-search input { padding-inline: 12px; font-size: 13px; }
  .portal-ai-search button { min-width: 48px; font-size: 0; }
  .portal-ai-search button svg { width: 20px; height: 20px; }
  .portal-quick-actions, .portal-service-zones { grid-template-columns: 1fr; }
  .portal-quick-actions > a { border-right: 0; border-bottom: 1px solid var(--portal-border); }
  .portal-quick-actions > a:last-child { border-bottom: 0; }
  .portal-service-zones > a { min-height: 106px; }
  .portal-information-grid article { padding-inline: 15px; }
  .portal-information-grid li a { grid-template-columns: 1fr; gap: 1px; padding-block: 8px; }
}
</style>
