from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.main import app

client = TestClient(app)


class DummySession:
    def add(self, *args, **kwargs):
        return None

    def commit(self):
        return None

    def refresh(self, obj, *args, **kwargs):
        if getattr(obj, "id", None) is None:
            obj.id = 1
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now(timezone.utc)
        return None

    def query(self, *args, **kwargs):
        raise AssertionError("This test should not hit the real database query path.")


def _override_user():
    return SimpleNamespace(
        id=1,
        email="student@example.com",
        role="etudiant",
        langue_preferee="fr",
    )


def _override_db():
    yield DummySession()


def test_generate_quiz_masks_correction(monkeypatch):
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        monkeypatch.setattr(
            "app.services.quiz_service.get_domain",
            lambda domaine: {"id": "comptabilite", "referentiels": ["OHADA", "IFRS"]},
        )
        monkeypatch.setattr(
            "app.services.quiz_service.build_domain_prompt",
            lambda domaine, intention: "PROMPT",
        )

        class Provider:
            @staticmethod
            def chat(*args, **kwargs):
                return "Question: calculez le bilan.\nCORRIGE:\nLe solde est correct."

        monkeypatch.setattr("app.services.quiz_service.get_llm_provider", lambda: Provider())

        response = client.post(
            "/quiz/generate",
            json={"domaine": "comptabilite", "sous_theme": "bilan", "referentiel": "OHADA"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["domaine"] == "comptabilite"
    assert body["statut"] == "genere"
    assert "corrige" not in body
    assert body["enonce"].startswith("Question")


def test_generate_quiz_unknown_domain():
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.post(
            "/quiz/generate",
            json={"domaine": "astrologie", "sous_theme": "lune", "referentiel": "None"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown domain: astrologie"


def test_generate_quiz_llm_failure(monkeypatch):
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        monkeypatch.setattr(
            "app.services.quiz_service.get_domain",
            lambda domaine: {"id": "finance", "referentiels": ["IFRS"]},
        )
        monkeypatch.setattr("app.services.quiz_service.build_domain_prompt", lambda domaine, intention: "PROMPT")

        class Provider:
            @staticmethod
            def chat(*args, **kwargs):
                raise RuntimeError("provider unavailable")

        monkeypatch.setattr("app.services.quiz_service.get_llm_provider", lambda: Provider())

        response = client.post(
            "/quiz/generate",
            json={"domaine": "finance", "sous_theme": "valuation", "referentiel": "IFRS"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json()["detail"] == "Quiz generation failed."


def test_submit_quiz_returns_correction(monkeypatch):
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        fake_attempt = SimpleNamespace(
            id=12,
            user_id=1,
            domaine="comptabilite",
            sous_theme="bilan",
            referentiel="OHADA",
            enonce="Question: expliquez le bilan.",
            corrige="Le bilan est le patrimoine.",
            reponse_etudiant=None,
            score=None,
            feedback_corrige=None,
            statut="genere",
        )
        monkeypatch.setattr("app.routers.quiz.get_attempt", lambda db, attempt_id, user_id: fake_attempt)
        monkeypatch.setattr("app.services.quiz_service._score_answer", lambda corrige, reponse: 88.0)
        monkeypatch.setattr(
            "app.services.quiz_service.build_domain_prompt",
            lambda domaine, intention: "PROMPT",
        )

        class Provider:
            @staticmethod
            def chat(*args, **kwargs):
                return "Feedback: votre réponse est bonne."

        monkeypatch.setattr("app.services.quiz_service.get_llm_provider", lambda: Provider())

        response = client.post("/quiz/12/submit", json={"reponse_etudiant": "Le bilan est le patrimoine."})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["statut"] == "corrige"
    assert body["score"] == 88.0
    assert body["corrige"] == "Le bilan est le patrimoine."
    assert body["feedback_corrige"] == "Feedback: votre réponse est bonne."


def test_submit_quiz_not_found(monkeypatch):
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        monkeypatch.setattr("app.routers.quiz.get_attempt", lambda db, attempt_id, user_id: None)
        response = client.post("/quiz/999/submit", json={"reponse_etudiant": "test"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Quiz attempt not found."


def test_progress_aggregates(monkeypatch):
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        attempts = [
            SimpleNamespace(id=1, domaine="comptabilite", sous_theme="bilan", referentiel="OHADA", statut="corrige", score=80.0, created_at="2026-09-01T00:00:00"),
            SimpleNamespace(id=2, domaine="finance", sous_theme="valuation", referentiel="IFRS", statut="genere", score=None, created_at="2026-09-02T00:00:00"),
            SimpleNamespace(id=3, domaine="comptabilite", sous_theme="bilan", referentiel="OHADA", statut="corrige", score=90.0, created_at="2026-09-03T00:00:00"),
        ]
        monkeypatch.setattr("app.routers.quiz.list_attempts", lambda db, user_id: attempts)
        response = client.get("/users/me/progress")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total_attempts"] == 3
    assert body["submitted_attempts"] == 2
    assert body["average_score"] == 85.0
    assert body["by_domain"]["comptabilite"] == 2
    assert body["by_domain"]["finance"] == 1
def test_generate_quiz_empty_llm_response_is_502(monkeypatch):
    """Empty LLM output must be a clean 502, never a 500 or a masked error."""
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        monkeypatch.setattr(
            "app.services.quiz_service.get_domain",
            lambda domaine: {"id": "comptabilite"},
        )
        monkeypatch.setattr(
            "app.services.quiz_service.build_domain_prompt",
            lambda domaine, intention: "PROMPT",
        )

        class Provider:
            @staticmethod
            def chat(*args, **kwargs):
                return "   "

        monkeypatch.setattr("app.services.quiz_service.get_llm_provider", lambda: Provider())
        response = client.post(
            "/quiz/generate",
            json={"domaine": "comptabilite", "sous_theme": "bilan", "referentiel": "OHADA"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502, response.text
    assert response.json()["detail"] == "Quiz generation failed."


def test_generate_quiz_without_correction_marker_stores_none(monkeypatch):
    """A model answer without the CORRIGE marker must not crash or leak."""
    from app.services.quiz_service import generate_quiz

    session = DummySession()
    monkeypatch.setattr(
        "app.services.quiz_service.get_domain",
        lambda domaine: {"id": "comptabilite"},
    )
    monkeypatch.setattr(
        "app.services.quiz_service.build_domain_prompt",
        lambda domaine, intention: "PROMPT",
    )

    class Provider:
        @staticmethod
        def chat(*args, **kwargs):
            return "ENONCE:\nCalculez la TVA a 20% sur 1000.\n"

    monkeypatch.setattr("app.services.quiz_service.get_llm_provider", lambda: Provider())
    user = SimpleNamespace(id=1, role="etudiant", langue_preferee="fr")
    attempt = generate_quiz(session, user, "comptabilite", "tva", "OHADA")

    assert attempt.statut == "genere"
    assert attempt.corrige is None
    assert "TVA" in attempt.enonce


def test_submit_quiz_marks_already_submitted_as_400(monkeypatch):
    """Submitting an already corrected attempt is rejected explicitly."""
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        fake_attempt = SimpleNamespace(
            id=13,
            user_id=1,
            domaine="comptabilite",
            sous_theme="bilan",
            referentiel="OHADA",
            enonce="Question.",
            corrige="Le bilan.",
            reponse_etudiant="Le bilan.",
            score=95.0,
            feedback_corrige="Bien.",
            statut="corrige",
        )
        monkeypatch.setattr(
            "app.routers.quiz.get_attempt", lambda db, attempt_id, user_id: fake_attempt
        )
        response = client.post("/quiz/13/submit", json={"reponse_etudiant": "Le bilan."})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Quiz attempt already submitted."


def test_submit_quiz_inter_user_attempt_is_404(monkeypatch):
    """An attempt owned by another user must be indistinguishable from missing."""
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        monkeypatch.setattr("app.routers.quiz.get_attempt", lambda db, attempt_id, user_id: None)
        response = client.post("/quiz/7/submit", json={"reponse_etudiant": "test"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Quiz attempt not found."

def test_submit_quiz_without_stored_correction_scores_none(monkeypatch):
    """No stored correction: score stays None, feedback is skipped, no 500."""
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        fake_attempt = SimpleNamespace(
            id=14,
            user_id=1,
            domaine="comptabilite",
            sous_theme="tva",
            referentiel="OHADA",
            enonce="Question sans corrige.",
            corrige=None,
            reponse_etudiant=None,
            score=None,
            feedback_corrige=None,
            statut="genere",
        )

        class Provider:
            @staticmethod
            def chat(*args, **kwargs):
                raise AssertionError("LLM must not be called without a stored correction.")

        monkeypatch.setattr(
            "app.routers.quiz.get_attempt", lambda db, attempt_id, user_id: fake_attempt
        )
        monkeypatch.setattr("app.services.quiz_service.get_llm_provider", lambda: Provider())
        monkeypatch.setattr(
            "app.services.quiz_service.build_domain_prompt", lambda domaine, intention: "PROMPT"
        )
        response = client.post("/quiz/14/submit", json={"reponse_etudiant": "tva 20%"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["statut"] == "corrige"
    assert body["score"] is None
    assert body["feedback_corrige"] is None
    assert body["corrige"] is None


def test_read_quiz_detail_masks_correction_until_submit(monkeypatch):
    """GET /quiz/{id} hides the correction while pending, then reveals it."""
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        pending = SimpleNamespace(
            id=15,
            user_id=1,
            domaine="comptabilite",
            sous_theme="tva",
            referentiel="OHADA",
            enonce="Question.",
            reponse_etudiant=None,
            corrige="Reponse secrete.",
            score=None,
            feedback_corrige=None,
            statut="genere",
            created_at="2026-09-01T00:00:00",
        )
        monkeypatch.setattr("app.routers.quiz.get_attempt", lambda db, attempt_id, user_id: pending)
        response = client.get("/quiz/15")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["statut"] == "genere"
        assert body["corrige"] is None
        assert body["feedback_corrige"] is None
        assert body["score"] is None

        corrected = SimpleNamespace(
            id=15,
            user_id=1,
            domaine="comptabilite",
            sous_theme="tva",
            referentiel="OHADA",
            enonce="Question.",
            reponse_etudiant="Ma reponse.",
            corrige="Reponse secrete.",
            score=80.0,
            feedback_corrige="Bien.",
            statut="corrige",
            created_at="2026-09-01T00:00:00",
        )
        monkeypatch.setattr("app.routers.quiz.get_attempt", lambda db, attempt_id, user_id: corrected)
        response = client.get("/quiz/15")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["statut"] == "corrige"
        assert body["corrige"] == "Reponse secrete."
        assert body["score"] == 80.0
    finally:
        app.dependency_overrides.clear()