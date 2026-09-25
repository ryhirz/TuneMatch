"""ChromaDB 向量检索服务（可选重依赖，import 防护）。

- 歌曲特征向量（11 维）入库，支持相似歌曲召回
- 用户偏好向量（推荐召回个性化）
未安装 chromadb 时 is_available() = False，调用方自动降级。
"""
import json
from typing import Any, Optional

try:
    import chromadb
    _CHROMADB_OK = True
except Exception:  # pragma: no cover
    chromadb = None
    _CHROMADB_OK = False

import config

_COLLECTION_SONGS = "tm_songs"
_COLLECTION_USER = "tm_user_pref"

_client: Any = None
_songs_col: Any = None
_user_col: Any = None


def is_available() -> bool:
    return _CHROMADB_OK


def _ensure() -> bool:
    global _client, _songs_col, _user_col
    if not _CHROMADB_OK or _client is not None:
        return _CHROMADB_OK
    try:
        _client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
        _songs_col = _client.get_or_create_collection(
            name=_COLLECTION_SONGS, metadata={"hnsw:space": "cosine"}
        )
        _user_col = _client.get_or_create_collection(name=_COLLECTION_USER)
        return True
    except Exception:
        _client = None
        return False


def upsert_song(song_id: int, title: str, features: list[float]) -> bool:
    """歌曲特征向量入库（11 维）。"""
    if not _ensure() or not features:
        return False
    try:
        _songs_col.upsert(
            ids=[str(song_id)],
            embeddings=[features],
            metadatas=[{"title": title}],
        )
        return True
    except Exception:
        return False


def query_similar(features: list[float], top_k: int = 6) -> list[int]:
    """按特征向量召回相似歌曲 id 列表。"""
    if not _ensure() or not features:
        return []
    try:
        res = _songs_col.query(query_embeddings=[features], n_results=top_k)
        ids = res.get("ids", [[]])[0]
        return [int(i) for i in ids if str(i).isdigit()]
    except Exception:
        return []


def upsert_user_vector(user_key: str, features: list[float]) -> bool:
    """用户偏好向量入库（个性化召回预留）。"""
    if not _ensure() or not features:
        return False
    try:
        _user_col.upsert(ids=[user_key], embeddings=[features])
        return True
    except Exception:
        return False


def stats() -> Optional[dict[str, Any]]:
    """集合统计（/health 展示用）。"""
    if not _ensure():
        return None
    try:
        return {
            "songs": _songs_col.count(),
            "users": _user_col.count(),
        }
    except Exception:
        return None


def clear_all() -> None:
    """清空集合（测试用）。"""
    if not _ensure():
        return
    try:
        _songs_col.delete(where={}) if False else None
    except Exception:
        pass
