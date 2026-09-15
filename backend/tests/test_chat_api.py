def test_health(client, stub_llm):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"


def test_health_reports_unavailable_source_verifier(client, monkeypatch):
    from app import main
    monkeypatch.setattr(main, 'evidence_ready', lambda settings: False)
    body = client.get('/health').json()
    assert body['status'] == 'degraded'
    assert body['evidence_available'] is False
    assert body["llm_provider"] == "stub"
    assert body["database_ok"] is True
    assert body["rag_index_count"] and body["rag_index_count"] > 0


def test_create_and_get_session(client):
    r = client.post("/sessions", json={"title": "my chat"})
    assert r.status_code == 201
    session = r.json()
    assert session["title"] == "my chat"
    assert session["id"]

    r2 = client.get(f"/sessions/{session['id']}")
    assert r2.status_code == 200
    assert r2.json()["id"] == session["id"]


def test_frontend_session_list_and_delete(client):
    session = client.post("/sessions", json={"title": "Frontend chat"}).json()
    sid = session["id"]
    client.post(f"/sessions/{sid}/messages", json={"content": "How do I find product market fit?"})
    rows = client.get("/sessions").json()
    assert any(row["id"] == sid for row in rows)
    assert client.delete(f"/sessions/{sid}").status_code == 204
    assert client.get(f"/sessions/{sid}").status_code == 404
    assert client.get(f"/sessions/{sid}/messages").status_code == 404
    assert all(row["id"] != sid for row in client.get("/sessions").json())
    assert client.delete(f"/sessions/{sid}").status_code == 404


def test_get_session_404():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        r = c.get("/sessions/not-a-real-id")
        assert r.status_code == 404


def test_send_message_is_grounded_with_citations(client, stub_llm):
    sid = client.post("/sessions", json={"title": "t"}).json()["id"]
    r = client.post(f"/sessions/{sid}/messages", json={"content": "How do I find product market fit?"})
    assert r.status_code == 200
    body = r.json()

    assert body["user_message"]["content"] == "How do I find product market fit?"
    assistant = body["assistant_message"]
    assert assistant["role"] == "assistant"
    assert assistant["content"] == "This is a stubbed grounded answer citing [1]."
    assert assistant["grounded"] is True
    assert len(assistant["citations"]) > 0
    first_citation = assistant["citations"][0]
    assert first_citation["youtube_url"].startswith("https://www.youtube.com/watch")
    assert "t=" in first_citation["deep_link"]


def test_session_history_passed_to_llm(client, stub_llm):
    sid = client.post("/sessions", json={"title": "t"}).json()["id"]
    client.post(f"/sessions/{sid}/messages", json={"content": "What is product market fit?"})
    client.post(f"/sessions/{sid}/messages", json={"content": "Can you expand on that?"})

    # The second call's history should include the first user/assistant turn.
    roles = [m.role for m in stub_llm.last_messages]
    assert "user" in roles
    assert "assistant" in roles


def test_message_history_persisted(client):
    sid = client.post("/sessions", json={"title": "t"}).json()["id"]
    client.post(f"/sessions/{sid}/messages", json={"content": "hello"})
    r = client.get(f"/sessions/{sid}/messages")
    assert r.status_code == 200
    msgs = r.json()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"


def test_send_message_to_missing_session_404(client):
    r = client.post("/sessions/does-not-exist/messages", json={"content": "hi"})
    assert r.status_code == 404


def test_send_message_rejects_empty_content(client):
    sid = client.post("/sessions", json={"title": "t"}).json()["id"]
    r = client.post(f"/sessions/{sid}/messages", json={"content": ""})
    assert r.status_code == 422  # pydantic min_length validation
