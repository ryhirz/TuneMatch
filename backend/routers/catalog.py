"""曲库增强路由：iTunes 同步封面与试听音频 + Jamendo 全首曲库。

- POST /api/catalog/sync：iTunes 批量同步（force 可选）
- GET /api/catalog/search?title=&artist=：iTunes 搜索单曲（测试用）
- POST /api/catalog/jamendo?client_id=&query=&tags=&limit=：拉取 Jamendo 全首曲目
- GET /api/catalog/jamendo/search：Jamendo 搜索预览（不写库）
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db
from schemas import ok
from services import catalog as catalog_svc
from services import jamendo as jamendo_svc

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.post("/sync")
async def sync_songs(force: bool = False, db: Session = Depends(get_db)) -> dict:
    """批量同步曲库封面与试听音频。force=true 强制刷新全部。"""
    result = await catalog_svc.sync_catalog(db, force=force)
    return ok(result, message=f"同步完成：更新 {result['updated']} 首")


@router.get("/search")
async def search(title: str, artist: str = "") -> dict:
    """测试用：在 iTunes 搜索单曲。"""
    info = await catalog_svc.search_track(title, artist)
    return ok(info)


@router.post("/jamendo")
async def sync_jamendo(
    client_id: str,
    query: str = "",
    tags: str = "",
    limit: int = 20,
    db: Session = Depends(get_db),
) -> dict:
    """拉取 Jamendo 全首曲目（需在 developer.jamendo.com 免费注册 client_id）。"""
    if not client_id or client_id == "test":
        return ok({"error": "need_real_client_id"},
                  message="请先在 developer.jamendo.com 免费注册获取 client_id")
    result = await jamendo_svc.sync_from_jamendo(db, client_id, query=query, tags=tags, limit=limit)
    return ok(result, message=f"Jamendo 同步完成：新增 {result['imported']} 首全首音乐")


@router.get("/jamendo/search")
async def jamendo_search(client_id: str, query: str = "", tags: str = "", limit: int = 10) -> dict:
    """测试用：搜索 Jamendo 全首曲目（不写入库）。"""
    tracks = await jamendo_svc.search_tracks(client_id, query=query, tags=tags, limit=limit)
    return ok(tracks)


@router.post("/hot")
async def sync_hot(country: str = "us", limit: int = 100, db: Session = Depends(get_db)) -> dict:
    """同步 Apple RSS 热门歌曲榜（真实封面 + 30s 试听）。"""
    result = await catalog_svc.sync_hot_songs(db, country=country, limit=limit)
    return ok(result, message=f"热门榜同步完成：新增 {result['imported']} 首")
