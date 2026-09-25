<!-- 应用外壳：侧边栏导航 + 毛玻璃顶栏 + 页面出口 + 全局播放条 + Toast
顶栏：Logo + 返回按钮 + 全局搜索 + 说出你的需求 -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PlayerBar from '@/components/PlayerBar.vue'
import Sidebar from '@/components/Sidebar.vue'
import ToastHost from '@/components/ToastHost.vue'
import { api, checkBackend } from '@/api'
import type { Song } from '@/api/types'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const route = useRoute()
const toast = useToastStore()

onMounted(async () => {
  const ok = await checkBackend()
  if (!ok) {
    toast.show('后端未连接，已进入 Mock 演示模式', 'info', 3600)
  }
})

// ---------- 全局搜索 ----------
const query = ref('')
const results = ref<Song[]>([])
const showResults = ref(false)
const searching = ref(false)
let debounceTimer: number | null = null

function onSearchInput() {
  showResults.value = true
  if (debounceTimer) clearTimeout(debounceTimer)
  const kw = query.value.trim()
  if (!kw) {
    results.value = []
    return
  }
  debounceTimer = window.setTimeout(async () => {
    searching.value = true
    try {
      const list = await api.listSongs({ keyword: kw })
      // 同时查 标题/歌手/专辑/情绪 模糊匹配
      const k = kw.toLowerCase()
      const merged = [
        ...list,
        ...(await api.listSongs({})).filter((s) =>
          s.title.toLowerCase().includes(k) ||
          s.artist.toLowerCase().includes(k) ||
          (s.album || '').toLowerCase().includes(k) ||
          (s.mood_tags || []).some((m) => m.toLowerCase().includes(k)),
        ),
      ]
      const seen = new Set<number>()
      results.value = merged.filter((s) => !seen.has(s.id) && seen.add(s.id)).slice(0, 10)
    } catch {
      results.value = []
    } finally {
      searching.value = false
    }
  }, 250)
}

function openResult(s: Song) {
  showResults.value = false
  query.value = ''
  router.push({ name: 'song-detail', params: { id: String(s.id) } })
}

function clearSearch() {
  query.value = ''
  results.value = []
  showResults.value = false
}

// ---------- 顶栏返回按钮 + Logo ----------
const navStack = ref<string[]>([])   // 记录进入的页面路径
const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '深夜好 🌙'
  if (h < 11) return '早上好 ☀️'
  if (h < 14) return '中午好 🍱'
  if (h < 18) return '下午好 👋'
  return '晚上好 🌆'
})

// 监听路由变化,记录栈(用于返回上级)
function trackNav(to: string, from: string) {
  if (!from || from === to) return
  if (route.meta?.title === 'TuneMatch') return  // 跳过顶部 path
  navStack.value.push(from)
  if (navStack.value.length > 30) navStack.value.shift()
}

function goBack() {
  if (navStack.value.length) {
    const prev = navStack.value.pop()!
    router.push(prev)
  } else if (window.history.length > 1) router.back()
  else router.push('/')
}

const showBack = computed(() => route.name !== 'home')

onMounted(() => {
  router.afterEach((to: any, from: any) => {
    trackNav(to.fullPath as string, from.fullPath as string)
  })
})
</script>

<template>
  <div class="min-h-screen flex flex-col bg-bg" @click="showResults = false">
    <!-- 顶部导航：毛玻璃 sticky -->
    <header class="sticky top-0 z-30 border-b border-line bg-bg/70 backdrop-blur-[20px] backdrop-saturate-[180%]">
      <div class="max-w-[1120px] mx-auto px-5 h-[52px] flex items-center gap-3 max-[560px]:px-3 max-[560px]:gap-2">
        <!-- 左：返回 + Logo + 问候 -->
        <div class="flex items-center gap-2.5 shrink-0">
          <button
            v-if="showBack"
            class="w-8 h-8 rounded-full grid place-items-center text-ink-soft hover:bg-black/5 hover:text-ink transition-colors"
            title="返回上级"
            @click="goBack"
          >
            <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </button>
          <button
            class="flex items-center gap-2 group"
            title="返回首页"
            @click="router.push('/')"
          >
            <span class="w-8 h-8 rounded-r-md bg-gradient-to-br from-brand to-ai grid place-items-center text-white font-bold text-[15px] shadow-btn transition-transform group-hover:scale-105 group-active:scale-95">♪</span>
            <span class="text-[15px] font-semibold text-ink tracking-tight max-[560px]:hidden">TuneMatch</span>
          </button>
          <span class="text-[13px] font-light text-ink-faint max-[560px]:hidden">{{ greeting }}</span>
        </div>

        <!-- 中：全局搜索 -->
        <div class="flex-1 relative max-w-md">
          <div
            class="flex items-center gap-2 bg-bg border rounded-pill px-3.5 py-2 text-[13px] transition-colors"
            :class="showResults ? 'border-brand shadow-btn' : 'border-line'"
          >
            <svg viewBox="0 0 24 24" class="w-4 h-4 text-ink-faint shrink-0" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="7" />
              <path d="M20 20l-3.5-3.5" />
            </svg>
            <input
              v-model="query"
              class="flex-1 bg-transparent text-ink placeholder:text-ink-faint focus:outline-none min-w-0"
              placeholder="搜索歌曲、艺人、专辑、心情..."
              @click.stop="showResults = !!query || true"
              @input="onSearchInput"
              @keyup.enter="onSearchInput"
            />
            <button
              v-if="query"
              class="w-4 h-4 grid place-items-center text-ink-faint hover:text-ink"
              title="清除"
              @click.stop="clearSearch"
            >
              <svg viewBox="0 0 24 24" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M6 18L18 6" /></svg>
            </button>
            <span v-if="searching" class="w-3.5 h-3.5 rounded-full border-2 border-brand/30 border-t-brand animate-spin shrink-0" />
          </div>

          <!-- 搜索结果下拉 -->
          <div
            v-if="showResults && query.trim()"
            class="absolute top-[calc(100%+6px)] left-0 right-0 bg-card rounded-r-md border border-line shadow-hover overflow-hidden z-40"
            @click.stop
          >
            <div v-if="searching && !results.length" class="px-3 py-4 text-center text-[12px] text-ink-faint">
              正在搜索「{{ query }}」…
            </div>
            <div v-else-if="!results.length" class="px-3 py-4 text-center text-[12px] text-ink-faint">
              没有匹配「{{ query }}」的歌曲
            </div>
            <div v-else class="max-h-[400px] overflow-y-auto">
              <button
                v-for="s in results"
                :key="s.id"
                class="w-full flex items-center gap-2.5 px-3 py-2 hover:bg-black/5 transition-colors text-left"
                @click="openResult(s)"
              >
                <img v-if="s.cover_url" :src="s.cover_url" :alt="s.title" class="w-9 h-9 rounded-r-sm object-cover shrink-0" />
                <div v-else class="w-9 h-9 rounded-r-sm grid place-items-center text-white text-[12px] font-semibold shrink-0" :style="{ background: `linear-gradient(150deg, ${s.cover_color}, ${s.cover_color}aa)` }">
                  {{ s.title.slice(0, 1) }}
                </div>
                <div class="min-w-0 flex-1">
                  <p class="text-[13px] font-medium text-ink truncate">{{ s.title }}</p>
                  <p class="text-[11px] font-light text-ink-faint truncate">{{ s.artist }} · {{ s.album || (s.mood_tags?.[0] || '') }}</p>
                </div>
                <svg viewBox="0 0 24 24" class="w-4 h-4 text-ink-faint shrink-0" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6" /></svg>
              </button>
            </div>
          </div>
        </div>

        <!-- 右：说出你的需求 -->
        <button class="shrink-0 flex items-center gap-[7px] px-[18px] py-[9px] rounded-pill text-[13.5px] font-medium text-white bg-brand hover:bg-brand-hover hover:scale-[1.03] active:scale-[0.97] transition-all max-[560px]:px-3" @click="router.push('/assistant')">
          <svg viewBox="0 0 24 24" class="w-[15px] h-[15px]" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round">
            <path d="M5 17V7.5" /><path d="M9 19V5" /><path d="M13 17v-7" /><path d="M17 19V9" />
          </svg>
          <span class="max-[560px]:hidden">说出你的需求</span>
        </button>
      </div>
    </header>

    <!-- 主体：侧边栏 + 内容 -->
    <div class="flex-1 flex min-w-0">
      <Sidebar />
      <main class="flex-1 min-w-0 pb-[64px] max-[768px]:pb-[56px]">
        <RouterView />
      </main>
    </div>

    <!-- 全局播放条 -->
    <PlayerBar />

    <!-- Toast -->
    <ToastHost />
  </div>
</template>
