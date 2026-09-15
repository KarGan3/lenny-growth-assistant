"""
Central configuration. Every setting is overridable via environment
variable (see .env.example at the repo root). This is the "flexible LLM
configuration" layer: LLM_PROVIDER picks anthropic / openai / ollama
without touching application code, and the selected provider + model are
surfaced back to the frontend via GET /health so it's visible in the UI.
"""

from functools import lru_cache
from pathlib import Path
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / '.env', env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "Lenny Growth Assistant"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # --- Persistence ---
    # Production target is PostgreSQL (Supabase/Railway). SQLite is supported
    # as a zero-setup local-dev fallback — swap DATABASE_URL, no code changes.
    DATABASE_URL: str = "sqlite:///./data/app.db"

    # --- LLM provider toggle ---
    # "ollama" is mandatory for the submitted demo per the assignment brief.
    LLM_PROVIDER: str = "ollama"  # anthropic | openai | ollama

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_CONTEXT_LENGTH: int = 8192

    LLM_FALLBACK_PROVIDER: str = ""  # if primary provider errors/unavailable, try this one
    LLM_TIMEOUT_SECONDS: int = 180
    LLM_MAX_OUTPUT_TOKENS: int = 512
    LLM_TEMPERATURE: float = 0.2
    CONTENT_MAX_OUTPUT_TOKENS: int = 2400
    DOCUMENT_MAX_OUTPUT_TOKENS: int = 800
    CONTENT_TIMEOUT_SECONDS: int = 600
    RAG_MAX_CONTEXT_CHARS: int = 10000
    RAG_MAX_HISTORY_CHARS: int = 3000

    # --- RAG ---
    RAG_PERSIST_DIR: str = "./data/chroma"
    RAG_EMBEDDER: str = "local-lexical"  # onnx-minilm | ollama | local-lexical
    RAG_TOP_K: int = 5
    RAG_MIN_SIMILARITY: float = 0.15
    ALLOW_GENERAL_KNOWLEDGE: bool = False
    EVIDENCE_MODEL_DIR: str = '.local/evidence'
    EVIDENCE_MIN_ENTAILMENT: float = Field(default=0.6, ge=0, le=1)

    @field_validator('RAG_PERSIST_DIR', 'EVIDENCE_MODEL_DIR')
    @classmethod
    def resolve_index_path(cls, value: str) -> str:
        path = Path(value)
        return str(path if path.is_absolute() else (PROJECT_ROOT / path).resolve())

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
