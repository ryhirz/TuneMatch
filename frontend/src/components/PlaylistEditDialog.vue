<!-- 歌单编辑弹窗：改名 + 头像上传（本地图片校验）+ 8 色封面 + 删除（Apple 风格）
- 头像上传由弹窗内部调用 api.uploadCover,自管 uploading/uploadPct
- 上传成功 emit 'cover-uploaded' 让 parent 刷新歌单列表 -->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { api } from '@/api'
import type { Playlist } from '@/api/types'
import { useToastStore } from '@/stores/toast'

const props = defineProps<{ playlist: Playlist | null }>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', patch: { name: string; cover_color: string }): void
  (e: 'cover-uploaded'): void
  (e: 'delete'): void
}>()

const toast = useToastStore()

const name = ref('')
const coverColor = ref('#4DABF7')
const coverUrl = ref('')
const uploading = ref(false)
const uploadPct = ref(0)

const COVER_COLORS = [
  '#FF6B6B', '#FFA94D', '#FFD43B', '#69DB7C',
  '#38D9A9', '#4DABF7', '#748FFC', '#F783AC',
]

watch(
  () => props.playlist,
  (p) => {
    if (p) {
      name.value = p.name
      coverColor.value = p.cover_color || '#4DABF7'
      coverUrl.value = p.cover_url || ''
      uploading.value = false
      uploadPct.value = 0
    }
  },
  { immediate: true },
)

const ALLOWED = ['image/png', 'image/jpeg', 'image/webp']
const MAX_SIZE = 2 * 1024 * 1024

async function pickCover(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return

  if (!ALLOWED.includes(file.type)) {
    toast.show('不支持的图片格式，仅支持 png/jpg/jpeg/webp', 'error')
    return
  }
  if (file.size > MAX_SIZE) {
    toast.show(`图片过大（${(file.size / 1024 / 1024).toFixed(1)}MB），请上传 2MB 以内`, 'error')
    return
  }
  if (!props.playlist) return

  // 本地预览
  const objectUrl = URL.createObjectURL(file)
  coverUrl.value = objectUrl
  uploading.value = true
  uploadPct.value = 0

  try {
    await api.uploadCover(props.playlist.id, file, (pct) => {
      uploadPct.value = pct
    })
    toast.show('头像已更新', 'success')
    uploadPct.value = 100
    emit('cover-uploaded')
  } catch (err) {
    // 失败：回退到旧头像 + 释放预览 URL
    URL.revokeObjectURL(objectUrl)
    coverUrl.value = props.playlist.cover_url || ''
    toast.show((err as Error).message || '头像上传失败', 'error')
  } finally {
    // 关键：必须把 uploading 复位，否则一直转圈
    setTimeout(() => {
      uploading.value = false
      uploadPct.value = 0
    }, 600) // 短暂显示 100% 后再隐藏
  }
}

function save() {
  if (!name.value.trim()) return
  emit('save', { name: name.value.trim(), cover_color: coverColor.value })
}
</script>

<template>
  <Transition name="modal">
    <div
      v-if="playlist"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4 backdrop-blur-[2px]"
      @click.self="emit('close')"
    >
      <div class="bg-card rounded-r-lg p-6 w-full max-w-sm shadow-hover">
        <div class="flex items-center justify-between mb-5">
          <h3 class="text-h3 text-ink">编辑歌单</h3>
          <button class="text-ink-faint hover:text-ink" @click="emit('close')">✕</button>
        </div>

        <!-- 头像 + 上传 -->
        <div class="flex items-center gap-4 mb-5">
          <div class="relative group shrink-0">
            <div
              class="w-16 h-16 rounded-r-md grid place-items-center text-white text-2xl font-bold overflow-hidden"
              :style="coverUrl ? {} : { background: `linear-gradient(150deg, ${coverColor}, ${coverColor}aa)` }"
            >
              <img v-if="coverUrl" :src="coverUrl" class="w-full h-full object-cover" alt="头像" />
              <span v-else>{{ name.slice(0, 1) || '♪' }}</span>
              <div
                v-if="uploading"
                class="absolute inset-0 bg-black/55 grid place-items-center text-white text-[11px] font-semibold"
              >
                {{ uploadPct }}%
              </div>
            </div>
            <button
              class="absolute -bottom-1.5 -right-1.5 w-7 h-7 rounded-full bg-ink text-white grid place-items-center opacity-90 hover:opacity-100 transition-opacity disabled:opacity-40"
              title="上传本地图片"
              :disabled="uploading"
              @click="($refs.coverInput as HTMLInputElement)?.click()"
            >
              <svg viewBox="0 0 24 24" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 5v14M5 12h14" />
              </svg>
            </button>
            <input ref="coverInput" type="file" accept="image/png,image/jpeg,image/webp" class="hidden" @change="pickCover" />
          </div>

          <div class="flex-1">
            <p class="text-[12px] text-ink-faint mb-1.5">封面颜色（无自定义头像时显示）</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="c in COVER_COLORS"
                :key="c"
                class="w-7 h-7 rounded-full transition-transform hover:scale-110"
                :class="{ 'ring-2 ring-offset-2 ring-ink': coverColor === c && !coverUrl }"
                :style="{ backgroundColor: c }"
                @click="coverUrl = ''; coverColor = c"
              />
            </div>
          </div>
        </div>

        <!-- 歌单名 -->
        <label class="block text-[12px] text-ink-faint mb-1.5">歌单名称</label>
        <input
          v-model="name"
          class="w-full bg-bg border border-line rounded-r-sm px-3 py-2 text-[15px] text-ink placeholder:text-ink-faint focus:outline-none focus:border-brand mb-5"
          placeholder="歌单名称"
          @keyup.enter="save"
        />

        <div class="flex items-center gap-2">
          <button class="tm-btn-danger !px-4" :disabled="uploading" @click="emit('delete')">删除</button>
          <div class="flex-1" />
          <button class="tm-btn-ghost !px-4" @click="emit('close')">取消</button>
          <button class="tm-btn !px-5" :disabled="!name.trim() || uploading" @click="save">保存</button>
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