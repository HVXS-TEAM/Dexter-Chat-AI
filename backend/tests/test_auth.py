"""Tests for auth routes."""
import os
import uuid
from fastapi.testclient import TestClient

os.environ["DB_URL"] = "sqlite:///./test_auth.db"

from app.main import app
from app.models.user import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)

client = TestClient(app)


def _register(email=None, password="SecurePass123!"):
    if email is None:
        email = f"test-{uuid.uuid4()}@example.com"
    payload = {
        "email": email,
        "password": password,
        "role": "etudiant",
        "filiere": "Informatique",
        "annee": "2025",
    }
    resp = client.post("/auth/register", json=payload)
    return resp


def test_register():
    resp = _register()
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_register_duplicate():
    email = f"dup-{uuid.uuid4()}@example.com"
    _register(email=email)
    resp = _register(email=email)
    assert resp.status_code == 400


def test_login():
    email = f"login-{uuid.uuid4()}@example.com"
    password = "MyPass123!"
    _register(email=email, password=password)
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password():
    email = f"wrong-{uuid.uuid4()}@example.com"
    _register(email=email, password="correct")
    resp = client.post("/auth/login", json={"email": email, "password": "wrong"})
    assert resp.status_code == 401


def test_get_profile():
    email = f"me-{uuid.uuid4()}@example.com"
    reg = _register(email=email)
    token = reg.json()["access_token"]
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == email
    assert "password_hash" not in data


def test_update_profile():
    email = f"patch-{uuid.uuid4()}@example.com"
    reg = _register(email=email)
    token = reg.json()["access_token"]
    payload = {"langue_preferee": "en", "filiere": "Finance"}
    resp = client.patch("/auth/me", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["langue_preferee"] == "en"


def test_unauthorized_access():
    resp = client.get("/auth/me")
    assert resp.status_code in (401, 403)
