"""导出路由：歌单 PDF / 分享海报。"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from db import get_db
from models import Playlist
from schemas import SongOut, err
from services import export as export_svc

router = APIRouter(prefix="/api/export", tags=["export"])


def _load_playlist(playlist_id: int, db: Session) -> Playlist:
    pl = db.get(Playlist, playlist_id)
    if not pl:
        raise HTTPException(status_code=404, detail=err(404, "歌单不存在"))
    if not pl.songs:
        raise HTTPException(status_code=422, detail=err(422, "歌单为空，无法导出"))
    return pl


@router.get("/playlist/{playlist_id}/pdf")
def export_pdf(playlist_id: int, db: Session = Depends(get_db)) -> FileResponse:
    """导出歌单 PDF。"""
    pl = _load_playlist(playlist_id, db)
    songs = [SongOut.from_song(s) for s in pl.songs]
    path, ex_err = export_svc.export_pdf(pl.name, songs)
    if ex_err:
        raise HTTPException(status_code=501, detail=err(501, ex_err))
    return FileResponse(path, media_type="application/pdf",
                        filename=f"{pl.name}.pdf")


@router.get("/playlist/{playlist_id}/poster")
def export_poster(playlist_id: int, db: Session = Depends(get_db)) -> FileResponse:
    """生成分享海报。"""
    pl = _load_playlist(playlist_id, db)
    songs = [SongOut.from_song(s) for s in pl.songs]
    path, ex_err = export_svc.export_poster(pl.name, songs)
    if ex_err:
        raise HTTPException(status_code=501, detail=err(501, ex_err))
    return FileResponse(path, media_type="image/png",
                        filename=f"{pl.name}.png")
