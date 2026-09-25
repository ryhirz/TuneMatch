"""曲库导入脚本：data/music_library.json → SQLite + ChromaDB。

用法（在 backend/ 目录下执行）：
    python ../scripts/init_library.py

行为：
- 读取 data/music_library.json（50 首）
- 生成 11 维音频特征（按曲风+情绪启发式，确定性）
- 批量写入 SQLite songs 表（song_id 冲突则跳过）
- 向量写入 ChromaDB（未安装则跳过并提示）
"""
import json
import os
import sys

# 允许从任意位置执行：把项目根/backend 加入 sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

from db import SessionLocal, init_db  # noqa: E402
from models import Song  # noqa: E402
from services import chroma  # noqa: E402

LIBRARY_PATH = os.getenv("MUSIC_LIBRARY_PATH", os.path.join(ROOT, "data", "music_library.json"))

# ---------- 11 维特征启发式生成（与 services/recommend.py 消费方式一致） ----------
GENRE_BASE = {
    "pop":       {"danceability": [0.6, 0.75], "energy": [0.55, 0.7],  "acousticness": [0.08, 0.25], "instrumentalness": [0.001, 0.01], "speechiness": [0.03, 0.06], "tempo": [92, 120], "loudness": [-9, -6]},
    "folk":      {"danceability": [0.45, 0.6], "energy": [0.4, 0.55],  "acousticness": [0.55, 0.8], "instrumentalness": [0.02, 0.15], "speechiness": [0.03, 0.05], "tempo": [80, 105], "loudness": [-12, -8]},
    "rock":      {"danceability": [0.45, 0.62], "energy": [0.72, 0.92], "acousticness": [0.02, 0.12], "instrumentalness": [0.001, 0.02], "speechiness": [0.04, 0.08], "tempo": [110, 140], "loudness": [-7, -4]},
    "edm":       {"danceability": [0.7, 0.88], "energy": [0.75, 0.95], "acousticness": [0.01, 0.08], "instrumentalness": [0.2, 0.55], "speechiness": [0.03, 0.08], "tempo": [118, 135], "loudness": [-6, -3]},
    "hip-hop":   {"danceability": [0.68, 0.82], "energy": [0.55, 0.75], "acousticness": [0.05, 0.2], "instrumentalness": [0.001, 0.02], "speechiness": [0.28, 0.45], "tempo": [85, 100], "loudness": [-9, -5]},
    "classical": {"danceability": [0.2, 0.35], "energy": [0.15, 0.3],  "acousticness": [0.9, 0.98], "instrumentalness": [0.85, 0.98], "speechiness": [0.01, 0.03], "tempo": [60, 90], "loudness": [-20, -12]},
    "jazz":      {"danceability": [0.4, 0.6], "energy": [0.3, 0.5],   "acousticness": [0.5, 0.8], "instrumentalness": [0.4, 0.9], "speechiness": [0.03, 0.06], "tempo": [75, 110], "loudness": [-16, -9]},
    "lofi":      {"danceability": [0.5, 0.65], "energy": [0.3, 0.45],  "acousticness": [0.55, 0.8], "instrumentalness": [0.6, 0.9], "speechiness": [0.03, 0.06], "tempo": [80, 100], "loudness": [-14, -9]},
    "ambient":   {"danceability": [0.05, 0.2], "energy": [0.02, 0.15], "acousticness": [0.8, 0.98], "instrumentalness": [0.9, 1.0], "speechiness": [0.0, 0.02], "tempo": [45, 75], "loudness": [-25, -15]},
    "r-n-b":     {"danceability": [0.55, 0.75], "energy": [0.4, 0.6], "acousticness": [0.2, 0.45], "instrumentalness": [0.01, 0.1], "speechiness": [0.04, 0.1], "tempo": [75, 105], "loudness": [-10, -6]},
}

GENRE_MAP = {"Pop": "pop", "Folk": "folk", "Rock": "rock", "Electronic": "edm", "Hip-Hop": "hip-hop"}

MOOD_FIX = {
    "热血": {"energy": 0.1, "tempo": 8, "valence": 0.05},
    "激昂": {"energy": 0.1, "tempo": 8, "valence": 0.05},
    "治愈": {"energy": -0.08, "valence": 0.05},
    "放松": {"energy": -0.08},
    "悲伤": {"valence": -0.25, "mode": 0},
    "孤独": {"valence": -0.15, "mode": 0},
    "浪漫": {"valence": 0.15, "mode": 1},
    "梦幻": {"instrumentalness": 0.05, "acousticness": 0.04},
    "怀旧": {"acousticness": 0.05},
    "开心": {"valence": 0.2, "mode": 1},
}


def _rng(seed: int):
    """确定性伪随机。"""
    s = seed * 9301 + 49297
    while True:
        s = (s * 9301 + 49297) % 233280
        yield s / 233280


def build_features(song: dict, idx: int) -> list[float]:
    """按曲风+情绪启发式生成 11 维特征（确定性）。"""
    r = _rng(idx + 1)
    genre = GENRE_MAP.get(song.get("genre", ""), "pop")
    base = GENRE_BASE.get(genre, GENRE_BASE["pop"])
    moods = song.get("mood_tags", [])

    energy = base["energy"][0] + next(r) * (base["energy"][1] - base["energy"][0])
    valence = 0.4 + next(r) * 0.3
    tempo = base["tempo"][0] + next(r) * (base["tempo"][1] - base["tempo"][0])
    acousticness = base["acousticness"][0] + next(r) * (base["acousticness"][1] - base["acousticness"][0])
    instrumentalness = base["instrumentalness"][0] + next(r) * (base["instrumentalness"][1] - base["instrumentalness"][0])
    mode = 1

    for m in moods:
        fix = MOOD_FIX.get(m)
        if not fix:
            continue
        for k, v in fix.items():
            if k == "energy":
                energy += v
            elif k == "tempo":
                tempo += v
            elif k == "valence":
                valence += v
            elif k == "mode":
                mode = v
            elif k == "acousticness":
                acousticness += v
            elif k == "instrumentalness":
                instrumentalness += v

    danceability = base["danceability"][0] + next(r) * (base["danceability"][1] - base["danceability"][0]) + (valence - 0.5) * 0.1
    speechiness = base["speechiness"][0] + next(r) * (base["speechiness"][1] - base["speechiness"][0])
    loudness = base["loudness"][0] + next(r) * (base["loudness"][1] - base["loudness"][0])

    def clamp(v, lo, hi):
        return min(hi, max(lo, v))

    return [
        round(clamp(danceability, 0.05, 0.95), 2),
        round(clamp(energy, 0.02, 0.98), 2),
        round(clamp(valence, 0.02, 0.98), 2),
        round(clamp(acousticness, 0.005, 0.99), 2),
        round(clamp(instrumentalness, 0.0005, 0.99), 2),
        round(clamp(speechiness, 0.005, 0.5), 2),
        round(clamp(tempo, 40, 200)),
        int(next(r) * 12) % 12,  # key 0-11
        mode,
        round(clamp(loudness, -30, -2), 1),
        song.get("duration", 200) * 1000,  # duration_ms
    ]


def main() -> None:
    if not os.path.exists(LIBRARY_PATH):
        print(f"[init_library] 找不到曲库文件: {LIBRARY_PATH}")
        sys.exit(1)

    with open(LIBRARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    songs = data.get("songs", data)  # 兼容 {"songs": [...]} 与纯数组

    init_db()
    db = SessionLocal()
    try:
        added = skipped = 0
        chroma_ok = chroma_skip = 0
        for i, s in enumerate(songs):
            genre = GENRE_MAP.get(s.get("genre", ""), (s.get("genre") or "pop").lower())
            features = build_features(s, i)
            existing = db.query(Song).filter(Song.song_id == s["song_id"]).first()
            if existing:
                skipped += 1
                continue
            song = Song(
                song_id=s["song_id"],
                title=s["title"],
                artist=s["artist"],
                album=s.get("album", ""),
                genre=genre,
                mood_tags=json.dumps(s.get("mood_tags", []), ensure_ascii=False),
                duration=s.get("duration", 200) * 1000,
                audio_url=s.get("audio_url", ""),
                cover_color=s.get("cover_color", "#4DABF7"),
                features=json.dumps(features),
            )
            db.add(song)
            db.flush()  # 拿到自增 id
            if chroma.upsert_song(song.id, song.title, features):
                chroma_ok += 1
            else:
                chroma_skip += 1
            added += 1
        db.commit()
        print(f"[init_library] 完成：新增 {added} 首，跳过（已存在）{skipped} 首")
        print(f"[init_library] ChromaDB：写入 {chroma_ok} 首，跳过 {chroma_skip} 首"
              + ("（未安装 chromadb，跳过向量入库）" if chroma_skip == added else ""))
        print(f"[init_library] 当前曲库总数: {db.query(Song).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
