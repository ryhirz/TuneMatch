// 路由配置：侧边栏导航 8 页 + 设置页
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: () => import('@/views/HomeView.vue'), meta: { title: '推荐' } },
    { path: '/scenes', name: 'scenes', component: () => import('@/views/SceneView.vue'), meta: { title: '场景' } },
    { path: '/genres', name: 'genres', component: () => import('@/views/GenreView.vue'), meta: { title: '曲风' } },
    { path: '/playlists', name: 'playlists', component: () => import('@/views/PlaylistView.vue'), meta: { title: '歌单' } },
    { path: '/profile', name: 'profile', component: () => import('@/views/ProfileView.vue'), meta: { title: '我的' } },
    { path: '/weekly', name: 'weekly', component: () => import('@/views/WeeklyReportView.vue'), meta: { title: '周报' } },
    { path: '/settings', name: 'settings', component: () => import('@/views/SettingsView.vue'), meta: { title: '设置' } },
    { path: '/help', name: 'help', component: () => import('@/views/HelpView.vue'), meta: { title: '帮助' } },
    { path: '/assistant', name: 'assistant', component: () => import('@/views/AIChatView.vue'), meta: { title: 'AI 助手' } },
    { path: '/recommendations', name: 'recommendations', component: () => import('@/views/RecommendationsView.vue'), meta: { title: 'AI 推荐' } },
    { path: '/song/:id(\\d+)', name: 'song-detail', component: () => import('@/views/SongDetailView.vue'), meta: { title: '歌曲详情' } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.afterEach((to) => {
  document.title = `${String(to.meta.title || 'TuneMatch')} · TuneMatch`
})

export default router
