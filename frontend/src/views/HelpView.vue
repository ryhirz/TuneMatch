<!-- 页面：帮助中心（简洁 FAQ，Apple 风格） -->
<script setup lang="ts">
const faqs = [
  { q: 'TuneMatch 是什么？', a: '一款 AI 智能音乐推荐平台，通过文本、语音、标签、音频多模态输入，为你推荐对味的音乐。' },
  { q: '如何获得推荐？', a: '在首页点「说出你的需求」，输入一句描述（如「健身时听的摇滚」），或切换标签/种子歌曲模式。' },
  { q: '为什么推荐里有重复？', a: 'TuneMatch 用艾宾浩斯渐弱曝光机制：未反馈的歌按 1/3/7/15/30 天递减曝光，避免疲劳，也保留再次推荐的机会。' },
  { q: '如何管理歌单？', a: '首页底部「新建歌单」，点歌单名称即可编辑名称、封面颜色或删除。' },
  { q: 'AI 推荐理由是怎么来的？', a: '由 LLM（默认硅基流动，可切换 DeepSeek/OpenAI）结合你的曲风/情绪/场景偏好生成；未配 Key 时降级为模板理由。' },
]
</script>

<template>
  <div class="max-w-[720px] mx-auto px-7 py-10 max-[560px]:px-4">
    <div class="mb-6">
      <p class="text-[13px] font-semibold tracking-[0.06em] text-brand uppercase mb-2">帮助 · Help</p>
      <h2 class="text-display text-ink">常见问题</h2>
    </div>

    <div class="flex flex-col gap-3">
      <div v-for="f in faqs" :key="f.q" class="bg-card rounded-r-lg p-5 border border-line">
        <h3 class="text-[15px] font-semibold text-ink mb-1.5">{{ f.q }}</h3>
        <p class="text-[13px] font-light text-ink-soft leading-relaxed">{{ f.a }}</p>
      </div>
    </div>
  </div>
</template>
