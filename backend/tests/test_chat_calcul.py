"""Tests for the deterministic calcul branch of /chat/message (Approche 1)."""
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.main import app
from app.schemas.chat import ClassificationResult
from app.services import chat_calculation


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


def test_chat_calcul_runs_without_referentiel_or_precision(monkeypatch):
    """Bug A : la branche calcul passe AVANT le gate referentiel/precision.

    Un calcul complet (montants + taux presents) ne doit jamais etre bloque
    par ``besoin_precision`` ni par l'absence de referentiel : c'est
    ``champs_manquants`` qui fait autorite (PRD S6).
    """
    def generate(question, classification, user, history_context=None):
        return "TVA de 200 EUR, TTC de 1200 EUR."

    response = _post(
        "Calcule la TVA pour 1000 EUR HT a 20%",
        _calc_classification(referentiel=None, besoin_precision=True),
        generate,
        monkeypatch,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["clarification_demandee"] is False
    assert body["mode"] == "calcul"
    assert body["calcul_result"]["result"] == 200.0
    assert body["champs_manquants"] == []


def test_chat_calcul_falls_back_when_sous_theme_is_not_registered(monkeypatch):
    """Bug B : le classifieur renvoie le vocabulaire du catalogue
    ("regroupement") et non celui du registre ("tva").

    Le repli domaine-seul s'applique car comptabilite n'a qu'un seul outil
    enregistre ; le resultat reste un calcul verifie dexter-calc.
    """
    def generate(question, classification, user, history_context=None):
        return "TVA de 200 EUR."

    response = _post(
        "Calcule la TVA pour 1000 EUR HT a 20%",
        _calc_classification(
            sous_theme="régularisation", question_sous_themes=["régularisation"]
        ),
        generate,
        monkeypatch,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["clarification_demandee"] is False
    assert body["mode"] == "calcul"
    assert body["calcul_result"]["result"] == 200.0
    assert body["calcul_result"]["sous_theme"] == "tva"


def test_chat_calcul_keeps_ambiguous_domain_failure_explicit(monkeypatch):
    """finance a 2 outils (VAN, amortissement) : aucun repli arbitraire.

    L'echec reste explicite et le LLM n'est jamais appele sur un calcul non
    verifie (regle 6).
    """
    def fail_generation(*args, **kwargs):
        raise AssertionError("LLM must not run when no calculator matches")

    response = _post(
        "VAN investissement 10000 flux 3000 4000 5000 taux 10%",
        _calc_classification(
            domaine="finance",
            sous_theme="inconnu",
            referentiel="IFRS",
            question_sous_themes=["inconnu"],
        ),
        fail_generation,
        monkeypatch,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["clarification_demandee"] is True
    assert body["mode"] == "calcul"
    assert body["calcul_result"] is None
    assert "Je ne peux pas calculer" in body["reponse"]


def test_chat_calcul_infers_domain_when_classifier_leaves_it_empty(monkeypatch):
    """Option C sur la route synchrone : domaine deduit du registre.

    ``tva`` n'est pas un mot-cle de ``domains.json``, le repli doit donc lire le
    registre des calculateurs pour que le calcul reste verifie par dexter-calc.
    """
    def generate(question, classification, user, history_context=None):
        return "TVA de 200 EUR, TTC de 1200 EUR."

    response = _post(
        "Calcule la TVA pour 1000 EUR HT a 20%",
        _calc_classification(domaine=None, sous_theme="calcul de la TVA"),
        generate,
        monkeypatch,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["domaine"] == "comptabilite"
    assert body["mode"] == "calcul"
    assert body["clarification_demandee"] is False
    assert body["calcul_result"]["result"] == 200.0


def test_infer_calcul_domain_reads_calculator_registry_vocabulary():
    """Option C : le domaine vient du sous-theme du registre des calculateurs."""
    classification = _calc_classification(
        domaine=None,
        sous_theme="calcul fiscal",
        question_sous_themes=["TVA"],
    )
    assert (
        chat_calculation.infer_calcul_domain(
            "Calcule la TVA pour 1000 EUR HT a 20%", classification
        )
        == "comptabilite"
    )


def test_infer_calcul_domain_normalizes_accents_and_word_starts():
    """``crédit``/``credits`` matchent, mais ``avant`` ne declenche pas ``van``."""
    classification = _calc_classification(
        domaine=None,
        sous_theme=None,
        question_sous_themes=[],
    )
    assert (
        chat_calculation.infer_calcul_domain(
            "Calcule la mensualite du crédit pour 12000 sur 24 mois", classification
        )
        == "banque"
    )
    assert (
        chat_calculation.infer_calcul_domain(
            "Calcule le total avant remise de 10%", classification
        )
        is None
    )


def test_infer_calcul_domain_returns_none_when_two_domains_tie():
    """Ambiguite : deux domaines a egalite -> aucune deduction arbitraire."""
    classification = _calc_classification(
        domaine=None,
        sous_theme=None,
        question_sous_themes=[],
    )
    assert (
        chat_calculation.infer_calcul_domain(
            "Calcule la VAN et la mensualite du credit", classification
        )
        is None
    )
