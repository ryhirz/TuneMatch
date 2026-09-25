<!-- 页面二：AI 音乐助手 —— Apple Store 风格
左侧历史 + 右侧聊天（AI 回复内嵌歌曲卡片 + 歌单上下文选择 + 输入区文本/标签/语音） -->
<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { smartApi } from '@/api'
import type { Song } from '@/api/types'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { useChatStore } from '@/stores/chat'
import { usePlayerStore } from '@/stores/player'
import { usePlaylistStore } from '@/stores/playlist'
import { useToastStore } from '@/stores/toast'

const router = useRouter()

const chat = useChatStore()
const player = usePlayerStore()
const playlistStore = usePlaylistStore()
const toast = useToastStore()

const input = ref('')
const listRef = ref<HTMLElement | null>(null)
const recording = ref(false)
const quickTags = ['开心', '浪漫', '治愈', '热血', '放松', '怀旧', '摇滚', '民谣', '电子', '嘻哈']

const recommendedSongs = ref<Song[]>([])
const lastQuery = ref('')

const scrollable = computed(() => chat.messages)

async function send() {
  const text = input.value.trim()
  if (!text || chat.streaming) return
  input.value = ''
  await chat.send(text, contextPlaylistId.value || undefined)
  scrollBottom()
  try {
    const r = await smartApi.recommend({ mode: 'text', text, limit: 4 })
    recommendedSongs.value = r.songs
    lastQuery.value = text
  } catch {
    recommendedSongs.value = []
  }
}

// 歌单上下文：选择后 AI 会结合歌单歌曲回答
const contextPlaylistId = ref<number | null>(null)
const contextPlaylist = computed(() =>
  playlistStore.playlists.find((p) => p.id === contextPlaylistId.value) || null,
)

function toggleContext(id: number) {
  contextPlaylistId.value = contextPlaylistId.value === id ? null : id
  toast.show(contextPlaylistId.value ? '已携带歌单上下文，AI 将结合歌单回答' : '已取消歌单上下文', 'info')
}

function sendQuickTag(tag: string) {
  input.value = tag
  send()
}

function scrollBottom() {
  nextTick(() => {
    if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
  })
}

function scrollToMessage(m: { id?: number }) {
  if (!m.id) return
  const el = document.getElementById(`msg-${m.id}`)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

/** 复制消息文本到剪贴板 */
/** 跳转歌曲详情页（AI 推荐卡片点击） */
function goSongDetail(id: number) {
  router.push({ name: 'song-detail', params: { id: String(id) } })
}

async function copyMessage(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    toast.show('已复制到剪贴板', 'success', 1500)
  } catch {
    // 老浏览器 fallback
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    toast.show('已复制（fallback）', 'success', 1500)
  }
}

onMounted(() => {
  chat.loadHistory()
  playlistStore.fetchAll()
  scrollBottom()
  document.addEventListener('click', onGlobalClick)
})

// ---------- 右键菜单（删除对话） ----------
const contextMenu = ref<{ x: number; y: number; messageId: number } | null>(null)
const confirmDeleteOne = ref<number | null>(null)
const showClearConfirm = ref(false)

function openContextMenu(e: MouseEvent, messageId: number) {
  e.preventDefault()
  // 边界处理：靠近右/下边缘时翻转
  const w = 180
  const h = 140
  const x = Math.min(e.clientX, window.innerWidth - w - 8)
  const y = Math.min(e.clientY, window.innerHeight - h - 8)
  contextMenu.value = { x, y, messageId }
}

function closeContextMenu() {
  contextMenu.value = null
}

function onGlobalClick(e: MouseEvent) {
  const target = e.target as HTMLElement | null
  if (target && !target.closest?.('.ctx-menu')) closeContextMenu()
}

function ctxDeleteOne() {
  if (!contextMenu.value) return
  confirmDeleteOne.value = contextMenu.value.messageId
  closeContextMenu()
}

function ctxCopy() {
  if (!contextMenu.value) return
  const id = contextMenu.value.messageId
  const msg = chat.messages.find((m) => m.id === id)
  if (msg) {
    closeContextMenu()
    void copyMessage(msg.content)
  } else {
    closeContextMenu()
  }
}

function ctxClearAll() {
  closeContextMenu()
  showClearConfirm.value = true
}

async function doConfirmDeleteOne() {
  if (confirmDeleteOne.value == null) return
  chat.removePair(confirmDeleteOne.value)
  confirmDeleteOne.value = null
  toast.show('已删除该对话', 'success')
}

async function doClearAll() {
  showClearConfirm.value = false
  await chat.clearAll()
  toast.show('已清空全部历史', 'success')
}

onUnmounted(() => {
  document.removeEventListener('click', onGlobalClick)
})

function toggleRecord() {
  recording.value = !recording.value
  if (!recording.value) {
    toast.show('语音识别（Mock）：已生成语音文本', 'success')
    input.value = '适合健身时听的摇滚'
  }
}
</script>

<template>
  <div class="flex h-[calc(100vh-128px)] max-[768px]:h-[calc(100vh-112px)]">
    <!-- 左侧历史对话 -->
    <aside class="w-64 shrink-0 border-r border-line bg-card/60 backdrop-blur-[20px] p-4 flex flex-col max-[768px]:hidden">
      <h2 class="text-[14px] font-semibold text-ink mb-3">历史对话</h2>
      <div class="flex flex-col gap-1 overflow-y-auto">
        <div
          v-for="m in chat.messages.filter((x) => x.role === 'user').slice(-20).reverse()"
          :key="m.id ?? m.content"
          class="group flex items-center gap-1 px-2 py-1 rounded-r-sm hover:bg-black/5"
          @contextmenu.prevent="openContextMenu($event, m.id!)"
        >
          <button
            class="flex-1 text-left text-[13px] font-light text-ink-soft truncate transition-colors hover:text-ink px-1"
            @click="scrollToMessage(m)"
          >
            {{ m.content }}
          </button>
          <button
            class="w-5 h-5 rounded-full grid place-items-center text-ink-faint opacity-0 group-hover:opacity-100 hover:bg-danger/10 hover:text-danger transition-all shrink-0"
            title="删除这段对话"
            @click="confirmDeleteOne = m.id!"
          >
            <svg viewBox="0 0 24 24" class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <path d="M6 6l12 12M6 18L18 6" />
            </svg>
          </button>
        </div>
        <p v-if="!chat.messages.length" class="text-[13px] font-light text-ink-faint px-3 py-2">暂无对话，右键历史项可删除</p>
      </div>

      <!-- 清空全部 + 底部快捷入口 -->
      <div class="border-t border-line mt-3 pt-3 flex flex-col gap-1">
        <button
          v-if="chat.messages.length"
          class="flex items-center gap-2.5 px-3 py-2 rounded-[10px] text-[12.5px] text-ink-faint hover:bg-danger/5 hover:text-danger transition-colors"
          @click="showClearConfirm = true"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
            <path d="M4 7h16M9 7V5h6v2M6 7l1 13h10l1-13" />
          </svg>
          清空全部历史
        </button>
        <button class="flex items-center gap-2.5 px-3 py-2 rounded-[10px] text-[13px] text-ink-soft hover:bg-black/5 hover:text-ink transition-colors" @click="router.push('/recommendations')">
          <svg viewBox="0 0 24 24" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
          让我直接推荐 ↗
        </button>
        <button class="flex items-center gap-2.5 px-3 py-2 rounded-[10px] text-[13px] text-ink-soft hover:bg-black/5 hover:text-ink transition-colors" @click="router.push('/playlists')">
          <svg viewBox="0 0 24 24" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 6h16v12H4zM4 10h16M8 14h8" />
          </svg>
          去歌单管理
        </button>
        <button class="flex items-center gap-2.5 px-3 py-2 rounded-[10px] text-[13px] text-ink-soft hover:bg-black/5 hover:text-ink transition-colors" @click="router.push('/settings')">
          <svg viewBox="0 0 24 24" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 15a3 3 0 100-6 3 3 0 000 6z" /><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09a1.65 1.65 0 00-1-1.51 1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09a1.65 1.65 0 001.51-1 1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33h0a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51h0a1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00.33 1.82v0a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
          </svg>
          AI 接口设置
        </button>
      </div>
    </aside>

    <!-- 右键菜单（固定定位，跟随鼠标） -->
    <Teleport to="body">
      <div
        v-if="contextMenu"
        class="ctx-menu fixed z-[100] bg-card rounded-r-md py-1 shadow-hover border border-line min-w-[160px]"
        :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
        @click.stop
      >
        <button
          class="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-ink-soft hover:bg-black/5 hover:text-ink transition-colors"
          @click="scrollToMessage({ id: contextMenu.messageId }); closeContextMenu()"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          定位到对话
        </button>
        <button
          class="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-ink-soft hover:bg-black/5 hover:text-ink transition-colors"
          @click="ctxCopy"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><rect x="9" y="9" width="13" height="13" rx="2" /><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" /></svg>
          复制内容
        </button>
        <div class="h-px bg-line my-0.5" />
        <button
          class="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-danger hover:bg-danger/5 transition-colors"
          @click="ctxDeleteOne"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M4 7h16M9 7V5h6v2M6 7l1 13h10l1-13" /></svg>
          删除该对话
        </button>
        <button
          class="flex items-center gap-2 w-full px-3 py-2 text-[13px] text-danger hover:bg-danger/5 transition-colors"
          @click="ctxClearAll"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" /></svg>
          清空全部
        </button>
      </div>
    </Teleport>

    <!-- 自定义确认对话框 -->
    <ConfirmDialog
      :open="confirmDeleteOne != null"
      title="删除这段对话？"
      message="将同时删除这条问题与 AI 的回答,不可恢复。"
      confirmText="删除"
      danger
      @confirm="doConfirmDeleteOne"
      @cancel="confirmDeleteOne = null"
    />
    <ConfirmDialog
      :open="showClearConfirm"
      title="清空全部历史？"
      message="将永久删除所有对话记录,无法恢复。"
      confirmText="清空"
      danger
      @confirm="doClearAll"
      @cancel="showClearConfirm = false"
    />

    <!-- 右侧聊天窗口 -->
    <div class="flex-1 min-w-0 flex flex-col bg-transparent">
      <!-- 消息区 -->
      <div ref="listRef" class="flex-1 overflow-y-auto p-6 max-[768px]:p-3">
        <div class="max-w-3xl mx-auto flex flex-col gap-4">
          <!-- 欢迎语 -->
          <div v-if="!chat.messages.length" class="text-center py-16">
            <div class="w-14 h-14 rounded-full bg-gradient-to-br from-[#10B981] to-[#059669] text-white grid place-items-center mx-auto mb-3 shadow-btn">
              <svg viewBox="0 0 24 24" class="w-7 h-7" fill="none" stroke="currentColor" stroke-width="1.6">
                <path d="M12 2a4 4 0 014 4c0 1.1-.45 2.1-1.17 2.83L16 10a6 6 0 01-8 0l1.17-1.17A4 4 0 0112 2z" stroke-linecap="round" />
                <path d="M12 10v4M8 14h8M9.5 18h5" stroke-linecap="round" />
              </svg>
            </div>
            <h2 class="text-h3 text-ink mb-2">你好，我是 TuneMatch AI 助手 🎵</h2>
            <p class="text-[15px] font-light text-ink-soft">告诉我你想听什么，比如「来点深夜治愈的民谣」或「健身时听的摇滚」</p>
          </div>

          <!-- 消息流 -->
          <template v-for="(m, i) in scrollable" :key="m.id ?? i">
            <div v-if="m.role === 'user'" class="flex justify-end group">
              <div
                :id="`msg-${m.id}`"
                class="relative max-w-[75%] bg-brand text-white rounded-r-md rounded-br-none px-4 py-2.5 text-[15px] select-text cursor-context-menu"
                style="user-select: text; -webkit-user-select: text;"
                @contextmenu.prevent="openContextMenu($event, m.id!)"
              >
                {{ m.content }}
                <button
                  v-if="m.content"
                  class="absolute -bottom-2 -right-2 w-6 h-6 rounded-full bg-white/90 text-ink shadow-btn opacity-0 group-hover:opacity-100 hover:!bg-brand hover:!text-white transition-all grid place-items-center"
                  title="复制消息"
                  @click="copyMessage(m.content)"
                >
                  <svg viewBox="0 0 24 24" class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="9" width="13" height="13" rx="2" /><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" /></svg>
                </button>
              </div>
            </div>
            <div v-else class="flex gap-3 group">
              <div :id="`msg-${m.id}`" class="w-9 h-9 rounded-full bg-gradient-to-br from-[#10B981] to-[#059669] text-white grid place-items-center shrink-0">
                <svg viewBox="0 0 24 24" class="w-4.5 h-4.5" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path d="M12 2a4 4 0 014 4c0 1.1-.45 2.1-1.17 2.83L16 10a6 6 0 01-8 0l1.17-1.17A4 4 0 0112 2z" stroke-linecap="round" />
                </svg>
              </div>
              <div
                class="relative max-w-[75%] bg-card border border-line rounded-r-md rounded-tl-none px-4 py-2.5 text-[15px] text-ink select-text cursor-context-menu"
                style="user-select: text; -webkit-user-select: text;"
                @contextmenu.prevent="openContextMenu($event, m.id!)"
              >
                <span v-if="chat.streaming && !m.content" class="text-ink-faint">正在思考…</span>
                <span>{{ m.content }}</span>
                <!-- AI 推荐的歌曲卡片（点击跳详情） -->
                <div v-if="m.songs?.length" class="mt-3 grid gap-2" style="grid-template-columns: repeat(auto-fill, minmax(150px, 1fr))">
                  <button
                    v-for="s in m.songs"
                    :key="s.id"
                    class="group/card flex items-center gap-2 p-1.5 rounded-r-sm hover:bg-black/5 text-left transition-colors border border-transparent hover:border-line"
                    :title="`查看《${s.title}》详情`"
                    @click="goSongDetail(s.id)"
                  >
                    <div class="w-9 h-9 rounded-r-sm overflow-hidden shrink-0 relative">
                      <img v-if="s.cover_url" :src="s.cover_url" :alt="s.title" class="w-full h-full object-cover" />
                      <div v-else class="w-full h-full grid place-items-center text-white text-[12px] font-semibold" :style="{ background: 'linear-gradient(150deg,#4DABF7,#7C3AED)' }">
                        {{ s.title.slice(0, 1) }}
                      </div>
                    </div>
                    <div class="min-w-0 flex-1">
                      <p class="text-[12px] font-medium text-ink truncate">{{ s.title }}</p>
                      <p class="text-[10px] font-light text-ink-faint truncate">{{ s.artist }}</p>
                    </div>
                    <span class="text-[10px] font-semibold text-brand shrink-0 bg-brand-soft rounded-pill px-1.5 py-0.5">
                      {{ s.match }}%
                    </span>
                  </button>
                </div>
                <button
                  v-if="m.content"
                  class="absolute -bottom-2 -right-2 w-6 h-6 rounded-full bg-white/90 text-ink shadow-btn opacity-0 group-hover:opacity-100 hover:!bg-brand hover:!text-white transition-all grid place-items-center"
                  title="复制消息"
                  @click="copyMessage(m.content)"
                >
                  <svg viewBox="0 0 24 24" class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="9" width="13" height="13" rx="2" /><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" /></svg>
                </button>
              </div>
            </div>
          </template>

          <!-- 推荐歌曲卡片 -->
          <div v-if="recommendedSongs.length" class="flex gap-3 pl-12 max-[768px]:pl-0">
            <div class="flex-1 bg-card rounded-r-lg p-4 shadow-hover flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <p class="text-[13px] font-medium text-ink">根据「{{ lastQuery }}」推荐</p>
                <span class="text-[12px] font-light text-ink-faint">点击播放</span>
              </div>
              <div class="grid gap-2" style="grid-template-columns: repeat(auto-fill, minmax(160px, 1fr))">
                <button
                  v-for="s in recommendedSongs"
                  :key="s.id"
                  class="flex items-center gap-2 p-2 rounded-r-sm hover:bg-black/5 text-left transition-colors"
                  @click="player.playSong(s, recommendedSongs)"
                >
                  <div
                    class="w-10 h-10 rounded-r-sm grid place-items-center text-white text-sm font-semibold shrink-0"
                    :style="{ background: `linear-gradient(150deg, ${s.cover_color}, ${s.cover_color}aa)` }"
                  >
                    {{ s.title.slice(0, 1) }}
                  </div>
                  <div class="min-w-0">
                    <p class="text-[13px] text-ink truncate">{{ s.title }}</p>
                    <p class="text-[12px] font-light text-ink-faint truncate">{{ s.artist }} · {{ s.match }}%</p>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="border-t border-line bg-[rgba(255,255,255,0.85)] backdrop-blur-[20px] p-4">
        <div class="max-w-3xl mx-auto flex flex-col gap-2">
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="t in quickTags"
              :key="t"
              class="px-3 py-1 rounded-pill text-[13px] border border-line bg-card text-ink-soft hover:text-brand hover:border-brand/40 transition-colors"
              @click="sendQuickTag(t)"
            >
              {{ t }}
            </button>
          </div>

          <!-- 歌单上下文选择 -->
          <div class="flex items-center gap-1.5 flex-wrap">
            <span class="text-[12px] font-light text-ink-faint">歌单上下文：</span>
            <button
              v-for="pl in playlistStore.playlists"
              :key="pl.id"
              class="px-3 py-1 rounded-pill text-[12px] border border-line bg-card text-ink-soft transition-colors"
              :class="{ '!bg-brand !text-white !border-brand font-medium': contextPlaylistId === pl.id }"
              @click="toggleContext(pl.id)"
            >
              {{ pl.name }} · {{ pl.song_count }}
            </button>
            <span v-if="!playlistStore.playlists.length" class="text-[12px] font-light text-ink-faint">
              暂无歌单（去首页创建）
            </span>
            <span v-if="contextPlaylist" class="text-[12px] font-light text-ai ml-1">
              ✓ AI 将结合「{{ contextPlaylist.name }}」回答
            </span>
          </div>

          <div class="flex items-center gap-2">
            <button
              class="w-10 h-10 rounded-full grid place-items-center text-ink-soft hover:text-ink hover:bg-black/5 transition-colors shrink-0"
              :class="{ '!bg-danger !text-white': recording }"
              :title="recording ? '停止录音' : '语音输入'"
              @click="toggleRecord"
            >
              <svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6">
                <path d="M12 3a3 3 0 00-3 3v5a3 3 0 006 0V6a3 3 0 00-3-3z" stroke-linecap="round" />
                <path d="M5 11a7 7 0 0014 0M12 18v3" stroke-linecap="round" />
              </svg>
            </button>

            <input
              v-model="input"
              class="flex-1 bg-card border border-line rounded-pill text-[15px] px-4 py-2.5 text-ink placeholder:text-ink-faint focus:outline-none focus:border-brand"
              placeholder="输入你的音乐需求…（回车发送）"
              @keyup.enter="send"
            />

            <button
              class="px-5 py-2.5 rounded-pill text-[14px] font-medium text-white bg-brand hover:bg-brand-hover disabled:opacity-40 transition-all shrink-0"
              :disabled="!input.trim() || chat.streaming"
              @click="send"
            >
              {{ chat.streaming ? '…' : '发送' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
