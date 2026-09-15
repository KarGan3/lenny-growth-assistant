from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CreateSessionRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    user_metadata: dict = Field(default_factory=dict)


class SessionOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    llm_provider: str = ''
    llm_model: str = ''

    model_config = ConfigDict(from_attributes=True)


class CitationOut(BaseModel):
    guest: str
    title: str
    youtube_url: str
    deep_link: str
    start_timestamp: str
    publish_date: str
    similarity: float
    source_url: str = ''


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    citations: list[CitationOut] = Field(default_factory=list)
    artifacts: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    skill: str = ""
    grounded: bool = True
    latency_ms: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    # Optional explicit skill invocation, e.g. "ship_30_for_30". If omitted,
    # the agent routes based on message content.
    skill: Literal['grounded_qa', 'ship_30_for_30', 'markdown_artifact', 'html_artifact'] | None = None
    provider_id: str | None = None


class SelectProviderRequest(BaseModel):
    provider_id: str


class SendMessageResponse(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut


class HealthOut(BaseModel):
    status: str
    llm_provider: str
    llm_model: str
    llm_available: bool
    rag_index_count: int | None = None
    database_ok: bool
    evidence_available: bool = False


class ErrorOut(BaseModel):
    error: str
    detail: str | None = None
