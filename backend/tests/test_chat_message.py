from types import SimpleNamespace

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


def test_chat_message_requests_clarification_without_generating(monkeypatch):
    classification = ClassificationResult(
        domaine=None,
        sous_theme=None,
        referentiel=None,
        intention="explication",
        langue="fr",
        confiance=0.2,
        besoin_precision=True,
        question_sous_themes=["bilan"],
    )
    generate_called = False

    monkeypatch.setattr("app.services.classifier.classify", lambda question, history: classification)

    def fail_generation(*args, **kwargs):
        nonlocal generate_called
        generate_called = True
        raise AssertionError("generation must not run during clarification")

    monkeypatch.setattr("app.services.chat_service.generate_answer", fail_generation)
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.post("/chat/message", json={"question": "explique le bilan"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["clarification_demandee"] is True
    assert body["reponse"] is None
    assert generate_called is False


def test_chat_message_generates_with_generation_model(monkeypatch):
    classification = ClassificationResult(
        domaine="comptabilite",
        sous_theme="bilan",
        referentiel="OHADA",
        intention="explication",
        langue="fr",
        confiance=0.95,
        besoin_precision=False,
        question_sous_themes=["bilan"],
    )
    calls = []

    monkeypatch.setattr("app.services.classifier.classify", lambda question, history: classification)

    def generate(question, classification, user, history_context=None):
        calls.append((question, classification, user, history_context))
        return "Voici une explication pédagogique."

    monkeypatch.setattr("app.services.chat_service.generate_answer", generate)
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.post("/chat/message", json={"question": "explique le bilan en OHADA"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["reponse"] == "Voici une explication pédagogique."
    assert body["mode"] == "explique_moi"
    assert body["domaine"] == "comptabilite"
    assert body["clarification_demandee"] is False
    assert len(calls) == 1


def test_chat_message_returns_502_when_generation_fails(monkeypatch):
    classification = ClassificationResult(
        domaine="comptabilite",
        sous_theme="bilan",
        referentiel="OHADA",
        intention="explication",
        langue="fr",
        confiance=0.95,
        besoin_precision=False,
        question_sous_themes=[],
    )

    monkeypatch.setattr("app.services.classifier.classify", lambda question, history: classification)
    monkeypatch.setattr(
        "app.services.chat_service.generate_answer",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("provider unavailable")),
    )
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.post("/chat/message", json={"question": "explique le bilan en OHADA"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json()["detail"] == "LLM generation failed."
