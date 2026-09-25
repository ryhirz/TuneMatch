"""应用配置：从环境变量 / .env 读取。

LLM 供应商可热切换（OpenAI SDK 兼容）：
- 硅基流动 SiliconFlow（默认）
- DeepSeek 官方
- OpenAI
- 任意 OpenAI 兼容端点
"""
import os

from dotenv import load_dotenv

load_dotenv()

# ---------- LLM（可切换供应商） ----------
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "deepseek-ai/DeepSeek-V3")

# ---------- 数据层 ----------
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tunematch.db")
CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")

# ---------- 音频能力（可选） ----------
ACOUSTID_API_KEY: str = os.getenv("ACOUSTID_API_KEY", "")

# ---------- 导出 ----------
EXPORT_DIR: str = os.getenv("EXPORT_DIR", "./exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

# ---------- 上传（歌单头像 / 歌曲文件） ----------
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
COVER_DIR: str = os.path.join(UPLOAD_DIR, "covers")
AUDIO_DIR: str = os.path.join(UPLOAD_DIR, "audio")
os.makedirs(COVER_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# 曲库 JSON 路径（相对 backend 目录，可由调用方覆盖）
MUSIC_LIBRARY_PATH: str = os.getenv("MUSIC_LIBRARY_PATH", "../data/music_library.json")

# 目录锚点：backend/ 的绝对路径（便于定位 data/）
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)


def has_llm_key() -> bool:
    """是否配置了 LLM Key（决定真实调用 vs 规则降级）。"""
    return bool(LLM_API_KEY and LLM_API_KEY != "sk-xxx")
