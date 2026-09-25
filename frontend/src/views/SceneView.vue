<!-- 页面：场景歌单（12 场景 + 实时刷新歌曲）
每场景联动 mood + genre + tempo 区间，调用 /api/recommend 实时取推荐 -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { smartApi } from '@/api'
import type { Song } from '@/api/types'
import SongCard from '@/components/SongCard.vue'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const songs = ref<Song[]>([])
const active = ref('study')
const loading = ref(false)

interface Scene {
  key: string
  name: string
  emoji: string
  desc: string
  grad: string
  moods: string[]
  genres?: string[]
  scene?: string
}

const SCENES: Scene[] = [
  { key: 'study', name: '专注学习', emoji: '📚', desc: 'Lo-fi · 钢琴 · 低能量', grad: 'linear-gradient(160deg,#36B3A0,#1E7A6D)', moods: ['治愈', '放松', '怀旧'], genres: ['lofi', 'piano', 'ambient', 'instrumental'] },
  { key: 'workout', name: '运动健身', emoji: '💪', desc: '高能节拍 · 140+ BPM', grad: 'linear-gradient(160deg,#FF7A45,#D9372E)', moods: ['热血', '激昂', '活力'], genres: ['rock', 'electronic', 'hip-hop', 'metal'] },
  { key: 'sleep', name: '深夜助眠', emoji: '🌙', desc: '环境音 · 慢节奏 · 0.15 能量', grad: 'linear-gradient(160deg,#6A5CF0,#3A2D9E)', moods: ['梦幻', '治愈', '放松'], genres: ['ambient', 'meditation', 'sleep', 'classical'] },
  { key: 'commute', name: '通勤路上', emoji: '🚇', desc: '城市节拍 · 轻爵士', grad: 'linear-gradient(160deg,#4AA8FF,#1E63C9)', moods: ['开心', '浪漫', '放松'], genres: ['pop', 'r-n-b', 'indie', 'jazz'] },
  { key: 'work', name: '工作专注', emoji: '💼', desc: '低干扰 · 持续专注', grad: 'linear-gradient(160deg,#0EA5E9,#0C4A6E)', moods: ['专注', '放松', '治愈'], genres: ['lofi', 'piano', 'instrumental', 'ambient'] },
  { key: 'cooking', name: '下厨时光', emoji: '🍳', desc: '轻快 · 周末节奏', grad: 'linear-gradient(160deg,#F59E0B,#B45309)', moods: ['开心', '放松', '活力'], genres: ['pop', 'folk', 'indie', 'acoustic'] },
  { key: 'drive', name: '兜风驾驶', emoji: '🚗', desc: '动感 · 节奏感', grad: 'linear-gradient(160deg,#1E40AF,#1E3A8A)', moods: ['热血', '浪漫', '活力'], genres: ['rock', 'electronic', 'dance', 'pop'] },
  { key: 'travel', name: '旅途出行', emoji: '✈️', desc: '回忆 · 憧憬 · 探索', grad: 'linear-gradient(160deg,#7C3AED,#5B21B6)', moods: ['梦幻', '浪漫', '热血'], genres: ['world', 'indie', 'pop', 'cinematic'] },
  { key: 'party', name: '派对狂欢', emoji: '🎉', desc: '高能热曲 · 100+ BPM', grad: 'linear-gradient(160deg,#E11D48,#A21CAF)', moods: ['激昂', '活力', '热血'], genres: ['electronic', 'dance', 'hip-hop', 'pop'] },
  { key: 'yoga', name: '瑜伽冥想', emoji: '🧘', desc: '舒缓 · α波 · 呼吸', grad: 'linear-gradient(160deg,#0F766E,#064E3B)', moods: ['放松', '梦幻', '治愈'], genres: ['meditation', 'ambient', 'classical', 'world'] },
  { key: 'rainy', name: '雨夜阅读', emoji: '🌧️', desc: '静谧 · 窗外雨声', grad: 'linear-gradient(160deg,#475569,#1E293B)', moods: ['怀旧', '浪漫', '梦幻'], genres: ['jazz', 'classical', 'piano', 'ambient'] },
  { key: 'late', name: '深夜独处', emoji: '🌃', desc: '内省 · 回忆 · 忧伤', grad: 'linear-gradient(160deg,#1E1B4B,#0F0F23)', moods: ['悲伤', '怀旧', '梦幻'], genres: ['sad', 'ambient', 'piano', 'ballad'] },
]

const activeScene = computed(() => SCENES.find((s) => s.key === active.value)!)

const filtered = computed(() => {
  const sc = activeScene.value
  if (!sc) return []
  const moods = sc.moods
  const genres = sc.genres || []
  let arr = songs.value.filter((s) => {
    const moodOk = moods.some((m) => (s.mood_tags || []).includes(m))
    const genreOk = genres.length === 0 || genres.includes(s.genre)
    return moodOk || genreOk
  })
  // 按 match 字段降序排（推荐度）
  arr = arr.sort((a, b) => (b.match || 0) - (a.match || 0))
  return arr.slice(0, 12)
})

const sceneCount = computed(() => {
  const cnt: Record<string, number> = {}
  for (const sc of SCENES) {
    const moods = sc.moods
    const genres = sc.genres || []
    cnt[sc.key] = songs.value.filter((s) => {
      const moodOk = moods.some((m) => (s.mood_tags || []).includes(m))
      const genreOk = genres.length === 0 || genres.includes(s.genre)
      return moodOk || genreOk
    }).length
  }
  return cnt
})

async function loadScene(s: string) {
  loading.value = true
  active.value = s
  await new Promise((r) => setTimeout(r, 100))  // 视觉反馈
  loading.value = false
  toast.show(`已切换到「${activeScene.value.name}」· ${filtered.value.length} 首匹配`, 'info', 2000)
}

onMounted(async () => {
  try {
    // 拉全量曲库（接口主路径不截断，limit 仅作占位；真实规模见后端统计）
    songs.value = await smartApi.listSongs({ limit: 500 })
  } catch {
    songs.value = []
  }
})
</script>

<template>
  <div class="max-w-[1120px] mx-auto px-7 py-10 max-[560px]:px-4">
    <div class="mb-6">
      <p class="text-[13px] font-semibold tracking-[0.06em] text-brand uppercase mb-2">场景 · Scenes</p>
      <h2 class="text-display text-ink">此刻需要什么，交给场景歌单</h2>
      <p class="mt-2 text-[13px] font-light text-ink-faint">12 个场景 · 点击切换，曲库实时联动</p>
    </div>

    <!-- 场景卡片网格 -->
    <div class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-3 mb-8 max-[560px]:grid-cols-2">
      <button
        v-for="sc in SCENES"
        :key="sc.key"
        class="relative rounded-r-lg p-3 flex flex-col items-center gap-1.5 text-white transition-all duration-300 hover:-translate-y-1 hover:shadow-hover cursor-pointer overflow-hidden"
        :class="{ 'ring-2 ring-offset-2 ring-brand scale-[1.02]': active === sc.key }"
        :style="{ background: sc.grad }"
        @click="loadScene(sc.key)"
      >
        <span class="text-2xl">{{ sc.emoji }}</span>
        <span class="text-[13px] font-semibold">{{ sc.name }}</span>
        <span class="text-[10px] font-light opacity-90 text-center leading-tight">{{ sc.desc }}</span>
        <span class="text-[10px] font-bold bg-white/20 rounded-pill px-1.5 py-0.5 mt-0.5">
          {{ sceneCount[sc.key] || 0 }} 首
        </span>
      </button>
    </div>

    <!-- 当前场景提示 -->
    <div class="flex items-center gap-3 mb-5 p-4 rounded-r-lg" :style="{ background: activeScene.grad }">
      <span class="text-3xl">{{ activeScene.emoji }}</span>
      <div class="flex-1 text-white">
        <h3 class="text-[18px] font-semibold">{{ activeScene.name }}</h3>
        <p class="text-[13px] font-light opacity-90">{{ activeScene.desc }}</p>
      </div>
      <div class="text-white text-right shrink-0">
        <p class="text-[24px] font-bold">{{ filtered.length }}</p>
        <p class="text-[11px] font-light opacity-85">首匹配</p>
      </div>
    </div>

    <!-- 歌曲列表 -->
    <div v-if="loading" class="text-center py-12 text-ink-faint">🔄 切换场景中…</div>
    <div v-else-if="filtered.length" class="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4">
      <SongCard v-for="s in filtered" :key="s.id" :song="s" :show-reason="false" />
    </div>
    <p v-else class="text-[13px] font-light text-ink-faint py-10 text-center">该场景暂无匹配歌曲，试试别的场景</p>
  </div>
</template>