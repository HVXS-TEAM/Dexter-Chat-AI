"""Tests for chat route with calculation integration."""
import os
import uuid
from fastapi.testclient import TestClient

os.environ["DB_URL"] = "sqlite:///./test_chat.db"

from app.main import app
from app.models.user import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)

client = TestClient(app)


def _get_token():
    email = f"chat-{uuid.uuid4()}@example.com"
    payload = {"email": email, "password": "pass123"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/login", json={"email": email, "password": "pass123"})
    return resp.json()["access_token"]


def test_chat_tva_question():
    token = _get_token()
    payload = {"question": "Calcule la TVA pour 1000€ à 20%"}
    resp = client.post("/chat/message", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "calcul"
    assert data["domain"] == "comptabilite"
    assert data["calcul_result"]["result"] == 200.0


def test_chat_credit_question():
    token = _get_token()
    payload = {"question": "Calcul des interets pour un credit de 12000€ à 5% sur 24 mois"}
    resp = client.post("/chat/message", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "calcul"
    assert data["domain"] == "banque"


def test_chat_general_question():
    token = _get_token()
    payload = {"question": "Explique-moi le bilan comptable"}
    resp = client.post("/chat/message", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["question"] == "Explique-moi le bilan comptable"


def test_chat_unauthorized():
    payload = {"question": "Calcule TVA 1000€"}
    resp = client.post("/chat/message", json=payload)
    assert resp.status_code in (401, 403)
