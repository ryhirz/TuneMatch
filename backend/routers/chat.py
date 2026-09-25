"""AI 对话路由：流式 SSE + 历史记录。

- POST /api/chat：SSE 流式响应（有 Key 走真实 LLM 流式；无 Key 走规则降级）
- GET /api/chat/history：历史对话列表
"""
import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

import config
from db import get_db
from models import ChatMessage, Playlist
from schemas import ChatRequest, err, ok
from services import llm as llm_svc

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _build_playlist_context(db: Session, playlist_id: int | None) -> str:
    """从歌单构建 AI 上下文（歌曲清单 + 统计），用于结合歌单推荐/整理。"""
    if not playlist_id:
        return ""
    pl = db.get(Playlist, playlist_id)
    if not pl or not pl.songs:
        return ""
    lines = [f"《{s.title}》- {s.artist}（{s.genre or '未知曲风'}）" for s in pl.songs[:30]]
    genres: dict[str, int] = {}
    for s in pl.songs:
        g = s.genre or "未知"
        genres[g] = genres.get(g, 0) + 1
    top_genres = "、".join(sorted(genres, key=genres.get, reverse=True)[:3]) or "未知"
    return (
        f"\n【当前歌单上下文】歌单名：{pl.name}（{len(pl.songs)} 首，主要曲风：{top_genres}）\n"
        f"歌单歌曲：{'；'.join(lines)}\n"
        "用户后续提问会围绕这个歌单，你可以基于歌单内容做推荐、整理或分类建议。"
    )


@router.post("")
async def chat(body: ChatRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    """AI 对话（SSE 流式）。

    事件格式：
      data: {"type": "delta", "content": "..."}   增量文本
      data: {"type": "reason", "content": "..."}  解析结果/推荐理由
      data: {"type": "done", "content": "..."}    完成（含完整回复）
    同时把 user 消息落库。支持 playlist_id 携带歌单上下文。
    """
    # 落库用户消息
    user_msg = ChatMessage(role="user", content=body.text, song_ids="[]")
    db.add(user_msg)
    db.commit()

    # 歌单上下文（结合歌单推荐/整理）
    ctx = _build_playlist_context(db, body.playlist_id)

    async def gen() -> AsyncGenerator[str, None]:
        if config.has_llm_key():
            async for chunk in _stream_llm(body.text, ctx, db):
                yield chunk
        else:
            async for chunk in _stream_rule(body.text, ctx, db):
                yield chunk
        # done 事件
        yield f'data: {json.dumps({"type": "done", "content": "OK"}, ensure_ascii=False)}\n\n'

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


async def _stream_llm(text: str, ctx: str = "", db: Session | None = None) -> AsyncGenerator[str, None]:
    """真实 LLM 流式（OpenAI SDK 兼容，默认硅基流动）。带 30s 超时保护，失败不卡死。"""
    from openai import OpenAI

    client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY, timeout=30.0, max_retries=1)
    system = (
        "你是 TuneMatch 的 AI 音乐助手，帮用户找歌、推荐歌单、整理歌单、聊音乐品味。"
        "回复简洁友好，中文输出，涉及歌曲时给出歌名与理由。"
    ) + ctx
    try:
        stream = client.chat.completions.create(
            model=config.LLM_MODEL_NAME,
            temperature=0.6,
            max_tokens=400,
            stream=True,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield f'data: {json.dumps({"type": "delta", "content": delta}, ensure_ascii=False)}\n\n'
    except Exception as e:
        # 失败时给出友好提示（不卡死流），并降级为库内推荐
        yield f'data: {json.dumps({"type": "delta", "content": "（AI 服务暂不可用，已为你生成库内推荐）"}, ensure_ascii=False)}\n\n'
        async for c in _stream_rule(text, ctx, db):
            yield c


async def _stream_rule(text: str, ctx: str = "", db: Session | None = None) -> AsyncGenerator[str, None]:
    """无 Key 规则降级：从曲库推荐歌曲（带歌曲卡片事件），分片输出模板回复（模拟流式）。"""
    from services import recommend as rec_svc

    parsed = llm_svc._rule_parse(text)
    scenes = ", ".join(parsed.get("scene") or []) if isinstance(parsed.get("scene"), list) else parsed.get("scene") or ""
    # 从曲库推荐（基于解析的曲风/情绪/场景，优先库内可听的歌）
    rec_songs, _ = rec_svc.recommend(
        db,
        text=text,
        tags=(parsed.get("genres") or []) + (parsed.get("moods") or []),
        scene=scenes,
        limit=5,
    )
    # 输出歌曲卡片事件（前端渲染可点击卡片）
    song_cards = [
        {
            "id": s.id, "title": s.title, "artist": s.artist,
            "cover_url": s.cover_url or "", "match": s.match,
            "genre": s.genre or "",
        }
        for s in rec_songs
    ]
    ctx_note = "已结合当前歌单上下文。" if ctx else ""
    reply = (
        f"{ctx_note}我理解你想找：{'、'.join(parsed.get('moods') or ['好听的歌'])} 风格的音乐"
        + (f"，适合{scenes}场景" if scenes else "")
        + "，为你推荐曲库中的以下歌曲：\n"
    )
    for i, s in enumerate(rec_songs, 1):
        reply += f"{i}. 《{s.title}》 - {s.artist}（匹配度 {s.match}%）\n"
    reply += "\n点击上方卡片即可试听；如需更精准推荐，可配置 LLM_API_KEY 获得 AI 自然语言推荐。"
    # 先发歌曲卡片事件
    if song_cards:
        yield f'data: {json.dumps({"type": "songs", "content": song_cards}, ensure_ascii=False)}\n\n'
    # 模拟流式：按 6-10 字切块
    for i in range(0, len(reply), 8):
        yield f'data: {json.dumps({"type": "delta", "content": reply[i:i + 8]}, ensure_ascii=False)}\n\n'
        await asyncio.sleep(0.02)


@router.get("/history")
def chat_history(db: Session = Depends(get_db)) -> dict:
    """历史对话列表（最新在前，每次最多 50 条）。"""
    msgs = db.query(ChatMessage).order_by(ChatMessage.created_at.desc()).limit(50).all()
    out = []
    for m in reversed(msgs):
        try:
            song_ids = json.loads(m.song_ids or "[]")
        except Exception:
            song_ids = []
        out.append({
            "id": m.id, "role": m.role, "content": m.content,
            "song_ids": song_ids,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })
    return ok(out)


@router.delete("/{message_id}")
def delete_message(message_id: int, db: Session = Depends(get_db)) -> dict:
    """删除单条对话消息。"""
    msg = db.get(ChatMessage, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail=err(404, "消息不存在"))
    db.delete(msg)
    db.commit()
    return ok(message="消息已删除")


@router.delete("")
def clear_history(db: Session = Depends(get_db)) -> dict:
    """清空全部历史对话。"""
    db.query(ChatMessage).delete()
    db.commit()
    return ok(message="历史已清空")
