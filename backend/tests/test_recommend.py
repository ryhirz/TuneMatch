"""推荐接口：输入 → 输出断言（无 Key，走规则引擎，零外部依赖）。"""


def test_recommend_text(client):
    """自然语言输入：应返回歌曲列表 + 解析结果。"""
    resp = client.post("/api/recommend", json={
        "mode": "text",
        "text": "想听适合学习的治愈民谣",
        "limit": 5,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert len(data["songs"]) <= 5
    assert data["parsed"]["genres"]  # 规则解析出曲风
    for s in data["songs"]:
        assert s["title"]
        assert s["artist"]
        assert 0 <= s["match"] <= 100


def test_recommend_tags(client):
    """标签输入：曲风 + 场景过滤。"""
    resp = client.post("/api/recommend", json={
        "mode": "tags",
        "tags": ["摇滚"],
        "scene": "workout",
        "limit": 3,
    })
    assert resp.status_code == 200
    songs = resp.json()["data"]["songs"]
    assert len(songs) <= 3
    # 规则解析：摇滚 → rock
    assert any(s["genre"] == "rock" for s in songs)


def test_recommend_seed(client):
    """种子歌曲：按歌名匹配 → 相似推荐。"""
    resp = client.post("/api/recommend", json={
        "mode": "seed",
        "text": "晴天",
        "limit": 4,
    })
    assert resp.status_code == 200
    songs = resp.json()["data"]["songs"]
    assert len(songs) > 0


def test_recommend_invalid_mode(client):
    """非法 mode → 422。"""
    resp = client.post("/api/recommend", json={"mode": "hack", "text": "x"})
    assert resp.status_code == 422


def test_recommend_audio_missing(client):
    """audio 模式缺 audio_base64 → 422。"""
    resp = client.post("/api/recommend", json={"mode": "audio"})
    assert resp.status_code == 422
