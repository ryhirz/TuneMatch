"""/health 健康检查：200 + 依赖状态字段。"""


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "ok"
    # 依赖状态字段齐全
    data = body["data"]
    assert "llm" in data
    assert "chromadb" in data
    assert "audio" in data


def test_health_llm_degraded(client):
    """未配 Key 时 llm.configured 应为 False（测试环境）。"""
    resp = client.get("/health")
    data = resp.json()["data"]
    assert data["llm"]["configured"] is False


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "TuneMatch API"
