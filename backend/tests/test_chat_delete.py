"""对话删除测试：单条删除 + 全部清空。"""
import json


def _create_message(client, role: str, content: str) -> int:
    """调用 chatStream 把 user/assistant 消息都落库。"""
    with client.stream("POST", "/api/chat", json={"text": content}) as resp:
        body = b"".join(resp.iter_bytes()).decode()
    assert "data:" in body
    msgs = client.get("/api/chat/history").json()["data"]
    assert msgs[-1]["content"] == content
    return msgs[-1]["id"]


def test_delete_single_message(client):
    """删除单条消息。"""
    mid = _create_message(client, "user", "删除测试")
    resp = client.delete(f"/api/chat/{mid}")
    assert resp.status_code == 200
    msgs = client.get("/api/chat/history").json()["data"]
    assert all(m["id"] != mid for m in msgs)


def test_delete_nonexistent_returns_404(client):
    resp = client.delete("/api/chat/99999")
    assert resp.status_code == 404


def test_clear_history(client):
    """清空全部历史。"""
    _create_message(client, "user", "清空测试")
    resp = client.delete("/api/chat")
    assert resp.status_code == 200
    msgs = client.get("/api/chat/history").json()["data"]
    assert msgs == []