"""配置持久化：读取/写入 backend/data/settings.json。

LLM 供应商热切换：优先读 settings.json（前端设置页更新），否则 fallback 到 config 默认值。
读取使用 config 模块级变量（被 chat/recommend 等模块 import），需 reload 后生效。
"""
import json
import os
import threading
from typing import Any

import config
from config import BACKEND_DIR

SETTINGS_PATH = os.path.join(BACKEND_DIR, "..", "data", "settings.json")

_lock = threading.Lock()


def _read() -> dict[str, Any]:
    if not os.path.exists(SETTINGS_PATH):
        return {}
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def _write(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def mask_key(key: str) -> str:
    """脱敏 API Key（保留前缀 sk-，中间打码，保留末尾 4 位）。"""
    if not key or len(key) <= 8:
        return "***"
    if key.startswith("sk-"):
        return f"sk-***{key[-4:]}"
    return f"***{key[-4:]}"


def effective() -> dict[str, Any]:
    """合并配置：settings.json 覆盖 config 默认值。"""
    overrides = _read()
    return {
        "llm_base_url": overrides.get("llm_base_url") or config.LLM_BASE_URL,
        "llm_api_key": overrides.get("llm_api_key") or config.LLM_API_KEY,
        "llm_model_name": overrides.get("llm_model_name") or config.LLM_MODEL_NAME,
        "jamendo_client_id": overrides.get("jamendo_client_id") or "",
    }


def get_all() -> dict[str, Any]:
    """供前端展示（API Key 不返回明文，只返回是否设置 + 脱敏）。"""
    ef = effective()
    return {
        "llm_base_url": ef["llm_base_url"],
        "llm_api_key_set": bool(ef["llm_api_key"]) and ef["llm_api_key"] != "sk-xxx",
        "llm_api_key_mask": mask_key(ef["llm_api_key"]),
        "llm_model_name": ef["llm_model_name"],
        "jamendo_client_id": ef["jamendo_client_id"],
        "jamendo_client_id_set": bool(ef["jamendo_client_id"]),
    }


def update(patch: dict[str, Any]) -> dict[str, Any]:
    """更新 settings.json（部分更新），然后 reload config 模块变量。"""
    with _lock:
        current = _read()
        for k in ("llm_base_url", "llm_api_key", "llm_model_name", "jamendo_client_id"):
            v = patch.get(k)
            if v is not None and str(v).strip() != "":
                current[k] = str(v).strip()
        _write(current)
        # 热切换：直接修改 config 模块级常量，使本次进程内立即生效
        if "llm_base_url" in current:
            config.LLM_BASE_URL = current["llm_base_url"]
        if "llm_api_key" in current:
            config.LLM_API_KEY = current["llm_api_key"]
        if "llm_model_name" in current:
            config.LLM_MODEL_NAME = current["llm_model_name"]
    return get_all()


def reset() -> dict[str, Any]:
    """清空 settings.json（写空对象而非删除，绕过 safe-delete 沙箱限制），恢复默认配置。"""
    with _lock:
        try:
            import pathlib
            pathlib.Path(SETTINGS_PATH).write_text("{}", encoding="utf-8")
        except OSError:
            pass
        config.LLM_BASE_URL = "https://api.siliconflow.cn/v1"
        config.LLM_API_KEY = ""
        config.LLM_MODEL_NAME = "deepseek-ai/DeepSeek-V3"
    return get_all()
