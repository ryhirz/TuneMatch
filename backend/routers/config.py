"""应用配置路由：前端设置页读写 LLM 供应商配置。

- GET  /api/config：返回当前配置（API Key 脱敏）+ 预设供应商列表
- PUT  /api/config：更新（覆盖）配置，热切换立即生效
- POST /api/config/reset：清除 settings.json，恢复 config.py 默认值
"""
from fastapi import APIRouter

import config as cfg
from schemas import SettingsOut, SettingsUpdate, err, ok
from services import settings as settings_svc

router = APIRouter(prefix="/api/config", tags=["config"])


PROVIDERS = [
    {
        "key": "siliconflow",
        "name": "硅基流动 SiliconFlow",
        "base_url": "https://api.siliconflow.cn/v1",
        "models": ["deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-72B-Instruct", "THUDM/glm-4-9b-chat"],
    },
    {
        "key": "deepseek",
        "name": "DeepSeek 官方",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"],
    },
    {
        "key": "openai",
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    },
    {
        "key": "custom",
        "name": "自定义 OpenAI 兼容端点",
        "base_url": "",
        "models": [],
    },
]


def _to_out() -> dict:
    current = settings_svc.get_all()
    return SettingsOut(
        llm_base_url=current["llm_base_url"],
        llm_api_key_set=current["llm_api_key_set"],
        llm_api_key_mask=current["llm_api_key_mask"],
        llm_model_name=current["llm_model_name"],
        jamendo_client_id=current.get("jamendo_client_id", ""),
        jamendo_client_id_set=current.get("jamendo_client_id_set", False),
        providers=PROVIDERS,
    ).model_dump()


@router.get("")
def get_config() -> dict:
    """获取当前 LLM 配置（Key 脱敏）+ 可用供应商列表。"""
    return ok(_to_out())


@router.put("")
def update_config(body: SettingsUpdate) -> dict:
    """更新 LLM 配置（部分字段更新），热切换立即生效。"""
    patch = {
        "llm_base_url": (body.llm_base_url or "").strip(),
        "llm_api_key": (body.llm_api_key or "").strip(),
        "llm_model_name": (body.llm_model_name or "").strip(),
        "jamendo_client_id": (body.jamendo_client_id or "").strip(),
    }
    # 过滤空值（用户没填的字段不动）
    patch = {k: v for k, v in patch.items() if v}
    if not patch:
        return err(422, "没有任何字段需要更新")

    result = settings_svc.update(patch)
    return ok({
        **result,
        "providers": PROVIDERS,
    }, message="配置已保存并生效")


@router.post("/reset")
def reset_config() -> dict:
    """恢复 config.py 默认配置。"""
    result = settings_svc.reset()
    return ok({
        **result,
        "providers": PROVIDERS,
    }, message="已恢复默认配置")
