<!-- EQ 调节器：10 段自定义竖向滑块（纯 div + 拖拽，避免 webkit thumb 偏移）
Apple 极简风格：细线轨道 + 圆形 thumb + 蓝色填充 + 标签刻度 -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { EQ_FREQS, EQ_PRESETS, EQ_RANGE, usePlayerStore } from '@/stores/player'
import { useToastStore } from '@/stores/toast'

const player = usePlayerStore()
const toast = useToastStore()

const presetNames = computed(() => Object.keys(EQ_PRESETS))
const activePreset = computed(() => {
  const cur = EQ_FREQS.map((f) => player.eq[String(f)] ?? 0)
  for (const [name, vals] of Object.entries(EQ_PRESETS)) {
    if (vals.every((v, i) => Math.abs(v - cur[i]) < 0.5)) return name
  }
  return ''
})

// 自定义预设：localStorage 持久化
const CUSTOM_KEY = 'tm_eq_custom'
const customPresets = ref<Record<string, number[]>>({})

function loadCustom() {
  try {
    const raw = localStorage.getItem(CUSTOM_KEY)
    if (raw) customPresets.value = JSON.parse(raw)
  } catch { /* ignore */ }
}

function saveCustom() {
  try {
    localStorage.setItem(CUSTOM_KEY, JSON.stringify(customPresets.value))
  } catch { /* ignore */ }
}

onMounted(loadCustom)

function applyCustom(name: string) {
  const vals = customPresets.value[name]
  if (!vals) return
  EQ_FREQS.forEach((f, i) => {
    player.eq[String(f)] = vals[i] ?? 0
  })
  player._persistEq()
  player.refreshFilters()
  toast.show(`已应用自定义预设「${name}」`, 'success')
}

function deleteCustom(name: string) {
  if (!confirm(`删除自定义预设「${name}」？`)) return
  delete customPresets.value[name]
  saveCustom()
}

// 自定义输入
const showCustomInput = ref(false)
const customName = ref('')

function startCustom() {
  // 必须有调整才能保存
  const cur = EQ_FREQS.map((f) => player.eq[String(f)] ?? 0)
  if (cur.every((v) => Math.abs(v) < 0.5)) {
    toast.show('请先调整至少一个频段再保存', 'info')
    return
  }
  showCustomInput.value = true
  customName.value = ''
}

function confirmCustom() {
  const name = customName.value.trim()
  if (!name) {
    toast.show('请输入预设名称', 'error')
    return
  }
  if (name in customPresets.value) {
    if (!confirm(`预设「${name}」已存在,覆盖吗？`)) return
  }
  const vals = EQ_FREQS.map((f) => player.eq[String(f)] ?? 0)
  customPresets.value[name] = vals
  saveCustom()
  showCustomInput.value = false
  customName.value = ''
  toast.show(`已保存为「${name}」`, 'success')
}

// ---------- 自定义竖向滑块 ----------
const TRACK_H = 80  // 轨道可用高度 px
const dragging = ref<{ freq: number; startY: number; startVal: number } | null>(null)

function valToPct(val: number): number {
  // val: -12 → 1 (底), +12 → 0 (顶)
  return 1 - (val + EQ_RANGE) / (2 * EQ_RANGE)
}

function startDrag(freq: number, e: PointerEvent) {
  const cur = player.eq[String(freq)] ?? 0
  dragging.value = { freq, startY: e.clientY, startVal: cur }
  ;(e.target as Element).setPointerCapture(e.pointerId)
}

function moveDrag(e: PointerEvent) {
  if (!dragging.value) return
  const dy = e.clientY - dragging.value.startY
  const delta = -dy * (EQ_RANGE * 2) / TRACK_H // 上滑增益
  const next = Math.max(-EQ_RANGE, Math.min(EQ_RANGE, Math.round(dragging.value.startVal + delta)))
  player.setEq(dragging.value.freq, next)
}

function endDrag() {
  dragging.value = null
}

function gainText(f: number): string {
  const v = player.eq[String(f)] ?? 0
  return v > 0 ? `+${v}` : String(v)
}

function fmtFreq(f: number): string {
  return f >= 1000 ? `${f / 1000}k` : String(f)
}
</script>

<template>
  <div class="w-[480px] max-w-[92vw] bg-card rounded-r-lg p-5 shadow-hover">
    <!-- 标题行 -->
    <div class="flex items-center justify-between mb-3">
      <h4 class="text-[15px] font-bold text-ink tracking-tight">EQ 调节器</h4>
      <span class="text-[11px] font-light text-ink-faint">{{ activePreset || (customPresets[Object.keys(customPresets).find(k => EQ_FREQS.every((f, i) => customPresets[k][i] === (player.eq[String(f)] ?? 0))) || ''] || '') ? '自定义' : '自定义' }}</span>
    </div>

    <!-- 预设按钮 -->
    <div class="flex flex-wrap gap-1.5 mb-4">
      <button
        v-for="name in presetNames"
        :key="name"
        class="px-2.5 py-1 rounded-pill text-[12px] border border-line bg-card text-ink-soft transition-colors"
        :class="{ '!bg-brand !text-white !border-brand font-medium': activePreset === name }"
        @click="player.applyPreset(name)"
      >
        {{ name }}
      </button>
      <button
        v-for="(_, name) in customPresets"
        :key="`c-${name}`"
        class="group relative px-2.5 py-1 rounded-pill text-[12px] border border-line bg-card text-ai transition-colors hover:!text-white hover:!bg-brand hover:!border-brand"
        :class="{ '!bg-brand !text-white !border-brand font-medium': activePreset === name }"
        @click="applyCustom(name)"
      >
        {{ name }}
        <span
          class="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-danger text-white text-[10px] hidden group-hover:grid place-items-center"
          @click.stop="deleteCustom(name)"
        >✕</span>
      </button>
      <button
        class="px-2.5 py-1 rounded-pill text-[12px] border border-dashed border-brand/40 bg-card text-brand hover:bg-brand-soft transition-colors"
        @click="startCustom"
      >
        ＋ 自定义
      </button>
      <button
        class="px-2.5 py-1 rounded-pill text-[12px] border border-line bg-card text-ink-soft hover:text-danger hover:border-danger/40 transition-colors"
        @click="player.resetEq()"
      >
        重置
      </button>
    </div>

    <!-- 自定义输入弹出 -->
    <div v-if="showCustomInput" class="flex items-center gap-2 mb-3 bg-bg rounded-r-md p-2">
      <input
        v-model="customName"
        class="flex-1 bg-card border border-line rounded-r-sm px-2.5 py-1 text-[13px] text-ink focus:outline-none focus:border-brand"
        placeholder="预设名称，如「我的耳机」"
        @keyup.enter="confirmCustom"
      />
      <button class="px-3 py-1 rounded-pill text-[12px] bg-brand text-white hover:bg-brand-hover transition-colors" @click="confirmCustom">保存</button>
      <button class="px-2 py-1 rounded-pill text-[12px] text-ink-faint hover:text-ink transition-colors" @click="showCustomInput = false">取消</button>
    </div>

    <!-- 10 段滑块 + 刻度尺 -->
    <div class="flex items-stretch gap-2">
      <!-- 左侧刻度 -->
      <div class="flex flex-col justify-between h-[110px] shrink-0 pr-1 text-[9px] font-light text-ink-faint">
        <span>+12</span>
        <span>+6</span>
        <span class="text-brand">0</span>
        <span>-6</span>
        <span>-12</span>
      </div>

      <!-- 10 段 -->
      <div class="flex-1 flex items-stretch gap-1.5">
        <div v-for="f in EQ_FREQS" :key="f" class="flex-1 flex flex-col items-center gap-1.5 min-w-0">
          <span class="text-[10px] font-semibold h-3.5 leading-none" :class="(player.eq[String(f)] ?? 0) !== 0 ? 'text-brand' : 'text-ink-faint'">
            {{ gainText(f) }}
          </span>
          <!-- 滑块轨道（点击 + 拖拽） -->
          <div
            class="relative rounded-full cursor-pointer touch-none select-none"
            style="width: 24px; height: 80px;"
            @pointerdown="startDrag(f, $event)"
            @pointermove="moveDrag($event)"
            @pointerup="endDrag"
            @pointercancel="endDrag"
            @dblclick="player.setEq(f, 0)"
          >
            <!-- 轨道 -->
            <div class="absolute inset-x-0 top-1/2 h-px bg-line" />
            <!-- 0dB 零线 -->
            <!-- 已填充区（中间到当前值） -->
            <div
              class="absolute inset-x-0 transition-all duration-75 rounded-full"
              :style="{
                top: (player.eq[String(f)] ?? 0) >= 0 ? '50%' : `${valToPct(player.eq[String(f)] ?? 0) * 100}%`,
                bottom: (player.eq[String(f)] ?? 0) >= 0 ? `${(1 - valToPct(player.eq[String(f)] ?? 0)) * 100}%` : '50%',
                background: 'linear-gradient(180deg, #0071E3 0%, #5E5CE6 100%)',
              }"
            />
            <!-- thumb -->
            <div
              class="absolute left-1/2 -translate-x-1/2 w-3.5 h-3.5 rounded-full bg-white shadow-btn border border-line transition-all duration-75"
              :style="{ top: `calc(${valToPct(player.eq[String(f)] ?? 0) * 100}% - 7px)` }"
            />
          </div>
          <span class="text-[10px] text-ink-faint leading-none">{{ fmtFreq(f) }}</span>
        </div>
      </div>
    </div>

    <!-- 底部 -->
    <p class="text-[10.5px] font-light text-ink-faint mt-3 leading-relaxed">
      拖动调节 · 双击归零 · 对本地音频实时生效 · 自动保存
    </p>
  </div>
</template>