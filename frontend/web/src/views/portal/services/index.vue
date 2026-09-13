<script setup lang="ts">
import { publicServices } from "./catalog";
</script>

<template>
  <main class="portal-page">
    <div class="portal-container">
      <header class="portal-page__intro">
        <span class="portal-section__kicker">公共 AI 服务</span>
        <h1>智能服务大厅</h1>
        <p>请选择适合的公共服务。平台仅处理公开或低敏材料，不收集企业经营核心数据。</p>
      </header>

      <section class="portal-service-hall" aria-label="公共服务目录">
        <article v-for="service in publicServices" :key="service.id" class="portal-service-hall__card">
          <div class="portal-service-hall__heading">
            <h2>{{ service.name }}</h2>
            <span class="portal-data-label" :class="{ 'portal-data-label--planned': service.status === 'planned' }">
              {{ service.status === "available" ? "可办理" : "规划中" }}
            </span>
          </div>
          <p>{{ service.description }}</p>
          <dl>
            <div><dt>办理方式</dt><dd>{{ service.method }}</dd></div>
            <div><dt>支持材料</dt><dd>{{ service.materials.join("、") }}</dd></div>
          </dl>
          <RouterLink v-if="service.status === 'available' && service.route" class="portal-button portal-button--secondary" :to="service.route">
            进入服务
          </RouterLink>
          <span v-else class="portal-service-hall__unavailable">该服务暂未开放办理</span>
        </article>
      </section>
    </div>
  </main>
</template>
