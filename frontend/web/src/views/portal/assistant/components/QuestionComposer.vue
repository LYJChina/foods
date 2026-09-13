<script setup lang="ts">
import { Icon } from "@iconify/vue";

defineProps<{ modelValue: string; submitting: boolean; retry: boolean }>();
defineEmits<{ "update:modelValue": [value: string]; submit: [] }>();
</script>

<template>
  <form class="public-assistant-composer" @submit.prevent="$emit('submit')">
    <label for="public-assistant-question">请输入您要咨询的问题</label>
    <div>
      <textarea
        id="public-assistant-question"
        :value="modelValue"
        :disabled="submitting"
        maxlength="2000"
        rows="3"
        placeholder="例如：出口合规需要准备哪些材料？"
        @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
        @keydown.ctrl.enter.prevent="$emit('submit')"
      ></textarea>
      <button type="submit" :disabled="submitting || !modelValue.trim()">
        <Icon :icon="retry ? 'ri:refresh-line' : 'ri:send-plane-2-line'" aria-hidden="true" />
        {{ retry ? "重新发送" : submitting ? "发送中" : "发送问题" }}
      </button>
    </div>
    <small>按 Ctrl + Enter 发送，问题最长 2000 字。</small>
  </form>
</template>
