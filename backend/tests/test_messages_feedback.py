import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _auth_headers() -> dict[str, str]:
    email = f"feedback-{uuid.uuid4()}@example.com"
    register = client.post(
        "/auth/register",
        json={"email": email, "password": "securepass123", "role": "etudiant"},
    )
    assert register.status_code == 201, register.text
    login = client.post(
        "/auth/login",
        json={"email": email, "password": "securepass123"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _message(headers: dict[str, str]) -> int:
    conversation = client.post("/conversations", headers=headers, json={"titre": "Feedback"})
    assert conversation.status_code == 201, conversation.text
    conversation_id = conversation.json()["id"]
    message = client.post(
        f"/conversations/{conversation_id}/messages",
        headers=headers,
        json={"role": "assistant", "content": "Réponse test"},
    )
    assert message.status_code == 201, message.text
    return message.json()["id"]


def test_update_message_feedback_persists():
    headers = _auth_headers()
    message_id = _message(headers)

    response = client.patch(
        f"/messages/{message_id}/feedback",
        headers=headers,
        json={"feedback": "up"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["feedback"] == "up"


def test_update_message_feedback_requires_authentication():
    headers = _auth_headers()
    message_id = _message(headers)

    response = client.patch(
        f"/messages/{message_id}/feedback",
        json={"feedback": "down"},
    )

    assert response.status_code in (401, 403)


def test_update_message_feedback_rejects_other_users_message():
    owner_headers = _auth_headers()
    other_headers = _auth_headers()
    message_id = _message(owner_headers)

    response = client.patch(
        f"/messages/{message_id}/feedback",
        headers=other_headers,
        json={"feedback": "down"},
    )

    assert response.status_code == 404
