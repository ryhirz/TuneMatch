// Mock 模式：后端未启动时提供静态 JSON 兜底（777 首，与后端曲库口径一致）
// 与后端响应结构保持一致，前端可无后端独立运行
import type { ApiResponse, ChatMessage, HealthInfo, Playlist, RecommendParams, RecommendResult, Song } from './types'
import library from '../assets/music_library.json'

interface LibrarySong {
  song_id: string
  title: string
  artist: string
  album: string
  genre: string
  mood_tags: string[]
  duration: number
  audio_url: string
  cover_url?: string
  cover_color: string
}

/** 从曲库 JSON 构建 Song（补 id / features / match） */
function toSong(raw: LibrarySong, idx: number): Song {
  return {
    id: idx + 1,
    song_id: raw.song_id,
    title: raw.title,
    artist: raw.artist,
    album: raw.album || '',
    genre: raw.genre || 'pop',
    mood_tags: raw.mood_tags || [],
    duration: (raw.duration || 200) * 1000,
    audio_url: raw.audio_url || '',
    cover_url: raw.cover_url || '',
    cover_color: raw.cover_color || '#4DABF7',
    lyrics: '',
    features: [],
    match: 70 + ((idx * 7) % 28),
  }
}

const songs: Song[] = (library.songs || []).map(toSong)

/** Mock 推荐：按 genre/mood 简单匹配 + 打散 */
function mockRecommend(params: RecommendParams): ApiResponse<RecommendResult> {
  const tags = params.tags || []
  const text = params.text?.toLowerCase() || ''
  const scene = params.scene || ''

  let pool = [...songs]
  if (tags.length) {
    pool = pool.filter((s) =>
      tags.some((t) => s.genre.includes(t.toLowerCase()) || s.mood_tags.includes(t)),
    )
  }
  if (text) {
    pool = pool.filter(
      (s) => s.title.toLowerCase().includes(text) || s.artist.toLowerCase().includes(text),
    )
  }
  if (!pool.length) pool = [...songs]

  // 简单打散 + 匹配度递增
  const out = pool
    .map((s, i) => ({ ...s, match: 88 - i * 3 }))
    .slice(0, params.limit || 6)

  return {
    code: 0,
    message: 'success',
    data: {
      songs: out,
      parsed: {
        genres: tags.filter((t) => ['pop', 'rock', 'folk', 'edm', 'hip-hop'].includes(t)),
        moods: tags.filter((t) => !['pop', 'rock', 'folk', 'edm', 'hip-hop'].includes(t)),
        scene,
      },
      degraded: true,
      degraded_reason: 'mock 模式',
    },
  }
}

/** Mock API 入口（所有接口 Promise 化，模拟网络延迟） */
export const mockApi = {
  health(): Promise<ApiResponse<HealthInfo>> {
    return delay({
      code: 0,
      message: 'success',
      data: {
        status: 'ok',
        llm: { configured: false, provider: 'mock', model: '-' },
        chromadb: null,
        audio: { librosa: false, whisper: false, acoustid: false },
      },
    })
  },

  listSongs(params: Record<string, string> = {}): Promise<ApiResponse<Song[]>> {
    let pool = [...songs]
    if (params.genre) pool = pool.filter((s) => s.genre === params.genre)
    if (params.mood) pool = pool.filter((s) => s.mood_tags.includes(params.mood!))
    const limitNum = params.limit ? Number(params.limit) : undefined
    if (limitNum) pool = pool.slice(0, limitNum)
    if (params.keyword) {
      const kw = params.keyword.toLowerCase()
      pool = pool.filter((s) => s.title.toLowerCase().includes(kw) || s.artist.toLowerCase().includes(kw))
    }
    return delay({ code: 0, message: 'success', data: pool })
  },

  recommend(params: RecommendParams): Promise<ApiResponse<RecommendResult>> {
    return delay(mockRecommend(params))
  },

  listPlaylists(): Promise<ApiResponse<Playlist[]>> {
    return delay({ code: 0, message: 'success', data: [] })
  },

  getSong(id: number): Promise<ApiResponse<Song>> {
    const raw = songs.find((s) => s.id === id) || songs[0]
    const song: Song = { ...raw }
    return delay({ code: 0, message: 'success', data: song })
  },

  createPlaylist(name: string, scene = ''): Promise<ApiResponse<Playlist>> {
    const pl: Playlist = {
      id: Date.now(),
      name,
      scene,
      description: '',
      cover_color: '#4DABF7',
      cover_url: '',
      song_count: 0,
      songs: [],
    }
    return delay({ code: 0, message: 'success', data: pl })
  },

  chatHistory(): Promise<ApiResponse<ChatMessage[]>> {
    return delay({ code: 0, message: 'success', data: [] })
  },
}

function delay<T>(data: T, ms = 120): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(data), ms))
}
