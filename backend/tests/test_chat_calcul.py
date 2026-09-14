"""Tests for the deterministic calcul branch of /chat/message (Approche 1)."""
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


def _calc_classification(**overrides):
    base = dict(
        domaine="comptabilite",
        sous_theme="tva",
        referentiel="OHADA",
        intention="calcul",
        langue="fr",
        confiance=0.95,
        besoin_precision=False,
        question_sous_themes=["tva"],
    )
    base.update(overrides)
    return ClassificationResult(**base)


def _post(question, classification, generate=None, monkeypatch=None):
    monkeypatch.setattr(
        "app.services.classifier.classify",
        lambda q, history: classification,
    )
    if generate is not None:
        monkeypatch.setattr(
            "app.services.chat_service.generate_answer", generate
        )
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    try:
        return client.post("/chat/message", json={"question": question})
    finally:
        app.dependency_overrides.clear()


def test_chat_calcul_tva_returns_verified_result(monkeypatch):
    """TVA complete -> dexter-calc runs, LLM explains, figures returned."""
    seen = {}

    def generate(question, classification, user, history_context=None):
        seen["history"] = history_context
        return "TVA de 200 EUR, TTC de 1200 EUR."

    response = _post(
        "Calcule la TVA pour 1000 EUR HT a 20%",
        _calc_classification(),
        generate,
        monkeypatch,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["clarification_demandee"] is False
    assert body["mode"] == "calcul"
    assert body["reponse"] == "TVA de 200 EUR, TTC de 1200 EUR."
    assert body["calcul_result"]["result"] == 200.0
    assert body["calcul_result"]["extra"]["montant_ttc"] == 1200.0
    assert body["champs_manquants"] == []
    assert "Resultat de calcul verifie" in seen["history"]


def test_chat_calcul_missing_rate_asks_clarification(monkeypatch):
    """TVA sans taux -> clarification explicite, sans appel LLM."""
    def fail_generation(*args, **kwargs):
        raise AssertionError("LLM must not run when params are missing")

    response = _post(
        "Calcule la TVA pour 1000 EUR HT",
        _calc_classification(),
        fail_generation,
        monkeypatch,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["clarification_demandee"] is True
    assert body["mode"] == "calcul"
    assert body["calcul_result"] is None
    assert "taux de TVA" in body["champs_manquants"]
    assert "taux de TVA" in body["reponse"]


def test_chat_calcul_van_returns_verified_result(monkeypatch):
    """VAN complete -> deterministic VAN via dexter-calc."""
    def generate(question, classification, user, history_context=None):
        return "VAN positive, projet rentable."

    response = _post(
        "VAN investissement 10000 flux 3000 4000 5000 taux 10%",
        _calc_classification(
            domaine="finance", sous_theme="van", referentiel="IFRS"
        ),
        generate,
        monkeypatch,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["clarification_demandee"] is False
    assert body["mode"] == "calcul"
    assert "van" in body["calcul_result"]["extra"]


def test_chat_calcul_explains_generation_failure_as_502(monkeypatch):
    """Calcul OK mais LLM en panne -> 502 explicite (regle 6)."""
    def fail_generation(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    response = _post(
        "Calcule la TVA pour 1000 EUR HT a 20%",
        _calc_classification(),
        fail_generation,
        monkeypatch,
    )
    assert response.status_code == 502
    assert response.json()["detail"] == "LLM generation failed."
