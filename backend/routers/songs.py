"""歌曲路由：列表（genre/mood/keyword 筛选）+ 详情。"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from db import get_db
from models import Song
from schemas import SongOut, err, ok

router = APIRouter(prefix="/api/songs", tags=["songs"])


@router.get("")
def list_songs(
    genre: Optional[str] = Query(default=None, description="曲风：pop/rock/folk/edm/hip-hop..."),
    mood: Optional[str] = Query(default=None, description="情绪：开心/悲伤/浪漫/治愈..."),
    keyword: Optional[str] = Query(default=None, description="标题/歌手关键词"),
    q: Optional[str] = Query(default=None, description="全文搜索关键字（标题/歌手/专辑/情绪标签，模糊匹配）"),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    """歌曲列表，支持 genre / mood / keyword / q(全文搜索) 筛选。"""
    import json as _json
    q_lower = (q or "").strip().lower()
    qry = db.query(Song)
    if genre:
        qry = qry.filter(Song.genre == genre.lower())
    if keyword:
        kw = f"%{keyword}%"
        qry = qry.filter(or_(Song.title.like(kw), Song.artist.like(kw)))
    if mood:
        all_rows = qry.all()
        def _match_mood(rows: list[Song], m: str) -> list:
            return [s for s in rows if m in _json.loads(s.mood_tags or "[]")]
        return ok([SongOut.from_song(s).model_dump() for s in _match_mood(all_rows, mood)][:limit])
    if q_lower:
        # 全文搜索：标题 / 歌手 / 专辑 / 情绪标签
        kw = f"%{q_lower}%"
        candidates = qry.all()
        def _hit(s: Song) -> bool:
            blob = f"{s.title} {s.artist} {s.album or ''} {s.mood_tags or ''} {s.genre or ''}".lower()
            return q_lower in blob
        candidates = [s for s in candidates if _hit(s)]
        return ok([SongOut.from_song(s).model_dump() for s in candidates][:limit])
    songs = qry.order_by(Song.id).all()
    return ok([SongOut.from_song(s).model_dump() for s in songs])


@router.get("/{song_id}")
def get_song(song_id: int, db: Session = Depends(get_db)) -> dict:
    """歌曲详情。"""
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=404, detail=err(404, "歌曲不存在"))
    return ok(SongOut.from_song(song).model_dump())


@router.get("/meta/genres")
def list_genres(db: Session = Depends(get_db)) -> dict:
    """曲风列表（前端筛选用）。"""
    genres = sorted({s.genre for s in db.query(Song).all() if s.genre})
    return ok(genres)


@router.post("/{song_id}/lyrics")
async def fetch_lyrics(song_id: int, db: Session = Depends(get_db)) -> dict:
    """拉取并保存歌词。已有 lyrics 直接返回；否则查 lyrics.ovh。"""
    from fastapi import HTTPException
    from services import lyrics as lyrics_svc

    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=404, detail=err(404, "歌曲不存在"))
    if song.lyrics:
        return ok({"lyrics": song.lyrics, "source": "cached"})
    fetched = await lyrics_svc.fetch_lyrics(song.artist, song.title)
    if fetched:
        song.lyrics = fetched
        db.commit()
        return ok({"lyrics": fetched, "source": "lyrics.ovh"})
    return ok({"lyrics": "", "source": "none"}, message="暂未找到歌词（独立音乐人作品通常无歌词）")
