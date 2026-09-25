"""推荐引擎：多模态输入 → 召回 → 打分排序 → AI 理由。

打分模型（与产品定位一致）：
- 内容契合 45%：genre 匹配 + mood 匹配 + 特征余弦相似
- 场景契合 25%：场景标签命中
- 新鲜度 15%：反馈/曝光衰减（基础版实现）
- 流行度 15%：popularity 归一化

无 Key / 空库均可运行（降级 Mock 曲库）。
"""
import json
import math
from typing import Any, Optional

from sqlalchemy.orm import Session

from models import Song
from schemas import SongOut
from services import llm

# 场景 → 期望特征（energy 区间 / tempo 区间 / valence 目标），与前端场景标签一致
SCENE_TARGETS: dict[str, dict[str, Any]] = {
    "commute": {"energy": [0.3, 0.6], "tempo": [70, 110], "valence": 0.55},
    "work": {"energy": [0.2, 0.45], "tempo": [65, 100], "valence": 0.45},
    "study": {"energy": [0.15, 0.4], "tempo": [60, 100], "valence": 0.4},
    "workout": {"energy": [0.75, 1.0], "tempo": [120, 150], "valence": 0.6},
    "sleep": {"energy": [0.0, 0.15], "tempo": [40, 80], "valence": 0.3},
    "cooking": {"energy": [0.4, 0.65], "tempo": [80, 120], "valence": 0.6},
    "drive": {"energy": [0.55, 0.85], "tempo": [90, 130], "valence": 0.55},
    "travel": {"energy": [0.4, 0.7], "tempo": [85, 120], "valence": 0.6},
    "party": {"energy": [0.7, 0.95], "tempo": [110, 140], "valence": 0.7},
}


def _parse_features(features_json: str) -> list[float]:
    try:
        feats = json.loads(features_json or "[]")
        return feats if isinstance(feats, list) else []
    except Exception:
        return []


def _feature_at(feats: list[float], idx: int, default: float = 0.5) -> float:
    return feats[idx] if len(feats) > idx else default


def _cosine_sim(a: list[float], b: list[float]) -> float:
    """11 维特征余弦相似度（空特征返回 0.5 中性值）。"""
    if not a or not b or len(a) != len(b):
        return 0.5
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(y * y for y in b)) or 1e-9
    return dot / (na * nb)


def _scene_fit(feats: list[float], scene: str) -> float:
    """特征 vs 场景目标拟合度 0-1。"""
    t = SCENE_TARGETS.get(scene)
    if not t or not feats:
        return 0.5
    energy = _feature_at(feats, 1)
    tempo = _feature_at(feats, 6, 100)
    valence = _feature_at(feats, 2)

    def in_range(v: float, r: list[float]) -> float:
        lo, hi = r
        if lo <= v <= hi:
            return 1.0
        return max(0.0, 1.0 - min(abs(v - lo), abs(v - hi)) / (hi - lo + 1e-6))

    e = in_range(energy, t["energy"])
    t_ = in_range(tempo, t["tempo"])
    v = max(0.0, 1.0 - abs(valence - t["valence"]))
    return e * 0.5 + t_ * 0.3 + v * 0.2


def recommend(db: Session, *, text: str = "", tags: Optional[list[str]] = None,
              scene: str = "", limit: int = 6) -> tuple[list[SongOut], dict[str, Any]]:
    """主推荐入口。返回 (歌曲列表带匹配度, 解析结果)。

    - text: 自然语言 / 种子歌曲名（mode=text|seed）
    - tags: 曲风/情绪标签
    - scene: 场景
    """
    tags = tags or []
    parsed: dict[str, Any] = {"genres": [], "moods": [], "scene": scene}
    query_text = (text or "").strip()

    # 1) 解析输入
    if query_text:
        parsed = llm.parse_nl(query_text)
        if not parsed.get("scene") and scene:
            parsed["scene"] = scene
    if tags:
        # 标签直接并入解析结果
        for t in tags:
            g = llm.GENRE_KEYWORDS.get(t.lower())
            m = llm.MOOD_KEYWORDS.get(t.lower())
            if g:
                parsed["genres"].append(g)
            elif m:
                parsed["moods"].append(m)
        parsed["genres"] = list(dict.fromkeys(parsed["genres"]))
        parsed["moods"] = list(dict.fromkeys(parsed["moods"]))

    # 2) 召回候选（全库；种子模式优先按歌名匹配）
    songs = db.query(Song).all()
    if query_text and "genres" not in (parsed or {}).get("_seed", {}):
        pass
    seed_song: Optional[Song] = None
    if query_text and not parsed.get("genres") and not parsed.get("moods") and not parsed.get("scene"):
        # 看起来是种子歌曲名 → 尝试匹配
        for s in songs:
            if query_text.lower() in s.title.lower() or query_text.lower() in s.artist.lower():
                seed_song = s
                break

    # 3) 打分排序
    scored: list[tuple[Song, float]] = []
    for s in songs:
        feats = _parse_features(s.features)
        score = _score_song(s, feats, parsed, seed_song, query_text)
        scored.append((s, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:limit]

    # 4) AI 理由（批量尽力而为，失败不阻塞）
    reasons: dict[int, str] = {}
    for s, _score in top:
        reasons[s.id] = llm.generate_reason(s.title, s.artist, parsed, parsed.get("scene") or "")

    # 5) 组装输出：匹配度 55-98
    out: list[SongOut] = []
    for i, (s, score) in enumerate(top):
        match = max(55, min(98, int(round(55 + score * 43 - i * 2))))
        o = SongOut.from_song(s, match=match)
        out.append(o)
    return out, parsed


def _score_song(song: Song, feats: list[float], parsed: dict[str, Any], seed_song: Optional[Song], query_text: str = "") -> float:
    """加权打分 0-1。

    权重（与产品定位一致）：
    - 内容契合 50%：genre + mood 交集 + 特征余弦 + 文本关键词
    - 场景契合 25%
    - 新鲜度 15%（固定 0.7 基值）
    - 流行度 10%
    """
    score = 0.0

    # 内容契合 50%：genre + mood + 特征 + 文本
    genre_hit = 0.0
    if parsed.get("genres"):
        genre_hit = 1.0 if (song.genre or "") in parsed["genres"] else 0.0
    mood_hit = 0.0
    try:
        moods = json.loads(song.mood_tags or "[]")
    except Exception:
        moods = []
    if parsed.get("moods"):
        inter = len(set(moods) & set(parsed["moods"]))
        total = max(1, len(set(parsed["moods"])))
        mood_hit = min(1.0, inter / total)
    feat_sim = 0.5
    if seed_song:
        seed_feats = _parse_features(seed_song.features)
        feat_sim = _cosine_sim(seed_feats, feats)
    # 文本关键词命中（标题/歌手包含查询词）
    text_hit = 0.0
    if query_text:
        q = query_text.lower()
        hay = f"{song.title} {song.artist}".lower()
        text_hit = 1.0 if q in hay else 0.0
    if parsed.get("genres") or parsed.get("moods") or seed_song:
        content = (
            genre_hit * 0.35
            + mood_hit * 0.25
            + feat_sim * 0.25
            + text_hit * 0.15
        )
    else:
        content = max(feat_sim, text_hit)
    score += content * 0.5

    # 场景契合 25%
    scene = parsed.get("scene") or ""
    score += _scene_fit(feats, scene) * 0.25

    # 新鲜度 15%（基础版：固定 0.7，后续接曝光日志）
    score += 0.7 * 0.15

    # 流行度 10%（用特征能量近似 + 中性基值）
    popularity = min(1.0, _feature_at(feats, 1) * 0.5 + 0.3)
    score += popularity * 0.1

    return score
