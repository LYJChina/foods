<script setup lang="ts">
import { computed, ref } from "vue";
import { Icon } from "@iconify/vue";
import { publicServices, serviceCategories, type ServiceCategory } from "./catalog";

const query = ref("");
const activeCategory = ref<ServiceCategory["id"] | "all">("all");
const filteredServices = computed(() => {
  const keyword = query.value.trim().toLowerCase();
  return publicServices.filter((service) => {
    const categoryMatch =
      activeCategory.value === "all" || service.categoryId === activeCategory.value;
    const text = [service.name, service.description, service.method, ...(service.keywords ?? [])]
      .join(" ")
      .toLowerCase();
    return categoryMatch && (!keyword || text.includes(keyword));
  });
});
function setCategory(category: ServiceCategory["id"] | "all") {
  activeCategory.value = category;
}
</script>

<template>
  <main class="portal-page portal-services-page">
    <div class="portal-container">
      <header class="portal-page__intro portal-services-intro">
        <span class="portal-section__kicker">公共 AI 服务</span>
        <h1>智能服务大厅</h1>
        <p>按服务类别选择办理事项。平台仅处理公开或低敏材料，不收集企业经营核心数据。</p>
      </header>
      <section class="service-toolbar" aria-label="服务筛选">
        <div class="service-tabs" role="tablist" aria-label="服务类别">
          <button
            type="button"
            :class="{ active: activeCategory === 'all' }"
            role="tab"
            :aria-selected="activeCategory === 'all'"
            @click="setCategory('all')"
          >
            全部服务
          </button>
          <button
            v-for="category in serviceCategories"
            :key="category.id"
            type="button"
            :class="{ active: activeCategory === category.id }"
            role="tab"
            :aria-selected="activeCategory === category.id"
            @click="setCategory(category.id)"
          >
            {{ category.name }}
          </button>
        </div>
        <label class="service-search"
          ><Icon icon="ri:search-line" aria-hidden="true" /><span class="sr-only">搜索服务</span
          ><input v-model="query" type="search" placeholder="搜索服务名称或关键词"
        /></label>
      </section>
      <div class="service-summary">
        <span>共 {{ filteredServices.length }} 项服务</span
        ><span
          >可办理
          {{ publicServices.filter((service) => service.status === "available").length }} 项</span
        >
      </div>
      <section class="portal-service-hall" aria-label="公共服务目录">
        <article
          v-for="service in filteredServices"
          :key="service.id"
          class="portal-service-hall__card"
        >
          <div class="portal-service-hall__heading">
            <div>
              <span class="service-card__category">{{
                serviceCategories.find((category) => category.id === service.categoryId)?.name
              }}</span>
              <h2>{{ service.name }}</h2>
            </div>
            <span
              class="portal-data-label"
              :class="{ 'portal-data-label--planned': service.status === 'planned' }"
              >{{ service.status === "available" ? "可办理" : "规划中" }}</span
            >
          </div>
          <p>{{ service.description }}</p>
          <dl>
            <div>
              <dt>办理方式</dt>
              <dd>{{ service.method }}</dd>
            </div>
            <div>
              <dt>支持材料</dt>
              <dd>{{ service.materials.join("、") }}</dd>
            </div>
          </dl>
          <RouterLink
            v-if="service.status === 'available' && service.route"
            class="portal-button portal-button--secondary"
            :to="service.route"
            >进入服务 <Icon icon="ri:arrow-right-line"
          /></RouterLink>
          <span v-else class="portal-service-hall__unavailable">该服务暂未开放办理</span>
        </article>
        <div v-if="filteredServices.length === 0" class="service-empty">
          <Icon icon="ri:search-eye-line" /><strong>未找到匹配服务</strong
          ><span>请尝试更换关键词或服务类别。</span>
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped lang="scss">
.portal-services-intro {
  margin-bottom: 22px;
}
.service-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-top: 1px solid var(--portal-border);
  border-bottom: 1px solid var(--portal-border);
}
.service-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.service-tabs button {
  min-height: 36px;
  padding: 6px 12px;
  cursor: pointer;
  color: #52667b;
  border: 1px solid transparent;
  background: transparent;
  font: inherit;
  font-size: 13px;
}
.service-tabs button:hover,
.service-tabs button.active {
  color: var(--portal-blue);
  border-color: #b8cede;
  background: #f1f7fb;
  font-weight: 700;
}
.service-search {
  display: flex;
  align-items: center;
  gap: 7px;
  width: 248px;
  min-height: 36px;
  padding: 0 10px;
  color: #718398;
  border: 1px solid #b7c6d4;
  background: #fff;
}
.service-search input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: 0;
  color: #24364b;
  background: transparent;
  font: inherit;
  font-size: 13px;
}
.service-summary {
  display: flex;
  gap: 16px;
  padding: 14px 0;
  color: #718398;
  font-size: 12px;
}
.service-summary span + span {
  padding-left: 16px;
  border-left: 1px solid #d6e0e8;
}
.service-card__category {
  display: block;
  margin-bottom: 3px;
  color: #718398;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.service-empty {
  grid-column: 1 / -1;
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 56px 24px;
  color: #718398;
  border: 1px solid var(--portal-border);
  background: #fff;
}
.service-empty svg {
  width: 28px;
  height: 28px;
  color: var(--portal-blue);
}
.service-empty strong {
  color: var(--portal-navy);
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
}
@media (max-width: 680px) {
  .service-toolbar {
    align-items: stretch;
    flex-direction: column;
  }
  .service-search {
    width: auto;
  }
}
</style>
