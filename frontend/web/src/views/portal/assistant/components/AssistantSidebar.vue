<script setup lang="ts">
import { Icon } from "@iconify/vue";

const items = [
  { label: "常见问题", icon: "ri:question-line" },
  { label: "热门服务", icon: "ri:service-line" },
  { label: "问答技巧", icon: "ri:lightbulb-line" },
];
</script>

<template>
  <aside class="public-assistant-sidebar" aria-label="问答辅助导航">
    <h2>服务导航</h2>
    <nav>
      <a v-for="item in items" :key="item.label" href="#assistant-conversation">
        <Icon :icon="item.icon" aria-hidden="true" /><span>{{ item.label }}</span>
      </a>
    </nav>
    <div class="public-assistant-sidebar__tip">
      <strong>提问建议</strong>
      <p>请说明事项、材料或目标市场等关键信息，避免提交配方、客户和订单数据。</p>
    </div>
  </aside>
</template>
