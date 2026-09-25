"""歌单导入与创意视觉生成。

支持格式：
- 纯文本清单（每行：歌名 - 歌手 或 歌名 歌手）
- Spotify 导出（专辑/歌曲 tab 分隔）兼容解析
- 解析后自动在本地曲库模糊匹配，生成歌单 + 曲风画像 + 创意视觉图（SVG）
"""
import io
import json
import re
from typing import Optional

from sqlalchemy.orm import Session

from models import Playlist, Song

# 曲风中文映射（与前端 utils/genre.ts 一致）
GENRE_ZH = {
    "pop": "流行", "rock": "摇滚", "folk": "民谣", "edm": "电子", "hip-hop": "嘻哈",
    "hip-hop/rap": "嘻哈说唱", "jazz": "爵士", "classical": "古典", "lofi": "Lo-fi",
    "ambient": "氛围", "r-n-b": "R&B", "electronic": "电子", "dance": "舞曲",
    "chill": "放松", "indie": "独立", "instrumental": "器乐", "piano": "钢琴",
    "acoustic": "原声", "metal": "金属", "reggae": "雷鬼", "blues": "蓝调",
    "country": "乡村", "soundtrack": "影视原声", "world": "世界音乐",
    "soul": "灵魂", "reggaeton": "雷鬼顿", "latin": "拉丁", "k-pop": "K-Pop",
}

# 曲风代表色
GENRE_COLOR = {
    "pop": "#FF6B9D", "rock": "#EF4444", "folk": "#84CC16", "edm": "#7C3AED",
    "hip-hop": "#0EA5E9", "hip-hop/rap": "#0EA5E9", "jazz": "#F59E0B",
    "classical": "#6366F1", "lofi": "#10B981", "ambient": "#0891B2",
    "r-n-b": "#EC4899", "electronic": "#7C3AED", "dance": "#F97316",
    "chill": "#06B6D4", "indie": "#F59E0B", "instrumental": "#8A8A8E",
    "piano": "#A78BFA", "acoustic": "#FCD34D", "metal": "#374151",
    "reggae": "#22C55E", "blues": "#2563EB", "country": "#A16207",
    "soundtrack": "#831843", "world": "#0D9488", "soul": "#F43F5E",
}


def parse_playlist_text(text: str) -> list[dict]:
    """解析歌单文本 → [{title, artist}]。兼容多行格式。"""
    out: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "//", "专辑", "歌曲", "Spotify")):
            continue
        # 支持 "歌名 - 歌手" / "歌名 - 歌手" / tab 分隔
        title = artist = ""
        for sep in [" - ", "–", "\t", "|", "—"]:
            if sep in line:
                parts = line.split(sep, 1)
                title, artist = parts[0].strip(), parts[1].strip()
                break
        if not title:
            continue
        if artist and artist.lower().startswith(("artist", "歌手")):
            artist = ""
        out.append({"title": title, "artist": artist})
    return out


def _normalize(s: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]", "", (s or "").lower())


def match_song(db: Session, title: str, artist: str = "") -> Optional[Song]:
    """在曲库模糊匹配。优先标题+歌手精确，再标题包含。"""
    nt = _normalize(title)
    if not nt:
        return None
    # 1) 标题完全一致 + 歌手一致
    if artist:
        na = _normalize(artist)
        hit = db.query(Song).filter(Song.title.ilike(f"%{title}%"), Song.artist.ilike(f"%{artist}%")).first()
        if hit:
            return hit
    # 2) 标题包含
    hit = db.query(Song).filter(Song.title.ilike(f"%{title}%")).first()
    if hit:
        return hit
    return None


def import_playlist(db: Session, name: str, text: str, description: str = "") -> dict:
    """导入歌单文本 → 创建歌单 + 关联曲库歌曲。返回统计 + 曲风画像。"""
    items = parse_playlist_text(text)
    matched: list[Song] = []
    unmatched: list[dict] = []
    seen: set[int] = set()
    for it in items:
        s = match_song(db, it["title"], it.get("artist", ""))
        if s and s.id not in seen:
            seen.add(s.id)
            matched.append(s)
        elif not s:
            unmatched.append(it)

    # 创建歌单
    pl = Playlist(name=name[:64], scene="", description=(description or "")[:256],
                  cover_color="#4DABF7", cover_url="")
    db.add(pl)
    db.flush()
    for s in matched:
        pl.songs.append(s)
    db.commit()

    # 曲风画像
    genre_cnt: dict[str, int] = {}
    mood_cnt: dict[str, int] = {}
    for s in matched:
        g = s.genre or "unknown"
        genre_cnt[g] = genre_cnt.get(g, 0) + 1
        try:
            moods = json.loads(s.mood_tags or "[]")
            for m in moods:
                mood_cnt[m] = mood_cnt.get(m, 0) + 1
        except Exception:
            pass

    top_genres = sorted(genre_cnt, key=genre_cnt.get, reverse=True)[:5]
    top_moods = sorted(mood_cnt, key=mood_cnt.get, reverse=True)[:5]

    return {
        "playlist_id": pl.id,
        "playlist_name": pl.name,
        "total_items": len(items),
        "matched": len(matched),
        "unmatched_count": len(unmatched),
        "unmatched": unmatched[:20],
        "genre_dist": [{"genre": g, "count": genre_cnt[g]} for g in sorted(genre_cnt, key=genre_cnt.get, reverse=True)],
        "mood_dist": [{"mood": m, "count": mood_cnt[m]} for m in top_moods],
        "top_genres": [GENRE_ZH.get(g, g) for g in top_genres],
        "profile": {
            "primary_genre": GENRE_ZH.get(top_genres[0], top_genres[0]) if top_genres else "未知",
            "genres": [GENRE_ZH.get(g, g) for g in top_genres],
            "moods": top_moods,
            "avg_duration_s": round(sum((s.duration or 0) for s in matched) / max(1, len(matched)) / 1000),
        },
    }


def generate_playlist_art(profile: dict, playlist_name: str, matched_count: int) -> str:
    """根据曲风画像生成创意视觉图（SVG 字符串，可嵌 <img src="data:...">）。

    风格：Apple Music 专辑封面风 —— 深色底 + 渐变圆 + 曲风色点阵 + 曲风标签。
    """
    genres = profile.get("genres") or ["pop"]
    primary = genres[0] if genres else "流行"
    color = GENRE_COLOR.get(primary.lower(), "#4DABF7")
    # 把主色换成风格色
    genre_colors = [GENRE_COLOR.get(g.lower(), "#4DABF7") for g in genres[:4]]
    while len(genre_colors) < 4:
        genre_colors.append("#4DABF7")

    # 背景渐变
    g1, g2 = genre_colors[0], genre_colors[-1]

    # 点阵（伪随机但稳定）
    import random
    rng = random.Random(playlist_name)
    dots = []
    for i in range(40):
        x = 5 + rng.random() * 90
        y = 5 + rng.random() * 90
        c = rng.choice(genre_colors)
        r = 1 + rng.random() * 2.5
        op = 0.25 + rng.random() * 0.5
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c}" opacity="{op:.2f}"/>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="400" height="400">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{g1}" stop-opacity="0.92"/>
      <stop offset="100%" stop-color="{g2}" stop-opacity="0.85"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.35" r="0.65">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.18"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="400" height="400" fill="url(#bg)"/>
  <rect width="400" height="400" fill="url(#glow)"/>
  {''.join(dots)}
  <!-- 中心唱片 -->
  <circle cx="200" cy="185" r="88" fill="#0b0b0f" opacity="0.85"/>
  <circle cx="200" cy="185" r="88" fill="none" stroke="rgba(255,255,255,0.25)" stroke-width="1.5"/>
  <circle cx="200" cy="185" r="34" fill="{g1}"/>
  <circle cx="200" cy="185" r="12" fill="#ffffff" opacity="0.9"/>
  <text x="200" y="185" text-anchor="middle" dominant-baseline="middle" font-family="system-ui" font-size="14" font-weight="700" fill="#ffffff">♪</text>
  <!-- 标题 -->
  <text x="200" y="318" text-anchor="middle" font-family="system-ui, sans-serif" font-size="26" font-weight="800" fill="#ffffff">{playlist_name[:14]}</text>
  <text x="200" y="348" text-anchor="middle" font-family="system-ui, sans-serif" font-size="15" font-weight="500" fill="rgba(255,255,255,0.85)">{primary} · {matched_count} 首</text>
  <text x="200" y="374" text-anchor="middle" font-family="system-ui, sans-serif" font-size="12" fill="rgba(255,255,255,0.6)">{', '.join(genres[:3])}</text>
</svg>'''
    return svg
