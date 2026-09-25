"""TuneMatch FastAPI 入口。

- 统一响应格式 {code, message, data}
- CORS 允许 http://localhost:5173
- /health 健康检查（含依赖连通状态）
"""
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from contextlib import asynccontextmanager

import config as cfg
from db import init_db
from routers import catalog, chat, config, export, feedback, playlists, recommend, songs, upload
from schemas import err, ok
from services import audio as audio_svc
from services import chroma, llm


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化数据库。"""
    init_db()
    yield


app = FastAPI(
    title="TuneMatch API",
    description="AI 智能音乐推荐平台后端（多模态输入 → 个性化推荐）",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS：允许前端联调
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件：上传的头像 / 歌曲文件
# 注意：不能用 app.mount + StaticFiles（FastAPI 的 CORSMiddleware 不作用于 mounted sub-app），
# MediaElementSource + crossOrigin=anonymous 需要服务器返回 CORS 头才能解码音频，
# 所以用自定义路由 + FileResponse，主动加 CORS header。
@app.api_route("/uploads/{file_path:path}", methods=["GET", "HEAD"])
def serve_upload(file_path: str):
    """提供上传文件，并带上 CORS header（让 MediaElementSource 能解码）。

    支持 GET 和 HEAD（浏览器探测资源时常发 HEAD 请求）。
    """
    full = Path(cfg.UPLOAD_DIR) / file_path
    if not full.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    # 推断 Content-Type
    ext = full.suffix.lower()
    ctype = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(ext, "application/octet-stream")
    resp = FileResponse(full, media_type=ctype)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Range, Content-Type"
    resp.headers["Accept-Ranges"] = "bytes"
    return resp


@app.options("/uploads/{file_path:path}")
def options_upload(file_path: str):
    """预检请求：直接返回 CORS 头。"""
    resp = JSONResponse({})
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Range, Content-Type"
    return resp


@app.get("/health")
def health() -> dict:
    """健康检查：服务状态 + 各依赖连通状态。"""
    llm_ok = cfg.has_llm_key()
    chroma_stats = chroma.stats()
    return ok({
        "status": "ok",
        "llm": {"configured": llm_ok, "provider": cfg.LLM_BASE_URL, "model": cfg.LLM_MODEL_NAME},
        "chromadb": chroma_stats if chroma.is_available() else None,
        "audio": audio_svc.capabilities(),
    })


@app.get("/")
def root() -> dict:
    return ok({
        "name": "TuneMatch API",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0",
    })


# 注册路由
app.include_router(songs.router)
app.include_router(recommend.router)
app.include_router(playlists.router)
app.include_router(chat.router)
app.include_router(config.router)
app.include_router(upload.router)
app.include_router(export.router)
app.include_router(catalog.router)
app.include_router(feedback.router)


# 统一异常响应格式（保持 {code, message, data}）
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # detail 已是 {code,message,data} 结构则直接透传
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content=err(exc.status_code, str(exc.detail)))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content=err(422, f"参数校验失败: {exc.errors()}"))


# 统一 500 处理
@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content=err(500, f"服务异常: {exc}"))
