#!/usr/bin/env python
# 从真实 SQLite 曲库（777 首）重新导出种子 JSON，统一"文档/数据库/前端离线兜底"三处口径。
# 用法：python scripts/export_library_json.py
import sqlite3, json, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "backend", "tunematch.db")
TARGETS = [
    os.path.join(ROOT, "data", "music_library.json"),
    os.path.join(ROOT, "frontend", "src", "assets", "music_library.json"),
]

c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row
rows = c.execute(
    "SELECT song_id,title,artist,album,genre,mood_tags,duration,audio_url,cover_color,cover_url,lyrics "
    "FROM songs ORDER BY id"
).fetchall()

songs = []
for r in rows:
    mt = r["mood_tags"]
    try:
        mt = json.loads(mt) if mt else []
    except Exception:
        mt = []
    dur = r["duration"]
    dur_s = round(dur / 1000) if isinstance(dur, (int, float)) else (dur or 0)
    songs.append({
        "song_id": r["song_id"],
        "title": r["title"],
        "artist": r["artist"],
        "album": r["album"] or "",
        "genre": (r["genre"] or "pop").lower(),
        "mood_tags": mt,
        "duration": dur_s,
        "audio_url": r["audio_url"] or "",
        "cover_color": r["cover_color"] or "#4DABF7",
        "cover_url": r["cover_url"] or "",
        "lyrics": r["lyrics"] or "",
    })

payload = {
    "version": "1.0",
    "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    "total": len(songs),
    "songs": songs,
}

for t in TARGETS:
    os.makedirs(os.path.dirname(t), exist_ok=True)
    with open(t, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

print(f"✅ 已从数据库导出 {len(songs)} 首 -> {len(TARGETS)} 个种子文件")
for t in TARGETS:
    print("   ", os.path.relpath(t, ROOT), os.path.getsize(t), "bytes")
