from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.calculators import router as calculators_router
from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router

app = FastAPI(
    title=settings.app_name,
    description="Educational chatbot with domain-specific calculators",
    version="0.1.0",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calculators_router, prefix="/calculators", tags=["calculators"])
app.include_router(auth_router, tags=["auth"])
app.include_router(chat_router, tags=["chat"])


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "app": settings.app_name}


@app.get("/", tags=["root"])
def root():
    return {
        "app": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
        "calculators": "/calculators",
        "auth": "/auth",
        "chat": "/chat",
    }

