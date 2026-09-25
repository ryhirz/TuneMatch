"""歌单路由：CRUD + 添加歌曲（含边界处理）+ 头像上传 + 歌曲文件导入。"""
import json
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import delete
from sqlalchemy.orm import Session

from db import get_db
from models import Playlist, Song, playlist_songs
from schemas import (
    PlaylistAddSong, PlaylistCreate, PlaylistOut, PlaylistUpdate, SongOut, err, ok,
)
from services import upload as upload_svc

router = APIRouter(prefix="/api/playlists", tags=["playlists"])


def _to_out(pl: Playlist) -> dict:
    return PlaylistOut(
        id=pl.id, name=pl.name, scene=pl.scene or "", description=pl.description or "",
        cover_color=pl.cover_color or "#4DABF7",
        cover_url=pl.cover_url or "",
        song_count=len(pl.songs),
        songs=[SongOut.from_song(s).model_dump() for s in pl.songs],
        created_at=pl.created_at.isoformat() if pl.created_at else None,
    ).model_dump()


@router.get("")
def list_playlists(db: Session = Depends(get_db)) -> dict:
    """歌单列表（含歌曲与数量）。"""
    pls = db.query(Playlist).order_by(Playlist.created_at.desc()).all()
    return ok([_to_out(p) for p in pls])


@router.post("")
def create_playlist(body: PlaylistCreate, db: Session = Depends(get_db)) -> dict:
    """创建歌单。"""
    pl = Playlist(
        name=body.name,
        scene=body.scene,
        description=body.description,
        cover_color=body.cover_color or "#4DABF7",
    )
    db.add(pl)
    db.commit()
    db.refresh(pl)
    return ok(_to_out(pl), message="歌单已创建")


@router.put("/{playlist_id}")
def update_playlist(playlist_id: int, body: PlaylistUpdate, db: Session = Depends(get_db)) -> dict:
    """更新歌单（名称/场景/描述/封面）。"""
    pl = db.get(Playlist, playlist_id)
    if not pl:
        raise HTTPException(status_code=404, detail=err(404, "歌单不存在"))
    if body.name is not None:
        pl.name = body.name
    if body.scene is not None:
        pl.scene = body.scene
    if body.description is not None:
        pl.description = body.description
    if body.cover_color is not None:
        pl.cover_color = body.cover_color
    if body.cover_url is not None:
        pl.cover_url = body.cover_url
    db.commit()
    db.refresh(pl)
    return ok(_to_out(pl), message="歌单已更新")


@router.delete("/{playlist_id}")
def delete_playlist(playlist_id: int, db: Session = Depends(get_db)) -> dict:
    """删除歌单（级联删除关联歌曲）。"""
    pl = db.get(Playlist, playlist_id)
    if not pl:
        raise HTTPException(status_code=404, detail=err(404, "歌单不存在"))
    db.execute(delete(playlist_songs).where(playlist_songs.c.playlist_id == playlist_id))
    db.delete(pl)
    db.commit()
    return ok(message="歌单已删除")


@router.post("/{playlist_id}/songs")
def add_song(playlist_id: int, body: PlaylistAddSong, db: Session = Depends(get_db)) -> dict:
    """添加歌曲到歌单（重复添加返回 400 语义错误）。"""
    pl = db.get(Playlist, playlist_id)
    if not pl:
        raise HTTPException(status_code=404, detail=err(404, "歌单不存在"))
    song = db.get(Song, body.song_id)
    if not song:
        raise HTTPException(status_code=404, detail=err(404, "歌曲不存在"))

    # 边界：重复添加
    if any(s.id == body.song_id for s in pl.songs):
        raise HTTPException(status_code=422, detail=err(422, "歌曲已在歌单中"))

    pl.songs.append(song)
    db.commit()
    db.refresh(pl)
    return ok(_to_out(pl), message="已加入歌单")


@router.delete("/{playlist_id}/songs/{song_id}")
def remove_song(playlist_id: int, song_id: int, db: Session = Depends(get_db)) -> dict:
    """从歌单移除歌曲。"""
    pl = db.get(Playlist, playlist_id)
    if not pl:
        raise HTTPException(status_code=404, detail=err(404, "歌单不存在"))
    pl.songs = [s for s in pl.songs if s.id != song_id]
    db.commit()
    db.refresh(pl)
    return ok(_to_out(pl), message="已从歌单移除")


@router.post("/{playlist_id}/cover")
async def upload_cover(playlist_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    """上传歌单头像（png/jpg/jpeg/webp ≤ 2MB）。"""
    pl = db.get(Playlist, playlist_id)
    if not pl:
        raise HTTPException(status_code=404, detail=err(404, "歌单不存在"))

    info, up_err = upload_svc.save_cover(file)
    if up_err:
        raise HTTPException(status_code=422, detail=err(422, up_err))

    pl.cover_url = info["url"]
    db.commit()
    db.refresh(pl)
    return ok(_to_out(pl), message="头像已更新")


@router.post("/{playlist_id}/songs/import")
async def import_songs(
    playlist_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """批量导入本地歌曲文件（mp3/wav/flac/m4a/ogg/aac ≤ 50MB）。

    非音频文件会被拒绝并返回原因，不中断其他文件导入。
    """
    pl = db.get(Playlist, playlist_id)
    if not pl:
        raise HTTPException(status_code=404, detail=err(404, "歌单不存在"))
    if not files:
        raise HTTPException(status_code=422, detail=err(422, "未选择任何文件"))

    saved, rejected, g_err = upload_svc.save_audio_files(files)

    imported = []
    for item in saved:
        song = Song(
            song_id=f"local-{datetime.now().strftime('%Y%m%d%H%M%S')}-{item['filename']}",
            title=item["title"],
            artist="本地导入",
            album="我的音乐",
            genre="local",
            mood_tags=json.dumps([]),
            duration=0,
            audio_url=item["audio_url"],
            cover_color="#8A8A8E",
            features=json.dumps([]),
        )
        db.add(song)
        db.flush()
        pl.songs.append(song)
        imported.append(SongOut.from_song(song).model_dump())

    db.commit()
    db.refresh(pl)

    return ok({
        "imported": imported,
        "imported_count": len(imported),
        "rejected": rejected,
        "rejected_count": len(rejected),
        "playlist": _to_out(pl),
    }, message=f"成功导入 {len(imported)} 首，拒绝 {len(rejected)} 个")


# ---------- 歌单文本导入 + 创意视觉图 ----------
@router.post("/import-text")
async def import_text_playlist(
    body: dict,
    db: Session = Depends(get_db),
) -> dict:
    """从其他音乐软件（Spotify/网易云/QQ音乐）歌单文本导入。

    请求体：{ name: 歌单名, text: 多行歌单文本, description?: 描述 }
    每行格式：歌名 - 歌手（或 tab 分隔 / 仅歌名）
    返回：匹配统计 + 曲风画像 + 创意视觉图 SVG。
    """
    from services import playlist_import as pi

    name = (body.get("name") or "导入歌单").strip()
    text = (body.get("text") or "").strip()
    description = (body.get("description") or "").strip()
    if not text:
        return err(422, "歌单内容为空")

    result = pi.import_playlist(db, name, text, description)
    if result["matched"] == 0:
        return ok({**result, "art_svg": ""}, message="没有匹配到曲库中的歌曲（可先同步 iTunes 热门曲库）")

    # 生成创意视觉图
    art = pi.generate_playlist_art(result["profile"], result["playlist_name"], result["matched"])
    result["art_svg"] = art
    return ok(result, message=f"导入成功：匹配 {result['matched']}/{result['total_items']} 首")
