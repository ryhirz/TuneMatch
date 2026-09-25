<!-- 拖拽上传区：批量导入本地歌曲（mp3/wav/flac/m4a/ogg/aac）
- 多文件拖拽 / 点击选择
- 实时上传进度
- 非音频文件明确提示并拒绝 -->
<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/api'
import type { ImportResult } from '@/api/types'
import { useToastStore } from '@/stores/toast'

const props = defineProps<{ playlistId: number }>()
const emit = defineEmits<{ (e: 'imported', result: ImportResult): void }>()

const toast = useToastStore()

const dragging = ref(false)
const importing = ref(false)
const progress = ref(0)
const currentFile = ref('')

const AUDIO_EXTS = ['mp3', 'wav', 'flac', 'm4a', 'ogg', 'aac', 'wma']
const AUDIO_MIMES = ['audio/', 'video/x-m4a', 'application/octet-stream']

function extOf(name: string): string {
  return (name.split('.').pop() || '').toLowerCase()
}

function isAudio(file: File): boolean {
  return AUDIO_EXTS.includes(extOf(file.name)) || AUDIO_MIMES.some((m) => file.type.startsWith(m))
}

function onDrop(e: DragEvent) {
  dragging.value = false
  const files = Array.from(e.dataTransfer?.files || [])
  if (!files.length) return
  handleFiles(files)
}

function onPick(e: Event) {
  const files = Array.from((e.target as HTMLInputElement).files || [])
  ;(e.target as HTMLInputElement).value = ''
  if (!files.length) return
  handleFiles(files)
}

function handleFiles(files: File[]) {
  // 1. 前置校验：非音频文件当场提示并拒绝
  const audio = files.filter(isAudio)
  const rejected = files.filter((f) => !isAudio(f))
  for (const f of rejected) {
    toast.show(`已拒绝「${f.name}」：非音频文件，仅支持 mp3/wav/flac/m4a/ogg/aac`, 'error', 3600)
  }
  if (!audio.length) return

  // 2. 逐文件上传（后端多文件接口，进度按整体）
  importing.value = true
  progress.value = 0
  currentFile.value = audio[0].name
  api
    .importSongs(props.playlistId, audio, (pct) => {
      progress.value = pct
    })
    .then((result) => {
      toast.show(
        `成功导入 ${result.imported_count} 首${result.rejected_count ? `，拒绝 ${result.rejected_count} 个` : ''}`,
        'success',
      )
      emit('imported', result)
    })
    .catch((e: Error) => toast.show(e.message || '导入失败', 'error'))
    .finally(() => {
      importing.value = false
      progress.value = 0
    })
}
</script>

<template>
  <div
    class="relative rounded-r-lg border-2 border-dashed transition-all duration-300 p-6 text-center cursor-pointer"
    :class="dragging ? 'border-brand bg-brand/5' : 'border-line bg-card hover:border-brand/40'"
    @dragover.prevent="dragging = true"
    @dragleave="dragging = false"
    @drop.prevent="onDrop"
    @click="($refs.fileInput as HTMLInputElement)?.click()"
  >
    <input ref="fileInput" type="file" multiple accept=".mp3,.wav,.flac,.m4a,.ogg,.aac,.wma" class="hidden" @change="onPick" />

    <!-- 导入中：进度条 -->
    <div v-if="importing" class="flex flex-col items-center gap-3">
      <div class="w-10 h-10 rounded-pill bg-brand text-white grid place-items-center">
        <svg viewBox="0 0 24 24" class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M12 3a9 9 0 109 9" />
        </svg>
      </div>
      <p class="text-[13px] text-ink">正在上传… {{ progress }}%</p>
      <div class="w-full max-w-xs h-1.5 bg-bg rounded-pill overflow-hidden">
        <div class="h-full bg-brand rounded-pill transition-all duration-200" :style="{ width: `${progress}%` }" />
      </div>
      <p class="text-[11px] font-light text-ink-faint">{{ currentFile }}</p>
    </div>

    <!-- 空闲态 -->
    <div v-else class="flex flex-col items-center gap-2">
      <div class="w-11 h-11 rounded-pill bg-brand-soft text-brand grid place-items-center">
        <svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 16V4M7 9l5-5 5 5M4 17v2a1 1 0 001 1h14a1 1 0 001-1v-2" />
        </svg>
      </div>
      <p class="text-[14px] text-ink font-medium">拖拽音频文件到这里，或点击选择</p>
      <p class="text-[12px] font-light text-ink-faint">支持批量导入 · mp3 / wav / flac / m4a / ogg / aac</p>
    </div>
  </div>
</template>
