import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.chat import ClassificationResult
from app.services.document_chunker import chunk_text
from app.services.document_extractor import extract_text

client = TestClient(app)


def _patch_indexing_dependencies(monkeypatch):
    monkeypatch.setattr(
        "app.services.rag_service.embed_texts",
        lambda texts: [[0.0] * 384 for _ in texts],
    )
    monkeypatch.setattr(
        "app.services.rag_service.classifier.classify",
        lambda text, historique=None: ClassificationResult(
            domaine="comptabilite",
            sous_theme="general",
            referentiel="OHADA",
            confiance=0.9,
        ),
    )


def _auth_headers(role: str = "etudiant") -> dict[str, str]:
    email = f"document-{uuid.uuid4()}@example.com"
    register = client.post(
        "/auth/register",
        json={"email": email, "password": "securepass123", "role": role},
    )
    assert register.status_code == 201, register.text
    login = client.post(
        "/auth/login",
        json={"email": email, "password": "securepass123"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _conversation(headers: dict[str, str]) -> int:
    response = client.post("/conversations", headers=headers, json={"titre": "Cours RAG"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_extract_text_txt():
    assert extract_text("lesson.txt", b"Balance sheet\n\nAssets") == "Balance sheet\n\nAssets"


def test_chunk_text_preserves_paragraphs():
    chunks = chunk_text("First paragraph.\n\nSecond paragraph.", max_chars=30, overlap=5)
    assert len(chunks) == 2
    assert chunks[0][0] == "First paragraph."
    assert chunks[1][0].endswith("Second paragraph.")


def test_upload_document_txt(monkeypatch):
    _patch_indexing_dependencies(monkeypatch)
    headers = _auth_headers()
    conversation_id = _conversation(headers)
    response = client.post(
        f"/conversations/{conversation_id}/documents",
        headers=headers,
        files={"file": ("lesson.txt", b"Balance sheet\n\nAssets", "text/plain")},
    )
    assert response.status_code == 201, response.text
    document = response.json()
    assert document["conversation_id"] == conversation_id
    assert document["type_fichier"] == "txt"
    assert document["statut_indexation"] == "indexe"


def test_upload_document_unsupported():
    headers = _auth_headers()
    conversation_id = _conversation(headers)
    response = client.post(
        f"/conversations/{conversation_id}/documents",
        headers=headers,
        files={"file": ("malware.exe", b"not supported", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_student_cannot_change_document_visibility(monkeypatch):
    _patch_indexing_dependencies(monkeypatch)
    headers = _auth_headers()
    conversation_id = _conversation(headers)
    upload = client.post(
        f"/conversations/{conversation_id}/documents",
        headers=headers,
        files={"file": ("lesson.txt", b"Course content", "text/plain")},
    )
    document_id = upload.json()["id"]
    response = client.patch(
        f"/documents/{document_id}/visibility",
        headers=headers,
        json={"visibilite": "partage_classe"},
    )
    assert response.status_code == 403


def test_professor_can_share_document(monkeypatch):
    _patch_indexing_dependencies(monkeypatch)
    headers = _auth_headers(role="professeur")
    conversation_id = _conversation(headers)
    upload = client.post(
        f"/conversations/{conversation_id}/documents",
        headers=headers,
        files={"file": ("cours_compta.txt", b"OHADA course content", "text/plain")},
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["id"]
    response = client.patch(
        f"/documents/{document_id}/visibility",
        headers=headers,
        json={"visibilite": "partage_classe"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["visibilite"] == "partage_classe"
    assert body["id"] == document_id
