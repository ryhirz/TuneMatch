"""检索测试：歌曲列表筛选（genre / keyword / 详情）+ 向量召回正确性。"""


def test_list_songs_all(client):
    resp = client.get("/api/songs")
    assert resp.status_code == 200
    songs = resp.json()["data"]
    assert len(songs) >= 6  # 种子曲库


def test_filter_by_genre(client):
    resp = client.get("/api/songs", params={"genre": "rock"})
    songs = resp.json()["data"]
    assert songs and all(s["genre"] == "rock" for s in songs)


def test_filter_by_keyword(client):
    resp = client.get("/api/songs", params={"keyword": "晴天"})
    songs = resp.json()["data"]
    assert songs and any("晴天" in s["title"] for s in songs)


def test_filter_by_mood(client):
    resp = client.get("/api/songs", params={"mood": "热血"})
    songs = resp.json()["data"]
    assert songs and all("热血" in s["mood_tags"] for s in songs)


def test_song_detail(client):
    songs = client.get("/api/songs").json()["data"]
    sid = songs[0]["id"]
    resp = client.get(f"/api/songs/{sid}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == sid


def test_song_detail_404(client):
    resp = client.get("/api/songs/99999")
    assert resp.status_code == 404


def test_genre_meta(client):
    resp = client.get("/api/songs/meta/genres")
    genres = resp.json()["data"]
    assert "rock" in genres and "pop" in genres


def test_vector_recall(client):
    """相似歌曲召回：同曲风的歌相似度应高于跨曲风（用推荐引擎的余弦近似验证）。

    说明：无 chromadb 时走服务层 cosine 逻辑；此用例验证推荐结果按契合度排序。
    """
    resp = client.post("/api/recommend", json={
        "mode": "tags", "tags": ["摇滚"], "limit": 6,
    })
    songs = resp.json()["data"]["songs"]
    # 摇滚标签 → rock 曲风应排前
    assert songs and songs[0]["genre"] == "rock"
    # 匹配度降序
    matches = [s["match"] for s in songs]
    assert matches == sorted(matches, reverse=True)
