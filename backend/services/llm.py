"""LLM 服务层：OpenAI SDK 兼容，供应商可热切换。

- 默认硅基流动（SiliconFlow），也支持 DeepSeek / OpenAI / 任意兼容端点
- 无 Key 时降级为规则解析（关键词 → 曲风/情绪/场景），保证全链路可跑
"""
import json
import re
from typing import Any, Optional

import config

# ---------- 中文标签词表（规则降级用） ----------
GENRE_KEYWORDS: dict[str, str] = {
    "民谣": "folk", "folk": "folk",
    "摇滚": "rock", "rock": "rock",
    "电子": "edm", "电子舞曲": "edm", "edm": "edm",
    "嘻哈": "hip-hop", "说唱": "hip-hop", "hip-hop": "hip-hop", "rap": "hip-hop",
    "流行": "pop", "pop": "pop",
    "古典": "classical",
    "爵士": "jazz",
    "轻音乐": "lofi", "lofi": "lofi", "lo-fi": "lofi",
    "氛围": "ambient", "ambient": "ambient",
}

MOOD_KEYWORDS: dict[str, str] = {
    "开心": "开心", "欢快": "欢快", "治愈": "治愈", "放松": "放松",
    "平静": "平静", "悲伤": "悲伤", "伤感": "悲伤", "孤独": "孤独",
    "浪漫": "浪漫", "梦幻": "梦幻", "怀旧": "怀旧", "热血": "热血", "激昂": "激昂",
    "丧": "悲伤", "emo": "悲伤", "chill": "放松", "calm": "平静",
    "happy": "开心", "sad": "悲伤", "romantic": "浪漫", "energetic": "激昂",
}

SCENE_KEYWORDS: dict[str, str] = {
    "通勤": "commute", "上班": "work", "工作": "work", "学习": "study",
    "看书": "study", "健身": "workout", "运动": "workout", "跑步": "workout",
    "助眠": "sleep", "睡觉": "sleep", "睡前": "sleep", "做饭": "cooking",
    "开车": "drive", "驾驶": "drive", "旅行": "travel", "路上": "commute",
    "聚会": "party", "派对": "party",
}

# 场景 → 中文名（用于推荐理由模板）
SCENE_NAMES: dict[str, str] = {
    "commute": "通勤", "work": "工作", "study": "学习", "workout": "健身",
    "sleep": "助眠", "cooking": "做饭", "drive": "开车", "travel": "旅行", "party": "聚会",
}


def _rule_parse(text: str) -> dict[str, Any]:
    """无 Key 时的关键词规则解析（确定性、可测试）。"""
    genres, moods, scenes = set(), set(), set()
    lowered = text.lower()
    for kw, g in GENRE_KEYWORDS.items():
        if kw in lowered:
            genres.add(g)
    for kw, m in MOOD_KEYWORDS.items():
        if kw in lowered:
            moods.add(m)
    for kw, s in SCENE_KEYWORDS.items():
        if kw in lowered:
            scenes.add(s)
    return {
        "genres": sorted(genres),
        "moods": sorted(moods),
        "scene": sorted(scenes)[0] if scenes else "",
    }


def parse_nl(text: str) -> dict[str, Any]:
    """自然语言 → 结构化需求（曲风/情绪/场景）。

    有 Key：LLM 输出 JSON；无 Key：规则解析。
    """
    if not config.has_llm_key():
        return _rule_parse(text)

    try:
        from openai import OpenAI

        client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)
        resp = client.chat.completions.create(
            model=config.LLM_MODEL_NAME,
            temperature=0.1,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是音乐推荐需求解析器。把用户需求解析为 JSON，只输出 JSON 不输出其他。"
                        '格式：{"genres":["pop","rock"],"moods":["开心"],"scene":"study"}。'
                        "genre 取值：pop/rock/folk/edm/hip-hop/classical/jazz/lofi/ambient；"
                        "mood 取值：开心/欢快/治愈/放松/平静/悲伤/孤独/浪漫/梦幻/怀旧/热血/激昂；"
                        "scene 取值：commute/work/study/workout/sleep/cooking/drive/travel/party；没有则空数组/空串。"
                    ),
                },
                {"role": "user", "content": text},
            ],
            timeout=15,
        )
        content = resp.choices[0].message.content or ""
        # 提取第一个 JSON 对象
        m = re.search(r"\{.*\}", content, re.S)
        if m:
            data = json.loads(m.group(0))
            return {
                "genres": data.get("genres") or [],
                "moods": data.get("moods") or [],
                "scene": data.get("scene") or "",
            }
    except Exception:
        pass  # 网络/解析失败 → 降级规则
    return _rule_parse(text)


def generate_reason(song_title: str, artist: str, parsed: dict[str, Any], scene: str = "") -> str:
    """生成单曲推荐理由。

    有 Key：LLM 生成；无 Key：特征模板理由。
    """
    if not config.has_llm_key():
        return _template_reason(song_title, artist, parsed, scene)

    try:
        from openai import OpenAI

        client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)
        resp = client.chat.completions.create(
            model=config.LLM_MODEL_NAME,
            temperature=0.7,
            max_tokens=120,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是 TuneMatch 音乐推荐官。用 30-50 字、真诚不套话地解释为什么把这首歌推荐给用户。"
                        "必须提及歌曲与用户需求（曲风/情绪/场景）的契合点，中文输出，不要使用'首先其次'等连接词。"
                    ),
                },
                {
                    "role": "user",
                    "content": f"歌曲：《{song_title}》- {artist}；用户需求：{json.dumps(parsed, ensure_ascii=False)}",
                },
            ],
            timeout=15,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return _template_reason(song_title, artist, parsed, scene)


def _template_reason(song_title: str, artist: str, parsed: dict[str, Any], scene: str = "") -> str:
    """无 Key 时的模板理由。"""
    parts: list[str] = []
    if parsed.get("genres"):
        parts.append(f"来自你偏好的 {parsed['genres'][0]} 曲风")
    if parsed.get("moods"):
        parts.append(f"{parsed['moods'][0]}的情绪氛围刚刚好")
    if scene and scene in SCENE_NAMES:
        parts.append(f"适合{SCENE_NAMES[scene]}场景")
    if not parts:
        parts.append("旋律与你的口味高度契合")
    return f"《{song_title}》— {artist}，{('、'.join(parts))}，值得一听。"


def chat_reply(text: str) -> str:
    """AI 助手对话（非流式主回复，供测试/降级）。流式走 routers/chat.py。"""
    if not config.has_llm_key():
        return (
            f"我听到啦：『{text}』。当前未配置 LLM Key，我按关键词规则帮你解析了需求。"
            "可以试试说『来点适合学习的民谣』或『健身时听的摇滚』。"
        )
    try:
        from openai import OpenAI

        client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)
        resp = client.chat.completions.create(
            model=config.LLM_MODEL_NAME,
            temperature=0.6,
            max_tokens=300,
            messages=[
                {
                    "role": "system",
                    "content": "你是 TuneMatch 的 AI 音乐助手，帮用户找歌、推荐歌单、聊音乐品味。回复简洁友好，可给出歌曲名建议。",
                },
                {"role": "user", "content": text},
            ],
            timeout=15,
        )
        return resp.choices[0].message.content or "抱歉，我没想好怎么回答。"
    except Exception:
        return "（LLM 服务暂不可用，已按规则回复）" + f" 关于『{text}』，建议尝试：适合学习的轻音乐，或健身时的电子摇滚。"
