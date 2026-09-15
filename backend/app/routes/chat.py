from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import select

from app.db import get_db
from app.config import get_settings, Settings
from app.models import ChatSession, ChatMessage
from app.schemas import (
    CreateSessionRequest, SessionOut, SendMessageRequest, SendMessageResponse, MessageOut,
    SelectProviderRequest,
)
from app.llm.base import LLMMessage
from app.llm.factory import RoutedLLMClient, build_client
from app.agent import handle_message
from app.skills.documents import is_conversion
from app.logging_config import get_logger
from app.rag_client import retriever_for
from fastapi.responses import StreamingResponse
from app.db import SessionLocal
import asyncio
import json
import threading
from datetime import datetime, timezone

router = APIRouter(prefix="/sessions", tags=["chat"])
config_router = APIRouter(prefix="/config", tags=["configuration"])
logger = get_logger(__name__)

_llm_singleton: RoutedLLMClient | None = None


@config_router.get("")
def model_config(settings: Settings = Depends(get_settings)):
    llm = get_llm(settings)
    providers = []
    for name in ('ollama', 'anthropic', 'openai'):
        client = build_client(name, settings)
        providers.append({'id': name, 'label': {'ollama': 'Ollama', 'anthropic': 'Anthropic Claude', 'openai': 'OpenAI'}[name],
                          'type': 'local' if name == 'ollama' else 'cloud', 'model': client.model_name,
                          'available': client.is_available()})
    return {'active_provider_id': llm.active_provider, 'providers': providers,
            'agent_framework': 'pi-coding-agent', 'fallback_provider': settings.LLM_FALLBACK_PROVIDER or None,
            'request_timeout_seconds': settings.LLM_TIMEOUT_SECONDS * 2 * (2 if settings.LLM_FALLBACK_PROVIDER else 1) + 105,
            'content_timeout_seconds': settings.CONTENT_TIMEOUT_SECONDS * 4 * (2 if settings.LLM_FALLBACK_PROVIDER else 1) + 15}


@config_router.post('/provider')
def select_provider(req: SelectProviderRequest, settings: Settings = Depends(get_settings)):
    global _llm_singleton
    if req.provider_id not in ('ollama', 'anthropic', 'openai'):
        raise HTTPException(400, detail='Unknown provider')
    if not build_client(req.provider_id, settings).is_available():
        raise HTTPException(409, detail='Provider unavailable. Configure its API key or install its Ollama model first.')
    _llm_singleton = RoutedLLMClient(settings.model_copy(update={'LLM_PROVIDER': req.provider_id}))
    return model_config(settings)


@router.get("", response_model=list[SessionOut])
def list_sessions(db: DBSession = Depends(get_db)):
    return db.scalars(select(ChatSession).order_by(ChatSession.updated_at.desc())).all()


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: str, db: DBSession = Depends(get_db)):
    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    db.delete(session)
    db.commit()
    return Response(status_code=204)


def get_llm(settings: Settings = Depends(get_settings)) -> RoutedLLMClient:
    global _llm_singleton
    if _llm_singleton is None:
        _llm_singleton = RoutedLLMClient(settings)
    return _llm_singleton


@router.post("", response_model=SessionOut, status_code=201)
def create_session(req: CreateSessionRequest, db: DBSession = Depends(get_db)):
    session = ChatSession(title=req.title or "New chat", user_metadata=req.user_metadata)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return session


@router.get("/{session_id}/messages", response_model=list[MessageOut])
def list_messages(session_id: str, db: DBSession = Depends(get_db)):
    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return session.messages


@router.post("/{session_id}/messages", response_model=SendMessageResponse)
def send_message(
    session_id: str,
    req: SendMessageRequest,
    db: DBSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    llm: RoutedLLMClient = Depends(get_llm),
):
    return process_message(session_id, req, db, settings, llm)


@router.post('/{session_id}/messages/stream')
def stream_message(session_id: str, req: SendMessageRequest,
                   db: DBSession = Depends(get_db), settings: Settings = Depends(get_settings),
                   llm: RoutedLLMClient = Depends(get_llm)):
    if db.get(ChatSession, session_id) is None:
        raise HTTPException(404, detail='session not found')
    if req.provider_id and req.provider_id not in ('ollama', 'anthropic', 'openai'):
        raise HTTPException(400, detail='Unknown provider')

    async def events():
        queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        closed = threading.Event()

        def emit(event):
            if closed.is_set():
                raise RuntimeError('Client disconnected')
            if event['type'] == 'delta' and not event['text']:
                return
            loop.call_soon_threadsafe(queue.put_nowait, event)

        def work():
            try:
                with SessionLocal() as worker_db:
                    result = process_message(session_id, req, worker_db, settings, llm, emit)
                    emit({'type': 'answer', 'text': result.assistant_message.content})
                    emit({'type': 'done', 'message_id': result.assistant_message.id})
            except Exception as exc:
                if not closed.is_set():
                    logger.error('stream processing failed', extra={'fields': {'session_id': session_id, 'type': type(exc).__name__}})
                    message = exc.detail if isinstance(exc, HTTPException) and isinstance(exc.detail, str) else 'Could not finish the answer. Please try again.'
                    loop.call_soon_threadsafe(queue.put_nowait, {'type': 'error', 'message': message})

        task = asyncio.create_task(asyncio.to_thread(work))
        try:
            yield json.dumps({'type': 'status', 'text': 'Finding transcript sources…'}) + '\n'
            while True:
                event = await queue.get()
                yield json.dumps(event) + '\n'
                if event['type'] in ('done', 'error'):
                    break
        finally:
            closed.set()
            task.cancel()

    return StreamingResponse(events(), media_type='application/x-ndjson', headers={'X-Accel-Buffering': 'no', 'Cache-Control': 'no-cache'})


def process_message(session_id, req, db, settings, llm, on_event=None):
    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    try:
        retriever_for(settings).collection.count()
    except Exception as exc:
        logger.error('knowledge index unavailable', extra={'fields': {'type': type(exc).__name__}})
        raise HTTPException(status_code=503, detail='The knowledge index is unavailable. Restart the backend after rebuilding the index, then retry.') from exc

    if req.provider_id:
        if req.provider_id not in ('ollama', 'anthropic', 'openai'):
            raise HTTPException(400, detail='Unknown provider')
        llm = RoutedLLMClient(settings.model_copy(update={'LLM_PROVIDER': req.provider_id}))
    user_msg = ChatMessage(session_id=session.id, role="user", content=req.content)
    db.add(user_msg)
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user_msg)

    history = [
        LLMMessage(role=m.role, content=m.content)
        for m in session.messages
        if m.role in ("user", "assistant") and m.id != user_msg.id
    ]
    document_source = None
    for index in range(len(session.messages)-1, -1, -1):
        message = session.messages[index]
        if message.role != 'assistant':
            continue
        previous_user = next((m for m in reversed(session.messages[:index]) if m.role == 'user'), None)
        if message.skill in ('html_artifact', 'markdown_artifact') and previous_user and is_conversion(previous_user.content, message.skill):
            continue  # Keep converting the original answer, not a shorter derivative.
        if message.grounded and message.citations:
            document_source = {'text': message.content, 'citations': message.citations}
            break
        break  # Do not reach past an unrelated refusal/general answer.

    try:
        result = handle_message(settings, llm, history, req.content, skill=req.skill, on_event=on_event,
                                document_source=document_source)
    except Exception as e:
        logger.error("agent processing failed", extra={"fields": {"session_id": session_id, "error": str(e)}})
        raise HTTPException(status_code=502, detail='Agent processing failed. Check model and retrieval health, then retry.') from e

    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=result.text,
        citations=result.citations,
        artifacts=result.artifacts,
        warnings=result.warnings,
        skill=result.skill,
        grounded=result.grounded,
        latency_ms=result.latency_ms,
    )
    db.add(assistant_msg)
    if not result.uses_saved_answer:
        session.llm_provider = getattr(llm, 'generated_provider', llm.active_provider)
        session.llm_model = getattr(llm, 'generated_model', llm.active_model)
    db.commit()
    db.refresh(assistant_msg)

    return SendMessageResponse(user_message=user_msg, assistant_message=assistant_msg)
