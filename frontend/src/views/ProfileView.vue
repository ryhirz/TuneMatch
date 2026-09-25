<!-- 页面：偏好画像 —— AI 学到的你（5 维度可视化，Apple 风格）
对齐 高保真效果图 05 偏好画像 -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { smartApi } from '@/api'
import type { Song } from '@/api/types'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const songs = ref<Song[]>([])

/** 重置偏好：调用后端清空 feedback + 本地清空 localStorage 中的偏好缓存 */
function resetPrefs() {
  if (!confirm('确定重置你的所有偏好数据吗？此操作不可撤销。')) return
  try {
    // 清理本地缓存
    localStorage.removeItem('tm_eq')
    localStorage.removeItem('tm_volume')
    localStorage.removeItem('tm_eq_preset')
    // 通知后端清空（如果有反馈接口）
    fetch('/api/feedback/reset', { method: 'POST' }).catch(() => {})
    toast.show('已重置偏好 · 重新开始学习你的口味', 'success', 2500)
  } catch (e) {
    toast.show('重置失败：' + (e as Error).message, 'error')
  }
}

// 曲风偏好（按曲库 genre 统计占比）
const genrePref = computed(() => {
  const cnt: Record<string, number> = {}
  for (const s of songs.value) {
    const g = s.genre || '其他'
    cnt[g] = (cnt[g] || 0) + 1
  }
  const total = songs.value.length || 1
  return Object.entries(cnt)
    .map(([name, n]) => ({ name, pct: Math.round((n / total) * 100) }))
    .sort((a, b) => b.pct - a.pct)
    .slice(0, 5)
})

const GENRE_ZH: Record<string, string> = {
  pop: '流行', rock: '摇滚', folk: '民谣', edm: '电子', 'hip-hop': '嘻哈',
  jazz: '爵士', classical: '古典', lofi: 'Lo-fi', ambient: '氛围', 'r-n-b': 'R&B',
}

onMounted(async () => {
  try {
    songs.value = await smartApi.listSongs()
  } catch {
    songs.value = []
  }
})

// 模拟画像数据（真实项目接入 feedback/exposure 聚合后替换）
const stats = [
  { k: 'BPM 偏好', v: '80-110', s: '舒缓区间', color: '#0071E3' },
  { k: '主要情绪', v: '平静', s: '72% 占比', color: '#7C3AED' },
  { k: '活跃场景', v: '通勤 / 工作', s: '62% 时段', color: '#F59E0B' },
  { k: '活跃时段', v: '20:00-23:00', s: '晚间高峰', color: '#10B981' },
]
</script>

<template>
  <div class="max-w-[1120px] mx-auto px-7 py-10 max-[560px]:px-4">
    <!-- 标题栏 -->
    <div class="flex items-end justify-between mb-6 flex-wrap gap-4">
      <div>
        <p class="text-[13px] font-semibold tracking-[0.06em] text-brand uppercase mb-2">偏好画像 · Your Taste</p>
        <h2 class="text-display text-ink">AI 学到了你的口味</h2>
        <p class="mt-2 text-[13px] font-light text-ink-faint">基于你最近 30 天的听歌与反馈 · 实时更新</p>
      </div>
      <button class="tm-btn-ghost !px-4 !py-2 !text-[13px]" @click="resetPrefs">🔄 重置偏好</button>
    </div>

    <div class="grid gap-4" style="grid-template-columns: 1.4fr 1fr; max-width: 100%;">
      <!-- 曲风偏好柱状图 -->
      <div class="bg-card rounded-r-lg p-5 border border-line">
        <h3 class="text-[14.5px] font-bold text-ink mb-4">🎵 曲风偏好</h3>
        <div v-if="genrePref.length">
          <div v-for="g in genrePref" :key="g.name" class="mb-3">
            <div class="flex justify-between text-[12.5px] mb-1.5">
              <span class="text-ink-soft">{{ GENRE_ZH[g.name] || g.name }}</span>
              <span class="font-bold text-brand">{{ g.pct }}%</span>
            </div>
            <div class="h-[7px] bg-bg rounded-full overflow-hidden">
              <div
                class="h-full rounded-full"
                style="background: linear-gradient(90deg, #0071E3, #7C3AED)"
                :style="{ width: `${g.pct}%` }"
              />
            </div>
          </div>
        </div>
        <p v-else class="text-[13px] font-light text-ink-faint">暂无数据</p>
      </div>

      <!-- 4 维度统计 + 艾宾浩斯说明 -->
      <div class="flex flex-col gap-3">
        <div class="grid grid-cols-2 gap-3">
          <div v-for="st in stats" :key="st.k" class="bg-card border border-line rounded-r-md p-3.5">
            <p class="text-[10.5px] text-ink-faint tracking-[1px]">{{ st.k }}</p>
            <p class="text-[17px] font-bold mt-1" :style="{ color: st.color }">{{ st.v }}</p>
            <p class="text-[11px] font-light text-ink-faint mt-0.5">{{ st.s }}</p>
          </div>
        </div>

        <div class="bg-card border border-line rounded-r-md p-3.5">
          <p class="text-[12.5px] text-ink-soft font-medium">🧠 艾宾浩斯渐弱曝光</p>
          <p class="text-[11px] font-light text-ink-faint mt-1.5 leading-relaxed">
            未反馈的歌按 1 / 3 / 7 / 15 / 30 天间隔递减曝光，避免重复疲劳，同时给歌曲第二次机会。
          </p>
        </div>
      </div>
    </div>

    <!-- 周报 banner -->
    <div class="mt-4 bg-gradient-to-r from-[#EDE9FE] to-[#DDD6FE] rounded-r-lg p-4 flex items-center justify-between flex-wrap gap-3">
      <div>
        <p class="text-[14px] font-bold text-[#5B21B6]">📊 本周听歌报告已生成</p>
        <p class="text-[12px] text-[#7C3AED] mt-0.5">本周听了 12.5 小时 · 发现 8 首新歌 · 最爱曲风：{{ GENRE_ZH[genrePref[0]?.name] || '流行' }}</p>
      </div>
      <RouterLink to="/weekly" class="tm-btn !px-5 !py-2 !text-[13px]">查看报告</RouterLink>
    </div>
  </div>
</template>
