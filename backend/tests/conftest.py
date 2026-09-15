import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Point at an isolated SQLite file before importing the app, so tests never
# touch the dev database.
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"
os.environ.setdefault("RAG_PERSIST_DIR", str(Path(__file__).resolve().parents[2] / "data/chroma"))
os.environ.setdefault("RAG_EMBEDDER", "local-lexical")
# Tests exercise the submitted strict mode independently of a developer's .env.
# Individual general-knowledge tests explicitly opt in through Settings.
os.environ["ALLOW_GENERAL_KNOWLEDGE"] = "false"

from app.main import app  # noqa: E402
from app import main as main_module
from app.routes import chat as chat_routes  # noqa: E402
from app.llm.base import LLMMessage  # noqa: E402


class StubLLMClient:
    """Deterministic fake standing in for a real provider so tests don't
    require Ollama, an Anthropic key, or network access."""

    provider_name = "stub"
    model_name = "stub-model"

    def __init__(self, reply: str = "This is a stubbed grounded answer citing [1]."):
        self._reply = reply
        self.last_system = None
        self.last_messages: list[LLMMessage] = []

    @property
    def active_provider(self):
        return self.provider_name

    @property
    def active_model(self):
        return self.model_name

    @property
    def primary(self):
        return self

    def is_available(self) -> bool:
        return True

    def generate(self, system: str, messages: list[LLMMessage]) -> str:
        self.last_system = system
        self.last_messages = messages
        return self._reply


@pytest.fixture
def stub_llm():
    stub = StubLLMClient()
    chat_routes._llm_singleton = stub
    yield stub
    chat_routes._llm_singleton = None


@pytest.fixture
def client(stub_llm, monkeypatch):
    monkeypatch.setattr(main_module, 'evidence_ready', lambda settings: True)
    with TestClient(app) as c:
        yield c
