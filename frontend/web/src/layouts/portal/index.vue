<script setup lang="ts">
import { RouterView } from "vue-router";
</script>

<template>
  <div class="portal-layout">
    <div class="portal-layout__demo" role="status">DEMO 原型</div>
    <RouterView />
  </div>
</template>

<style scoped>
.portal-layout {
  min-height: 100vh;
  color: #172b4d;
  background: #f3f6fa;
}

.portal-layout__demo {
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  color: #fff;
  background: #174a82;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.08em;
}
</style>
