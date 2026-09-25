// 歌单 store：列表 + 当前选中 + CRUD 操作
import { defineStore } from 'pinia'
import { smartApi } from '@/api'
import type { Playlist } from '@/api/types'

export const usePlaylistStore = defineStore('playlist', {
  state: () => ({
    playlists: [] as Playlist[],
    activeId: 0,
    loading: false,
  }),
  getters: {
    active: (s): Playlist | null => s.playlists.find((p) => p.id === s.activeId) || null,
    totalCount: (s): number => s.playlists.reduce((acc, p) => acc + p.song_count, 0),
  },
  actions: {
    async fetchAll() {
      this.loading = true
      try {
        this.playlists = await smartApi.listPlaylists()
        if (!this.activeId && this.playlists.length) {
          this.activeId = this.playlists[0].id
        }
      } finally {
        this.loading = false
      }
    },
    async create(name: string, scene = '') {
      const pl = await smartApi.createPlaylist({ name, scene })
      this.playlists.unshift(pl)
      this.activeId = pl.id
      return pl
    },
    select(id: number) {
      this.activeId = id
    },
    async update(id: number, patch: { name?: string; scene?: string; description?: string; cover_color?: string }) {
      const { api } = await import('@/api')
      let updated: Playlist | null = null
      try {
        updated = await api.updatePlaylist(id, patch)
      } catch {
        /* 后端不可用时本地更新 */
      }
      const idx = this.playlists.findIndex((p) => p.id === id)
      if (idx >= 0) {
        this.playlists[idx] = updated
          ? updated
          : { ...this.playlists[idx], ...patch }
      }
      return this.playlists[idx]
    },
    async remove(id: number) {
      const { api } = await import('@/api')
      try {
        await api.deletePlaylist(id)
      } catch {
        /* 后端不可用时本地移除 */
      }
      this.playlists = this.playlists.filter((p) => p.id !== id)
      if (this.activeId === id) this.activeId = this.playlists[0]?.id || 0
    },
  },
})
