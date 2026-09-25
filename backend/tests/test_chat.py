"""AI 对话：SSE 流式响应格式校验（无 Key 走规则降级流）。"""
import json


def test_chat_stream_format(client):
    """SSE 流式：逐事件解析，delta 事件 + done 事件。"""
    with client.stream("POST", "/api/chat", json={"text": "推荐几首健身听的歌"}) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")

        body = b"".join(resp.iter_bytes()).decode("utf-8")
    assert "data:" in body

    events = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            events.append(json.loads(line[5:].strip()))

    types = [e["type"] for e in events]
    assert "delta" in types
    assert "done" in types  # 结束事件
    assert events[-1]["type"] == "done"
    # delta 内容非空
    assert any(e.get("content") for e in events if e["type"] == "delta")


def test_chat_history_saved(client):
    """对话后历史记录应包含 user 消息。"""
    client.post("/api/chat", json={"text": "来点学习时的轻音乐"})
    hist = client.get("/api/chat/history").json()["data"]
    assert hist
    roles = [m["role"] for m in hist]
    assert "user" in roles


def test_chat_empty_text_422(client):
    resp = client.post("/api/chat", json={"text": ""})
    assert resp.status_code == 422
