<!-- 全局播放条：Apple 风格（64px 固定底部 · 毛玻璃 · 胶囊控制钮）
支持真实音频播放 + EQ 调节器弹层 + 播放队列 -->
<script setup lang="ts">
import { useRouter } from 'vue-router'
import EqualizerPanel from '@/components/EqualizerPanel.vue'
import { usePlayerStore } from '@/stores/player'

const router = useRouter()
const player = usePlayerStore()

const coverStyle = () => ({ background: `linear-gradient(150deg, ${player.current?.cover_color || '#4DABF7'}, ${player.current?.cover_color || '#4DABF7'}aa)` })

/** 点击封面/标题 → 进入当前歌曲详情页 */
function goDetail() {
  if (player.current) router.push({ name: 'song-detail', params: { id: String(player.current.id) } })
}

function fmtTime(s: number): string {
  if (!isFinite(s) || s <= 0) return '0:00'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${String(sec).padStart(2, '0')}`
}
</script>

<template>
  <footer
    class="fixed bottom-0 left-0 right-0 h-16 bg-[rgba(255,255,255,0.85)] backdrop-blur-[20px] backdrop-saturate-[180%] border-t border-line z-40 flex items-center px-4 gap-3 max-[768px]:h-14"
  >
    <!-- 左侧：封面 + 歌名（点击封面/标题进入详情） -->
    <div class="flex items-center gap-3 min-w-0 flex-shrink">
      <button
        class="w-12 h-12 rounded-r-sm grid place-items-center text-white font-semibold shrink-0 overflow-hidden relative cursor-pointer hover:ring-2 hover:ring-brand/40 transition-shadow max-[768px]:w-10 max-[768px]:h-10"
        :style="!player.current?.cover_url ? coverStyle() : undefined"
        title="查看歌曲详情"
        @click="goDetail"
      >
        <img v-if="player.current?.cover_url" :src="player.current.cover_url" :alt="player.current.title" class="w-full h-full object-cover" />
        <span v-else>{{ player.current ? player.current.title.slice(0, 1) : '♪' }}</span>
      </button>
      <div class="min-w-0 max-[768px]:hidden">
        <button
          class="text-[14px] font-medium text-ink truncate max-w-[200px] hover:text-brand transition-colors text-left"
          title="查看歌曲详情"
          @click="goDetail"
        >
          {{ player.current?.title || '未在播放' }}
        </button>
        <p class="text-[12px] font-light text-ink-soft truncate flex items-center gap-1.5">
          {{ player.current?.artist || '选择一首歌开始' }}
          <span v-if="player.isRealAudio && player.audioUrl.startsWith('http')" class="text-[10px] text-ai bg-emerald-50 rounded-pill px-1.5 py-0.5">试听 30s</span>
          <span v-else-if="player.isRealAudio" class="text-[10px] text-ai bg-emerald-50 rounded-pill px-1.5 py-0.5">本地音频</span>
          <span v-else-if="player.current" class="text-[10px] text-ink-faint bg-bg rounded-pill px-1.5 py-0.5">无音频</span>
        </p>
      </div>
    </div>

    <!-- 中间：播放控制 -->
    <div class="flex items-center gap-1.5 mx-auto shrink-0">
      <button class="w-9 h-9 rounded-full grid place-items-center text-ink-soft hover:text-ink hover:bg-black/5 transition-colors" :disabled="!player.hasQueue" @click="player.prev()">
        <svg viewBox="0 0 24 24" class="w-5 h-5" fill="currentColor"><path d="M6 5h2v14H6zM20 5v14L9 12z" /></svg>
      </button>
      <button
        class="w-10 h-10 rounded-full bg-brand text-white grid place-items-center hover:bg-brand-hover hover:scale-[1.05] active:scale-[0.95] transition-all disabled:opacity-40"
        :disabled="!player.hasQueue"
        @click="player.toggle()"
      >
        <svg v-if="player.playing" viewBox="0 0 24 24" class="w-5 h-5" fill="currentColor"><path d="M7 5h4v14H7zM13 5h4v14h-4z" /></svg>
        <svg v-else viewBox="0 0 24 24" class="w-5 h-5" fill="currentColor"><path d="M8 5v14l11-7z" /></svg>
      </button>
      <button class="w-9 h-9 rounded-full grid place-items-center text-ink-soft hover:text-ink hover:bg-black/5 transition-colors" :disabled="!player.hasQueue" @click="player.next()">
        <svg viewBox="0 0 24 24" class="w-5 h-5" fill="currentColor"><path d="M16 5h2v14h-2zM4 5v14l11-7z" /></svg>
      </button>
    </div>

    <!-- 右侧：EQ + 进度 + 队列 -->
    <div class="flex items-center gap-3 flex-shrink-0 w-80 max-[1024px]:w-48 max-[768px]:hidden">
      <span class="text-[11px] text-ink-faint w-8 text-right shrink-0">{{ fmtTime((player.progress / 100) * player.duration) }}</span>
      <input
        type="range" min="0" max="100" :value="player.progress"
        class="w-full accent-[#0071E3] cursor-pointer"
        @input="player.seek(Number(($event.target as HTMLInputElement).value))"
      />
      <span class="text-[11px] text-ink-faint w-8 shrink-0">{{ fmtTime(player.duration) }}</span>
      <button
        class="w-8 h-8 grid place-items-center transition-colors shrink-0"
        :class="player.showDevice ? 'text-brand' : 'text-ink-soft hover:text-ink'"
        :title="player.showDevice ? '收起输出设备' : '输出设备'"
        @click="player.showDevice = !player.showDevice; player.showEq = false; player.showQueue = false; if (player.showDevice) player.refreshOutputDevices()"
      >
        <svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 5L6 9H3v6h3l5 4V5zM16 9a3 3 0 010 6" />
        </svg>
      </button>
      <button
        class="w-8 h-8 grid place-items-center transition-colors shrink-0"
        :class="player.showEq ? 'text-brand' : 'text-ink-soft hover:text-ink'"
        :title="player.showEq ? '收起 EQ' : 'EQ 调节器'"
        @click="player.showEq = !player.showEq; player.showQueue = false; player.showDevice = false"
      >
        <svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
          <path d="M5 7h14M5 12h14M5 17h14" />
          <circle cx="9" cy="7" r="2" fill="currentColor" stroke="none" />
          <circle cx="15" cy="12" r="2" fill="currentColor" stroke="none" />
          <circle cx="7" cy="17" r="2" fill="currentColor" stroke="none" />
        </svg>
      </button>
      <button
        class="w-8 h-8 grid place-items-center transition-colors shrink-0"
        :class="player.showQueue ? 'text-brand' : 'text-ink-soft hover:text-ink'"
        :title="player.showQueue ? '收起队列' : '播放队列'"
        @click="player.showQueue = !player.showQueue; player.showEq = false; player.showDevice = false"
      >
        <svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6">
          <path d="M4 6h16M4 12h16M4 18h10" stroke-linecap="round" />
        </svg>
      </button>
    </div>

    <!-- 移动端简化控制 -->
    <div class="max-[768px]:flex items-center gap-2 ml-auto shrink-0 hidden">
      <button
        class="w-8 h-8 grid place-items-center transition-colors"
        :class="player.showEq ? 'text-brand' : 'text-ink-soft'"
        title="EQ"
        @click="player.showEq = !player.showEq; player.showQueue = false; player.showDevice = false"
      >
        <svg viewBox="0 0 24 24" class="w-4.5 h-4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
          <path d="M5 7h14M5 12h14M5 17h14" /><circle cx="9" cy="7" r="2" fill="currentColor" stroke="none" />
          <circle cx="15" cy="12" r="2" fill="currentColor" stroke="none" /><circle cx="7" cy="17" r="2" fill="currentColor" stroke="none" />
        </svg>
      </button>
    </div>

    <!-- EQ 弹层 -->
    <Transition name="fade">
      <div v-if="player.showEq" class="absolute bottom-16 right-4 z-50">
        <EqualizerPanel />
      </div>
    </Transition>

    <!-- 输出设备弹层 -->
    <Transition name="fade">
      <div v-if="player.showDevice" class="absolute bottom-16 right-4 w-72 bg-card rounded-r-md p-3 shadow-hover z-50">
        <p class="text-[12px] font-medium text-ink mb-2 flex items-center gap-1.5">
          <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M11 5L6 9H3v6h3l5 4V5zM16 9a3 3 0 010 6" stroke-linecap="round" /></svg>
          音频输出设备
        </p>
        <div class="flex flex-col gap-1 max-h-56 overflow-y-auto">
          <!-- 系统默认 -->
          <button
            class="flex items-center gap-2 px-3 py-2 rounded-r-sm text-left text-[13px] hover:bg-black/5 transition-colors"
            :class="{ '!bg-brand-soft !text-brand font-medium': !player.outputDeviceId }"
            @click="void player.setOutputDevice('')"
          >
            <span class="w-4 h-4 rounded-full grid place-items-center shrink-0" :class="!player.outputDeviceId ? 'bg-brand text-white' : 'border border-line'">
              <span v-if="!player.outputDeviceId" class="w-1.5 h-1.5 rounded-full bg-white" />
            </span>
            <span class="truncate">系统默认输出</span>
          </button>
          <!-- 各设备 -->
          <button
            v-for="d in player.outputDevices"
            :key="d.deviceId || 'default'"
            class="flex items-center gap-2 px-3 py-2 rounded-r-sm text-left text-[13px] hover:bg-black/5 transition-colors"
            :class="{ '!bg-brand-soft !text-brand font-medium': player.outputDeviceId === d.deviceId }"
            @click="void player.setOutputDevice(d.deviceId)"
          >
            <span class="w-4 h-4 rounded-full grid place-items-center shrink-0" :class="player.outputDeviceId === d.deviceId ? 'bg-brand text-white' : 'border border-line'">
              <span v-if="player.outputDeviceId === d.deviceId" class="w-1.5 h-1.5 rounded-full bg-white" />
            </span>
            <span class="truncate">{{ d.label || ('未设备 (' + d.deviceId.slice(0, 8) + ')') }}</span>
          </button>
          <p v-if="!player.outputDevices.length" class="text-[12px] font-light text-ink-faint px-3 py-3 text-center">
            尚未获取到设备列表<br />
            <span class="text-[11px]">点击下方按钮授权一次后即可列出全部</span>
          </p>
        </div>
        <button
          class="w-full mt-2 px-3 py-1.5 rounded-pill text-[12px] text-brand border border-brand/40 hover:bg-brand-soft transition-colors"
          @click="player.refreshOutputDevices()"
        >
          🔄 刷新设备列表
        </button>
        <p class="text-[10.5px] font-light text-ink-faint mt-2 px-1 leading-relaxed">
          切换仅影响本地音频 · 需要 Chrome 110+ / Edge
        </p>
      </div>
    </Transition>

    <!-- 播放队列浮层 -->
    <Transition name="fade">
      <div v-if="player.showQueue" class="absolute bottom-16 right-4 w-72 bg-card rounded-r-md p-3 shadow-hover z-50">
        <p class="text-[12px] font-light text-ink-soft mb-2">播放队列（{{ player.queue.length }}）</p>
        <div class="flex flex-col gap-1 max-h-48 overflow-y-auto">
          <button
            v-for="(s, i) in player.queue"
            :key="s.id"
            class="flex items-center gap-2 px-2 py-1.5 rounded-r-sm hover:bg-black/5 text-left"
            @click="player.index = i; player.playing = true; void player._loadCurrent()"
          >
            <span class="text-[12px] text-ink-faint w-4">{{ i + 1 }}</span>
            <span class="text-[13px] text-ink truncate flex-1">{{ s.title }}</span>
            <span class="text-[12px] font-light text-ink-faint">{{ s.artist }}</span>
          </button>
          <p v-if="!player.queue.length" class="text-[12px] font-light text-ink-faint text-center py-3">队列为空</p>
        </div>
      </div>
    </Transition>
  </footer>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
