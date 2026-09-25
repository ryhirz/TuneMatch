<!-- 页面：曲风探索（Bento / 大图标分类网格 + 歌曲列表）
特点：新人一眼看出 36 个分类（小图标 + 渐变 + 卡片） -->
<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { smartApi } from '@/api'
import type { Song } from '@/api/types'
import SongCard from '@/components/SongCard.vue'
import { useToastStore } from '@/stores/toast'
import { GENRE_META, GENRE_ZH } from '@/utils/genre'

const route = useRoute()
const toast = useToastStore()
const songs = ref<Song[]>([])
const active = ref('')
const moodFilter = ref('')
const genreFilter = ref('')

const genres = computed(() => {
  const cnt: Record<string, number> = {}
  for (const s of songs.value) cnt[s.genre] = (cnt[s.genre] || 0) + 1
  return Object.entries(cnt).map(([g, n]) => ({ key: g, name: GENRE_ZH[g] || g, count: n }))
})

const filtered = computed(() => {
  let arr = songs.value
  if (genreFilter.value) arr = arr.filter((s) => s.genre === genreFilter.value)
  if (active.value) arr = arr.filter((s) => s.genre === active.value)
  if (moodFilter.value) arr = arr.filter((s) => (s.mood_tags || []).includes(moodFilter.value))
  return arr.slice(0, 16)
})

// 曲风分类元数据合并：GENRE_META 与实际库内曲风取交集
const popularGenres = computed(() => GENRE_META.filter((g) => g.category === '热门'))
const moodGenres = computed(() => GENRE_META.filter((g) => g.category === '心情'))
const eraGenres = computed(() => GENRE_META.filter((g) => g.category === '时代'))
const themeGenres = computed(() => GENRE_META.filter((g) => g.category === '主题'))

function syncFromQuery() {
  const m = route.query.mood as string | undefined
  const g = route.query.genre as string | undefined
  moodFilter.value = m || ''
  genreFilter.value = g || ''
  if (g) active.value = g
  if (m) toast.show(`已应用情绪筛选「${m}」`, 'info', 2000)
  else if (g) toast.show(`已应用曲风筛选「${GENRE_ZH[g] || g}」`, 'info', 2000)
}

function pickGenre(key: string) {
  // 切换激活态：单击切换，再点取消
  active.value = active.value === key ? '' : key
  genreFilter.value = ''
  moodFilter.value = ''
}

function clearFilter() {
  active.value = ''
  genreFilter.value = ''
  moodFilter.value = ''
}

onMounted(async () => {
  try { songs.value = await smartApi.listSongs() } catch { songs.value = [] }
  syncFromQuery()
})

watch(() => route.query, syncFromQuery)
</script>

<template>
  <div class="max-w-[1120px] mx-auto px-7 py-10 max-[560px]:px-4">
    <!-- 标题 -->
    <div class="mb-8">
      <p class="text-[13px] font-semibold tracking-[0.06em] text-brand uppercase mb-2">曲风 · Genres</p>
      <h2 class="text-display text-ink">
        {{ moodFilter ? `情绪「${moodFilter}」的歌曲` : (active ? `${GENRE_ZH[active] || active}曲风` : '探索你的曲风世界') }}
      </h2>
      <p class="mt-2 text-[13px] font-light text-ink-faint">
        {{ active ? `已选「${GENRE_ZH[active] || active}」曲风 · 查看下方歌曲` : `共 ${songs.length} 首歌曲 · 36 个分类 · 单击图标选择分类` }}
      </p>
    </div>

    <!-- 分类大图标网格（一目了然） -->
    <template v-if="!active && !moodFilter && !genreFilter">
      <!-- 热门分类 -->
      <section class="mb-8">
        <h3 class="text-[14px] font-semibold text-ink mb-3 uppercase tracking-[0.04em]">🔥 热门曲风</h3>
        <div class="grid gap-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
          <button
            v-for="g in popularGenres"
            :key="g.key"
            class="relative h-24 rounded-r-lg overflow-hidden flex flex-col items-center justify-center text-white font-medium transition-all hover:scale-[1.05] hover:shadow-hover cursor-pointer"
            :style="{ background: g.gradient }"
            @click="pickGenre(g.key)"
          >
            <span class="text-3xl mb-1">{{ g.icon }}</span>
            <span class="text-[14px] font-semibold">{{ g.label }}</span>
            <span class="text-[10px] opacity-80 mt-0.5">{{ genres.find((x) => x.key === g.key)?.count || 0 }} 首</span>
          </button>
        </div>
      </section>

      <!-- 心情分类 -->
      <section class="mb-8">
        <h3 class="text-[14px] font-semibold text-ink mb-3 uppercase tracking-[0.04em]">💖 心情分类</h3>
        <div class="grid gap-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
          <button
            v-for="g in moodGenres"
            :key="g.key"
            class="relative h-24 rounded-r-lg overflow-hidden flex flex-col items-center justify-center text-white font-medium transition-all hover:scale-[1.05] hover:shadow-hover cursor-pointer"
            :style="{ background: g.gradient }"
            @click="pickGenre(g.key)"
          >
            <span class="text-3xl mb-1">{{ g.icon }}</span>
            <span class="text-[14px] font-semibold">{{ g.label }}</span>
            <span class="text-[10px] opacity-80 mt-0.5">{{ genres.find((x) => x.key === g.key)?.count || 0 }} 首</span>
          </button>
        </div>
      </section>

      <!-- 时代 -->
      <section class="mb-8">
        <h3 class="text-[14px] font-semibold text-ink mb-3 uppercase tracking-[0.04em]">📅 时代经典</h3>
        <div class="grid gap-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
          <button
            v-for="g in eraGenres"
            :key="g.key"
            class="relative h-24 rounded-r-lg overflow-hidden flex flex-col items-center justify-center text-white font-medium transition-all hover:scale-[1.05] hover:shadow-hover cursor-pointer"
            :style="{ background: g.gradient }"
            @click="pickGenre(g.key)"
          >
            <span class="text-3xl mb-1">{{ g.icon }}</span>
            <span class="text-[14px] font-semibold">{{ g.label }}</span>
            <span class="text-[10px] opacity-80 mt-0.5">{{ genres.find((x) => x.key === g.key)?.count || 0 }} 首</span>
          </button>
        </div>
      </section>

      <!-- 主题 -->
      <section class="mb-8">
        <h3 class="text-[14px] font-semibold text-ink mb-3 uppercase tracking-[0.04em]">🎬 主题</h3>
        <div class="grid gap-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
          <button
            v-for="g in themeGenres"
            :key="g.key"
            class="relative h-24 rounded-r-lg overflow-hidden flex flex-col items-center justify-center text-white font-medium transition-all hover:scale-[1.05] hover:shadow-hover cursor-pointer"
            :style="{ background: g.gradient }"
            @click="pickGenre(g.key)"
          >
            <span class="text-3xl mb-1">{{ g.icon }}</span>
            <span class="text-[14px] font-semibold">{{ g.label }}</span>
            <span class="text-[10px] opacity-80 mt-0.5">{{ genres.find((x) => x.key === g.key)?.count || 0 }} 首</span>
          </button>
        </div>
      </section>
    </template>

    <!-- 选中分类后：歌曲列表（带清除筛选/返回分类） -->
    <template v-else>
      <div class="flex items-center gap-2 mb-5">
        <button class="tm-btn-ghost !px-3" @click="clearFilter">← 返回分类</button>
        <p class="text-[13px] font-light text-ink-soft">
          {{ filtered.length }} 首 · 来自「{{ GENRE_ZH[active || genreFilter] || moodFilter }}」分类
        </p>
      </div>

      <div v-if="filtered.length" class="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4">
        <SongCard v-for="s in filtered" :key="s.id" :song="s" :show-reason="false" />
      </div>
      <p v-else class="text-[13px] font-light text-ink-faint py-10 text-center">暂无歌曲</p>
    </template>
  </div>
</template>