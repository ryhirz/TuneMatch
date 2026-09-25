"""上传/导入测试：歌单头像、歌曲文件批量导入、非音频拒绝。"""
import io

IMAGE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200  # 伪造但扩展名合法的 png


def _create_playlist(client):
    r = client.post("/api/playlists", json={"name": "导入测试", "scene": "study"})
    return r.json()["data"]["id"]


def test_upload_cover_ok(client):
    pl_id = _create_playlist(client)
    resp = client.post(
        f"/api/playlists/{pl_id}/cover",
        files={"file": ("avatar.png", io.BytesIO(IMAGE_PNG), "image/png")},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["cover_url"].startswith("/uploads/covers/")


def test_upload_cover_reject_bad_ext(client):
    pl_id = _create_playlist(client)
    resp = client.post(
        f"/api/playlists/{pl_id}/cover",
        files={"file": ("hack.exe", io.BytesIO(b"MZ" + b"\x00" * 100), "application/octet-stream")},
    )
    assert resp.status_code == 422
    assert "不支持的图片格式" in resp.json()["message"]


def test_import_audio_ok(client):
    pl_id = _create_playlist(client)
    resp = client.post(
        f"/api/playlists/{pl_id}/songs/import",
        files=[
            ("files", ("夏日.mp3", io.BytesIO(b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\xff\xfb\x90\x00" + b"\x00" * 500), "audio/mpeg")),
            ("files", ("夜风.wav", io.BytesIO(_make_wav()), "audio/wav")),
        ],
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["imported_count"] == 2
    assert data["rejected_count"] == 0
    assert data["playlist"]["song_count"] == 2


def test_import_reject_non_audio(client):
    pl_id = _create_playlist(client)
    resp = client.post(
        f"/api/playlists/{pl_id}/songs/import",
        files=[
            ("files", ("歌.mp3", io.BytesIO(b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\xff\xfb\x90\x00" + b"\x00" * 100), "audio/mpeg")),
            ("files", ("文档.pdf", io.BytesIO(b"%PDF-1.4" + b"\x00" * 200), "application/pdf")),
        ],
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["imported_count"] == 1   # 合法 mp3 导入成功
    assert data["rejected_count"] == 1   # pdf 被拒绝
    assert "非音频文件" in data["rejected"][0]["reason"]


def test_import_no_files_422(client):
    pl_id = _create_playlist(client)
    resp = client.post(f"/api/playlists/{pl_id}/songs/import")
    assert resp.status_code == 422


def test_upload_cover_missing_playlist(client):
    resp = client.post(
        "/api/playlists/99999/cover",
        files={"file": ("a.png", io.BytesIO(IMAGE_PNG), "image/png")},
    )
    assert resp.status_code == 404


def test_chat_with_playlist_context(client):
    """对话携带歌单上下文：无 Key 时走规则降级但应返回 200 流式。"""
    pl_id = _create_playlist(client)
    # 先导入一首
    client.post(
        f"/api/playlists/{pl_id}/songs/import",
        files=[("files", ("夜曲.mp3", io.BytesIO(b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\xff\xfb\x90\x00" + b"\x00" * 100), "audio/mpeg"))],
    )
    with client.stream("POST", "/api/chat", json={"text": "帮我整理这个歌单", "playlist_id": pl_id}) as resp:
        assert resp.status_code == 200
        body = b"".join(resp.iter_bytes()).decode("utf-8")
    assert "data:" in body


# ---------- 音频嗅探 ----------
import math
import struct


def _make_wav(sr=8000, dur=0.5, freq=440) -> bytes:
    n = int(sr * dur)
    pcm = b"".join(
        struct.pack("<h", int(8000 * math.sin(2 * math.pi * freq * i / n)))
        for i in range(n)
    )
    return struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + n * 2, b"WAVE", b"fmt ", 16, 1, 1, sr, sr * 2, 2, 16,
        b"data", n * 2,
    ) + pcm


def test_audio_sniff_wav_valid(client):
    pl_id = _create_playlist(client)
    resp = client.post(
        f"/api/playlists/{pl_id}/songs/import",
        files=[("files", ("tone.wav", io.BytesIO(_make_wav()), "audio/wav"))],
    )
    data = resp.json()["data"]
    assert data["imported_count"] == 1
    assert data["rejected_count"] == 0


def test_audio_sniff_reject_fake_mp3(client):
    """带 ID3 头但无 MPEG 同步字节的「伪 mp3」必须被拒绝。"""
    pl_id = _create_playlist(client)
    fake = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"X" * 1024  # 仅有 ID3 头
    resp = client.post(
        f"/api/playlists/{pl_id}/songs/import",
        files=[("files", ("fake.mp3", io.BytesIO(fake), "audio/mpeg"))],
    )
    data = resp.json()["data"]
    assert data["imported_count"] == 0
    assert data["rejected_count"] == 1
    assert "不是合法音频" in data["rejected"][0]["reason"]


def test_audio_sniff_reject_empty(client):
    """空 mp3 文件必须被拒绝。"""
    pl_id = _create_playlist(client)
    resp = client.post(
        f"/api/playlists/{pl_id}/songs/import",
        files=[("files", ("empty.mp3", io.BytesIO(b"\x00" * 100), "audio/mpeg"))],
    )
    data = resp.json()["data"]
    assert data["imported_count"] == 0
    assert data["rejected_count"] == 1


def test_audio_sniff_accept_mp3_with_sync(client):
    """带 MPEG sync 字节的 mp3 应该被接受。"""
    pl_id = _create_playlist(client)
    payload = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\xff\xfb\x90\x00" + b"\x00" * 100
    resp = client.post(
        f"/api/playlists/{pl_id}/songs/import",
        files=[("files", ("real.mp3", io.BytesIO(payload), "audio/mpeg"))],
    )
    data = resp.json()["data"]
    assert data["imported_count"] == 1
