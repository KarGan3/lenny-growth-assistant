from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text as sql_text
from sqlalchemy.exc import SQLAlchemyError
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from app.config import get_settings
from app.db import init_db, SessionLocal
from app.logging_config import configure_logging, get_logger
from app.routes.chat import router as chat_router, config_router, get_llm
from app.schemas import HealthOut, ErrorOut
from app.rag_client import retriever_for
from app.evidence_audit import evidence_ready

settings = get_settings()
configure_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting up", extra={"fields": {"llm_provider": settings.LLM_PROVIDER}})
    try:
        init_db()
    except SQLAlchemyError:
        logger.error('database startup failed')
    # Load the cached index before accepting requests, avoiding a first-chat delay.
    try:
        retriever_for(settings)
    except Exception as exc:
        logger.error("rag startup failed", extra={"fields": {"error": str(exc)}})
    if not evidence_ready(settings):
        logger.error('source verifier unavailable; run scripts/setup-evidence.py')
    yield
    logger.info("shutting down")


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(config_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled exception", extra={"fields": {"path": str(request.url), "error": str(exc)}})
    return JSONResponse(status_code=500, content=ErrorOut(error="internal_error", detail='An internal error occurred. Check the backend logs.').model_dump())


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error('database request failed', extra={'fields': {'path': request.url.path, 'type': type(exc).__name__}})
    return JSONResponse(status_code=503, content={'error': 'database_unavailable', 'detail': 'The database is unavailable. Check PostgreSQL and retry.'})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={'error': 'request_error', 'detail': exc.detail}, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={'error': 'validation_error', 'detail': 'Invalid request. Check the supplied fields.',
        'issues': [{'field': '.'.join(map(str, e['loc'])), 'message': e['msg']} for e in exc.errors()]})


@app.get("/health", response_model=HealthOut)
def health():
    llm = get_llm(settings)
    database_ok = True
    try:
        with SessionLocal() as db:
            db.execute(sql_text("SELECT 1"))
    except Exception as e:
        logger.error("database health check failed", extra={"fields": {"error": str(e)}})
        database_ok = False

    rag_count = None
    try:
        rag_count = retriever_for(settings).collection.count()
    except Exception as e:
        logger.error("rag health check failed", extra={"fields": {"error": str(e)}})

    available = llm.primary.is_available()
    verifier_available = evidence_ready(settings)
    return HealthOut(
        status="ok" if database_ok and available and rag_count and verifier_available else "degraded",
        llm_provider=llm.active_provider,
        llm_model=llm.active_model,
        llm_available=available,
        rag_index_count=rag_count,
        database_ok=database_ok,
        evidence_available=verifier_available,
    )
