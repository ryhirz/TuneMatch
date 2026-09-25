"""歌单 CRUD + 边界用例（空歌单 / 重复添加 / 404）。"""


def _create_playlist(client, name="我的最爱", scene="study"):
    resp = client.post("/api/playlists", json={"name": name, "scene": scene})
    assert resp.status_code == 200
    return resp.json()["data"]


def test_create_and_list(client):
    pl = _create_playlist(client)
    assert pl["name"] == "我的最爱"
    assert pl["scene"] == "study"
    assert pl["song_count"] == 0

    lst = client.get("/api/playlists").json()["data"]
    assert any(p["id"] == pl["id"] for p in lst)


def test_add_song_and_count(client):
    pl = _create_playlist(client, name="跑步歌单", scene="workout")
    songs = client.get("/api/songs").json()["data"]
    assert songs, "种子曲库不应为空"
    song = songs[0]

    resp = client.post(f"/api/playlists/{pl['id']}/songs", json={"song_id": song["id"]})
    assert resp.status_code == 200
    assert resp.json()["data"]["song_count"] == 1


def test_add_duplicate_song(client):
    """重复添加 → 422 边界。"""
    pl = _create_playlist(client, name="去重测试")
    songs = client.get("/api/songs").json()["data"]
    song_id = songs[0]["id"]

    client.post(f"/api/playlists/{pl['id']}/songs", json={"song_id": song_id})
    resp = client.post(f"/api/playlists/{pl['id']}/songs", json={"song_id": song_id})
    assert resp.status_code == 422
    assert resp.json()["message"]  # 明确错误信息


def test_update_playlist(client):
    pl = _create_playlist(client, name="旧名字")
    resp = client.put(f"/api/playlists/{pl['id']}", json={"name": "新名字", "description": "改描述"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "新名字"
    assert data["description"] == "改描述"


def test_delete_playlist(client):
    pl = _create_playlist(client, name="待删除")
    resp = client.delete(f"/api/playlists/{pl['id']}")
    assert resp.status_code == 200
    # 删除后再删除 → 404
    assert client.delete(f"/api/playlists/{pl['id']}").status_code == 404


def test_playlist_not_found(client):
    resp = client.put("/api/playlists/99999", json={"name": "x"})
    assert resp.status_code == 404
    resp = client.delete("/api/playlists/99999")
    assert resp.status_code == 404


def test_add_song_to_missing_playlist(client):
    resp = client.post("/api/playlists/99999/songs", json={"song_id": 1})
    assert resp.status_code == 404


def test_remove_song(client):
    pl = _create_playlist(client, name="移除测试")
    songs = client.get("/api/songs").json()["data"]
    sid = songs[0]["id"]
    client.post(f"/api/playlists/{pl['id']}/songs", json={"song_id": sid})
    resp = client.delete(f"/api/playlists/{pl['id']}/songs/{sid}")
    assert resp.status_code == 200
    assert resp.json()["data"]["song_count"] == 0
