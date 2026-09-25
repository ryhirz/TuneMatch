// 11 维音频特征元数据与展示工具
// 顺序与后端 Song.features(11 维) 严格对齐，语义对标 Spotify audio-features：
//   0 原声度  1 律动感  2 能量感  3 愉悦度  4 语音性  5 现场感
//   6 节奏(BPM)  7 器乐度  8 调式(大/小调)  9 响度(dB)  10 时长(ms)
// 实测校验：曲库 777 首中 774 首为完整 11 维；features[10] 与 duration 字段完全一致。

export type FeatureKind = 'ratio' | 'bpm' | 'mode' | 'db' | 'ms'

export interface FeatureMeta {
  key: string
  label: string
  kind: FeatureKind
}

export const FEATURE_META: FeatureMeta[] = [
  { key: 'acousticness', label: '原声度', kind: 'ratio' },
  { key: 'danceability', label: '律动感', kind: 'ratio' },
  { key: 'energy', label: '能量感', kind: 'ratio' },
  { key: 'valence', label: '愉悦度', kind: 'ratio' },
  { key: 'speechiness', label: '语音性', kind: 'ratio' },
  { key: 'liveness', label: '现场感', kind: 'ratio' },
  { key: 'tempo', label: '节奏', kind: 'bpm' },
  { key: 'instrumentalness', label: '器乐度', kind: 'ratio' },
  { key: 'mode', label: '调式', kind: 'mode' },
  { key: 'loudness', label: '响度', kind: 'db' },
  { key: 'duration', label: '时长', kind: 'ms' },
]

const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x))
const clamp01 = (x: number) => clamp(x, 0, 1)

/** 归一化为 0-100（用于条形图 / 雷达半径） */
export function featurePct(v: number, kind: FeatureKind): number {
  switch (kind) {
    case 'ratio':
      return Math.round(clamp01(v) * 100)
    case 'bpm':
      return Math.round(clamp(v / 200, 0, 1) * 100)
    case 'mode':
      return Math.round(clamp01(v) * 100)
    case 'db':
      return Math.round(clamp((v + 60) / 60, 0, 1) * 100)
    case 'ms':
      return Math.round(clamp(v / 360000, 0, 1) * 100)
  }
}

/** 人类可读文本（如「大调」「138 BPM」「-6.7 dB」「4:02」） */
export function featureText(v: number, kind: FeatureKind): string {
  switch (kind) {
    case 'mode':
      return v >= 0.5 ? '大调' : '小调'
    case 'bpm':
      return `${Math.round(v)} BPM`
    case 'db':
      return `${v.toFixed(1)} dB`
    case 'ms': {
      const s = Math.round(v / 1000)
      return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
    }
    default:
      return v.toFixed(2)
  }
}

/** 把原始 features 数组映射为带展示信息的条目（不足 11 维则返回空，避免误展示） */
export function buildFeatures(arr?: number[]): { key: string; label: string; kind: FeatureKind; value: number; pct: number; text: string }[] {
  if (!arr || arr.length < FEATURE_META.length) return []
  return FEATURE_META.map((m, i) => {
    const v = arr[i] ?? 0
    return { ...m, value: v, pct: featurePct(v, m.kind), text: featureText(v, m.kind) }
  })
}
