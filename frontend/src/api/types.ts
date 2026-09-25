// TuneMatch 前端类型定义（与后端 schemas 对齐）

/** 统一响应格式 */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

/** 歌曲 */
export interface Song {
  id: number
  song_id: string
  title: string
  artist: string
  album: string
  genre: string
  mood_tags: string[]
  duration: number // 毫秒
  audio_url: string
  cover_url: string
  cover_color: string
  lyrics: string
  features: number[]
  match: number // 推荐匹配度 0-100
}

/** 歌单 */
export interface Playlist {
  id: number
  name: string
  scene: string
  description: string
  cover_color: string
  cover_url: string
  song_count: number
  songs: Song[]
  created_at?: string
}

/** 歌单文本导入结果（含曲风画像 + 创意视觉图 SVG） */
export interface PlaylistImportResult {
  playlist_id: number
  playlist_name: string
  total_items: number
  matched: number
  unmatched_count: number
  unmatched: { title: string; artist?: string }[]
  genre_dist: { genre: string; count: number }[]
  mood_dist: { mood: string; count: number }[]
  top_genres: string[]
  profile: {
    primary_genre: string
    genres: string[]
    moods: string[]
    avg_duration_s: number
  }
  art_svg: string
}

/** 导入歌曲结果 */
export interface ImportResult {
  imported: Song[]
  imported_count: number
  rejected: { filename: string; reason: string }[]
  rejected_count: number
  playlist: Playlist
}

/** 推荐请求 */
export interface RecommendParams {
  mode: 'text' | 'tags' | 'seed' | 'audio'
  text?: string
  tags?: string[]
  scene?: string
  audio_base64?: string
  limit?: number
}

/** 推荐结果 */
export interface RecommendResult {
  songs: Song[]
  parsed: {
    genres?: string[]
    moods?: string[]
    scene?: string
    mode?: string
  }
  degraded?: boolean
  degraded_reason?: string
}

/** 对话消息 */
export interface ChatMessage {
  id?: number
  role: 'user' | 'assistant'
  content: string
  song_ids?: number[]
  songs?: ChatSongCard[]
  created_at?: string
}

/** SSE 对话事件 */
export interface ChatEvent {
  type: 'delta' | 'reason' | 'done' | 'songs'
  content?: string
  songs?: ChatSongCard[]
}

/** AI 回复中的歌曲卡片（点击跳详情） */
export interface ChatSongCard {
  id: number
  title: string
  artist: string
  cover_url: string
  match: number
  genre: string
}

/** 健康状态 */
export interface HealthInfo {
  status: string
  llm: { configured: boolean; provider: string; model: string }
  chromadb: { songs: number; users: number } | null
  audio: Record<string, boolean>
}

/** 导出类型 */
export interface ExportInfo {
  url: string
  filename: string
}

/** LLM 配置 */
export interface LlmProvider {
  key: string
  name: string
  base_url: string
  models: string[]
}

export interface Settings {
  llm_base_url: string
  llm_api_key_set: boolean
  llm_api_key_mask: string
  llm_model_name: string
  providers: LlmProvider[]
  jamendo_client_id: string
  jamendo_client_id_set: boolean
}

/** Jamendo 全首曲目 */
export interface JamendoTrack {
  jamendo_id: string
  title: string
  artist: string
  album: string
  cover_url: string
  audio_url: string
  duration: number
  tags: string[]
  genre: string
  license: string
}
