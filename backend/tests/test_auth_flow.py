import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_register_login_and_refresh_flow():
    email = f"user-{uuid.uuid4()}@example.com"
    payload = {
        "email": email,
        "password": "securepass123",
        "role": "etudiant",
        "filiere": "Informatique",
        "annee": "2025",
    }

    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == 201, register_response.text
    assert register_response.json()["email"] == email

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": "securepass123"},
    )
    assert login_response.status_code == 200, login_response.text
    tokens = login_response.json()
    assert "access_token" in tokens and "refresh_token" in tokens

    me_response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_response.status_code == 200, me_response.text
    assert me_response.json()["email"] == email

    update_response = client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"langue_preferee": "fr"},
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["langue_preferee"] == "fr"

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_response.status_code == 200, refresh_response.text
    refreshed = refresh_response.json()
    assert "access_token" in refreshed and "refresh_token" in refreshed
