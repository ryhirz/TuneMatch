// 曲风中文映射 + 分类元数据（颜色/图标/分类）— 前端共用
export const GENRE_ZH: Record<string, string> = {
  pop: '流行', rock: '摇滚', folk: '民谣', edm: '电子', 'hip-hop': '嘻哈',
  jazz: '爵士', classical: '古典', lofi: 'Lo-fi', ambient: '氛围', 'r-n-b': 'R&B',
  electronic: '电子', dance: '舞曲', chill: '放松', indie: '独立',
  instrumental: '器乐', piano: '钢琴', acoustic: '原声', metal: '金属',
  reggae: '雷鬼', blues: '蓝调', country: '乡村', soundtrack: '影视原声',
  world: '世界音乐', orchestral: '管弦', vocal: '人声',
  '90s': '90年代', '80s': '80年代', cinematic: '电影配乐',
  meditation: '冥想', epic: '史诗', sad: '悲伤', happy: '快乐',
  energetic: '活力', romantic: '浪漫', dream: '梦幻', study: '学习',
  sleep: '助眠', workout: '健身', party: '派对',
  jamendo: 'Jamendo', local: '本地',
}

// 曲风大分类（用于曲风界面的"一目了然"图标网格）
export interface GenreMeta {
  key: string
  label: string
  color: string
  gradient: string
  icon: string  // emoji
  desc: string
  category: '热门' | '心情' | '场景' | '时代' | '主题'
}

export const GENRE_META: GenreMeta[] = [
  { key: 'pop', label: '流行', color: '#FF6B9D', gradient: 'linear-gradient(135deg, #FF6B9D, #FF9A76)', icon: '🎤', desc: '当下热门流行金曲', category: '热门' },
  { key: 'rock', label: '摇滚', color: '#EF4444', gradient: 'linear-gradient(135deg, #EF4444, #F59E0B)', icon: '🎸', desc: '释放你的电吉他能量', category: '热门' },
  { key: 'electronic', label: '电子', color: '#7C3AED', gradient: 'linear-gradient(135deg, #7C3AED, #EC4899)', icon: '🎛️', desc: 'EDM/合成器/电子节拍', category: '热门' },
  { key: 'lofi', label: 'Lo-Fi', color: '#10B981', gradient: 'linear-gradient(135deg, #10B981, #06B6D4)', icon: '📻', desc: '低保真学习/工作背景', category: '热门' },
  { key: 'jazz', label: '爵士', color: '#F59E0B', gradient: 'linear-gradient(135deg, #F59E0B, #DC2626)', icon: '🎷', desc: '慵懒的萨克斯与蓝调', category: '热门' },
  { key: 'classical', label: '古典', color: '#6366F1', gradient: 'linear-gradient(135deg, #6366F1, #8B5CF6)', icon: '🎻', desc: '贝多芬/莫扎特/交响', category: '热门' },
  { key: 'hip-hop', label: '嘻哈', color: '#0EA5E9', gradient: 'linear-gradient(135deg, #0EA5E9, #1E40AF)', icon: '🎧', desc: '说唱/街拍/Trap 律动', category: '热门' },
  { key: 'folk', label: '民谣', color: '#84CC16', gradient: 'linear-gradient(135deg, #84CC16, #22C55E)', icon: '🪕', desc: '质朴吉他与诗意', category: '热门' },
  { key: 'r-n-b', label: 'R&B', color: '#EC4899', gradient: 'linear-gradient(135deg, #EC4899, #F43F5E)', icon: '💿', desc: '灵魂乐与都市情感', category: '热门' },
  { key: 'ambient', label: '氛围', color: '#0891B2', gradient: 'linear-gradient(135deg, #0891B2, #4F46E5)', icon: '🌌', desc: '环境/空间/沉浸', category: '热门' },
  { key: 'dance', label: '舞曲', color: '#F97316', gradient: 'linear-gradient(135deg, #F97316, #FCD34D)', icon: '🪩', desc: 'House / Trance 律动', category: '热门' },
  { key: 'metal', label: '金属', color: '#374151', gradient: 'linear-gradient(135deg, #374151, #1F2937)', icon: '⚡', desc: '硬摇滚/重金之声', category: '热门' },
  { key: 'piano', label: '钢琴', color: '#A78BFA', gradient: 'linear-gradient(135deg, #A78BFA, #FBBF24)', icon: '🎹', desc: '纯净钢琴独奏', category: '主题' },
  { key: 'acoustic', label: '原声', color: '#FCD34D', gradient: 'linear-gradient(135deg, #FCD34D, #FB923C)', icon: '🪵', desc: '不插电/木吉他', category: '主题' },
  { key: 'reggae', label: '雷鬼', color: '#22C55E', gradient: 'linear-gradient(135deg, #22C55E, #FACC15)', icon: '🇯🇲', desc: '加勒比海律动', category: '主题' },
  { key: 'blues', label: '蓝调', color: '#2563EB', gradient: 'linear-gradient(135deg, #2563EB, #1E3A8A)', icon: '🎺', desc: '蓝调吉他的根源', category: '主题' },
  { key: 'country', label: '乡村', color: '#A16207', gradient: 'linear-gradient(135deg, #A16207, #CA8A04)', icon: '🤠', desc: '美国乡村/牛仔情结', category: '主题' },
  { key: 'world', label: '世界音乐', color: '#0D9488', gradient: 'linear-gradient(135deg, #0D9488, #0EA5E9)', icon: '🌍', desc: '跨文化跨地域', category: '主题' },
  { key: 'cinematic', label: '电影配乐', color: '#7C2D12', gradient: 'linear-gradient(135deg, #7C2D12, #B91C1C)', icon: '🎬', desc: '史诗 / 影视 / 配乐', category: '主题' },
  { key: 'soundtrack', label: '影视原声', color: '#831843', gradient: 'linear-gradient(135deg, #831843, #DB2777)', icon: '🎞️', desc: '电影/动画原声', category: '主题' },
  { key: 'orchestral', label: '管弦', color: '#581C87', gradient: 'linear-gradient(135deg, #581C87, #9333EA)', icon: '🎼', desc: '大型管弦乐作品', category: '主题' },
  { key: '90s', label: '90年代', color: '#9333EA', gradient: 'linear-gradient(135deg, #9333EA, #EC4899)', icon: '📼', desc: '90年代金曲怀旧', category: '时代' },
  { key: '80s', label: '80年代', color: '#DB2777', gradient: 'linear-gradient(135deg, #DB2777, #F59E0B)', icon: '🎞️', desc: '80年代复古经典', category: '时代' },
  { key: 'chill', label: '放松', color: '#06B6D4', gradient: 'linear-gradient(135deg, #06B6D4, #3B82F6)', icon: '🍃', desc: '慵懒放松时光', category: '心情' },
  { key: 'indie', label: '独立', color: '#F59E0B', gradient: 'linear-gradient(135deg, #F59E0B, #EF4444)', icon: '🌟', desc: '独立音乐人作品', category: '主题' },
  { key: 'meditation', label: '冥想', color: '#0F766E', gradient: 'linear-gradient(135deg, #0F766E, #0EA5E9)', icon: '🧘', desc: '冥想/瑜伽/正念', category: '心情' },
  { key: 'sleep', label: '助眠', color: '#1E1B4B', gradient: 'linear-gradient(135deg, #1E1B4B, #4338CA)', icon: '😴', desc: '深度睡眠音乐', category: '心情' },
  { key: 'study', label: '学习', color: '#1D4ED8', gradient: 'linear-gradient(135deg, #1D4ED8, #3B82F6)', icon: '📚', desc: '专注学习/工作', category: '心情' },
  { key: 'workout', label: '健身', color: '#DC2626', gradient: 'linear-gradient(135deg, #DC2626, #F97316)', icon: '💪', desc: '高能运动节拍', category: '心情' },
  { key: 'party', label: '派对', color: '#E11D48', gradient: 'linear-gradient(135deg, #E11D48, #A21CAF)', icon: '🎉', desc: '派对热曲', category: '心情' },
  { key: 'romantic', label: '浪漫', color: '#F43F5E', gradient: 'linear-gradient(135deg, #F43F5E, #FB7185)', icon: '💕', desc: '浪漫情调', category: '心情' },
  { key: 'dream', label: '梦幻', color: '#A78BFA', gradient: 'linear-gradient(135deg, #A78BFA, #F0ABFC)', icon: '✨', desc: '梦幻迷离', category: '心情' },
  { key: 'happy', label: '快乐', color: '#FBBF24', gradient: 'linear-gradient(135deg, #FBBF24, #F97316)', icon: '😄', desc: '轻松愉悦', category: '心情' },
  { key: 'sad', label: '悲伤', color: '#1E40AF', gradient: 'linear-gradient(135deg, #1E40AF, #3730A3)', icon: '💧', desc: '低沉情绪音乐', category: '心情' },
  { key: 'energetic', label: '活力', color: '#F97316', gradient: 'linear-gradient(135deg, #F97316, #DC2626)', icon: '⚡', desc: '充满能量', category: '心情' },
  { key: 'epic', label: '史诗', color: '#7F1D1D', gradient: 'linear-gradient(135deg, #7F1D1D, #F59E0B)', icon: '🗡️', desc: '宏大史诗感', category: '心情' },
]
