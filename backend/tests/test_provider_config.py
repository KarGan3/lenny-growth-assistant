from types import SimpleNamespace

from app.routes import chat
from app.config import Settings
from app.llm.base import LLMUnavailableError
from app.llm.factory import RoutedLLMClient


def test_provider_selection_and_validation(client, monkeypatch):
    monkeypatch.setattr(chat, 'build_client', lambda name, settings: SimpleNamespace(
        model_name=f'{name}-model', is_available=lambda: name != 'openai'))
    config = client.get('/config').json()
    assert config['agent_framework'] == 'pi-coding-agent'
    assert {p['id'] for p in config['providers']} == {'ollama', 'anthropic', 'openai'}
    selected = client.post('/config/provider', json={'provider_id': 'anthropic'})
    assert selected.status_code == 200
    assert selected.json()['active_provider_id'] == 'anthropic'
    assert client.get('/config').json()['active_provider_id'] == 'anthropic'
    assert client.post('/config/provider', json={'provider_id': 'openai'}).status_code == 409
    assert client.post('/config/provider', json={'provider_id': 'unknown'}).status_code == 400
    assert client.get('/config').json()['active_provider_id'] == 'anthropic'


def test_invalid_message_provider_does_not_save_question(client):
    sid = client.post('/sessions', json={'title': 'Provider validation'}).json()['id']
    r = client.post(f'/sessions/{sid}/messages', json={'content': 'Question', 'provider_id': 'invalid'})
    assert r.status_code == 400
    assert client.get(f'/sessions/{sid}/messages').json() == []


def test_fallback_records_actual_provider(monkeypatch):
    import app.llm.factory as factory
    def fail(*args):
        raise LLMUnavailableError('Primary unavailable')
    clients = {
        'ollama': SimpleNamespace(provider_name='ollama', model_name='local', generate=fail),
        'anthropic': SimpleNamespace(provider_name='anthropic', model_name='cloud', generate=lambda *a: 'Fallback answer'),
    }
    monkeypatch.setattr(factory, 'build_client', lambda name, settings: clients[name])
    routed = RoutedLLMClient(Settings(LLM_PROVIDER='ollama', LLM_FALLBACK_PROVIDER='anthropic'))
    assert routed.generate('System', []) == 'Fallback answer'
    assert routed.active_provider == 'ollama'
    assert routed.generated_provider == 'anthropic'
    assert routed.generated_model == 'cloud'
