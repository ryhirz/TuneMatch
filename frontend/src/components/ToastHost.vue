<!-- 通用组件：Toast 提示容器 -->
<script setup lang="ts">
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()

const colorMap: Record<string, string> = {
  info: 'bg-ink text-white',
  success: 'bg-ai text-white',
  error: 'bg-danger text-white',
}
</script>

<template>
  <div class="fixed top-16 right-4 z-50 flex flex-col gap-2 pointer-events-none">
    <TransitionGroup name="toast">
      <div
        v-for="t in toast.items"
        :key="t.id"
        class="px-4 py-2 rounded-btn text-note flex items-center gap-2 shadow-none"
        :class="colorMap[t.type]"
      >
        <span>{{ t.text }}</span>
        <button class="opacity-70 hover:opacity-100 text-note" @click="toast.dismiss(t.id)">✕</button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.2s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(16px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(16px);
}
</style>
