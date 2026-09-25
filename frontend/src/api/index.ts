// API 统一出口：优先真实后端，失败自动降级 Mock
import http, { unwrap } from './client'
import { mockApi } from './mock'
import type {
  ApiResponse, ChatEvent, ChatMessage, HealthInfo, ImportResult, JamendoTrack, Playlist,
  PlaylistImportResult, RecommendParams, RecommendResult, Settings, Song,
} from './types'

/** 后端是否可用（健康检查缓存） */
let backendOk: boolean | null = null

/** multipart 上传（单文件） */
function uploadFile<T>(
  url: string, field: string, file: File, onProgress?: (pct: number) => void,
): Promise<T> {
  return new Promise((resolve, reject) => {
    const fd = new FormData()
    fd.append(field, file)
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${http.defaults.baseURL}${url}`)
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(Math.round((e.loaded / e.total) * 100))
    }
    xhr.onload = () => {
      try {
        const body = JSON.parse(xhr.responseText) as ApiResponse<T>
        if (xhr.status >= 200 && xhr.status < 300 && body.code === 0) resolve(body.data as T)
        else reject(new Error(body.message || '上传失败'))
      } catch {
        reject(new Error('上传响应解析失败'))
      }
    }
    xhr.onerror = () => reject(new Error('网络异常，上传失败'))
    xhr.send(fd)
  })
}

/** multipart 上传（多文件） */
function uploadFiles<T>(
  url: string, field: string, files: File[], onProgress?: (pct: number) => void,
): Promise<T> {
  return new Promise((resolve, reject) => {
    const fd = new FormData()
    for (const f of files) fd.append(field, f)
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${http.defaults.baseURL}${url}`)
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(Math.round((e.loaded / e.total) * 100))
    }
    xhr.onload = () => {
      try {
        const body = JSON.parse(xhr.responseText) as ApiResponse<T>
        if (xhr.status >= 200 && xhr.status < 300 && body.code === 0) resolve(body.data as T)
        else reject(new Error(body.message || '导入失败'))
      } catch {
        reject(new Error('导入响应解析失败'))
      }
    }
    xhr.onerror = () => reject(new Error('网络异常，导入失败'))
    xhr.send(fd)
  })
}

export async function checkBackend(): Promise<boolean> {
  if (backendOk !== null) return backendOk
  try {
    const h = await api.health()
    backendOk = h.status === 'ok'
  } catch {
    backendOk = false
  }
  return backendOk
}

/** 强制走 Mock（用于测试/演示） */
export function forceMock(on: boolean) {
  backendOk = on ? false : null
}

export const api = {
  // ---------- 健康 ----------
  health(): Promise<HealthInfo> {
    return unwrap(http.get<ApiResponse<HealthInfo>>('/health'))
  },

  // ---------- 歌曲 ----------
  listSongs(params: { genre?: string; mood?: string; keyword?: string; limit?: number } = {}): Promise<Song[]> {
    return unwrap(http.get<ApiResponse<Song[]>>('/api/songs', { params }))
  },
  getSong(id: number): Promise<Song> {
    return unwrap(http.get<ApiResponse<Song>>(`/api/songs/${id}`))
  },
  fetchLyrics(id: number): Promise<{ lyrics: string; source: string; message?: string }> {
    return unwrap(http.post<ApiResponse<{ lyrics: string; source: string }>>(`/api/songs/${id}/lyrics`))
  },
  listGenres(): Promise<string[]> {
    return unwrap(http.get<ApiResponse<string[]>>('/api/songs/meta/genres'))
  },

  // ---------- 推荐 ----------
  recommend(params: RecommendParams): Promise<RecommendResult> {
    return unwrap(http.post<ApiResponse<RecommendResult>>('/api/recommend', params))
  },

  // ---------- 歌单 ----------
  listPlaylists(): Promise<Playlist[]> {
    return unwrap(http.get<ApiResponse<Playlist[]>>('/api/playlists'))
  },
  importTextPlaylist(body: { name: string; text: string; description?: string }): Promise<PlaylistImportResult> {
    return unwrap(http.post<ApiResponse<PlaylistImportResult>>('/api/playlists/import-text', body))
  },
  createPlaylist(body: { name: string; scene?: string; description?: string; cover_color?: string }): Promise<Playlist> {
    return unwrap(http.post<ApiResponse<Playlist>>('/api/playlists', body))
  },
  updatePlaylist(id: number, body: Partial<{ name: string; scene: string; description: string; cover_color: string; cover_url: string }>): Promise<Playlist> {
    return unwrap(http.put<ApiResponse<Playlist>>(`/api/playlists/${id}`, body))
  },
  deletePlaylist(id: number): Promise<void> {
    return unwrap(http.delete<ApiResponse<void>>(`/api/playlists/${id}`))
  },
  addSongToPlaylist(id: number, songId: number): Promise<Playlist> {
    return unwrap(http.post<ApiResponse<Playlist>>(`/api/playlists/${id}/songs`, { song_id: songId }))
  },
  removeSongFromPlaylist(id: number, songId: number): Promise<Playlist> {
    return unwrap(http.delete<ApiResponse<Playlist>>(`/api/playlists/${id}/songs/${songId}`))
  },
  /** 上传歌单头像（multipart，返回完整歌单） */
  uploadCover(id: number, file: File, onProgress?: (pct: number) => void): Promise<Playlist> {
    return uploadFile(`/api/playlists/${id}/cover`, 'file', file, onProgress)
  },
  /** 批量导入歌曲文件（multipart files，返回导入结果） */
  importSongs(id: number, files: File[], onProgress?: (pct: number) => void): Promise<ImportResult> {
    return uploadFiles(`/api/playlists/${id}/songs/import`, 'files', files, onProgress)
  },

  // ---------- 对话（SSE） ----------
  chatStream(text: string, onEvent: (e: ChatEvent) => void, playlistId?: number): Promise<string> {
    return new Promise((resolve, reject) => {
      const controller = new AbortController()
      // 45s 超时保护：流式卡死时强制结束，避免聊天区一直"生成中"
      const timer = setTimeout(() => controller.abort(), 45000)
      fetch(`${http.defaults.baseURL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, playlist_id: playlistId ?? null }),
        signal: controller.signal,
      })
        .then(async (resp) => {
          if (!resp.ok || !resp.body) {
            reject(new Error(`对话请求失败: ${resp.status}`))
            return
          }
          const reader = resp.body.getReader()
          const decoder = new TextDecoder()
          let buffer = ''
          for (;;) {
            const { done, value } = await reader.read()
            if (done) break
            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''
            for (const line of lines) {
              const t = line.trim()
              if (!t.startsWith('data:')) continue
              try {
                const evt = JSON.parse(t.slice(5).trim()) as ChatEvent
                onEvent(evt)
                if (evt.type === 'done') resolve('ok')
              } catch {
                /* 忽略坏帧 */
              }
            }
          }
          resolve('ok')
        })
        .catch((e) => {
          // 超时/中止也算完成（避免卡死），返回 ok 让 store 结束 streaming
          if (e?.name === 'AbortError') {
            onEvent({ type: 'done', content: 'timeout' })
            resolve('ok')
            return
          }
          reject(e)
        })
        .finally(() => clearTimeout(timer))
    })
  },
  chatHistory(): Promise<ChatMessage[]> {
    return unwrap(http.get<ApiResponse<ChatMessage[]>>('/api/chat/history'))
  },

  // ---------- 配置（LLM 供应商热切换） ----------
  getConfig(): Promise<Settings> {
    return unwrap(http.get<ApiResponse<Settings>>('/api/config'))
  },
  updateConfig(body: Partial<{ llm_base_url: string; llm_api_key: string; llm_model_name: string }>): Promise<Settings> {
    return unwrap(http.put<ApiResponse<Settings>>('/api/config', body))
  },
  resetConfig(): Promise<Settings> {
    return unwrap(http.post<ApiResponse<Settings>>('/api/config/reset'))
  },

  // ---------- 曲库增强（iTunes / Jamendo） ----------
  syncCatalog(force = false): Promise<{ total: number; updated: number; failed: number }> {
    return unwrap(http.post<ApiResponse<{ total: number; updated: number; failed: number }>>('/api/catalog/sync', null, { params: { force } }))
  },
  syncJamendo(clientId: string, query = '', tags = '', limit = 20): Promise<{ total: number; imported: number; skipped: number }> {
    return unwrap(http.post<ApiResponse<{ total: number; imported: number; skipped: number }>>('/api/catalog/jamendo', null, {
      params: { client_id: clientId, query, tags, limit },
    }))
  },
  jamendoSearch(clientId: string, query = '', limit = 10): Promise<JamendoTrack[]> {
    return unwrap(http.get<ApiResponse<JamendoTrack[]>>('/api/catalog/jamendo/search', {
      params: { client_id: clientId, query, limit },
    }))
  },

  // ---------- 对话历史删除 ----------
  deleteChatMessage(id: number): Promise<void> {
    return unwrap(http.delete<ApiResponse<void>>(`/api/chat/${id}`))
  },
  clearChatHistory(): Promise<void> {
    return unwrap(http.delete<ApiResponse<void>>('/api/chat'))
  },

  // ---------- 导出（返回可下载 URL） ----------
  exportPdf(playlistId: number): string {
    return `${http.defaults.baseURL}/api/export/playlist/${playlistId}/pdf`
  },
  exportPoster(playlistId: number): string {
    return `${http.defaults.baseURL}/api/export/playlist/${playlistId}/poster`
  },
}

/** 智能 API：后端挂了自动走 Mock（页面级使用） */
export const smartApi = {
  async health(): Promise<HealthInfo> {
    if (await checkBackend()) return api.health()
    return mockApi.health().then((r) => r.data)
  },
  async listSongs(params: { genre?: string; mood?: string; keyword?: string; limit?: number } = {}): Promise<Song[]> {
    if (await checkBackend()) return api.listSongs(params)
    const mockParams: Record<string, string> = {}
    if (params.genre) mockParams.genre = params.genre
    if (params.mood) mockParams.mood = params.mood
    if (params.keyword) mockParams.keyword = params.keyword
    if (params.limit) mockParams.limit = String(params.limit)
    return mockApi.listSongs(mockParams).then((r) => r.data)
  },
  async listGenres(): Promise<string[]> {
    if (await checkBackend()) return api.listGenres()
    return ['pop', 'rock', 'folk', 'edm', 'hip-hop']
  },
  async recommend(params: RecommendParams): Promise<RecommendResult> {
    if (await checkBackend()) return api.recommend(params)
    return mockApi.recommend(params).then((r) => r.data)
  },
  async listPlaylists(): Promise<Playlist[]> {
    if (await checkBackend()) return api.listPlaylists()
    return mockApi.listPlaylists().then((r) => r.data)
  },
  async createPlaylist(body: { name: string; scene?: string; description?: string; cover_color?: string }): Promise<Playlist> {
    if (await checkBackend()) return api.createPlaylist(body)
    return mockApi.createPlaylist(body.name, body.scene).then((r) => r.data)
  },
  async getSong(id: number): Promise<Song> {
    if (await checkBackend()) return api.getSong(id)
    // 后端不可用：返回兜底歌曲，避免详情页崩溃 / 误报「未找到」
    const r = await mockApi.getSong(id)
    return r.data
  },
  async fetchLyrics(id: number): Promise<{ lyrics: string; source: string; message?: string }> {
    if (await checkBackend()) return api.fetchLyrics(id)
    return { lyrics: '', source: 'mock', message: 'Mock 模式：暂无歌词' }
  },
}
