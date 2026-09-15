import json


def test_stream_returns_sources_answer_and_persisted_history(client):
    sid = client.post('/sessions', json={'title': 'Streaming verification'}).json()['id']
    r = client.post(f'/sessions/{sid}/messages/stream', json={'content': 'How do I find product market fit?'})
    assert r.status_code == 200
    assert r.headers['content-type'].startswith('application/x-ndjson')
    events = [json.loads(line) for line in r.text.splitlines()]
    assert events[0]['type'] == 'status'
    source_event = next(e for e in events if e['type'] == 'sources')
    assert source_event['sources']
    assert next(i for i,e in enumerate(events) if e['type'] == 'sources') < next(i for i,e in enumerate(events) if e['type'] == 'delta')
    answer = next(e['text'] for e in events if e['type'] == 'answer')
    assert answer == 'This is a stubbed grounded answer citing [1].'
    assert events[-1]['type'] == 'done'
    messages = client.get(f'/sessions/{sid}/messages').json()
    assert len(messages) == 2
    assert messages[-1]['id'] == events[-1]['message_id']
    assert messages[-1]['content'] == answer


def test_invalid_stream_provider_does_not_save_question(client):
    sid = client.post('/sessions', json={}).json()['id']
    assert client.post(f'/sessions/{sid}/messages/stream', json={'content': 'Hello', 'provider_id': 'invalid'}).status_code == 400
    assert client.get(f'/sessions/{sid}/messages').json() == []


def test_unavailable_index_stream_explains_recovery_and_does_not_save_question(client, monkeypatch):
    from app.routes import chat
    sid = client.post('/sessions', json={}).json()['id']
    def unavailable(settings):
        raise RuntimeError('Old collection ID no longer exists')
    monkeypatch.setattr(chat, 'retriever_for', unavailable)
    response = client.post(f'/sessions/{sid}/messages/stream', json={'content': 'How should we grow?'})
    events = [json.loads(line) for line in response.text.splitlines()]
    assert events[-1]['type'] == 'error'
    assert 'Restart the backend' in events[-1]['message']
    assert client.get(f'/sessions/{sid}/messages').json() == []
