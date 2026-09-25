"""歌词服务：多源获取歌词。

优先级：
1. 歌曲库 lyrics 字段（用户已拉取过的）
2. lyrics.ovh（https://api.lyrics.ovh/v1/{artist}/{title}，免费、公开、无需 key）
3. 都失败返回空字符串

lyrics.ovh 对主流歌手匹配度高（周杰伦、五月天、英文歌手等）；
Jamendo 独立音乐人通常没有歌词（多器乐/电子），返回空属正常。
"""
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

LYRICS_OVH = "https://api.lyrics.ovh/v1/{artist}/{title}"
TIMEOUT = 10.0
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
}


def _clean_query(s: str) -> str:
    """清洗：去掉 (feat. xxx)、括号注释、- Remastered 等变体。"""
    s = s.strip()
    for sep in [" (", " [", " - ", " feat.", " feat "]:
        if sep in s:
            s = s.split(sep)[0].strip()
    return s or ""


async def fetch_lyrics(artist: str, title: str) -> Optional[str]:
    """从 lyrics.ovh 拉取歌词。返回清洗后的文本或 None。"""
    artist_q = _clean_query(artist)
    title_q = _clean_query(title)
    if not artist_q or not title_q:
        return None
    url = LYRICS_OVH.format(artist=artist_q, title=title_q)
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, headers=UA, follow_redirects=True) as client:
            resp = await client.get(url)
        if resp.status_code == 200:
            data = resp.json()
            lyrics = (data.get("lyrics") or "").strip()
            return lyrics or None
    except Exception as e:
        logger.info("lyrics.ovh fetch failed for %s - %s: %s", artist_q, title_q, e)
    return None
