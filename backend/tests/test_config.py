"""配置路由测试：GET/PUT/reset + Key 脱敏。"""
import json


def test_get_config_default(client):
    """默认 GET：返回默认 Base URL + Key 脱敏 + 4 个预设供应商。"""
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["llm_base_url"].startswith("http")
    assert data["llm_api_key_set"] is False
    assert data["llm_api_key_mask"] == "***"
    assert len(data["providers"]) >= 3
    keys = [p["key"] for p in data["providers"]]
    assert "siliconflow" in keys and "deepseek" in keys


def test_update_partial(client):
    """PUT 部分更新：只改 model_name，其他不变。"""
    resp = client.put("/api/config", json={"llm_model_name": "deepseek-chat"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["llm_model_name"] == "deepseek-chat"
    # 之前未设 Key，所以 set=False
    assert data["llm_api_key_set"] is False


def test_update_with_key_mask(client):
    """PUT 设置 Key：返回的 mask 保留前 3 后 4，中间打码。"""
    client.put("/api/config", json={
        "llm_api_key": "sk-abcdefghijklmnop1234",
        "llm_model_name": "deepseek-ai/DeepSeek-V3",
    })
    resp = client.get("/api/config")
    data = resp.json()["data"]
    assert data["llm_api_key_set"] is True
    assert data["llm_api_key_mask"].startswith("sk-")
    assert "***" in data["llm_api_key_mask"]
    assert data["llm_api_key_mask"].endswith("1234")
    # 不应返回明文
    assert "abcdefghij" not in json.dumps(data)


def test_reset_clears_overrides(client):
    """POST reset：清空设置，恢复默认值。"""
    client.put("/api/config", json={"llm_model_name": "gpt-4o"})
    resp = client.post("/api/config/reset")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["llm_model_name"] != "gpt-4o"  # 应恢复默认
