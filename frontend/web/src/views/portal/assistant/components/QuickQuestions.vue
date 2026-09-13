<script setup lang="ts">
defineProps<{ questions: string[] }>();
defineEmits<{ select: [question: string] }>();
</script>

<template>
  <div class="public-assistant-quick" aria-label="快捷问题">
    <button
      v-for="question in questions"
      :key="question"
      type="button"
      @click="$emit('select', question)"
    >
      {{ question }}
    </button>
  </div>
</template>
