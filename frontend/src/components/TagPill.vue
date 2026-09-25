<!-- 通用组件：TagPill（曲风/情绪标签） -->
<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  text: string
  kind?: 'genre' | 'mood' | 'scene' | 'default'
}>(), { kind: 'default' })

const cls = computed(() => {
  switch (props.kind) {
    case 'genre': return 'tm-pill-genre'
    case 'mood': return 'tm-pill-mood'
    case 'scene': return 'tm-pill !text-ink-soft'
    default: return 'tm-pill'
  }
})
</script>

<template>
  <span :class="cls" class="whitespace-nowrap">{{ text }}</span>
</template>
