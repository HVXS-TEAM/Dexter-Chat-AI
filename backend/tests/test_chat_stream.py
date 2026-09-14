import json
import os
from types import SimpleNamespace

os.environ["DB_URL"] = "sqlite:///./test_chat_stream.db"

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.main import app
from app.schemas.chat import ClassificationResult


client = TestClient(app)


def _override_user():
    return SimpleNamespace(
        id=1,
        email="student@example.com",
        role="etudiant",
        langue_preferee="fr",
    )


def _override_db():
    yield SimpleNamespace()


def _classification():
    return ClassificationResult(
        domaine="comptabilite",
        sous_theme="bilan",
        referentiel="OHADA",
        intention="explication",
        langue="fr",
        confiance=0.95,
        besoin_precision=False,
        question_sous_themes=["bilan"],
    )


def _events(response):
    return [json.loads(line.removeprefix("data: ").strip()) for line in response.text.splitlines() if line.startswith("data: ")]


def test_chat_stream_sends_tokens_and_done(monkeypatch):
    monkeypatch.setattr("app.services.classifier.classify", lambda question, history: _classification())

    async def generate_stream(*args, **kwargs):
        yield "Bonjour "
        yield "Dexter."

    monkeypatch.setattr("app.services.chat_service._generate_stream", generate_stream)
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.post("/chat/stream", json={"question": "Explique le bilan en OHADA"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"
    assert _events(response) == [
        {"type": "token", "content": "Bonjour "},
        {"type": "token", "content": "Dexter."},
        {"type": "done"},
    ]


def test_chat_stream_returns_error_for_empty_stream(monkeypatch):
    monkeypatch.setattr("app.services.classifier.classify", lambda question, history: _classification())

    async def generate_stream(*args, **kwargs):
        if False:
            yield ""

    monkeypatch.setattr("app.services.chat_service._generate_stream", generate_stream)
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.post("/chat/stream", json={"question": "Explique le bilan en OHADA"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert _events(response) == [{"type": "error", "message": "La génération de la réponse a échoué."}]


def test_chat_stream_returns_error_when_llm_fails(monkeypatch):
    monkeypatch.setattr("app.services.classifier.classify", lambda question, history: _classification())

    async def generate_stream(*args, **kwargs):
        raise RuntimeError("provider unavailable")
        yield "unreachable"

    monkeypatch.setattr("app.services.chat_service._generate_stream", generate_stream)
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.post("/chat/stream", json={"question": "Explique le bilan en OHADA"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert _events(response) == [{"type": "error", "message": "La génération de la réponse a échoué."}]
