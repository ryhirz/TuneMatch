import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

// TuneMatch 前端构建配置
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: true,
    allowedHosts: true,
    port: 5173,
    proxy: {
      // 联调：/api → FastAPI :8000
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: true,
    allowedHosts: true,
    port: 4173,
  },
  build: {
    // 部署沙箱对目录删除敏感（safe-delete 拦截），关闭自动清空以避免构建卡死；
    // 首次部署沙箱内 dist 不存在，无需删除；重复部署允许旧文件留存（demo 场景可接受）
    emptyOutDir: false,
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
