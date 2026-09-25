<!-- 页面一：推荐主页 —— Apple Store 风格
Bento Grid Top 5 + 场景探索（4 渐变卡）+ 智能录入弹层 -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { smartApi } from '@/api'
import type { ImportResult, Playlist, RecommendResult, Song } from '@/api/types'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import DropZoneUpload from '@/components/DropZoneUpload.vue'
import PlaylistEditDialog from '@/components/PlaylistEditDialog.vue'
import SongCard from '@/components/SongCard.vue'
import { usePlayerStore } from '@/stores/player'
import { usePlaylistStore } from '@/stores/playlist'
import { useToastStore } from '@/stores/toast'

const playlistStore = usePlaylistStore()
const player = usePlayerStore()
const toast = useToastStore()

const songs = ref<Song[]>([])
const loading = ref(false)
const search = ref('')
const filterGenre = ref('')
const filterMood = ref('')
const genres = ref<string[]>([])
const moods = ['开心', '悲伤', '浪漫', '治愈', '怀旧', '热血', '放松', '梦幻']

// 歌单编辑弹窗
const editingPlaylist = ref<Playlist | null>(null)
const showDeleteConfirm = ref(false)
const pendingDeleteId = ref(0)

// 智能录入弹层
const showInput = ref(false)
const inputMode = ref<'text' | 'tags' | 'seed'>('text')
const inputText = ref('')
const inputTags = ref<string[]>([])
const inputScene = ref('')
const scenes = ['通勤', '健身', '助眠', '学习', '工作', '做饭', '开车', '旅行', '聚会']
const recommendResult = ref<RecommendResult | null>(null)
const recommending = ref(false)

const sceneNames: Record<string, string> = {
  commute: '通勤', work: '工作', study: '学习', workout: '健身',
  sleep: '助眠', cooking: '做饭', drive: '开车', travel: '旅行', party: '聚会',
}

// 场景探索（Apple 稿 4 卡）
const sceneCards = [
  { key: 'study', name: '专注学习', sub: 'Lo-fi · 白噪音 · 钢琴 · 60–90 BPM', grad: 'linear-gradient(160deg,#36B3A0,#1E7A6D)', icon: 'M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z' },
  { key: 'workout', name: '运动健身', sub: '高强度节拍 · 140+ BPM · 燃脂进行时', grad: 'linear-gradient(160deg,#FF7A45,#D9372E)', icon: 'M6.5 6.5L17.5 17.5M17.5 6.5L6.5 17.5M12 3.5a8.5 8.5 0 1 0 0 17 8.5 8.5 0 0 0 0-17z' },
  { key: 'sleep', name: '深夜助眠', sub: '环境音 · 慢节奏 · 自然白噪', grad: 'linear-gradient(160deg,#6A5CF0,#3A2D9E)', icon: 'M21 12.5A8.5 8.5 0 1 1 11.5 3 7 7 0 0 0 21 12.5z' },
  { key: 'commute', name: '通勤路上', sub: '城市节拍 · 轻爵士 · 早高峰提振', grad: 'linear-gradient(160deg,#4AA8FF,#1E63C9)', icon: 'M5 4h14a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1zM5 11h14M9 18v2M15 18v2' },
]

// Bento Top5（大卡 + 4 小卡）
const top5 = computed(() => [...filteredSongs.value].slice(0, 5))
const featured = computed(() => top5.value[0])
const smallCards = computed(() => top5.value.slice(1))

const filteredSongs = computed(() => {
  let list = [...songs.value]
  if (filterGenre.value) list = list.filter((s) => s.genre === filterGenre.value)
  if (filterMood.value) list = list.filter((s) => s.mood_tags.includes(filterMood.value))
  if (search.value.trim()) {
    const kw = search.value.trim().toLowerCase()
    list = list.filter((s) => s.title.toLowerCase().includes(kw) || s.artist.toLowerCase().includes(kw))
  }
  return list
})

async function loadSongs() {
  loading.value = true
  try {
    songs.value = await smartApi.listSongs()
  } finally {
    loading.value = false
  }
}

async function loadGenres() {
  try {
    genres.value = await smartApi.listGenres()
  } catch {
    genres.value = []
  }
}

onMounted(async () => {
  await Promise.all([loadSongs(), loadGenres(), playlistStore.fetchAll()])
})

function playAll() {
  if (!top5.value.length) return
  player.playSong(top5.value[0], top5.value)
}

function onAddToPlaylist(song: Song) {
  const pl = playlistStore.active
  if (!pl) {
    toast.show('请先创建歌单', 'info')
    return
  }
  toast.show(`已将《${song.title}》加入「${pl.name}」`, 'success')
}

// 新建歌单 → 直接打开编辑弹窗
async function createPlaylist() {
  const pl = await playlistStore.create('新建歌单')
  editingPlaylist.value = pl
}

function openEdit(pl: Playlist) {
  playlistStore.select(pl.id)
  editingPlaylist.value = pl
}

async function savePlaylist(patch: { name: string; cover_color: string }) {
  if (!editingPlaylist.value) return
  await playlistStore.update(editingPlaylist.value.id, patch)
  editingPlaylist.value = null
  toast.show('歌单已保存', 'success')
}

function deleteEditingPlaylist() {
  if (!editingPlaylist.value) return
  pendingDeleteId.value = editingPlaylist.value.id
  editingPlaylist.value = null
  showDeleteConfirm.value = true
}

async function confirmDelete() {
  await playlistStore.remove(pendingDeleteId.value)
  showDeleteConfirm.value = false
  toast.show('歌单已删除', 'success')
}

// 拖拽导入完成 → 刷新歌单列表
async function onImported(_result: ImportResult) {
  await playlistStore.fetchAll()
}

// 从歌单移除歌曲
async function removeSongFromPlaylist(songId: number) {
  const pl = playlistStore.active
  if (!pl) return
  try {
    const { api } = await import('@/api')
    await api.removeSongFromPlaylist(pl.id, songId)
    await playlistStore.fetchAll()
    toast.show('已从歌单移除', 'success')
  } catch (e) {
    toast.show((e as Error).message || '移除失败', 'error')
  }
}

async function submitRecommend() {
  recommending.value = true
  recommendResult.value = null
  try {
    if (inputMode.value === 'tags') {
      recommendResult.value = await smartApi.recommend({ mode: 'tags', tags: inputTags.value, scene: inputScene.value, limit: 6 })
    } else {
      recommendResult.value = await smartApi.recommend({ mode: 'text', text: inputText.value, limit: 6 })
    }
  } catch (e) {
    toast.show((e as Error).message || '推荐失败', 'error')
  } finally {
    recommending.value = false
  }
}

function resetInput() {
  showInput.value = true
  inputMode.value = 'text'
  inputText.value = ''
  inputTags.value = []
  inputScene.value = ''
  recommendResult.value = null
}

function toggleTag(t: string) {
  const i = inputTags.value.indexOf(t)
  if (i >= 0) inputTags.value.splice(i, 1)
  else inputTags.value.push(t)
}
</script>

<template>
  <div class="max-w-[1120px] mx-auto px-7 max-[560px]:px-4">
    <!-- ============ 首屏 · 本周上新 Top 5 ============ -->
    <section class="pt-14 pb-4 max-[900px]:pt-10">
      <div class="flex items-end justify-between mb-[26px] flex-wrap gap-4">
        <div>
          <p class="text-[13px] font-semibold tracking-[0.06em] text-brand uppercase mb-2">本周上新 · New Arrivals</p>
          <h2 class="text-display text-ink">为你甄选的 Top 5</h2>
          <p class="mt-2.5 text-[16px] font-light text-ink-soft max-w-[560px]">
            基于你的听歌习惯与此刻心情，AI 从曲库中精选五首——每一首都值得完整听完。
          </p>
        </div>
        <button class="flex items-center gap-[7px] px-[22px] py-[9px] rounded-pill text-[14px] font-medium text-white bg-brand hover:bg-brand-hover hover:scale-[1.03] active:scale-[0.97] transition-all" @click="playAll">
          <svg viewBox="0 0 24 24" class="w-[15px] h-[15px]" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round">
            <path d="M5 17V7.5" /><path d="M9 19V5" /><path d="M13 17v-7" /><path d="M17 19V9" />
          </svg>
          播放全部
        </button>
      </div>

      <div v-if="loading" class="text-center text-ink-soft py-24 text-body">加载中…</div>

      <!-- Bento Grid -->
      <div v-else-if="top5.length" class="grid grid-cols-3 gap-4 auto-rows-[300px] max-[900px]:grid-cols-2 max-[900px]:auto-rows-auto max-[560px]:grid-cols-1">
        <!-- Top1 大卡（占 2 行） -->
        <SongCard
          v-if="featured"
          :song="featured"
          :featured="true"
          :rank="1"
          class="max-[900px]:col-span-2 max-[560px]:col-span-1"
          @add="onAddToPlaylist"
        />
        <!-- Top 2-5 小卡 -->
        <SongCard
          v-for="(s, i) in smallCards"
          :key="s.id"
          :song="s"
          :rank="i + 2"
          :show-reason="false"
          @add="onAddToPlaylist"
        />
      </div>
      <div v-else class="text-center text-ink-faint py-24 text-body">没有匹配的歌曲</div>
    </section>

    <!-- ============ 场景探索 · 帮手在此 ============ -->
    <section class="pt-[68px] pb-4">
      <div class="section-head mb-[26px]">
        <div>
          <p class="text-[13px] font-semibold tracking-[0.06em] text-brand uppercase mb-2">帮手在此 · Ready to Help</p>
          <h2 class="text-display text-ink">此刻需要什么，交给场景歌单</h2>
          <p class="mt-2.5 text-[16px] font-light text-ink-soft max-w-[560px]">
            说出场景，AI 自动匹配能量、BPM 与曲风——四组场景，一键生成专属歌单。
          </p>
        </div>
      </div>

      <div class="grid grid-cols-4 gap-4 max-[900px]:grid-cols-2 max-[560px]:grid-cols-1">
        <article
          v-for="sc in sceneCards"
          :key="sc.key"
          class="relative aspect-square rounded-r-lg overflow-hidden flex flex-col justify-between p-[22px] text-white cursor-pointer transition-all duration-[450ms] hover:-translate-y-1 hover:shadow-hover"
          :style="{ background: sc.grad }"
          @click="inputScene = sceneNames[sc.key] as string; inputMode = 'tags'; resetInput(); inputTags = ['学习','治愈']; inputScene = sceneNames[sc.key] as string"
        >
          <!-- 背景音符装饰 -->
          <svg viewBox="0 0 280 280" preserveAspectRatio="xMidYMid slice" class="absolute inset-0 w-full h-full opacity-90">
            <g fill="rgba(255,255,255,0.15)">
              <rect x="46" y="80" width="12" height="120" rx="6" /><rect x="70" y="56" width="12" height="168" rx="6" />
              <rect x="94" y="96" width="12" height="88" rx="6" /><rect x="118" y="40" width="12" height="200" rx="6" />
              <rect x="142" y="72" width="12" height="136" rx="6" /><rect x="166" y="60" width="12" height="160" rx="6" />
              <rect x="190" y="92" width="12" height="96" rx="6" /><rect x="214" y="48" width="12" height="184" rx="6" />
            </g>
          </svg>

          <div class="relative z-10 w-11 h-11 rounded-[13px] bg-white/20 backdrop-blur-[6px] grid place-items-center">
            <svg viewBox="0 0 24 24" class="w-[22px] h-[22px]" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path :d="sc.icon" />
            </svg>
          </div>
          <div class="relative z-10">
            <h3 class="text-[20px] font-bold tracking-[-0.015em]">{{ sc.name }}</h3>
            <p class="text-[13px] font-light opacity-85 mt-0.5">{{ sc.sub }}</p>
            <span class="inline-flex items-center gap-1.5 text-[13px] font-medium mt-3.5 opacity-0 translate-y-1.5 transition-all duration-300 group-hover:opacity-100 group-hover:translate-y-0 hover:opacity-100">
              生成歌单
              <svg viewBox="0 0 24 24" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
            </span>
          </div>
        </article>
      </div>
    </section>

    <!-- ============ 全部歌曲 + 筛选 ============ -->
    <section class="pt-[68px] pb-8">
      <div class="flex items-center justify-between mb-6 flex-wrap gap-3">
        <h2 class="text-display text-ink">全部歌曲</h2>
        <div class="flex items-center gap-2 max-[560px]:w-full">
          <!-- 显眼搜索框（搜索图标 + 大圆角 + 占满宽度） -->
          <div class="flex items-center gap-2 bg-card border border-line rounded-pill px-4 py-2 focus-within:border-brand transition-colors w-72 max-[560px]:flex-1">
            <svg viewBox="0 0 24 24" class="w-4 h-4 text-ink-faint shrink-0" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="7" />
              <path d="M20 20l-3.5-3.5" />
            </svg>
            <input
              v-model="search"
              class="flex-1 bg-transparent text-[14px] text-ink placeholder:text-ink-faint focus:outline-none min-w-0"
              placeholder="搜索歌曲、艺人、心情..."
            />
          </div>
          <select v-model="filterGenre" class="bg-card border border-line rounded-pill text-[14px] px-3 py-2 text-ink focus:outline-none focus:border-brand">
            <option value="">全部曲风</option>
            <option v-for="g in genres" :key="g" :value="g">{{ g }}</option>
          </select>
          <select v-model="filterMood" class="bg-card border border-line rounded-pill text-[14px] px-3 py-2 text-ink focus:outline-none focus:border-brand">
            <option value="">全部情绪</option>
            <option v-for="m in moods" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>
      </div>

      <div class="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4">
        <SongCard v-for="s in filteredSongs.slice(5)" :key="s.id" :song="s" :show-reason="false" @add="onAddToPlaylist" />
      </div>
      <p class="text-[12px] font-light text-ink-faint mt-6">
        共 {{ filteredSongs.length }} 首 · 最高匹配 {{ filteredSongs.length ? Math.max(...filteredSongs.map((s) => s.match)) : 0 }}%
      </p>
    </section>

    <!-- ============ 智能录入弹层 ============ -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showInput" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4 overflow-y-auto" @click.self="showInput = false">
          <div class="bg-card rounded-r-lg p-6 w-full max-w-2xl my-8 shadow-hover">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-h3 text-ink">说出你的需求</h3>
              <button class="text-ink-faint hover:text-ink" @click="showInput = false">✕</button>
            </div>

            <div class="flex gap-2 mb-4">
              <button
                v-for="m in [{ k: 'text', label: '文本' }, { k: 'tags', label: '标签' }, { k: 'seed', label: '种子歌曲' }]"
                :key="m.k"
                class="px-4 py-1.5 rounded-pill text-[13px] border border-line bg-card text-ink-soft transition-colors"
                :class="{ '!bg-brand !text-white !border-brand': inputMode === m.k }"
                @click="inputMode = m.k as 'text' | 'tags' | 'seed'"
              >
                {{ m.label }}
              </button>
            </div>

            <template v-if="inputMode !== 'tags'">
              <textarea
                v-model="inputText"
                class="w-full min-h-[72px] bg-bg border border-line rounded-r-sm px-3 py-2 text-[14px] text-ink placeholder:text-ink-faint focus:outline-none focus:border-brand mb-3"
                :placeholder="inputMode === 'seed' ? '输入种子歌曲名，如：晴天' : '描述你想听的音乐，如：适合下夜班听的治愈系民谣'"
              />
            </template>
            <template v-else>
              <div class="flex flex-wrap gap-2 mb-3">
                <button
                  v-for="m in moods"
                  :key="m"
                  class="px-3 py-1 rounded-pill text-[13px] border border-line bg-card text-ink-soft transition-colors"
                  :class="{ '!bg-brand !text-white !border-brand': inputTags.includes(m) }"
                  @click="toggleTag(m)"
                >
                  {{ m }}
                </button>
              </div>
              <div class="flex flex-wrap items-center gap-2 mb-3">
                <span class="text-[13px] text-ink-soft">场景：</span>
                <select v-model="inputScene" class="bg-card border border-line rounded-pill text-[13px] px-3 py-1 text-ink focus:outline-none focus:border-brand">
                  <option value="">不限</option>
                  <option v-for="s in scenes" :key="s" :value="s">{{ s }}</option>
                </select>
              </div>
            </template>

            <button
              class="w-full py-2.5 rounded-pill text-[14px] font-medium text-white bg-brand hover:bg-brand-hover disabled:opacity-40 transition-all"
              :disabled="recommending || (inputMode !== 'tags' && !inputText.trim())"
              @click="submitRecommend"
            >
              {{ recommending ? '推荐中…' : '开始推荐' }}
            </button>

            <div v-if="recommendResult" class="mt-4 flex flex-col gap-2">
              <div class="flex items-center gap-2">
                <h4 class="text-h3 text-ink">为你推荐</h4>
                <span v-if="recommendResult.degraded" class="text-[12px] text-ink-faint">（Mock 模式）</span>
              </div>
              <div class="flex flex-col gap-2 max-h-72 overflow-y-auto pr-1">
                <div
                  v-for="s in recommendResult.songs"
                  :key="s.id"
                  class="flex items-center gap-3 bg-card rounded-r-md p-3 cursor-pointer border border-line hover:border-brand/40 transition-colors"
                  @click="player.playSong(s, recommendResult!.songs)"
                >
                  <div
                    class="w-10 h-10 rounded-r-sm grid place-items-center text-white text-sm font-semibold shrink-0"
                    :style="{ background: `linear-gradient(150deg, ${s.cover_color}, ${s.cover_color}aa)` }"
                  >
                    {{ s.title.slice(0, 1) }}
                  </div>
                  <div class="min-w-0 flex-1">
                    <p class="text-[14px] text-ink truncate">{{ s.title }}</p>
                    <p class="text-[12px] font-light text-ink-soft truncate">{{ s.artist }} · {{ s.genre }}</p>
                  </div>
                  <span class="text-[13px] font-bold text-brand bg-brand-soft rounded-pill px-2.5 py-[3px]">{{ s.match }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 删除确认 -->
    <ConfirmDialog :open="showDeleteConfirm" title="删除歌单" message="删除后不可恢复，确定继续吗？" @confirm="confirmDelete" @cancel="showDeleteConfirm = false" />

    <!-- 歌单编辑弹窗 -->
    <PlaylistEditDialog
      :playlist="editingPlaylist"
      @close="editingPlaylist = null"
      @save="savePlaylist"
      @cover-uploaded="playlistStore.fetchAll()"
      @delete="deleteEditingPlaylist"
    />

    <!-- 我的歌单栏 -->
    <section class="pt-8 pb-12">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-h3 text-ink">我的歌单</h3>
        <button class="flex items-center gap-2 px-4 py-2 rounded-pill text-[13px] font-medium text-white bg-ink hover:bg-black transition-colors" @click="createPlaylist">
          <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14" stroke-linecap="round" /></svg>
          新建歌单
        </button>
      </div>

      <div v-if="playlistStore.playlists.length" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <div
          v-for="pl in playlistStore.playlists"
          :key="pl.id"
          class="bg-card rounded-r-lg overflow-hidden border border-line cursor-pointer group hover:-translate-y-1 hover:shadow-hover transition-all duration-300"
          :class="{ 'ring-2 ring-brand': playlistStore.activeId === pl.id }"
          @click="playlistStore.select(pl.id)"
        >
          <!-- 封面（自定义头像优先） -->
          <div class="h-24 grid place-items-center text-white text-3xl font-bold relative overflow-hidden">
            <img v-if="pl.cover_url" :src="pl.cover_url" class="absolute inset-0 w-full h-full object-cover" alt="封面" />
            <div
              v-else
              class="absolute inset-0 grid place-items-center"
              :style="{ background: `linear-gradient(150deg, ${pl.cover_color}, ${pl.cover_color}aa)` }"
            >
              {{ pl.name.slice(0, 1) || '♪' }}
            </div>
            <!-- 编辑按钮 -->
            <button
              class="absolute top-2 right-2 w-7 h-7 rounded-full bg-white/90 text-ink grid place-items-center opacity-0 group-hover:opacity-100 transition-opacity z-10"
              title="编辑歌单"
              @click.stop="openEdit(pl)"
            >
              <svg viewBox="0 0 24 24" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 20h9M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z" />
              </svg>
            </button>
          </div>
          <div class="p-3">
            <p class="text-[13px] font-semibold text-ink truncate">{{ pl.name }}</p>
            <p class="text-[11px] font-light text-ink-faint">{{ pl.song_count }} 首{{ pl.scene ? ' · ' + pl.scene : '' }}</p>
          </div>
        </div>
      </div>
      <p v-else class="text-[13px] font-light text-ink-faint py-6 text-center">
        还没有歌单，点「新建歌单」创建第一个吧
      </p>

      <!-- 当前歌单详情：拖拽导入 + 歌曲列表 -->
      <div v-if="playlistStore.active" class="mt-8">
        <div class="flex items-center gap-3 mb-4">
          <h4 class="text-h3 text-ink">「{{ playlistStore.active.name }}」的歌曲</h4>
          <span class="text-[12px] font-light text-ink-faint">{{ playlistStore.active.song_count }} 首</span>
          <button class="ml-auto text-[13px] text-brand hover:underline" @click="openEdit(playlistStore.active!)">管理歌单</button>
        </div>

        <!-- 拖拽导入区 -->
        <DropZoneUpload
          v-if="playlistStore.active"
          :playlist-id="playlistStore.active.id"
          @imported="onImported"
        />

        <!-- 歌单内歌曲 -->
        <div v-if="playlistStore.active.songs.length" class="mt-4 flex flex-col gap-2">
          <div
            v-for="(s, i) in playlistStore.active.songs"
            :key="s.id"
            class="flex items-center gap-3 bg-card rounded-r-md p-3 border border-line hover:border-brand/40 transition-colors cursor-pointer"
            @click="player.playSong(s, playlistStore.active!.songs)"
          >
            <span class="text-[12px] font-light text-ink-faint w-5 text-center">{{ i + 1 }}</span>
            <div
              class="w-10 h-10 rounded-r-sm grid place-items-center text-white text-sm font-semibold shrink-0"
              :style="{ background: `linear-gradient(150deg, ${s.cover_color}, ${s.cover_color}aa)` }"
            >
              {{ s.title.slice(0, 1) }}
            </div>
            <div class="min-w-0 flex-1">
              <p class="text-[14px] text-ink truncate">{{ s.title }}</p>
              <p class="text-[12px] font-light text-ink-soft truncate">{{ s.artist }}{{ s.genre && s.genre !== 'local' ? ' · ' + s.genre : '' }}</p>
            </div>
            <span v-if="s.genre === 'local'" class="text-[11px] text-ink-faint bg-bg rounded-pill px-2 py-0.5 shrink-0">本地导入</span>
            <button
              class="w-8 h-8 rounded-full grid place-items-center text-ink-faint hover:text-danger hover:bg-danger/5 transition-colors shrink-0"
              title="从歌单移除"
              @click.stop="removeSongFromPlaylist(s.id)"
            >
              <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                <path d="M4 7h16M9 7V5h6v2M6 7l1 13h10l1-13" />
              </svg>
            </button>
          </div>
        </div>
        <p v-else-if="playlistStore.active.song_count === 0" class="text-[13px] font-light text-ink-faint py-4 text-center">
          这个歌单还是空的，拖拽歌曲文件导入，或从上方推荐卡片「加入歌单」
        </p>
      </div>
    </section>
  </div>
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
