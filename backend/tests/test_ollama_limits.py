import httpx

from app.llm.base import LLMMessage
from app.llm.ollama_client import OllamaClient


def test_ollama_limits_generation_and_connection_wait(monkeypatch):
    captured = {}

    def respond(request):
        import json
        captured["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"message": {"content": "Grounded answer [1]"}})

    real_client = httpx.Client

    def client_factory(**kwargs):
        captured["timeout"] = kwargs["timeout"]
        return real_client(transport=httpx.MockTransport(respond), **kwargs)

    monkeypatch.setattr(httpx, "Client", client_factory)
    llm = OllamaClient("http://localhost:11434", "test-model", timeout=60, max_output_tokens=256)
    assert llm.generate("Use sources", [LLMMessage(role="user", content="Question")]) == "Grounded answer [1]"
    assert captured["timeout"].connect == 3
    assert captured["timeout"].read == 60
    assert captured["payload"]["options"]["num_predict"] == 256


def test_availability_requires_the_configured_model(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: httpx.Response(200, json={"models": [{"name": "other:latest"}]}))
    assert not OllamaClient("http://localhost:11434", "llama3.1:8b").is_available()
    monkeypatch.setattr(httpx, "get", lambda *a, **k: httpx.Response(200, json={"models": [{"name": "llama3.1:8b"}]}))
    assert OllamaClient("http://localhost:11434", "llama3.1:8b").is_available()
