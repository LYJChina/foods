<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const title = computed(() => String(route.meta.title ?? "功能页"));
</script>

<template>
  <main class="portal-placeholder">
    <h1>{{ title }}</h1>
    <p>本页面为 DEMO 原型占位，将在后续增量中完成交互。</p>
  </main>
</template>

<style scoped>
.portal-placeholder {
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
  padding: 64px 0;
  font-size: 16px;
  line-height: 1.6;
}
</style>
