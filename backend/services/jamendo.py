"""Jamendo 全首曲库接入：CC 授权完整版音乐。

- Jamendo API（https://api.jamendo.com/v3.0）需要免费注册的 client_id
- 注册地址：https://developer.jamendo.com（1 分钟，选 "Personal/Test" 即可）
- 返回 track.audio = 全首 mp3 直链（CC 授权，合法免费）+ track.image = 封面
"""
import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

API_BASE = "https://api.jamendo.com/v3.0"
TIMEOUT = 15.0
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
}


async def search_tracks(client_id: str, *, query: str = "", tags: str = "",
                        limit: int = 20, offset: int = 0, audioformat: str = "mp32") -> list[dict]:
    """在 Jamendo 搜索全首曲目。

    返回每首：title / artist / cover / audio_url(全首) / duration / license / tags / id
    """
    params: dict[str, Any] = {
        "client_id": client_id,
        "format": "json",
        "limit": min(limit, 200),
        "offset": offset,
        "include": "musicinfo",
        "audioformat": audioformat,  # mp32 = VBR 高质量
        "imagesize": 600,
        "order": "popularity_total_desc",
    }
    if query:
        params["search"] = query
    if tags:
        params["tags"] = tags
    # include=lyrics 让 Jamendo 直接返回歌词（独立音乐人多数无歌词，会为空）
    if "include" in params:
        params["include"] += "+lyrics"
    else:
        params["include"] = "musicinfo+lyrics"

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, headers=UA, follow_redirects=True) as client:
            resp = await client.get(f"{API_BASE}/tracks/", params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning("Jamendo search failed: %s", e)
        return []

    if data.get("headers", {}).get("status") != "success":
        logger.warning("Jamendo error: %s", data.get("headers", {}).get("error_message"))
        return []

    results = data.get("results", [])
    out = []
    for t in results:
        info = t.get("musicinfo", {})
        out.append({
            "jamendo_id": t.get("id"),
            "title": t.get("name", ""),
            "artist": t.get("artist_name", ""),
            "album": t.get("album_name", ""),
            "cover_url": t.get("image", ""),
            "audio_url": t.get("audio", ""),          # 全首 mp3 直链
            "duration": t.get("duration") or 0,
            "tags": info.get("tags", []) or [],
            "genre": (info.get("tags") or [""])[0] if isinstance(info.get("tags"), list) and info.get("tags") else "",
            "license": t.get("license_ccurl", ""),
            "lyrics": t.get("lyrics", "") or "",       # Jamendo 自带歌词（多数为空）
        })
    return out


async def sync_from_jamendo(db, client_id: str, *, query: str = "", tags: str = "",
                            limit: int = 20, keep_existing: bool = True) -> dict:
    """拉取 Jamendo 全首曲目入库（genre 由调用方传入的 tags 决定；空则 'jamendo'）。

    返回 {total, imported, skipped}
    """
    from models import Song

    tracks = await search_tracks(client_id, query=query, tags=tags, limit=limit)
    imported = skipped = 0
    # 决定入库 genre：优先用 tags（调用方传什么就是什么），否则 jamendo
    primary_genre = (tags or "").strip().lower() or "jamendo"

    for t in tracks:
        if not t["audio_url"]:
            skipped += 1
            continue
        # 去重：同 Jamendo id / 同标题+歌手
        dup = db.query(Song).filter(Song.song_id == f"JAM-{t['jamendo_id']}").first()
        if not dup:
            dup = db.query(Song).filter(Song.title == t["title"], Song.artist == t["artist"]).first()
        if dup:
            if keep_existing:
                skipped += 1
                continue
            dup.audio_url = t["audio_url"]
            dup.cover_url = t["cover_url"] or dup.cover_url
            db.commit()
            imported += 1
            continue

        # 新增（给 11 维特征默认中性值，保证推荐可跑）
        import json
        from datetime import datetime, timezone

        # 规范化 tags 为 list[str]
        raw_tags = t.get("tags", [])
        if isinstance(raw_tags, str):
            raw_tags = [x.strip() for x in raw_tags.split(",") if x.strip()]
        elif not isinstance(raw_tags, list):
            raw_tags = []

        s = Song(
            song_id=f"JAM-{t['jamendo_id']}",
            title=t["title"][:120],
            artist=t["artist"][:120],
            album=(t.get("album") or "")[:120],
            genre=primary_genre,
            mood_tags=json.dumps(raw_tags[:5], ensure_ascii=False),
            duration=int(t["duration"] * 1000) if t["duration"] else 0,
            audio_url=t["audio_url"][:250],
            cover_url=t["cover_url"][:250],
            cover_color="#8A8A8E",
            lyrics=t.get("lyrics", "")[:5000],
            features=json.dumps([0.5] * 11),
            created_at=datetime.now(timezone.utc),
        )
        db.add(s)
        imported += 1

    db.commit()
    return {"total": len(tracks), "imported": imported, "skipped": skipped}
