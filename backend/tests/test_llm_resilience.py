import pytest
from fastapi.testclient import TestClient

from app.llm.base import LLMUnavailableError
from app.routes import chat as chat_routes
from app.main import app


class AlwaysFailsLLM:
    provider_name = "broken"
    model_name = "broken-model"

    @property
    def primary(self):
        return self

    @property
    def active_provider(self):
        return self.provider_name

    @property
    def active_model(self):
        return self.model_name

    def is_available(self) -> bool:
        return False

    def generate(self, system, messages):
        raise LLMUnavailableError("simulated provider outage")


@pytest.fixture
def broken_client():
    chat_routes._llm_singleton = AlwaysFailsLLM()
    with TestClient(app) as c:
        yield c
    chat_routes._llm_singleton = None


def test_health_reports_llm_unavailable(broken_client):
    r = broken_client.get("/health")
    assert r.status_code == 200
    assert r.json()["llm_available"] is False


def test_message_send_degrades_gracefully_when_llm_down(broken_client):
    sid = broken_client.post("/sessions", json={"title": "t"}).json()["id"]
    r = broken_client.post(f"/sessions/{sid}/messages", json={"content": "How do I find PMF?"})
    # Should NOT be a 500 — the agent catches the provider error and returns
    # a clear, persisted message instead of crashing the request.
    assert r.status_code == 200
    assistant = r.json()["assistant_message"]
    assert "couldn't reach" in assistant["content"].lower()
    assert assistant["grounded"] is False
    # Retrieval still ran and citations were still computed even though
    # generation failed — nothing about retrieval depends on the LLM.
    assert len(assistant["citations"]) > 0
