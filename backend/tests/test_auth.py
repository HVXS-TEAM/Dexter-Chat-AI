"""Tests for auth routes and the authenticated user profile.

Real API contract (app/routers/auth.py, app/routers/users.py):
- POST  /auth/register -> UserRead (201), no tokens
- POST  /auth/login    -> TokenPair (200) or 401; password must be >= 8 chars
- GET   /users/me      -> UserRead (Bearer access token required)
- PATCH /users/me      -> UserRead (Bearer access token required)

The test database is provided by tests/conftest.py (temporary SQLite).
"""
import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

DEFAULT_PASSWORD = "SecurePass123!"


def _email(prefix):
    return f"{prefix}-{uuid.uuid4()}@example.com"


def _register(email=None, password=DEFAULT_PASSWORD):
    if email is None:
        email = _email("test")
    payload = {
        "email": email,
        "password": password,
        "role": "etudiant",
        "filiere": "Informatique",
        "annee": "2025",
    }
    return client.post("/auth/register", json=payload)


def _auth_header(email, password=DEFAULT_PASSWORD):
    """Return an Authorization header for an existing user (register is
    token-free by design; only /auth/login issues tokens)."""
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_register_returns_user_without_tokens():
    email = _email("reg")
    resp = _register(email=email)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == email
    assert data["role"] == "etudiant"
    assert "id" in data and "created_at" in data
    # Registration must NOT leak credentials or tokens.
    assert "access_token" not in data
    assert "refresh_token" not in data
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate():
    email = _email("dup")
    _register(email=email)
    resp = _register(email=email)
    assert resp.status_code == 400


def test_login_returns_token_pair():
    email = _email("login")
    password = "MyPass123!"
    _register(email=email, password=password)
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


def test_login_wrong_password_returns_401():
    email = _email("wrong")
    _register(email=email, password="RightPass123!")
    # A different password of valid length (>= 8 chars) so the request
    # passes schema validation and the endpoint answers 401, not 422.
    resp = client.post("/auth/login", json={"email": email, "password": "WrongPass123!"})
    assert resp.status_code == 401


def test_get_profile():
    email = _email("me")
    _register(email=email)
    resp = client.get("/users/me", headers=_auth_header(email))
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == email
    assert "password_hash" not in data


def test_update_profile():
    email = _email("patch")
    _register(email=email)
    payload = {"langue_preferee": "en", "filiere": "Finance"}
    resp = client.patch("/users/me", json=payload, headers=_auth_header(email))
    assert resp.status_code == 200
    data = resp.json()
    assert data["langue_preferee"] == "en"
    assert data["filiere"] == "Finance"


def test_unauthorized_access():
    resp = client.get("/users/me")
    assert resp.status_code in (401, 403)
