<!-- 歌单文本导入弹窗：从其他音乐软件（Spotify/网易云/QQ音乐）粘贴歌单
导入后：自动匹配曲库 → 展示曲风画像 + 创意视觉图 -->
<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/api'
import type { PlaylistImportResult } from '@/api/types'
import { useToastStore } from '@/stores/toast'

const emit = defineEmits<{ (e: 'imported'): void }>()
const toast = useToastStore()

const open = ref(false)
const name = ref('')
const text = ref('')
const loading = ref(false)
const result = ref<PlaylistImportResult | null>(null)
const error = ref('')

function show() {
  open.value = true
  name.value = ''
  text.value = ''
  result.value = null
  error.value = ''
}

function close() {
  open.value = false
  result.value = null
}

async function doImport() {
  if (!text.value.trim()) {
    toast.show('请先粘贴歌单内容', 'error')
    return
  }
  loading.value = true
  error.value = ''
  try {
    result.value = await api.importTextPlaylist({
      name: name.value.trim() || '导入歌单',
      text: text.value,
    })
    emit('imported')
    if (!result.value.art_svg) {
      toast.show(result.value.matched ? `已导入，匹配 ${result.value.matched} 首` : '没有匹配到曲库歌曲', result.value.matched ? 'success' : 'info', 2600)
    } else {
      toast.show(`导入成功！匹配 ${result.value.matched}/${result.value.total_items} 首`, 'success', 2400)
    }
  } catch (e) {
    error.value = (e as Error).message || '导入失败'
  } finally {
    loading.value = false
  }
}

defineExpose({ show })
</script>

<template>
  <!-- 弹层背景 -->
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" @click.self="close">
      <div class="w-full max-w-[680px] max-h-[88vh] overflow-y-auto bg-card rounded-r-lg shadow-hover p-6">
        <div class="flex items-center justify-between mb-5">
          <h3 class="text-[17px] font-semibold text-ink">📥 导入歌单</h3>
          <button class="w-8 h-8 rounded-full grid place-items-center text-ink-faint hover:bg-black/5" @click="close">
            <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M6 18L18 6" /></svg>
          </button>
        </div>

        <!-- 导入表单 -->
        <template v-if="!result">
          <label class="block text-[12px] text-ink-faint mb-1.5">歌单名称（可选）</label>
          <input
            v-model="name"
            class="w-full bg-bg border border-line rounded-r-sm px-3 py-2 text-[14px] text-ink placeholder:text-ink-faint focus:outline-none focus:border-brand mb-4"
            placeholder="如：我的深夜歌单"
          />
          <label class="block text-[12px] text-ink-faint mb-1.5">歌单内容（每行一首：歌名 - 歌手）</label>
          <textarea
            v-model="text"
            rows="8"
            class="w-full bg-bg border border-line rounded-r-sm px-3 py-2 text-[13px] text-ink font-mono placeholder:text-ink-faint focus:outline-none focus:border-brand resize-y"
            placeholder="晴天 - 周杰伦&#10;Viva La Vida - Coldplay&#10;海阔天空 - Beyond"
          />
          <p class="text-[11px] font-light text-ink-faint mt-1.5 mb-4">
            💡 支持 Spotify / 网易云 / QQ音乐 导出的歌单文本（歌名 - 歌手 或 tab 分隔），导入后自动在曲库匹配。
          </p>
          <div class="flex items-center gap-2">
            <button class="tm-btn" :disabled="loading" @click="doImport">
              {{ loading ? '导入分析中…' : '🚀 导入并生成视觉图' }}
            </button>
            <button class="tm-btn-ghost" @click="close">取消</button>
          </div>
          <p v-if="error" class="text-danger text-[12px] mt-3">{{ error }}</p>
        </template>

        <!-- 导入结果：视觉图 + 曲风画像 -->
        <div v-else class="flex flex-col gap-4">
          <div class="grid grid-cols-[160px_1fr] gap-4 max-[560px]:grid-cols-1">
            <!-- 创意视觉图 -->
            <div class="rounded-r-md overflow-hidden border border-line aspect-square" v-html="result.art_svg ? decodeURIComponent(result.art_svg) : '<div class=w-full h-full grid place-items-center text-ink-faint>无匹配</div>'" />
            <!-- 统计 -->
            <div class="flex flex-col gap-2">
              <p class="text-[15px] font-semibold text-ink">{{ result.playlist_name }}</p>
              <div class="flex gap-3 text-[12px]">
                <span class="text-ink-soft">匹配 <b class="text-brand">{{ result.matched }}/{{ result.total_items }}</b></span>
                <span v-if="result.unmatched_count" class="text-ink-faint">未匹配 {{ result.unmatched_count }}</span>
              </div>
              <!-- 曲风分布 -->
              <p class="text-[12px] text-ink-faint mt-1">主要曲风</p>
              <div class="flex flex-wrap gap-1.5">
                <span v-for="g in result.genre_dist.slice(0, 6)" :key="g.genre" class="text-[11px] bg-brand-soft text-brand rounded-pill px-2 py-0.5">
                  {{ g.genre }} × {{ g.count }}
                </span>
              </div>
              <!-- 情绪画像 -->
              <p v-if="result.mood_dist.length" class="text-[12px] text-ink-faint mt-1">情绪画像</p>
              <div class="flex flex-wrap gap-1.5">
                <span v-for="m in result.mood_dist.slice(0, 4)" :key="m.mood" class="text-[11px] bg-ai/10 text-ai rounded-pill px-2 py-0.5">
                  {{ m.mood }} × {{ m.count }}
                </span>
              </div>
              <!-- 平均时长 -->
              <p class="text-[11px] font-light text-ink-faint mt-1">
                平均时长 {{ Math.floor(result.profile.avg_duration_s / 60) }}:{{ String(result.profile.avg_duration_s % 60).padStart(2, '0') }} · 主曲风「{{ result.profile.primary_genre }}」
              </p>
            </div>
          </div>
          <!-- 未匹配提示 -->
          <p v-if="result.unmatched_count" class="text-[11px] font-light text-ink-faint">
            未匹配（{{ result.unmatched_count }} 首）：{{ result.unmatched.map((u) => u.title).slice(0, 8).join('、') }}{{ result.unmatched_count > 8 ? '…' : '' }}
          </p>
          <div class="flex items-center gap-2 mt-2">
            <button class="tm-btn" @click="close">完成</button>
            <button class="tm-btn-ghost" @click="result = null; text = ''">继续导入</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>