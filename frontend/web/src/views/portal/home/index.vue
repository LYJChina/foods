<script setup lang="ts">
import { Icon } from "@iconify/vue";

import { coverageItems, portalMetrics, portalServices } from "../content";
</script>

<template>
  <main class="portal-home">
    <section class="portal-hero">
      <div class="portal-container portal-hero__grid">
        <div class="portal-hero__copy">
          <span class="portal-eyebrow">潮州食品产业·公共 AI 服务</span>
          <h1>让食品企业看得见 AI、用得上、接得住 AI</h1>
          <p>
            面向糖果、休闲食品、卤制品、保健食品等企业，提供不依赖企业核心数据的公共能力、出口合规辅助与场景验证入口。
          </p>
          <div class="portal-hero__actions">
            <RouterLink class="portal-button portal-button--primary" to="/portal/precheck">
              开始出口合规预检 <Icon icon="ri:arrow-right-line" aria-hidden="true" />
            </RouterLink>
            <RouterLink class="portal-button portal-button--secondary" to="/portal/scenarios">查看场景 Demo</RouterLink>
            <RouterLink class="portal-button portal-button--secondary" to="/portal/documents">智能文档解析</RouterLink>
          </div>
        </div>
        <aside class="portal-hero__boundary" aria-label="数据边界说明">
          <Icon icon="ri:shield-keyhole-line" aria-hidden="true" />
          <h2>企业核心数据不进入平台</h2>
          <p>请仅使用标签、包装、规格书等低敏材料。配方、工艺、成本、客户、订单和生产经营数据请保留在企业侧。</p>
        </aside>
      </div>
    </section>

    <section class="portal-container portal-section" aria-labelledby="service-title">
      <div class="portal-section__heading">
        <div><span class="portal-section__kicker">我要解决什么问题</span><h2 id="service-title">四类公共服务</h2></div>
        <p>先看、先试、再决定是否开展企业侧建设。</p>
      </div>
      <div class="portal-service-grid">
        <article v-for="service in portalServices" :key="service.title" class="portal-service-card" :class="`portal-service-card--${service.tone}`" data-testid="service-card">
          <span class="portal-service-card__icon" aria-hidden="true"><Icon :icon="service.icon" /></span>
          <h3>{{ service.title }}</h3>
          <p>{{ service.description }}</p>
          <RouterLink :to="service.to">{{ service.action }} <Icon icon="ri:arrow-right-line" aria-hidden="true" /></RouterLink>
        </article>
      </div>
    </section>

    <section class="portal-overview">
      <div class="portal-container portal-section">
        <div class="portal-section__heading">
          <div><span class="portal-section__kicker">一期 Demo 范围</span><h2>公共能力一览</h2></div>
          <span class="portal-data-label">演示数据，非实时统计</span>
        </div>
        <dl class="portal-metrics">
          <div v-for="metric in portalMetrics" :key="metric.label"><dt>{{ metric.value }}</dt><dd>{{ metric.label }}</dd></div>
        </dl>
        <div class="portal-dashboard">
          <article class="portal-panel">
            <h3>重点细分方向·公共知识覆盖示意</h3>
            <ul class="portal-bars">
              <li v-for="item in coverageItems" :key="item.label">
                <span>{{ item.label }}</span><span class="portal-bars__track"><i :style="{ width: `${item.value}%` }"></i></span><strong>{{ item.level }}</strong>
              </li>
            </ul>
          </article>
          <article class="portal-panel">
            <h3>平台能力输出方式</h3>
            <div class="portal-output">
              <div class="portal-output__ring" role="img" aria-label="直接在线使用与通过 API MCP Skill 开放调用两种方式"><span>2<small>种方式</small></span></div>
              <ul><li><i class="is-blue"></i><span><strong>在线直接使用</strong><small>面向普通中小企业</small></span></li><li><i class="is-green"></i><span><strong>开放能力调用</strong><small>API / MCP / Skill 规划边界</small></span></li></ul>
            </div>
          </article>
        </div>
      </div>
    </section>
  </main>
</template>
