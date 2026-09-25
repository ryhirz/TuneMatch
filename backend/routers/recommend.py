"""推荐路由：AI 推荐（text / tags / seed / audio 四种模式）。"""
import base64
import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from models import Song
from schemas import RecommendRequest, SongOut, err, ok
from services import audio as audio_svc
from services import chroma, recommend as recommend_svc

router = APIRouter(prefix="/api/recommend", tags=["recommend"])


@router.post("")
def recommend(req: RecommendRequest, db: Session = Depends(get_db)) -> dict:
    """主推荐接口。

    入参 mode:
    - text:  自然语言描述（如"想要适合下夜班听的治愈系民谣"）
    - tags:  标签数组（曲风/情绪）+ 可选 scene
    - seed:  text 为种子歌曲名（如"晴天 周杰伦"）
    - audio: audio_base64 为音频（特征提取 → 相似召回）
    """
    # audio 模式：特征提取 → 向量相似召回（无 librosa 则降级全库）
    if req.mode == "audio":
        return _recommend_audio(req, db)

    songs, parsed = recommend_svc.recommend(
        db, text=req.text, tags=req.tags, scene=req.scene, limit=req.limit
    )
    return ok(
        {
            "songs": [s.model_dump() for s in songs],
            "parsed": parsed,
            "degraded": False,
        }
    )


def _recommend_audio(req: RecommendRequest, db: Session) -> dict:
    if not req.audio_base64:
        raise HTTPException(status_code=422, detail=err(422, "audio 模式需要 audio_base64 字段"))
    try:
        file_bytes = base64.b64decode(req.audio_base64)
    except Exception:
        raise HTTPException(status_code=422, detail=err(422, "audio_base64 格式错误"))

    features, fe_err = audio_svc.extract_features(file_bytes)
    if fe_err:
        # 无 librosa：降级为全库推荐（带提示）
        songs, parsed = recommend_svc.recommend(db, text=req.text, limit=req.limit)
        return ok({
            "songs": [s.model_dump() for s in songs],
            "parsed": parsed,
            "degraded": True,
            "degraded_reason": fe_err,
        })

    # 特征入库 + 相似召回
    song_ids = chroma.query_similar(features, top_k=req.limit)
    songs: list[Song] = []
    for sid in song_ids:
        s = db.get(Song, sid)
        if s:
            songs.append(s)
    if not songs:  # 空库回退
        songs = db.query(Song).limit(req.limit).all()

    out: list[SongOut] = []
    for i, s in enumerate(songs):
        out.append(SongOut.from_song(s, match=max(60, 95 - i * 4)))
    return ok({"songs": [s.model_dump() for s in out], "parsed": {"mode": "audio"}, "degraded": False})
