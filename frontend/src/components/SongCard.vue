<!-- 歌曲卡片：Apple Store 风格（大圆角 18-22px · 封面渐变 · 悬浮播放钮 · 匹配度胶囊）
单击封面/标题进入详情页 · 单击悬浮播放按钮直接播放 -->
<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { Song } from '@/api/types'
import { usePlayerStore } from '@/stores/player'
import { useToastStore } from '@/stores/toast'

const props = withDefaults(defineProps<{
  song: Song
  rank?: number       // Bento 排行（有则显示 rank-badge）
  featured?: boolean  // 大卡（占 2 行）
  showReason?: boolean
}>(), { showReason: true, featured: false })

const emit = defineEmits<{ (e: 'add', song: Song): void }>()

const router = useRouter()
const player = usePlayerStore()
const toast = useToastStore()

function goDetail() {
  router.push({ name: 'song-detail', params: { id: String(props.song.id) } })
}

// 封面渐变：基于 cover_color 生成 Apple 风格渐变（主色 + 深色叠加）
const coverGradient = computed(() => {
  const c = props.song.cover_color || '#4DABF7'
  return `linear-gradient(150deg, ${c}, ${c}cc 55%, ${c}88)`
})

function fmtDuration(ms: number): string {
  const s = Math.floor(ms / 1000)
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

function play() {
  player.playSong(props.song)
}

function like() {
  toast.show(`已收藏《${props.song.title}》`, 'success')
}
</script>

<template>
  <article
    class="relative overflow-hidden bg-card rounded-r-lg flex flex-col cursor-pointer group"
    :class="featured ? 'row-span-2' : ''"
    style="transition: box-shadow 0.25s ease, transform 0.25s ease;"
    @mouseenter=""
    @click="goDetail"
  >
    <!-- 封面区：封面图/渐变 + 音符装饰 + 排行徽章 + 悬浮播放按钮 -->
    <div class="relative overflow-hidden" :class="featured ? 'flex-1 min-h-0' : 'h-[128px]'">
      <!-- 有真实封面图时显示图片 -->
      <img
        v-if="song.cover_url"
        :src="song.cover_url"
        :alt="song.title"
        class="absolute inset-0 w-full h-full object-cover"
        loading="lazy"
      />
      <!-- 无封面时用渐变 + 音符装饰 -->
      <div v-else class="absolute inset-0 w-full h-full" :style="{ background: coverGradient }">
        <!-- 音符装饰 -->
        <svg viewBox="0 0 400 200" preserveAspectRatio="xMidYMid slice" class="w-full h-full opacity-90">
          <g fill="rgba(255,255,255,0.35)">
            <rect x="60" y="90" width="8" height="44" rx="4" /><rect x="76" y="72" width="8" height="80" rx="4" />
            <rect x="92" y="96" width="8" height="36" rx="4" /><rect x="108" y="62" width="8" height="104" rx="4" />
            <rect x="124" y="84" width="8" height="60" rx="4" /><rect x="140" y="54" width="8" height="120" rx="4" />
            <rect x="156" y="92" width="8" height="40" rx="4" /><rect x="172" y="68" width="8" height="88" rx="4" />
            <rect x="188" y="98" width="8" height="28" rx="4" />
          </g>
          <circle cx="290" cy="60" r="30" fill="rgba(255,255,255,0.9)" />
          <circle cx="290" cy="60" r="24" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="1.5" />
          <path d="M282 48v26l16-10z" :fill="song.cover_color" />
        </svg>
      </div>
      <!-- 封面底部压暗 -->
      <div class="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent pointer-events-none" />

      <!-- 排行徽章 -->
      <span
        v-if="rank"
        class="absolute top-3.5 left-3.5 z-10 text-[12px] font-semibold tracking-[0.04em] text-white/90 bg-black/30 backdrop-blur-[8px] px-[11px] py-[5px] rounded-pill"
      >
        {{ rank === 1 ? 'TOP 1 · 今日最佳' : String(rank).padStart(2, '0') }}
      </span>

      <!-- 悬浮播放按钮 -->
      <button
        class="absolute z-10 grid place-items-center rounded-full bg-white/95 text-brand shadow-btn transition-all duration-300"
        :class="featured ? 'opacity-100 w-16 h-16' : 'opacity-0 scale-90 translate-y-2 group-hover:opacity-100 group-hover:scale-100 group-hover:translate-y-0 w-[52px] h-[52px]'"
        style="inset: 0; margin: auto;"
        @click.stop="play"
        aria-label="播放"
      >
        <svg viewBox="0 0 24 24" class="fill-current" :class="featured ? 'w-[26px] h-[26px]' : 'w-5 h-5'" style="margin-left:2px">
          <path d="M7 4.5v15l13-7.5z" />
        </svg>
      </button>
    </div>

    <!-- 卡片体 -->
    <div class="px-[18px] pt-[14px] pb-4 flex flex-col gap-0.5" :class="featured ? 'px-[22px] pt-[18px] pb-5' : ''">
      <h3 class="text-h3 text-ink truncate">{{ song.title }}</h3>
      <p class="text-[13px] font-light text-ink-soft truncate">{{ song.artist }} · {{ song.genre }}</p>
      <div class="flex items-center gap-2 mt-[7px]">
        <span class="text-[13px] font-bold text-brand bg-brand-soft rounded-pill px-2.5 py-[3px]">
          匹配度 {{ song.match }}%
        </span>
        <span v-if="featured" class="text-[12px] font-light text-ink-faint">
          ♫ {{ fmtDuration(song.duration) }}
        </span>
      </div>
      <!-- AI 理由（大卡展示） -->
      <p v-if="featured && showReason" class="text-[13px] font-light text-ai mt-2 leading-snug line-clamp-2">
        《{{ song.title }}》契合你的音乐口味，值得一听。
      </p>

      <!-- 操作（hover 显示，大卡常驻） -->
      <div class="flex items-center gap-2 mt-2.5" :class="featured ? '' : 'opacity-0 group-hover:opacity-100 transition-opacity'">
        <button
          class="w-8 h-8 rounded-full grid place-items-center text-ink-soft hover:bg-black/5 hover:text-ink transition-colors"
          title="收藏"
          @click.stop="like"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 21s-7.5-4.7-9.5-9C1 8.5 3 5.5 6.5 5.5c2 0 3.6 1.2 4.5 2.5.9-1.3 2.5-2.5 4.5-2.5 3.5 0 5.5 3 4 6.5-2 4.3-9.5 9-9.5 9z" />
          </svg>
        </button>
        <button
          class="w-8 h-8 rounded-full grid place-items-center text-ink-soft hover:bg-black/5 hover:text-ink transition-colors"
          title="加入歌单"
          @click.stop="emit('add', song)"
        >
          <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
            <path d="M12 5v14M5 12h14" />
          </svg>
        </button>
      </div>
    </div>
  </article>
</template>
