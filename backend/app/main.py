"""Dexter backend application entrypoint."""

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

app = FastAPI(
    title="Dexter API",
    description="Chatbot tutor API for students and professors.",
    version="0.1.0",
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
