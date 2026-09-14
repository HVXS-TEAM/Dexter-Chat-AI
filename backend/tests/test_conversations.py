import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def auth_headers():
    email = f"conv-{uuid.uuid4()}@example.com"
    register = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "securepass123",
            "role": "etudiant",
            "filiere": "Informatique",
            "annee": "2025",
        },
    )
    assert register.status_code == 201, register.text

    login = client.post(
        "/auth/login",
        json={"email": email, "password": "securepass123"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_list_conversation(auth_headers):
    create_response = client.post(
        "/conversations",
        headers=auth_headers,
        json={"titre": "Comptabilité baseline"},
    )
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["titre"] == "Comptabilité baseline"

    list_response = client.get("/conversations", headers=auth_headers)
    assert list_response.status_code == 200, list_response.text
    items = list_response.json()
    assert any(item["id"] == created["id"] for item in items)


def test_add_message_and_detail(auth_headers):
    created = client.post(
        "/conversations",
        headers=auth_headers,
        json={"titre": "Session compta"},
    )
    conversation_id = created.json()["id"]

    message_response = client.post(
        "/conversations/{conversation_id}/messages".format(conversation_id=conversation_id),
        headers=auth_headers,
        json={"role": "user", "content": "Quel est le bilan comptable ?"},
    )
    assert message_response.status_code == 201, message_response.text
    message = message_response.json()
    assert message["conversation_id"] == conversation_id
    assert message["content"] == "Quel est le bilan comptable ?"

    detail_response = client.get(
        f"/conversations/{conversation_id}",
        headers=auth_headers,
    )
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert len(detail["messages"]) >= 1


def test_chat_message_with_conversation_id_persists(auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.services.classifier.classify",
        lambda question, historique=None: type(
            "X",
            (),
            {
                "domaine": "comptabilite",
                "sous_theme": "bilan",
                "referentiel": "OHADA",
                "intention": "explication",
                "langue": "fr",
                "confiance": 0.9,
                "besoin_precision": False,
                "question_sous_themes": ["bilan"],
            },
        )(),
    )
    monkeypatch.setattr(
        "app.services.chat_service.generate_answer",
        lambda question, classification, user, historique=None: "Réponse pédagogique test.",
    )

    conversation = client.post(
        "/conversations",
        headers=auth_headers,
        json={"titre": "Contexte test"},
    )
    conversation_id = conversation.json()["id"]

    response = client.post(
        "/chat/message",
        headers=auth_headers,
        json={
            "question": "Explique-moi le bilan comptable",
            "conversation_id": conversation_id,
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["domaine"] == "comptabilite"
    assert body["conversation_id"] == conversation_id

    detail = client.get(f"/conversations/{conversation_id}", headers=auth_headers)
    stored = detail.json()
    assert len(stored["messages"]) >= 2


def test_update_conversation(auth_headers):
    created = client.post(
        "/conversations",
        headers=auth_headers,
        json={"titre": "Titre initial"},
    )
    conversation_id = created.json()["id"]

    update_response = client.patch(
        f"/conversations/{conversation_id}",
        headers=auth_headers,
        json={"titre": "Titre modifié", "referentiel_actif": "OHADA"},
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["titre"] == "Titre modifié"
    assert updated["referentiel_actif"] == "OHADA"


def test_delete_conversation(auth_headers):
    created = client.post(
        "/conversations",
        headers=auth_headers,
        json={"titre": "À supprimer"},
    )
    conversation_id = created.json()["id"]

    delete_response = client.delete(
        f"/conversations/{conversation_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204, delete_response.text

    detail_response = client.get(
        f"/conversations/{conversation_id}",
        headers=auth_headers,
    )
    assert detail_response.status_code == 404, detail_response.text


def test_conversation_belongs_to_user(auth_headers):
    """A user cannot access another user's conversation."""
    # Create a conversation with the first user.
    created = client.post(
        "/conversations",
        headers=auth_headers,
        json={"titre": "Conversation privée"},
    )
    conversation_id = created.json()["id"]

    # Register and login a second user.
    email2 = f"other-{uuid.uuid4()}@example.com"
    client.post(
        "/auth/register",
        json={
            "email": email2,
            "password": "securepass123",
            "role": "etudiant",
            "filiere": "Informatique",
            "annee": "2025",
        },
    )
    login2 = client.post(
        "/auth/login",
        json={"email": email2, "password": "securepass123"},
    )
    headers2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}

    # The second user must get a 404.
    detail_response = client.get(
        f"/conversations/{conversation_id}",
        headers=headers2,
    )
    assert detail_response.status_code == 404, detail_response.text


def test_chat_message_without_conversation_id(auth_headers, monkeypatch):
    """Without conversation_id, the endpoint behaves as before (no persistence)."""
    monkeypatch.setattr(
        "app.services.classifier.classify",
        lambda question, historique=None: type(
            "X",
            (),
            {
                "domaine": "comptabilite",
                "sous_theme": "bilan",
                "referentiel": "OHADA",
                "intention": "explication",
                "langue": "fr",
                "confiance": 0.9,
                "besoin_precision": False,
                "question_sous_themes": ["bilan"],
            },
        )(),
    )
    monkeypatch.setattr(
        "app.services.chat_service.generate_answer",
        lambda question, classification, user, historique=None: "Réponse sans persistance.",
    )

    response = client.post(
        "/chat/message",
        headers=auth_headers,
        json={"question": "Explique-moi le bilan comptable"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["conversation_id"] is None


def test_referentiel_actif_updated(auth_headers, monkeypatch):
    """The conversation referentiel_actif is updated after a chat message."""
    monkeypatch.setattr(
        "app.services.classifier.classify",
        lambda question, historique=None: type(
            "X",
            (),
            {
                "domaine": "comptabilite",
                "sous_theme": "bilan",
                "referentiel": "OHADA",
                "intention": "explication",
                "langue": "fr",
                "confiance": 0.9,
                "besoin_precision": False,
                "question_sous_themes": ["bilan"],
            },
        )(),
    )
    monkeypatch.setattr(
        "app.services.chat_service.generate_answer",
        lambda question, classification, user, historique=None: "Réponse avec référentiel.",
    )

    conversation = client.post(
        "/conversations",
        headers=auth_headers,
        json={"titre": "Test référentiel"},
    )
    conversation_id = conversation.json()["id"]

    response = client.post(
        "/chat/message",
        headers=auth_headers,
        json={
            "question": "Explique-moi le bilan comptable",
            "conversation_id": conversation_id,
        },
    )
    assert response.status_code == 200, response.text

    detail = client.get(f"/conversations/{conversation_id}", headers=auth_headers)
    stored = detail.json()
    assert stored["referentiel_actif"] == "OHADA"


def test_auto_title_generated(auth_headers, monkeypatch):
    """The conversation title is auto-generated from the first message."""
    monkeypatch.setattr(
        "app.services.classifier.classify",
        lambda question, historique=None: type(
            "X",
            (),
            {
                "domaine": "comptabilite",
                "sous_theme": "bilan",
                "referentiel": "OHADA",
                "intention": "explication",
                "langue": "fr",
                "confiance": 0.9,
                "besoin_precision": False,
                "question_sous_themes": ["bilan"],
            },
        )(),
    )
    monkeypatch.setattr(
        "app.services.chat_service.generate_answer",
        lambda question, classification, user, historique=None: "Réponse avec titre auto.",
    )

    conversation = client.post(
        "/conversations",
        headers=auth_headers,
        json={},
    )
    conversation_id = conversation.json()["id"]
    assert conversation.json()["titre"] == "Nouvelle conversation"

    response = client.post(
        "/chat/message",
        headers=auth_headers,
        json={
            "question": "Explique-moi le bilan comptable en OHADA",
            "conversation_id": conversation_id,
        },
    )
    assert response.status_code == 200, response.text

    detail = client.get(f"/conversations/{conversation_id}", headers=auth_headers)
    stored = detail.json()
    assert stored["titre"] != "Nouvelle conversation"
    assert "Explique-moi le bilan comptable" in stored["titre"]


def test_generate_resume_empty_conversation(auth_headers):
    """Generating a resume for an empty conversation returns 400."""
    conversation = client.post(
        "/conversations",
        headers=auth_headers,
        json={"titre": "Vide"},
    )
    conversation_id = conversation.json()["id"]

    response = client.post(
        f"/conversations/{conversation_id}/resume",
        headers=auth_headers,
    )
    assert response.status_code == 400, response.text