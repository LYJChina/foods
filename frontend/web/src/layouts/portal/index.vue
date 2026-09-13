<script setup lang="ts">
import { Icon } from "@iconify/vue";
import { RouterView } from "vue-router";
</script>

<template>
  <div class="portal-layout">
    <a class="portal-skip-link" href="#portal-main">跳到主要内容</a>
    <header class="portal-header">
      <div class="portal-utility-bar">
        <div class="portal-container portal-utility-bar__inner">
          <span>食品行业公共服务平台</span>
          <span class="portal-utility-bar__links">
            <a href="#portal-main">无障碍浏览</a>
            <RouterLink to="/portal/guide">使用帮助</RouterLink>
          </span>
        </div>
      </div>
      <div class="portal-container portal-header__brand-row">
        <RouterLink
          class="portal-brand"
          to="/portal/home"
          aria-label="食品行业 AI 公共服务平台首页"
        >
          <span class="portal-brand__mark" aria-hidden="true"
            ><Icon icon="ri:seedling-line"
          /></span>
          <span
            ><small>食品行业公共服务</small
            ><strong>食品行业 AI 公共服务平台</strong></span
          >
        </RouterLink>
      </div>
      <nav class="portal-nav" aria-label="主导航">
        <div class="portal-container portal-nav__inner">
          <RouterLink to="/portal/home">首页</RouterLink>
          <RouterLink to="/portal/services">智能服务</RouterLink>
          <RouterLink to="/portal/records">办理记录</RouterLink>
          <RouterLink to="/portal/guide">使用指南</RouterLink>
        </div>
      </nav>
    </header>
    <div id="portal-main"><RouterView /></div>
    <footer class="portal-footer">
      <div class="portal-container portal-footer__inner">
        <p><strong>安全提示：</strong>不得上传配方、工艺、成本、客户、订单和生产经营数据。</p>
        <p>食品行业 AI 公共服务平台</p>
      </div>
    </footer>
  </div>
</template>

<style src="@/styles/portal.scss"></style>
