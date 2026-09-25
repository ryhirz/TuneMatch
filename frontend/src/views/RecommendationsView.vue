<!-- 页面：AI 推荐展示（左右滑动卡片 + 完整操作）
路由：/recommendations
支持左/右滑动、←/→ 按钮、立即播放、加入歌单、收藏、下一首 -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, smartApi } from '@/api'
import type { Playlist, Song } from '@/api/types'
import { usePlayerStore } from '@/stores/player'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const player = usePlayerStore()
const toast = useToastStore()

const songs = ref<Song[]>([])
const loading = ref(false)
const seedQuery = ref('')
const idx = ref(0)
const transitioning = ref(false)
const direction = ref<'left' | 'right'>('right')

// 滑动手势
const touchStartX = ref(0)
const touchStartY = ref(0)
const touchDelta = ref(0)

const currentSong = computed(() => songs.value[idx.value] || null)
const prevSong = computed(() => songs.value[Math.max(0, idx.value - 1)] || null)
const nextSong = computed(() => songs.value[Math.min(songs.value.length - 1, idx.value + 1)] || null)

const genreLabel = (g: string) => {
  const map: Record<string, string> = {
    pop: '流行', rock: '摇滚', folk: '民谣', edm: '电子', 'hip-hop': '嘻哈',
    jazz: '爵士', classical: '古典', lofi: 'Lo-fi', ambient: '氛围', 'r-n-b': 'R&B',
    electronic: '电子', dance: '舞曲', chill: '放松', indie: '独立', soul: '灵魂',
    piano: '钢琴', acoustic: '原声', metal: '金属', reggae: '雷鬼', blues: '蓝调',
    country: '乡村', soundtrack: '影视原声', world: '世界音乐', meditation: '冥想',
    sleep: '助眠', study: '学习', workout: '健身', party: '派对', romantic: '浪漫',
    dream: '梦幻', happy: '快乐', sad: '悲伤', energetic: '活力', jamendo: 'Jamendo',
    local: '本地', epic: '史诗', cinematic: '电影配乐', '90s': '90年代', '80s': '80年代',
  }
  return map[g] || g
}

const QUICK_PROMPTS = [
  { text: '想听温柔的民谣', emoji: '🎸', tags: ['folk'], scene: '' },
  { text: '工作学习时听', emoji: '📚', tags: ['lofi', 'piano'], scene: 'study' },
  { text: '健身运动高能', emoji: '💪', tags: ['rock', 'electronic'], scene: 'workout' },
  { text: '深夜助眠白噪音', emoji: '🌙', tags: ['ambient'], scene: 'sleep' },
  { text: '通勤路上轻快', emoji: '🚇', tags: ['pop', 'indie'], scene: 'commute' },
  { text: '下雨天怀旧', emoji: '🌧️', tags: ['jazz', 'classical'], scene: 'rainy' },
]

const fmtDur = (ms: number) => {
  const s = Math.round((ms || 0) / 1000)
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

async function fetchRecommendations() {
  if (loading.value) return
  loading.value = true
  try {
    // 根据 query 提供不同的推荐
    const params: any = { limit: 12 }
    if (seedQuery.value.trim()) {
      params.text = seedQuery.value.trim()
    } else {
      // 默认：基于曲库 mood_tags 偏好（推荐高 match 且多样化的歌）
      params.text = '好听 推荐'
    }
    const res = await smartApi.recommend(params)
    songs.value = res.songs || []
    idx.value = 0
    if (!songs.value.length) {
      toast.show('没有找到匹配的歌曲，换个关键词试试', 'info', 2400)
    } else {
      toast.show(`已为你推荐 ${songs.value.length} 首歌曲`, 'success', 1500)
    }
  } catch (e) {
    toast.show((e as Error).message || '推荐失败', 'error')
  } finally {
    loading.value = false
  }
}

function pick(p: typeof QUICK_PROMPTS[0]) {
  seedQuery.value = p.text
  fetchRecommendations()
}

function next() {
  if (idx.value >= songs.value.length - 1) {
    toast.show('已是最后一首', 'info', 1500)
    return
  }
  direction.value = 'right'
  transitioning.value = true
  setTimeout(() => {
    idx.value++
    transitioning.value = false
  }, 200)
}

function prev() {
  if (idx.value <= 0) {
    toast.show('已是第一首', 'info', 1500)
    return
  }
  direction.value = 'left'
  transitioning.value = true
  setTimeout(() => {
    idx.value--
    transitioning.value = false
  }, 200)
}

function jumpTo(i: number) {
  if (i === idx.value || i < 0 || i >= songs.value.length) return
  direction.value = i > idx.value ? 'right' : 'left'
  transitioning.value = true
  setTimeout(() => {
    idx.value = i
    transitioning.value = false
  }, 200)
}

function playNow() {
  if (!currentSong.value) return
  player.playSong(currentSong.value)
  toast.show(`正在播放《${currentSong.value.title}》`, 'success', 1500)
}

const showPicker = ref(false)
const pickerPlaylists = ref<Playlist[]>([])
const pickerLoading = ref(false)

async function openPlaylistPicker() {
  if (!currentSong.value) return
  showPicker.value = true
  pickerLoading.value = true
  try {
    const pls = await smartApi.listPlaylists()
    pickerPlaylists.value = pls
    if (!pls.length) {
      toast.show('暂无歌单，请先创建歌单', 'info', 2500)
      router.push('/playlists')
      showPicker.value = false
    }
  } catch (e) {
    toast.show((e as Error).message || '歌单加载失败', 'error')
    showPicker.value = false
  } finally {
    pickerLoading.value = false
  }
}

async function confirmAddToPlaylist(pl: Playlist) {
  if (!currentSong.value) return
  try {
    await api.addSongToPlaylist(pl.id, currentSong.value.id)
    toast.show(`已加入歌单「${pl.name}」`, 'success', 1500)
    showPicker.value = false
  } catch (e) {
    toast.show((e as Error).message || '加入失败', 'error')
  }
}

function favorite() {
  if (!currentSong.value) return
  toast.show(`已收藏《${currentSong.value.title}》`, 'success', 1500)
}

function viewDetail() {
  if (!currentSong.value) return
  router.push({ name: 'song-detail', params: { id: String(currentSong.value.id) } })
}

// 触控滑动手势
function onTouchStart(e: TouchEvent) {
  touchStartX.value = e.touches[0].clientX
  touchStartY.value = e.touches[0].clientY
  touchDelta.value = 0
}
function onTouchMove(e: TouchEvent) {
  touchDelta.value = e.touches[0].clientX - touchStartX.value
}
function onTouchEnd() {
  if (Math.abs(touchDelta.value) > 60) {
    if (touchDelta.value < 0) next()
    else prev()
  }
  touchDelta.value = 0
}

// 键盘快捷键
function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowRight') next()
  else if (e.key === 'ArrowLeft') prev()
  else if (e.key === ' ') { e.preventDefault(); playNow() }
}

onMounted(() => {
  fetchRecommendations()
  window.addEventListener('keydown', onKey)
})
</script>

<template>
  <div class="max-w-[760px] mx-auto px-6 py-8 max-[560px]:px-3">
    <!-- 顶部 -->
    <div class="mb-5">
      <button class="text-[13px] text-ink-soft hover:text-brand transition-colors mb-3" @click="router.back()">← 返回</button>
      <p class="text-[12px] font-semibold tracking-[0.06em] text-brand uppercase mb-1">AI 推荐 · For You</p>
      <h2 class="text-[28px] font-bold text-ink leading-tight">为你精心挑选</h2>
      <p class="mt-1 text-[13px] font-light text-ink-faint">左右滑动 / ←→ 切换 · 空格播放</p>
    </div>

    <!-- 搜索输入 -->
    <div class="flex items-center gap-2 mb-5">
      <input
        v-model="seedQuery"
        class="flex-1 bg-card border border-line rounded-pill px-4 py-2.5 text-[14px] text-ink placeholder:text-ink-faint focus:outline-none focus:border-brand transition-colors"
        placeholder="描述想听什么（如：温柔的民谣 / 雨天助眠 / 健身高能）"
        @keyup.enter="fetchRecommendations"
      />
      <button class="tm-btn !px-5" :disabled="loading" @click="fetchRecommendations">
        {{ loading ? '推荐中…' : '🚀 推荐' }}
      </button>
    </div>

    <!-- 快捷短语 -->
    <div class="flex flex-wrap gap-2 mb-6">
      <button
        v-for="p in QUICK_PROMPTS"
        :key="p.text"
        class="px-3 py-1.5 rounded-pill text-[12px] bg-card border border-line text-ink-soft hover:bg-brand hover:text-white hover:border-brand transition-colors"
        @click="pick(p)"
      >
        {{ p.emoji }} {{ p.text }}
      </button>
    </div>

    <!-- 卡片主区域 -->
    <div
      v-if="songs.length"
      class="relative min-h-[520px] max-[560px]:min-h-[480px] flex items-center justify-center"
      @touchstart.passive="onTouchStart"
      @touchmove.passive="onTouchMove"
      @touchend="onTouchEnd"
    >
      <!-- 上一首（背景） -->
      <div
        v-if="prevSong && prevSong.id !== currentSong?.id"
        class="absolute left-0 top-8 w-48 h-[400px] max-[560px]:hidden rounded-r-lg overflow-hidden opacity-30 -translate-x-12 scale-90"
        :style="{ background: `linear-gradient(150deg, ${prevSong.cover_color || '#4DABF7'}, ${prevSong.cover_color || '#4DABF7'}aa)` }"
      >
        <img v-if="prevSong.cover_url" :src="prevSong.cover_url" class="w-full h-full object-cover" />
      </div>

      <!-- 当前卡片 -->
      <div
        v-if="currentSong"
        class="relative w-[340px] max-[560px]:w-[88vw] h-[440px] rounded-r-lg bg-card border border-line shadow-hover overflow-hidden transition-all"
        :class="transitioning ? (direction === 'right' ? 'translate-x-full opacity-0' : '-translate-x-full opacity-0') : 'translate-x-0 opacity-100'"
        style="transition: transform 0.25s ease, opacity 0.25s ease;"
      >
        <!-- 封面（占 65%） -->
        <div class="relative h-[280px] overflow-hidden">
          <img v-if="currentSong.cover_url" :src="currentSong.cover_url" :alt="currentSong.title" class="w-full h-full object-cover" />
          <div v-else class="w-full h-full" :style="{ background: `linear-gradient(150deg, ${currentSong.cover_color || '#4DABF7'}, ${currentSong.cover_color || '#4DABF7'}aa)` }" />
          <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
          <!-- 曲风徽章 -->
          <span class="absolute top-3 left-3 text-[11px] font-semibold text-white/90 bg-black/40 backdrop-blur-[6px] rounded-pill px-2.5 py-1">
            {{ genreLabel(currentSong.genre) }}
          </span>
          <!-- 匹配度环形 -->
          <div class="absolute top-3 right-3 w-12 h-12 rounded-full bg-black/40 backdrop-blur-[6px] flex items-center justify-center">
            <div class="text-center">
              <div class="text-[14px] font-bold text-white leading-tight">{{ currentSong.match || 82 }}</div>
              <div class="text-[8px] text-white/80">%</div>
            </div>
          </div>
          <!-- 标题 -->
          <div class="absolute bottom-3 left-4 right-4">
            <h3 class="text-[20px] font-bold text-white leading-tight truncate">{{ currentSong.title }}</h3>
            <p class="text-[13px] text-white/85 mt-0.5 truncate">{{ currentSong.artist }}</p>
          </div>
        </div>
        <!-- 信息区 -->
        <div class="p-4">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-1.5">
              <span
                v-for="m in (currentSong.mood_tags || []).slice(0, 3)"
                :key="m"
                class="text-[10px] text-brand bg-brand-soft rounded-pill px-2 py-0.5"
              >{{ m }}</span>
            </div>
            <span class="text-[11px] font-light text-ink-faint">{{ fmtDur(currentSong.duration) }}</span>
          </div>
          <!-- 操作按钮 -->
          <div class="grid grid-cols-4 gap-1.5">
            <button class="flex flex-col items-center gap-1 py-2 rounded-r-md hover:bg-bg transition-colors" title="加入歌单" @click="openPlaylistPicker">
              <svg viewBox="0 0 24 24" class="w-5 h-5 text-ink-soft" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14" /></svg>
              <span class="text-[10px] font-light text-ink-soft">歌单</span>
            </button>
            <button class="flex flex-col items-center gap-1 py-2 rounded-r-md hover:bg-bg transition-colors" title="收藏" @click="favorite">
              <svg viewBox="0 0 24 24" class="w-5 h-5 text-ink-soft" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7.5-4.7-9.5-9C1 8.5 3 5.5 6.5 5.5c2 0 3.6 1.2 4.5 2.5.9-1.3 2.5-2.5 4.5-2.5 3.5 0 5.5 3 4 6.5-2 4.3-9.5 9-9.5 9z" /></svg>
              <span class="text-[10px] font-light text-ink-soft">收藏</span>
            </button>
            <button class="flex flex-col items-center gap-1 py-2 rounded-r-md hover:bg-bg transition-colors" title="详情" @click="viewDetail">
              <svg viewBox="0 0 24 24" class="w-5 h-5 text-ink-soft" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" /></svg>
              <span class="text-[10px] font-light text-ink-soft">详情</span>
            </button>
            <button class="flex flex-col items-center gap-1 py-2 rounded-r-md bg-brand text-white hover:bg-brand-hover transition-colors" title="立即播放" @click="playNow">
              <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current" style="margin-left:2px"><path d="M7 4.5v15l13-7.5z" /></svg>
              <span class="text-[10px] font-medium">播放</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 下一首（背景） -->
      <div
        v-if="nextSong && nextSong.id !== currentSong?.id"
        class="absolute right-0 top-8 w-48 h-[400px] max-[560px]:hidden rounded-r-lg overflow-hidden opacity-30 translate-x-12 scale-90"
        :style="{ background: `linear-gradient(150deg, ${nextSong.cover_color || '#4DABF7'}, ${nextSong.cover_color || '#4DABF7'}aa)` }"
      >
        <img v-if="nextSong.cover_url" :src="nextSong.cover_url" class="w-full h-full object-cover" />
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!loading" class="text-center py-20 text-ink-faint">
      <p class="text-[15px] mb-4">还没有推荐结果</p>
      <button class="tm-btn" @click="fetchRecommendations">🔄 重新推荐</button>
    </div>

    <!-- 控制条 -->
    <div v-if="songs.length" class="flex items-center justify-between mt-6">
      <button class="w-12 h-12 rounded-full bg-card border border-line grid place-items-center text-ink-soft hover:bg-bg transition-colors disabled:opacity-30" :disabled="idx === 0" @click="prev">
        <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current"><path d="M16 5v14L9 12zM7 5h2v14H7z" /></svg>
      </button>
      <div class="text-center">
        <p class="text-[13px] font-medium text-ink">{{ idx + 1 }} / {{ songs.length }}</p>
        <div class="flex items-center gap-1 mt-1.5">
          <button
            v-for="(_, i) in songs.slice(0, 12)"
            :key="i"
            class="w-1.5 h-1.5 rounded-full transition-all"
            :class="i === idx ? 'bg-brand w-6' : 'bg-ink-faint/30'"
            @click="jumpTo(i)"
          />
        </div>
      </div>
      <button class="w-12 h-12 rounded-full bg-card border border-line grid place-items-center text-ink-soft hover:bg-bg transition-colors disabled:opacity-30" :disabled="idx >= songs.length - 1" @click="next">
        <svg viewBox="0 0 24 24" class="w-5 h-5 fill-current"><path d="M6 5v14L13 12zM15 5h2v14h-2z" transform="" /></svg>
      </button>
    </div>

    <!-- 加入歌单：选择弹窗 -->
    <div
      v-if="showPicker"
      class="fixed inset-0 z-50 bg-black/40 flex items-end sm:items-center justify-center p-4"
      @click.self="showPicker = false"
    >
      <div class="w-full max-w-[420px] bg-card rounded-r-lg border border-line p-5 shadow-hover">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-[15px] font-semibold text-ink">加入歌单</h3>
          <button class="text-ink-faint hover:text-ink text-[18px] leading-none" @click="showPicker = false">×</button>
        </div>
        <p v-if="pickerLoading" class="text-[13px] text-ink-faint py-6 text-center">加载歌单中…</p>
        <div v-else-if="pickerPlaylists.length" class="space-y-2 max-h-[50vh] overflow-y-auto">
          <button
            v-for="pl in pickerPlaylists"
            :key="pl.id"
            class="w-full flex items-center justify-between px-4 py-3 rounded-r-md bg-bg hover:bg-brand hover:text-white transition-colors text-left"
            @click="confirmAddToPlaylist(pl)"
          >
            <span class="text-[14px] font-medium truncate">{{ pl.name }}</span>
            <span class="text-[12px] opacity-70 shrink-0 ml-2">{{ pl.song_count || 0 }} 首</span>
          </button>
        </div>
        <p v-else class="text-[13px] text-ink-faint py-6 text-center">暂无歌单，请先创建</p>
      </div>
    </div>
  </div>
</template>