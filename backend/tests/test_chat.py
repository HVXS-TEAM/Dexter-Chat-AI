"""Tests for the synchronous chat endpoint /chat/message (full routing flow).

The real classifier is an LLM: the same TVA question was observed returning
``domaine="comptabilite"`` in one run and ``domaine=None`` (clarification) in
another. Like test_chat_stream.py and test_chat_calcul.py, these tests patch
the classifier and the answer generation so they stay deterministic, while
the routing logic, the deterministic calcul branch and dexter-calc run for
real. Contract under test (ChatMessageResponse): ``reponse``, ``mode``,
``domaine``, ``calcul_result`` — not the legacy ``domain``/``question`` keys.
"""
import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.chat import ClassificationResult

client = TestClient(app)

# Password must be >= 8 chars (UserCreate/UserLogin schema validation).
PASSWORD = "ChatPass123!"


def _get_token():
    """Register a fresh user and return its access token."""
    email = f"chat-{uuid.uuid4()}@example.com"
    payload = {"email": email, "password": PASSWORD}
    register = client.post("/auth/register", json=payload)
    assert register.status_code == 201, register.text
    resp = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _classification(**overrides):
    base = dict(
        domaine="comptabilite",
        sous_theme="tva",
        referentiel="OHADA",
        intention="calcul",
        langue="fr",
        confiance=0.95,
        besoin_precision=False,
        question_sous_themes=[],
    )
    base.update(overrides)
    return ClassificationResult(**base)


def _post(question, token, classification, generate, monkeypatch):
    monkeypatch.setattr(
        "app.services.classifier.classify",
        lambda q, history: classification,
    )
    monkeypatch.setattr("app.services.chat_service.generate_answer", generate)
    return client.post(
        "/chat/message",
        json={"question": question},
        headers={"Authorization": f"Bearer {token}"},
    )


def test_chat_tva_question(monkeypatch):
    token = _get_token()
    response = _post(
        "Calcule la TVA pour 1000€ à 20%",
        token,
        _classification(),
        lambda *args, **kwargs: "La TVA collectée est de 200 EUR.",
        monkeypatch,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    # Deterministic branch: dexter-calc really computed 1000 x 20%.
    assert body["mode"] == "calcul"
    assert body["domaine"] == "comptabilite"
    assert body["clarification_demandee"] is False
    assert body["reponse"] == "La TVA collectée est de 200 EUR."
    assert body["calcul_result"]["result"] == 200.0
    assert body["champs_manquants"] == []


def test_chat_credit_question(monkeypatch):
    token = _get_token()
    response = _post(
        "Calcul des interets pour un credit de 12000€ à 5% sur 24 mois",
        token,
        _classification(domaine="banque", sous_theme="credit", referentiel="Bâle III"),
        lambda *args, **kwargs: "L'intérêt simple est de 1200 EUR.",
        monkeypatch,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["mode"] == "calcul"
    assert body["domaine"] == "banque"
    assert body["clarification_demandee"] is False
    # dexter-calc really computed 12000 + (12000 x 5% x 24/12).
    assert body["calcul_result"]["result"] == 13200.0
    assert body["calcul_result"]["extra"]["interet_simple"] == 1200.0


def test_chat_general_question(monkeypatch):
    token = _get_token()
    response = _post(
        "Explique-moi le bilan comptable",
        token,
        _classification(sous_theme="bilan", intention="explication"),
        lambda *args, **kwargs: "Le bilan est le tableau de la situation patrimoniale.",
        monkeypatch,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["mode"] == "explique_moi"
    assert body["reponse"] == "Le bilan est le tableau de la situation patrimoniale."
    assert body["calcul_result"] is None


def test_chat_unauthorized():
    payload = {"question": "Calcule TVA 1000€"}
    resp = client.post("/chat/message", json=payload)
    assert resp.status_code in (401, 403)
