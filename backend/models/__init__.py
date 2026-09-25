"""SQLAlchemy 模型层。

- Song：曲库（含 11 维音频特征 JSON）
- Playlist / PlaylistSong：歌单（多对多，带排序）
- ChatMessage：AI 对话历史
- UserFeedback：用户反馈（用于个性化）
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String, Table, Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Song(Base):
    """歌曲。features 存 11 维音频特征（与 Spotify audio-features 对齐）。"""

    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    song_id = Column(String(32), unique=True, nullable=False, index=True)  # 如 TM-0001
    title = Column(String(128), nullable=False)
    artist = Column(String(128), nullable=False)
    album = Column(String(128), default="")
    genre = Column(String(32), default="", index=True)
    mood_tags = Column(Text, default="[]")          # JSON 数组字符串
    duration = Column(Integer, default=0)           # 毫秒
    audio_url = Column(String(256), default="")
    cover_url = Column(String(256), default="")     # 封面图 URL（iTunes/上传）
    cover_color = Column(String(16), default="#4DABF7")
    lyrics = Column(Text, default="")               # 歌词（多行；空 = 未拉到）
    features = Column(Text, default="[]")           # 11 维特征 JSON 数组
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Song {self.song_id} {self.title} - {self.artist}>"


# 歌单 <-> 歌曲 多对多关联表（带添加顺序）
playlist_songs = Table(
    "playlist_songs",
    Base.metadata,
    Column("playlist_id", Integer, ForeignKey("playlists.id", ondelete="CASCADE"), primary_key=True),
    Column("song_id", Integer, ForeignKey("songs.id", ondelete="CASCADE"), primary_key=True),
    Column("position", Integer, default=0),
)


class Playlist(Base):
    """用户歌单。"""

    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    scene = Column(String(32), default="")          # 场景标签：通勤/健身/助眠/学习...
    description = Column(String(256), default="")
    cover_color = Column(String(16), default="#4DABF7")  # 8 色预设封面
    cover_url = Column(String(256), default="")          # 上传的自定义头像 URL
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    songs = relationship("Song", secondary=playlist_songs, lazy="selectin")


class ChatMessage(Base):
    """AI 对话历史（一条用户消息 + 一条 AI 回复成对存储）。"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String(16), nullable=False)       # user | assistant
    content = Column(Text, nullable=False)
    song_ids = Column(Text, default="[]")           # AI 回复关联的歌曲 id 列表（JSON）
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserFeedback(Base):
    """用户对歌曲的显式反馈（like/dislike），后续用于偏好画像。"""

    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    song_id = Column(Integer, ForeignKey("songs.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(16), nullable=False)     # like | dislike
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
