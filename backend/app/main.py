"""Dexter backend application entrypoint."""

import logging
import threading
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.routers.auth import router as auth_router
from app.routers.calculators import router as calculators_router
from app.routers.chat import api_router as api_chat_router
from app.routers.chat import router as chat_router
from app.routers.classes import router as classes_router
from app.routers.conversations import router as conversations_router
from app.routers.domains import router as domains_router
from app.routers.documents import router as documents_router
from app.routers.messages import router as messages_router
from app.routers.quiz import router as quiz_router
from app.routers.users import router as users_router
from app.rate_limiter import limiter
from app.services.embedding_service import embed_text, get_embedding_model

# The project configures no logging: application loggers propagate to the root
# logger, whose effective level is WARNING, so `logging.getLogger(__name__).info`
# would never be emitted. Uvicorn is the only logger already configured at INFO
# level, therefore the preload trace is routed through it.
_logger = logging.getLogger("uvicorn.error")


def _preload_embedding_model() -> None:
    """Load and warm the embedding model outside of any request thread.

    The first load imports torch and sentence-transformers, and the first
    inference initializes kernels and tokenizers. Both monopolise the GIL
    long enough to delay every other request (a login was measured above 60 s
    while a load was in flight). A failure here is never fatal: the model
    stays uncached, so the next real use retries through the lazy paths, and
    the trace keeps the reason visible.
    """
    started = time.perf_counter()
    try:
        get_embedding_model()
        # Warm the inference path too: a merely loaded model still spends ~5 s
        # on its first encode. The text is a dummy warm-up, never stored.
        embed_text("Dexter embedding warm-up.")
    except Exception:  # noqa: BLE001 - the server must stay up; the cause is logged
        _logger.exception(
            "Embedding model preload failed; the load will be retried on first real use."
        )
        return
    _logger.info("Embedding model preloaded in %.1f s.", time.perf_counter() - started)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Start serving immediately and warm the embedding model in the background."""
    thread = threading.Thread(
        target=_preload_embedding_model,
        name="embedding-preload",
        daemon=True,
    )
    thread.start()
    _logger.info("Embedding model preload running in background thread.")
    yield


app = FastAPI(
    title="Dexter API",
    description="Chatbot tutor API for students and professors.",
    version="0.1.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:4173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(calculators_router)
app.include_router(domains_router)
app.include_router(chat_router)
app.include_router(api_chat_router)
app.include_router(classes_router)
app.include_router(conversations_router)
app.include_router(messages_router)
app.include_router(documents_router)
app.include_router(quiz_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Return the service health status."""
    return {"status": "ok"}
