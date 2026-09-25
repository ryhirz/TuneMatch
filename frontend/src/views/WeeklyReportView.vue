<!-- 页面：周度听歌报告（仪表盘风格 · 多种可视化）
- 顶部 4 个核心指标 + 半圆仪表盘
- 8 维特征雷达图
- 曲风圆环占比 + 情绪词云
- 情绪-特征散点分布
- 本周推荐 -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { smartApi } from '@/api'
import type { Song } from '@/api/types'
import { FEATURE_META, featurePct } from '@/utils/features'
import { usePlayerStore } from '@/stores/player'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const player = usePlayerStore()
const toast = useToastStore()
const songs = ref<Song[]>([])

// ---------- 核心指标 ----------
const totalMs = computed(() => songs.value.reduce((acc, s) => acc + (s.duration || 0), 0))
const totalHours = computed(() => (totalMs.value / 3600000).toFixed(1))
const totalMinutes = computed(() => Math.round(totalMs.value / 60000))

const GENRE_ZH: Record<string, string> = { pop: '流行', rock: '摇滚', folk: '民谣', edm: '电子', 'hip-hop': '嘻哈', jamendo: '独立', lofi: 'Lo-fi', jazz: '爵士', classical: '古典', ambient: '氛围', electronic: '电子', dance: '舞曲', chill: '放松', indie: '独立', instrumental: '器乐', piano: '钢琴', acoustic: '原声', metal: '金属', reggae: '雷鬼', blues: '蓝调', country: '乡村', soundtrack: '影视原声', world: '世界音乐', cinematic: '电影配乐', meditation: '冥想', sleep: '助眠', study: '学习', workout: '健身', party: '派对', romantic: '浪漫', dream: '梦幻', happy: '快乐', sad: '悲伤', energetic: '活力', epic: '史诗', 'r-n-b': 'R&B', '90s': '90年代', '80s': '80年代', orchestral: '管弦', vocal: '人声' }
const GENRE_COLOR: Record<string, string> = {
  pop: '#FF6B9D', rock: '#EF4444', folk: '#84CC16', edm: '#7C3AED',
  'hip-hop': '#0EA5E9', jamendo: '#0EA5E9', lofi: '#10B981', jazz: '#F59E0B',
  classical: '#6366F1', ambient: '#0891B2', electronic: '#7C3AED',
  dance: '#F97316', metal: '#374151', piano: '#A78BFA', acoustic: '#FCD34D',
  world: '#0D9488', soundtrack: '#831843', cinematic: '#7C2D12',
}

// 曲风圆环占比（取前 6）
const genreDist = computed(() => {
  const cnt: Record<string, number> = {}
  for (const s of songs.value) cnt[s.genre] = (cnt[s.genre] || 0) + 1
  const total = Math.max(1, songs.value.length)
  return Object.entries(cnt)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([g, n], i) => ({
      genre: g,
      label: GENRE_ZH[g] || g,
      count: n,
      pct: Math.round((n / total) * 100),
      color: GENRE_COLOR[g] || ['#0071E3', '#7C3AED', '#F59E0B', '#10B981', '#EF4444', '#0EA5E9'][i],
    }))
})

// 11 维特征雷达图数据（用全部歌曲特征均值，按各自量纲归一化到 0-1）
const radarFeats = computed(() => {
  const feats = songs.value.filter((s) => (s.features?.length || 0) >= 11)
  if (!feats.length) return { labels: [] as string[], values: [] as number[] }
  const values = FEATURE_META.map((m, i) => {
    const avg = feats.reduce((a, s) => a + (s.features?.[i] ?? 0.5), 0) / feats.length
    return featurePct(avg, m.kind) / 100
  })
  return { labels: FEATURE_META.map((m) => m.label), values }
})

// 情绪词云
const moodDist = computed(() => {
  const cnt: Record<string, number> = {}
  for (const s of songs.value) for (const m of s.mood_tags || []) cnt[m] = (cnt[m] || 0) + 1
  const max = Math.max(1, ...Object.values(cnt))
  return Object.entries(cnt).sort((a, b) => b[1] - a[1]).slice(0, 12)
    .map(([m, n]) => ({ mood: m, count: n, size: 13 + Math.round((n / max) * 14) }))
})

const topGenre = computed(() => genreDist.value[0]?.label || '流行')
const topGenrePct = computed(() => genreDist.value[0]?.pct || 0)
const avgMood = computed(() => {
  const feats = songs.value.filter((s) => s.features?.length >= 3)
  if (!feats.length) return 55
  return Math.round((feats.reduce((a, s) => a + (s.features[2] ?? 0), 0) / feats.length) * 100)
})
const uniqueArtists = computed(() => new Set(songs.value.map((s) => s.artist)).size)

const cards = computed(() => [
  { label: '本周听歌时长', value: totalHours.value, unit: '小时', sub: `${songs.value.length} 首 · ${uniqueArtists.value} 位歌手`, color: '#0071E3', icon: '⏱' },
  { label: '最爱曲风', value: topGenre.value, unit: '', sub: `占比 ${topGenrePct.value}% · Top 1`, color: '#F59E0B', icon: '🎵' },
  { label: '情绪愉悦度', value: avgMood.value, unit: '%', sub: 'valence 均值', color: '#10B981', icon: '💖' },
  { label: '曲库收藏', value: songs.value.length, unit: '首', sub: `${uniqueArtists.value} 位独立音乐人`, color: '#7C3AED', icon: '📚' },
])

// 情绪-曲风散点
const scatterData = computed(() => {
  return songs.value.slice(0, 50).map((s) => ({
    id: s.id,
    title: s.title,
    valence: s.features?.[2] ?? 0.5,
    energy: s.features?.[1] ?? 0.5,
    genre: GENRE_ZH[s.genre] || s.genre,
  }))
})

function goMood(mood: string) {
  router.push({ path: '/genres', query: { mood } })
}
function playWeekly(song: Song) {
  player.playSong(song)
  toast.show(`正在播放《${song.title}》`, 'success', 1500)
}

onMounted(async () => {
  try { songs.value = await smartApi.listSongs() } catch { songs.value = [] }
})

const fmt = (ms: number) => {
  const s = Math.round(ms / 1000)
  const m = Math.floor(s / 60)
  return `${m}:${String(s % 60).padStart(2, '0')}`
}

// SVG 工具：极坐标点
const polar = (cx: number, cy: number, r: number, deg: number) => {
  const a = (deg - 90) * Math.PI / 180
  return [cx + r * Math.cos(a), cy + r * Math.sin(a)]
}
</script>

<template>
  <div class="max-w-[1120px] mx-auto px-7 py-10 max-[560px]:px-4">
    <!-- 页头 -->
    <div class="mb-8">
      <p class="text-[13px] font-semibold tracking-[0.06em] text-brand uppercase mb-2">周报 · Weekly Report</p>
      <h2 class="text-display text-ink">你的听歌仪表盘</h2>
      <p class="mt-2 text-[13px] font-light text-ink-faint">基于曲库实时统计 · 每周一 09:00 自动生成</p>
    </div>

    <!-- ============ 仪表盘一：核心指标 + 半圆表 ============ -->
    <section class="grid lg:grid-cols-[1fr_1.2fr] gap-5 mb-5">
      <!-- 左：4 个核心指标 -->
      <div class="grid grid-cols-2 gap-4">
        <div
          v-for="c in cards"
          :key="c.label"
          class="bg-card rounded-r-lg p-5 border border-line relative overflow-hidden hover:-translate-y-0.5 transition-all"
        >
          <div class="text-3xl mb-2">{{ c.icon }}</div>
          <p class="text-[12px] text-ink-faint mb-1">{{ c.label }}</p>
          <p class="text-[32px] font-bold tracking-tight leading-none" :style="{ color: c.color }">
            {{ c.value }}<span class="text-[14px] font-medium ml-1">{{ c.unit }}</span>
          </p>
          <p class="text-[11px] font-light text-ink-faint mt-2">{{ c.sub }}</p>
          <!-- 角标装饰 -->
          <div class="absolute -top-2 -right-2 w-12 h-12 rounded-full opacity-10" :style="{ background: c.color }" />
        </div>
      </div>

      <!-- 右：半圆仪表盘（情绪愉悦度） -->
      <div class="bg-card rounded-r-lg p-6 border border-line flex flex-col">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-[14px] font-semibold text-ink">情绪仪表盘</h3>
          <span class="text-[11px] font-light text-ink-faint">valence 0-100</span>
        </div>
        <div class="flex-1 flex items-center justify-center">
          <svg viewBox="0 0 240 140" class="w-full max-w-[280px]">
            <!-- 背景弧 -->
            <path d="M 20 120 A 100 100 0 0 1 220 120" fill="none" stroke="#E5E5EA" stroke-width="16" stroke-linecap="round" />
            <!-- 渐变定义 -->
            <defs>
              <linearGradient id="gauge-grad" x1="0" x2="1" y1="0" y2="0">
                <stop offset="0%" stop-color="#EF4444" />
                <stop offset="50%" stop-color="#F59E0B" />
                <stop offset="100%" stop-color="#10B981" />
              </linearGradient>
            </defs>
            <!-- 进度弧 -->
            <path
              d="M 20 120 A 100 100 0 0 1 220 120"
              fill="none"
              stroke="url(#gauge-grad)"
              stroke-width="16"
              stroke-linecap="round"
              :stroke-dasharray="314"
              :stroke-dashoffset="314 - (314 * avgMood / 100)"
              style="transition: stroke-dashoffset 1s ease-out;"
            />
            <!-- 中心数字 -->
            <text x="120" y="100" text-anchor="middle" class="text-[36px] font-bold fill-ink" font-size="36" font-weight="700" :fill="avgMood > 60 ? '#10B981' : avgMood > 30 ? '#F59E0B' : '#EF4444'">
              {{ avgMood }}
            </text>
            <text x="120" y="118" text-anchor="middle" font-size="11" fill="#8A8A8E">
              情绪愉悦度
            </text>
            <!-- 刻度标签 -->
            <text x="20" y="138" font-size="9" fill="#8A8A8E">低</text>
            <text x="220" y="138" text-anchor="end" font-size="9" fill="#8A8A8E">高</text>
          </svg>
        </div>
        <div class="grid grid-cols-3 gap-2 mt-3 text-center text-[11px]">
          <div>
            <p class="text-ink-faint">总时长</p>
            <p class="text-[16px] font-semibold text-ink">{{ totalMinutes }} <span class="text-[11px] font-normal">分钟</span></p>
          </div>
          <div>
            <p class="text-ink-faint">曲库总数</p>
            <p class="text-[16px] font-semibold text-ink">{{ songs.length }} <span class="text-[11px] font-normal">首</span></p>
          </div>
          <div>
            <p class="text-ink-faint">独立音乐人</p>
            <p class="text-[16px] font-semibold text-ink">{{ uniqueArtists }} <span class="text-[11px] font-normal">位</span></p>
          </div>
        </div>
      </div>
    </section>

    <!-- ============ 仪表盘二：雷达图 + 曲风圆环 ============ -->
    <section class="grid lg:grid-cols-2 gap-5 mb-5">
      <!-- 左：11 维特征雷达 -->
      <div class="bg-card rounded-r-lg p-6 border border-line">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-[14px] font-semibold text-ink">🎯 11 维特征雷达</h3>
          <span class="text-[11px] font-light text-ink-faint">库内均值</span>
        </div>
        <div v-if="radarFeats.labels.length" class="aspect-square max-w-[320px] mx-auto">
          <svg viewBox="0 0 320 320" class="w-full h-full">
            <!-- 背景网格 -->
            <g v-for="r in [0.25, 0.5, 0.75, 1]" :key="r">
              <polygon
                :points="radarFeats.labels.map((_, i) => polar(160, 160, 130 * r, (360 / radarFeats.labels.length) * i).join(',')).join(' ')"
                fill="none"
                stroke="#E5E5EA"
                stroke-width="1"
              />
            </g>
            <!-- 轴线 -->
            <g v-for="(_, i) in radarFeats.labels.length" :key="'ax-' + i">
              <line
                :x1="polar(160, 160, 0, (360 / radarFeats.labels.length) * i)[0]"
                :y1="polar(160, 160, 0, (360 / radarFeats.labels.length) * i)[1]"
                :x2="polar(160, 160, 130, (360 / radarFeats.labels.length) * i)[0]"
                :y2="polar(160, 160, 130, (360 / radarFeats.labels.length) * i)[1]"
                stroke="#E5E5EA"
                stroke-width="1"
              />
            </g>
            <!-- 数据多边形 -->
            <polygon
              :points="radarFeats.values.map((v, i) => polar(160, 160, 130 * v, (360 / radarFeats.labels.length) * i).join(',')).join(' ')"
              fill="rgba(124, 58, 237, 0.25)"
              stroke="#7C3AED"
              stroke-width="2"
              stroke-linejoin="round"
            />
            <!-- 数据点 -->
            <circle
              v-for="(v, i) in radarFeats.values"
              :key="'pt-' + i"
              :cx="polar(160, 160, 130 * v, (360 / radarFeats.labels.length) * i)[0]"
              :cy="polar(160, 160, 130 * v, (360 / radarFeats.labels.length) * i)[1]"
              r="4"
              fill="#7C3AED"
            />
            <!-- 标签 -->
            <text
              v-for="(lbl, i) in radarFeats.labels"
              :key="'lbl-' + i"
              :x="polar(160, 160, 150, (360 / radarFeats.labels.length) * i)[0]"
              :y="polar(160, 160, 150, (360 / radarFeats.labels.length) * i)[1]"
              text-anchor="middle"
              dominant-baseline="middle"
              font-size="11"
              fill="#3A3A3C"
            >{{ lbl }}</text>
          </svg>
        </div>
        <p v-else class="text-center text-ink-faint text-[13px] py-8">无特征数据</p>
      </div>

      <!-- 右：曲风圆环分布（donut chart） -->
      <div class="bg-card rounded-r-lg p-6 border border-line">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-[14px] font-semibold text-ink">🍩 曲风圆环分布</h3>
          <span class="text-[11px] font-light text-ink-faint">Top {{ genreDist.length }}</span>
        </div>
        <div class="flex items-center gap-6">
          <!-- 圆环 -->
          <svg viewBox="0 0 120 120" class="w-32 h-32 shrink-0">
            <circle cx="60" cy="60" r="50" fill="none" stroke="#F2F2F7" stroke-width="16" />
            <template v-for="(g, i) in genreDist" :key="g.genre">
              <circle
                cx="60" cy="60" r="50"
                fill="none"
                :stroke="g.color"
                stroke-width="16"
                :stroke-dasharray="`${(g.pct / 100) * 314.16} 314.16`"
                :stroke-dashoffset="-(genreDist.slice(0, i).reduce((a, x) => a + x.pct, 0) / 100) * 314.16"
                transform="rotate(-90 60 60)"
                style="transition: stroke-dasharray 0.8s ease-out;"
              />
            </template>
            <text x="60" y="58" text-anchor="middle" font-size="24" font-weight="700" fill="#1A1A1A">{{ genreDist[0]?.pct || 0 }}%</text>
            <text x="60" y="74" text-anchor="middle" font-size="10" fill="#8A8A8E">{{ topGenre }}</text>
          </svg>
          <!-- 图例 -->
          <div class="flex-1 space-y-1.5 max-h-[180px] overflow-y-auto">
            <div v-for="g in genreDist" :key="g.genre" class="flex items-center gap-2 text-[12px]">
              <span class="w-3 h-3 rounded-sm shrink-0" :style="{ background: g.color }" />
              <span class="flex-1 text-ink-soft">{{ g.label }}</span>
              <span class="font-mono text-ink-faint">{{ g.pct }}%</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ============ 仪表盘三：情绪词云 + 散点图 ============ -->
    <section class="grid lg:grid-cols-2 gap-5 mb-5">
      <!-- 情绪词云（可点击） -->
      <div class="bg-card rounded-r-lg p-6 border border-line">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-[14px] font-semibold text-ink">💭 情绪词云</h3>
          <span class="text-[11px] font-light text-ink-faint">点击跳转</span>
        </div>
        <div class="flex flex-wrap items-center gap-2 min-h-[140px] content-center">
          <button
            v-for="m in moodDist"
            :key="m.mood"
            class="rounded-pill px-3 py-1.5 font-medium transition-all hover:scale-110 hover:shadow-btn cursor-pointer"
            :style="{
              fontSize: m.size + 'px',
              background: `linear-gradient(135deg, #4DABF7${Math.min(40, 10 + m.count * 5)} , #7C3AED${Math.min(30, 8 + m.count * 4)})`,
              color: '#fff',
            }"
            @click="goMood(m.mood)"
          >
            {{ m.mood }}
          </button>
          <p v-if="!moodDist.length" class="text-[13px] font-light text-ink-faint">暂无情绪数据</p>
        </div>
      </div>

      <!-- 散点：valence × energy -->
      <div class="bg-card rounded-r-lg p-6 border border-line">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-[14px] font-semibold text-ink">📊 情绪 × 能量散点</h3>
          <span class="text-[11px] font-light text-ink-faint">{{ scatterData.length }} 个点</span>
        </div>
        <svg viewBox="0 0 320 200" class="w-full">
          <!-- 象限背景 -->
          <rect x="160" y="0" width="160" height="100" fill="rgba(16, 185, 129, 0.06)" />
          <rect x="0" y="0" width="160" height="100" fill="rgba(245, 158, 11, 0.06)" />
          <rect x="0" y="100" width="160" height="100" fill="rgba(239, 68, 68, 0.06)" />
          <rect x="160" y="100" width="160" height="100" fill="rgba(124, 58, 237, 0.06)" />
          <!-- 轴 -->
          <line x1="0" y1="100" x2="320" y2="100" stroke="#D1D1D6" stroke-width="1" />
          <line x1="160" y1="0" x2="160" y2="200" stroke="#D1D1D6" stroke-width="1" />
          <!-- 标签 -->
          <text x="160" y="195" text-anchor="middle" font-size="10" fill="#8A8A8E">愉悦度 →</text>
          <text x="5" y="105" font-size="10" fill="#8A8A8E">↑ 能量</text>
          <!-- 象限标签 -->
          <text x="80" y="14" text-anchor="middle" font-size="9" fill="#F59E0B">激昂</text>
          <text x="240" y="14" text-anchor="middle" font-size="9" fill="#10B981">热血</text>
          <text x="80" y="190" text-anchor="middle" font-size="9" fill="#EF4444">忧伤</text>
          <text x="240" y="190" text-anchor="middle" font-size="9" fill="#7C3AED">梦幻</text>
          <!-- 数据点 -->
          <circle
            v-for="p in scatterData"
            :key="p.id"
            :cx="p.valence * 320"
            :cy="200 - p.energy * 200"
            r="4"
            fill="#7C3AED"
            opacity="0.6"
          >
            <title>{{ p.title }} ({{ p.genre }})</title>
          </circle>
        </svg>
      </div>
    </section>

    <!-- ============ 本周推荐 ============ -->
    <div class="flex items-center justify-between mt-8 mb-4">
      <h3 class="text-h3 text-ink">本周为你推荐</h3>
      <span class="text-[12px] font-light text-ink-faint">AI 基于曲风 / 情绪 / 特征匹配</span>
    </div>
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
      <div
        v-for="s in songs.slice(0, 5)"
        :key="s.id"
        class="bg-card rounded-r-lg overflow-hidden border border-line hover:-translate-y-0.5 hover:shadow-hover transition-shadow duration-300 group cursor-pointer"
        @click="playWeekly(s)"
      >
        <div class="relative h-24 overflow-hidden">
          <img v-if="s.cover_url" :src="s.cover_url" :alt="s.title" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" loading="lazy" />
          <div v-else class="w-full h-full grid place-items-center text-white text-xl font-bold" :style="{ background: `linear-gradient(150deg, ${s.cover_color}, ${s.cover_color}aa)` }">
            {{ s.title.slice(0, 1) }}
          </div>
          <div class="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
          <span class="absolute bottom-1.5 right-1.5 text-[10px] font-medium text-white/90 bg-black/40 backdrop-blur-[6px] rounded-pill px-2 py-0.5">
            {{ GENRE_ZH[s.genre] || s.genre }}
          </span>
        </div>
        <div class="p-3">
          <p class="text-[13px] font-semibold text-ink truncate">{{ s.title }}</p>
          <p class="text-[11px] font-light text-ink-faint truncate mt-0.5">{{ s.artist }} · {{ fmt(s.duration) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>