<script setup lang="ts">
import { Icon } from "@iconify/vue";
import { RouterView } from "vue-router";

import PortalAssistant from "@/views/portal/components/PortalAssistant.vue";
</script>

<template>
  <div class="portal-layout">
    <a class="portal-skip-link" href="#portal-main">跳到主要内容</a>
    <header class="portal-header">
      <div class="portal-container portal-header__brand-row">
        <RouterLink class="portal-brand" to="/portal/home" aria-label="潮州市食品行业 AI 公共服务平台首页">
          <span class="portal-brand__mark" aria-hidden="true"><Icon icon="ri:seedling-line" /></span>
          <span><small>食品行业·政务公共服务 Demo</small><strong>潮州市食品行业 AI 公共服务平台</strong></span>
        </RouterLink>
        <span class="portal-demo-badge" role="status">DEMO 原型</span>
      </div>
      <nav class="portal-nav" aria-label="主导航">
        <div class="portal-container portal-nav__inner">
          <RouterLink to="/portal/home">首页</RouterLink>
          <RouterLink to="/portal/documents">智能文档解析</RouterLink>
          <RouterLink to="/portal/precheck">出口合规预检</RouterLink>
          <RouterLink to="/portal/scenarios">场景 Demo</RouterLink>
          <RouterLink to="/portal/diagnosis">数智化诊断</RouterLink>
        </div>
      </nav>
    </header>
    <div id="portal-main"><RouterView /></div>
    <footer class="portal-footer">
      <div class="portal-container portal-footer__inner">
        <p><strong>提示：</strong>本平台为公共服务 AI 能力演示原型，不得上传企业核心数据。</p>
        <p>demo v0.1·潮州市食品行业 AI 公共服务平台</p>
      </div>
    </footer>
    <PortalAssistant />
  </div>
</template>

<style src="@/styles/portal.scss"></style>
