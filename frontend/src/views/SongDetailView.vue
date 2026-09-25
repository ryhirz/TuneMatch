<!-- 歌曲详情页：大封面 + 信息 + 11 维特征 + 歌词（lyrics.ovh 回退） -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { smartApi } from '@/api'
import type { Song } from '@/api/types'
import { usePlayerStore } from '@/stores/player'
import { useToastStore } from '@/stores/toast'
import { GENRE_ZH } from '@/utils/genre'
import { buildFeatures } from '@/utils/features'

const route = useRoute()
const router = useRouter()
const player = usePlayerStore()
const toast = useToastStore()

const song = ref<Song | null>(null)
const loading = ref(false)
const lyrics = ref('')
const lyricsLoading = ref(false)
const lyricsSource = ref<'cached' | 'lyrics.ovh' | 'none' | null>(null)
const audioUrl = ref('')

const id = computed(() => Number(route.params.id))

const GENRE_NAMES: Record<string, string> = { ...GENRE_ZH, jamendo: '独立音乐', local: '本地音乐' }

const coverGradient = computed(() => {
  const c = song.value?.cover_color || '#4DABF7'
  return `linear-gradient(150deg, ${c}, ${c}cc 55%, ${c}88)`
})

const durationFmt = computed(() => {
  const s = Math.round((song.value?.duration || 0) / 1000)
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
})

// 11 维音频特征（与后端 Song.features 顺序严格对齐，见 utils/features.ts）
const features = computed(() => buildFeatures(song.value?.features))

async function fetchLyrics(silent = false) {
  if (!song.value) return
  lyricsLoading.value = true
  try {
    const res = await smartApi.fetchLyrics(song.value.id)
    lyrics.value = res.lyrics || ''
    lyricsSource.value = res.source as typeof lyricsSource.value
    if (res.lyrics) {
      if (song.value) song.value.lyrics = res.lyrics
      if (!silent) toast.show('已拉到歌词', 'success', 1500)
    } else {
      if (!silent) toast.show(res.message || '未找到歌词', 'info', 2500)
    }
  } catch (e) {
    console.error('fetch lyrics failed', e)
    lyricsSource.value = 'none'
    if (!silent) toast.show((e as Error).message || '获取歌词失败', 'error')
  } finally {
    lyricsLoading.value = false
  }
}

async function loadSong() {
  loading.value = true
  try {
    const s = await smartApi.getSong(id.value)
    song.value = s
    if (s?.lyrics) {
      // 已有缓存歌词：直接显示，不重复拉
      lyrics.value = s.lyrics
      lyricsSource.value = 'cached'
    } else {
      // 没有歌词：进入页面自动拉取（silent 模式不弹错误 toast，避免误报）
      toast.show(`正在自动拉取《${s.title}》的歌词…`, 'info', 1800)
      await fetchLyrics(true)
    }
    if (s?.audio_url) audioUrl.value = s.audio_url
  } catch (e) {
    toast.show((e as Error).message || '加载失败', 'error')
  } finally {
    loading.value = false
  }
}

function play() {
  if (song.value) {
    player.playSong(song.value)
    toast.show(`正在播放《${song.value.title}》`, 'success', 1500)
  }
}

/** 标签跳转：曲风/情绪/歌手/专辑 */
function goGenre(g: string) {
  if (!g) return
  router.push({ path: '/genres', query: { genre: g } })
}
function goMood(m: string) {
  router.push({ path: '/genres', query: { mood: m } })
}
function goArtist(artist: string) {
  if (!artist) return
  router.push({ path: '/', query: { q: artist } })  // 跳首页带搜索
}
function goAlbum(album: string) {
  if (!album) return
  router.push({ path: '/', query: { q: album } })
}

function back() {
  if (window.history.length > 1) router.back()
  else router.push('/')
}

onMounted(loadSong)
</script>

<template>
  <div class="max-w-[960px] mx-auto px-7 py-8 max-[560px]:px-4">
    <!-- 返回按钮 -->
    <button class="tm-btn-ghost !px-3 mb-5" @click="back">← 返回</button>

    <!-- 加载状态 -->
    <div v-if="loading && !song" class="text-center py-20 text-ink-faint">加载中…</div>

    <div v-else-if="song" class="grid lg:grid-cols-[320px_1fr] gap-8 max-[768px]:grid-cols-1">
      <!-- 左：大封面 + 操作 -->
      <div class="flex flex-col gap-4">
        <div class="relative aspect-square rounded-r-lg overflow-hidden shadow-hover">
          <img v-if="song.cover_url" :src="song.cover_url" :alt="song.title" class="w-full h-full object-cover" />
          <div v-else class="w-full h-full grid place-items-center text-white text-6xl font-bold" :style="{ background: coverGradient }">
            {{ song.title.slice(0, 1) }}
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <button class="tm-btn !px-5 flex items-center justify-center gap-2" @click="play">
            <svg viewBox="0 0 24 24" class="w-4 h-4 fill-current" style="margin-left:2px"><path d="M7 4.5v15l13-7.5z" /></svg>
            立即播放
          </button>
          <button v-if="song.audio_url" class="tm-btn-ghost !px-3 text-[12px]" @click="audioUrl = song.audio_url; toast.show('已复制音频链接', 'success', 1500)">
            🔗 复制音频链接
          </button>
        </div>
      </div>

      <!-- 右：信息 + 特征 + 歌词 -->
      <div class="flex flex-col gap-6">
        <!-- 标题区 -->
        <div>
          <!-- 曲风徽章（可点击 → 曲风分类） -->
          <button
            class="text-[12px] font-semibold tracking-[0.06em] text-brand uppercase mb-2 hover:underline transition-all"
            title="查看此曲风分类下所有歌曲"
            @click="goGenre(song.genre)"
          >
            {{ GENRE_NAMES[song.genre] || song.genre }}
          </button>
          <h1 class="text-[36px] font-bold text-ink leading-tight tracking-tight">{{ song.title }}</h1>
          <!-- 歌手（可点击 → 搜索歌手） -->
          <p class="text-[18px] font-light text-ink-soft mt-1">
            <button class="hover:text-brand hover:underline transition-colors" title="搜索该歌手的歌曲" @click="goArtist(song.artist)">{{ song.artist }}</button>
            <span v-if="song.album" class="text-ink-faint"> · </span>
            <button v-if="song.album" class="text-ink-faint hover:text-brand hover:underline transition-colors" title="搜索该专辑" @click="goAlbum(song.album)">{{ song.album }}</button>
          </p>
          <div class="flex flex-wrap items-center gap-2 mt-3 text-[13px] text-ink-soft">
            <span class="px-2.5 py-0.5 rounded-pill bg-bg">⏱ {{ durationFmt }}</span>
            <!-- 情绪标签（可点击 → 情绪分类） -->
            <span v-if="song.mood_tags?.length" class="flex flex-wrap gap-1.5">
              <button
                v-for="m in song.mood_tags.slice(0, 5)"
                :key="m"
                class="px-2.5 py-0.5 rounded-pill bg-brand-soft text-brand text-[12px] hover:bg-brand hover:text-white transition-colors"
                :title="`查看「${m}」分类所有歌曲`"
                @click="goMood(m)"
              >
                {{ m }}
              </button>
            </span>
          </div>
        </div>

        <!-- 11 维特征条形图 -->
        <div v-if="features.length" class="bg-card rounded-r-lg p-5 border border-line">
          <h3 class="text-[14px] font-semibold text-ink mb-3">音频特征（11 维）</h3>
          <div class="grid grid-cols-2 gap-x-6 gap-y-2.5">
            <div v-for="f in features" :key="f.key" class="flex flex-col gap-1">
              <div class="flex items-center justify-between text-[12px]">
                <span class="text-ink-soft">{{ f.label }}</span>
                <span class="text-ink-faint font-mono">{{ f.text }}</span>
              </div>
              <div class="h-1.5 rounded-full bg-bg overflow-hidden">
                <div class="h-full rounded-full bg-gradient-to-r from-brand to-ai transition-all duration-700" :style="{ width: f.pct + '%' }" />
              </div>
            </div>
          </div>
        </div>

        <!-- 歌词 -->
        <div class="bg-card rounded-r-lg p-6 border border-line">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-[14px] font-semibold text-ink flex items-center gap-2">
              歌词
              <span v-if="lyricsLoading" class="text-[11px] font-normal text-ink-faint flex items-center gap-1">
                <span class="inline-block w-3 h-3 rounded-full border-2 border-brand border-t-transparent animate-spin" />
                正在自动拉取…
              </span>
              <span v-else-if="lyricsSource === 'cached'" class="text-[10px] font-normal text-emerald-600 bg-emerald-50 rounded-pill px-2 py-0.5">已保存到本地</span>
              <span v-else-if="lyricsSource === 'lyrics.ovh'" class="text-[10px] font-normal text-ink-faint bg-bg rounded-pill px-2 py-0.5">来源 lyrics.ovh</span>
              <span v-else-if="lyricsSource === 'none'" class="text-[10px] font-normal text-ink-faint bg-bg rounded-pill px-2 py-0.5">暂未找到</span>
            </h3>
            <button class="tm-btn-ghost !px-2.5 !py-1 text-[12px]" :disabled="lyricsLoading" @click="fetchLyrics()">
              {{ lyricsLoading ? '拉取中…' : '🔄 重新拉取' }}
            </button>
          </div>
          <pre
            v-if="lyrics"
            class="text-[14px] font-light text-ink-soft leading-[1.9] whitespace-pre-wrap font-sans select-text"
            style="user-select: text; -webkit-user-select: text;"
          >{{ lyrics }}</pre>
          <div v-else-if="lyricsLoading" class="py-10 flex flex-col items-center gap-2 text-ink-faint">
            <div class="w-8 h-8 rounded-full border-2 border-brand/30 border-t-brand animate-spin" />
            <p class="text-[12px]">正在自动从 lyrics.ovh 拉取歌词…</p>
          </div>
          <div v-else class="py-8 text-center text-[13px] text-ink-faint font-light">
            <p class="mb-1">⚠️ 这首歌暂无歌词</p>
            <p class="text-[11.5px] text-ink-faint/80">独立音乐人作品通常不上传歌词 · 可点击「重新拉取」再试一次</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载失败 -->
    <div v-else class="text-center py-20">
      <p class="text-ink-faint mb-4">未找到这首歌曲</p>
      <button class="tm-btn" @click="back">返回</button>
    </div>
  </div>
</template>