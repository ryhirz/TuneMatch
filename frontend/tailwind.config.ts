import type { Config } from 'tailwindcss'

// TuneMatch Design Tokens —— Apple Store 设计语言（对齐 首页-AppleStore风格.html）
// 主色 #0071E3 · 背景 #F5F5F7 · 卡片 #FFF · 文字 #1D1D1F/#6E6E73/#86868B
// 大圆角 18-22px · 胶囊按钮 980px · 毛玻璃导航 · Bento Grid
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: '#0071E3', hover: '#0077ED', soft: 'rgba(0,113,227,0.10)' },
        bg: { DEFAULT: '#F5F5F7', deep: '#E8E8ED' },
        card: '#FFFFFF',
        line: 'rgba(0,0,0,0.08)',
        ink: {
          DEFAULT: '#1D1D1F',
          soft: '#6E6E73',
          faint: '#86868B',
        },
        playing: '#3B82F6',
        ai: '#10B981',
        danger: '#FF3B30',
        // 场景卡渐变（四场景）
        scene: {
          focus: ['#36B3A0', '#1E7A6D'],
          workout: ['#FF7A45', '#D9372E'],
          sleep: ['#6A5CF0', '#3A2D9E'],
          commute: ['#4AA8FF', '#1E63C9'],
        },
      },
      borderRadius: {
        'r-lg': '22px',
        'r-md': '18px',
        'r-sm': '14px',
        pill: '980px',
      },
      boxShadow: {
        hover: '0 14px 36px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.05)',
        btn: '0 4px 14px rgba(0,0,0,0.18)',
        none: 'none',
      },
      fontSize: {
        // Apple Store 标题体系
        display: ['40px', { fontWeight: '700', lineHeight: '1.1', letterSpacing: '-0.022em' }],
        h3: ['17px', { fontWeight: '600', lineHeight: '1.25', letterSpacing: '-0.01em' }],
        body: ['15px', { lineHeight: '1.5' }],
        note: ['13px', { lineHeight: '1.4' }],
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', '"SF Pro Display"', '"SF Pro Text"',
          '"Helvetica Neue"', '"PingFang SC"', '"HarmonyOS Sans SC"', '"Microsoft YaHei"', 'sans-serif'],
      },
      transitionTimingFunction: {
        ease: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
      },
    },
  },
  plugins: [],
} satisfies Config
