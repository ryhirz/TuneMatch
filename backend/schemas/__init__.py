"""Pydantic v2 Schemas：统一响应格式 + 各接口入参/出参校验。

统一响应：{ "code": 0, "message": "success", "data": {...} }
错误码：422 参数校验失败 / 404 资源不存在 / 500 服务异常
"""
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


# ---------- 统一响应 ----------
class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: Optional[T] = None


def ok(data: Any = None, message: str = "success") -> dict:
    return {"code": 0, "message": message, "data": data}


def err(code: int, message: str) -> dict:
    return {"code": code, "message": message, "data": None}


# ---------- 歌曲 ----------
class SongOut(BaseModel):
    id: int
    song_id: str
    title: str
    artist: str
    album: str = ""
    genre: str = ""
    mood_tags: List[str] = Field(default_factory=list)
    duration: int = 0
    audio_url: str = ""
    cover_url: str = ""
    cover_color: str = "#4DABF7"
    lyrics: str = ""
    features: List[float] = Field(default_factory=list)
    match: int = Field(default=0, description="推荐匹配度 0-100")

    @classmethod
    def from_song(cls, song, match: int = 0) -> "SongOut":
        import json
        moods = json.loads(song.mood_tags or "[]")
        feats = json.loads(song.features or "[]")
        # 列表场景没有显式 match（默认 0）：根据 features + 歌曲 id 生成稳定 70-98 之间的「基础匹配度」
        if match == 0:
            if feats:
                # 用 features 前 4 维（acoustic/dance/energy/valence）算分数
                base = sum(feats[:4]) / max(1, min(4, len(feats)))
                # 加歌曲 id 偏置让不同歌曲有差异（70-95）
                bias = (song.id * 7) % 25
                match = max(70, min(98, int(70 + base * 18 + bias * 0.3)))
            else:
                # 无特征：纯 id 偏置（70-95）
                bias = (song.id * 11) % 26
                match = 70 + bias
        return cls(
            id=song.id, song_id=song.song_id, title=song.title, artist=song.artist,
            album=song.album or "", genre=song.genre or "",
            mood_tags=moods if isinstance(moods, list) else [],
            duration=song.duration or 0, audio_url=song.audio_url or "",
            cover_url=song.cover_url or "", cover_color=song.cover_color or "#4DABF7",
            lyrics=song.lyrics or "", features=feats, match=match,
        )


# ---------- 歌单 ----------
class PlaylistOut(BaseModel):
    id: int
    name: str
    scene: str = ""
    description: str = ""
    cover_color: str = "#4DABF7"
    cover_url: str = ""
    song_count: int = 0
    songs: List[SongOut] = Field(default_factory=list)
    created_at: Optional[str] = None


class PlaylistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    scene: str = Field(default="", max_length=32)
    description: str = Field(default="", max_length=256)
    cover_color: str = Field(default="#4DABF7", max_length=16)


class PlaylistUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    scene: Optional[str] = Field(default=None, max_length=32)
    description: Optional[str] = Field(default=None, max_length=256)
    cover_color: Optional[str] = Field(default=None, max_length=16)
    cover_url: Optional[str] = Field(default=None, max_length=256)


class PlaylistAddSong(BaseModel):
    song_id: int = Field(gt=0)


# ---------- 推荐 ----------
class RecommendRequest(BaseModel):
    mode: str = Field(default="text", pattern="^(text|tags|seed|audio)$")
    text: str = Field(default="", max_length=500, description="自然语言描述 / 种子歌曲名")
    tags: List[str] = Field(default_factory=list, description="标签输入：曲风/情绪")
    scene: str = Field(default="", max_length=32, description="场景：通勤/健身/助眠/学习/聚会/驾驶/旅行")
    audio_base64: Optional[str] = Field(default=None, description="音频（base64，识曲/特征提取）")
    limit: int = Field(default=6, ge=1, le=20)

    @field_validator("tags")
    @classmethod
    def _strip_tags(cls, v: List[str]) -> List[str]:
        return [t.strip() for t in v if t and t.strip()]


# ---------- 配置 ----------
class SettingsOut(BaseModel):
    llm_base_url: str = ""
    llm_api_key_set: bool = False          # 是否已配置（不返回明文）
    llm_api_key_mask: str = ""              # 脱敏后的 key（如 sk-***xx）
    llm_model_name: str = ""
    jamendo_client_id: str = ""
    jamendo_client_id_set: bool = False
    providers: List[dict] = Field(default_factory=list)  # 预设供应商列表


class SettingsUpdate(BaseModel):
    llm_base_url: Optional[str] = None
    llm_api_key: Optional[str] = None      # 用户填写的新 key（明文，写入 settings.json）
    llm_model_name: Optional[str] = None
    jamendo_client_id: Optional[str] = None


# ---------- 对话 ----------
class ChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    playlist_id: Optional[int] = Field(default=None, description="携带歌单上下文（AI 结合歌单推荐/整理）")


class ChatHistoryOut(BaseModel):
    id: int
    role: str
    content: str
    song_ids: List[int] = Field(default_factory=list)
    created_at: Optional[str] = None
