<!-- 通用确认对话框：标题 / 描述 / 自定义图标 / 操作按钮（替代原生 confirm） -->
<script setup lang="ts">
defineProps<{
  open: boolean
  title: string
  message?: string
  confirmText?: string
  cancelText?: string
  danger?: boolean
}>()
const emit = defineEmits<{ (e: 'confirm'): void; (e: 'cancel'): void }>()
</script>

<template>
  <Transition name="modal">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4 backdrop-blur-[2px]"
      @click.self="emit('cancel')"
    >
      <div class="bg-card rounded-r-lg p-6 w-full max-w-sm shadow-hover">
        <div class="flex items-start gap-3 mb-5">
          <div
            v-if="danger"
            class="w-10 h-10 rounded-full bg-danger-soft grid place-items-center shrink-0"
          >
            <svg viewBox="0 0 24 24" class="w-5 h-5 text-danger" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 9v4M12 17v.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            </svg>
          </div>
          <div v-else class="w-10 h-10 rounded-full bg-brand-soft grid place-items-center shrink-0">
            <svg viewBox="0 0 24 24" class="w-5 h-5 text-brand" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17h.01" />
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="text-[15px] font-semibold text-ink leading-tight">{{ title }}</h3>
            <p v-if="message" class="text-[13px] font-light text-ink-soft mt-1.5 leading-relaxed">{{ message }}</p>
          </div>
        </div>

        <div class="flex items-center gap-2 justify-end">
          <button class="tm-btn-ghost !px-4" @click="emit('cancel')">
            {{ cancelText || '取消' }}
          </button>
          <button
            :class="danger ? 'tm-btn-danger !px-5' : 'tm-btn !px-5'"
            @click="emit('confirm')"
          >
            {{ confirmText || '确定' }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>