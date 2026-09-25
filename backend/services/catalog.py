"""曲库增强服务：通过 iTunes Search API 获取真实歌曲的封面图 + 30 秒试听音频。

- iTunes Search API（https://itunes.apple.com/search）免费、公开、无需 Key
- 返回 artworkUrl（封面，可调整尺寸）+ previewUrl（30 秒 AAC 试听）
- 用歌名 + 歌手匹配，批量更新曲库中缺失封面/音频的歌曲
"""
import asyncio
import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

ITUNES_SEARCH = "https://itunes.apple.com/search"
ITUNES_LOOKUP = "https://itunes.apple.com/lookup"
TIMEOUT = 12.0
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
}


async def search_track(title: str, artist: str, country: str = "CN") -> dict | None:
    """按歌名+歌手在 iTunes 搜索单曲。返回 {cover_url, audio_url, duration_ms, album, track_name} 或 None。

    匹配策略：优先精确匹配曲名（忽略大小写/空格），若没有精确匹配取第一首。
    """
    query = f"{title} {artist}"
    params = {
        "term": query,
        "media": "music",
        "entity": "song",
        "limit": 10,
        "country": country,
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, headers=UA, follow_redirects=True) as client:
            resp = await client.get(ITUNES_SEARCH, params=params)
            resp.raise_for_status()
            results = resp.json().get("results", [])
    except Exception as e:
        logger.warning("iTunes search failed for %s: %s", query, e)
        return None

    if not results:
        return None

    # 精确匹配候选
    def norm(s: str) -> str:
        return "".join(s.lower().split())

    norm_title = norm(title)
    exact = [
        r for r in results
        if norm(r.get("trackName", "")).find(norm_title) >= 0
        or norm_title in norm(r.get("trackName", ""))
    ]
    pick = exact[0] if exact else results[0]

    artwork = pick.get("artworkUrl100", "")
    # 放大封面：100x100 → 600x600
    if artwork:
        artwork = artwork.replace("100x100bb", "600x600bb")

    return {
        "cover_url": artwork,
        "audio_url": pick.get("previewUrl", ""),
        "duration_ms": pick.get("trackTimeMillis") or 0,
        "album": pick.get("collectionName", ""),
        "track_name": pick.get("trackName", ""),
    }


async def sync_catalog(db, force: bool = False) -> dict:
    """批量同步曲库：为缺失封面/音频的歌曲拉取 iTunes 数据。

    - force=False：只补 audio_url 为空的歌曲
    - force=True：全部重新拉取
    返回统计 {total, updated, failed}
    """
    from models import Song

    songs = db.query(Song).all()
    updated = failed = 0
    sem = asyncio.Semaphore(4)  # 限速并发

    async def one(song: Song) -> None:
        nonlocal updated, failed
        if not force and song.audio_url and song.cover_url:
            return
        async with sem:
            info = await search_track(song.title, song.artist)
        if not info or not info["audio_url"]:
            failed += 1
            return
        changed = False
        if info["audio_url"] and (force or not song.audio_url):
            song.audio_url = info["audio_url"]
            changed = True
        if info["cover_url"] and (force or not song.cover_url):
            song.cover_url = info["cover_url"]
            changed = True
        if info["album"]:
            song.album = info["album"] or song.album
        if info["duration_ms"] and song.duration in (0, 200000):
            song.duration = info["duration_ms"]
        if changed:
            updated += 1
        await asyncio.sleep(0.1)  # iTunes 限流礼貌

    await asyncio.gather(*(one(s) for s in songs))
    db.commit()

    return {"total": len(songs), "updated": updated, "failed": failed}


# ---------- Apple RSS 热门榜单同步 ----------

async def sync_hot_songs(db, *, country: str = "us", limit: int = 100) -> dict:
    """从 Apple RSS Feed 拉取热门歌曲入库（真实封面 + 30s 试听）。

    端点（无需 key）：https://rss.applemarketingtools.com/api/v2/{country}/music/most-played/{limit}/songs.json
    """
    import json as _json
    from datetime import datetime, timezone

    from models import Song

    url = f"https://rss.applemarketingtools.com/api/v2/{country}/music/most-played/{limit}/songs.json"
    imported = skipped = 0
    try:
        async with httpx.AsyncClient(timeout=20, headers=UA, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning("Apple RSS fetch failed: %s", e)
        return {"total": 0, "imported": 0, "skipped": 0, "error": str(e)}

    results = data.get("feed", {}).get("results", [])
    # RSS 榜单不带 previewUrl，用 iTunes lookup 批量补（每批 50 个 id）
    hot_ids = [str(r.get("id")) for r in results if r.get("id")]
    preview_map: dict[str, str] = {}
    for i in range(0, len(hot_ids), 50):
        batch = hot_ids[i:i + 50]
        try:
            async with httpx.AsyncClient(timeout=20, headers=UA, follow_redirects=True) as client:
                r = await client.get("https://itunes.apple.com/lookup", params={"id": ",".join(batch), "entity": "song"})
                data2 = r.json()
            for item in data2.get("results", []):
                if item.get("kind") == "song" and item.get("previewUrl"):
                    preview_map[str(item.get("trackId") or item.get("id"))] = item["previewUrl"]
        except Exception as e:
            logger.warning("iTunes lookup batch failed: %s", e)
        await asyncio.sleep(0.3)

    for r in results:
        name = (r.get("name") or "").strip()
        artist = (r.get("artistName") or "").strip()
        rid = str(r.get("id") or "")
        audio = preview_map.get(rid) or ""
        artwork = (r.get("artworkUrl100") or "").replace("100x100bb", "600x600bb")
        if not name or not audio:
            skipped += 1
            continue
        # 去重：标题+歌手
        dup = db.query(Song).filter(Song.title == name, Song.artist == artist).first()
        if dup:
            skipped += 1
            continue
        genre = "pop"
        raw_genres = r.get("genres") or []
        if isinstance(raw_genres, list) and raw_genres and isinstance(raw_genres[0], dict):
            genre = (raw_genres[0].get("name") or "pop").lower().replace(" ", "-")
        s = Song(
            song_id=f"HT-{r.get('id', '')}",
            title=name[:120],
            artist=artist[:120],
            album=(r.get("collectionName") or "")[:120],
            genre=genre,
            mood_tags=_json.dumps([], ensure_ascii=False),
            duration=int(r.get("durationInMillis") or 200000),
            audio_url=audio[:250],
            cover_url=artwork[:250],
            cover_color="#4DABF7",
            features=_json.dumps([0.5] * 11),
            created_at=datetime.now(timezone.utc),
        )
        db.add(s)
        imported += 1

    db.commit()
    return {"total": len(results), "imported": imported, "skipped": skipped}
