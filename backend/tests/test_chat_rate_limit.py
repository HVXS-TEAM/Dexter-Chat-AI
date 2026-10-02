from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.main import app
from app.routers.chat import limiter

client = TestClient(app)


def _current_user():
    return SimpleNamespace(id=1, role="etudiant", langue_preferee="fr")


def _database():
    yield SimpleNamespace()


def test_api_chat_limits_requests_by_client_ip(monkeypatch):
    async def fake_stream(*args, **kwargs):
        yield 'data: {"type":"done"}\n\n'

    monkeypatch.setattr("app.routers.chat._stream_chat_events", fake_stream)
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_db] = _database
    limiter.reset()
    try:
        responses = [
            client.post(
                "/api/chat" if index % 2 == 0 else "/chat/stream",
                json={"question": "Explique le bilan"},
            )
            for index in range(21)
        ]
    finally:
        limiter.reset()
        app.dependency_overrides.clear()

    assert all(response.status_code == 200 for response in responses[:20])
    assert responses[20].status_code == 429
    assert "20 per 1 minute" in responses[20].text
