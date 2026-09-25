<!-- 侧边栏：Apple 风格竖向导航（Logo + 6 导航项）
对齐 高保真效果图 侧边栏模块 -->
<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const items = [
  { to: '/', label: '推荐', icon: 'M4 12a8 8 0 118 8 8 8 0 01-8-8zm3.2 0a4.8 4.8 0 109.6 0 4.8 4.8 0 00-9.6 0zM12 7.5l1.5 3 3 1.5-3 1.5-1.5 3-1.5-3-3-1.5 3-1.5z' },
  { to: '/scenes', label: '场景', icon: 'M4 5h16M6 5v14h12V5M9 12h6' },
  { to: '/genres', label: '曲风', icon: 'M12 3a9 9 0 100 18 9 9 0 000-18zm0 2a7 7 0 110 14 7 7 0 010-14z' },
  { to: '/playlists', label: '歌单', icon: 'M4 6h16v12H4zM4 10h16M8 14h8' },
  { to: '/profile', label: '我的', icon: 'M12 12a4 4 0 100-8 4 4 0 000 8zm-7 8a7 7 0 0114 0' },
  { to: '/weekly', label: '周报', icon: 'M4 5h16v14H4zM8 9h8M8 13h5M8 17h3' },
  { to: '/settings', label: '设置', icon: 'M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09a1.65 1.65 0 00-1-1.51 1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09a1.65 1.65 0 001.51-1 1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33h0a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51h0a1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00.33 1.82v0a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z' },
  { to: '/help', label: '帮助', icon: 'M12 21a9 9 0 100-18 9 9 0 000 18zm0-13v.01M12 12v4' },
]
</script>

<template>
  <aside class="w-[200px] shrink-0 bg-card/60 backdrop-blur-[20px] border-r border-line p-3.5 flex flex-col gap-1 max-[768px]:hidden">
    <!-- Logo -->
    <div class="flex items-center gap-2 px-2.5 pt-1.5 pb-4">
      <div class="w-8 h-8 rounded-[10px] bg-gradient-to-br from-[#378ADD] to-[#7C3AED] grid place-items-center text-white font-extrabold text-[15px]">
        T
      </div>
      <span class="font-bold text-[15px] text-ink">TuneMatch</span>
    </div>

    <!-- 导航项 -->
    <RouterLink
      v-for="it in items"
      :key="it.to"
      :to="it.to"
      class="flex items-center gap-2.5 px-3 py-2.5 rounded-[10px] text-[13.5px] text-ink-soft hover:bg-black/5 hover:text-ink transition-colors"
      :class="{ '!bg-gradient-to-r from-[#EFF6FF] to-[#EDE9FE] !text-[#5B21B6] font-semibold': route.path === it.to }"
    >
      <svg viewBox="0 0 24 24" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <path :d="it.icon" />
      </svg>
      {{ it.label }}
    </RouterLink>

    <!-- 底部：AI 助手入口 -->
    <div class="border-t border-line mt-3 pt-3">
      <RouterLink
        to="/assistant"
        class="flex items-center gap-2.5 px-3 py-2.5 rounded-[10px] text-[13.5px] text-ink-soft hover:bg-black/5 hover:text-ink transition-colors"
        :class="{ '!bg-gradient-to-r from-[#EFF6FF] to-[#EDE9FE] !text-[#5B21B6] font-semibold': route.path === '/assistant' }"
      >
        <svg viewBox="0 0 24 24" class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a4 4 0 014 4c0 1.1-.45 2.1-1.17 2.83L16 10a6 6 0 01-8 0l1.17-1.17A4 4 0 0112 2zM12 10v4M8 14h8M9.5 18h5" />
        </svg>
        AI 助手
      </RouterLink>
    </div>
  </aside>
</template>
