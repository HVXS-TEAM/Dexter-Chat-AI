from app.domains.loader import get_domain, list_domains
from app.services.classifier import classify


def test_domains_are_loaded_from_configuration():
    domains = list_domains()
    assert len(domains) >= 2
    assert any(domain["id"] == "comptabilite" for domain in domains)
    assert any(domain["id"] == "finance" for domain in domains)

    domain = get_domain("comptabilite")
    assert domain is not None
    assert "OHADA" in domain["referentiels"]


def test_classify_handles_known_question_without_crashing(monkeypatch):
    class DummyProvider:
        def chat(self, messages, temperature, max_tokens):
            return '{"domaine": "comptabilite", "sous_theme": "bilan", "referentiel": "OHADA", "intention": "explication", "langue": "fr", "confiance": 0.9, "besoin_precision": false, "question_sous_themes": ["bilan"]}'

    monkeypatch.setattr("app.services.classifier.get_llm_provider", lambda: DummyProvider())

    result = classify("explique-moi le bilan comptable en OHADA")
    assert result.domaine == "comptabilite"
    assert result.langue == "fr"
    assert result.confiance >= 0.6


def test_classify_returns_uncertain_state_for_unrelated_question(monkeypatch):
    class DummyProvider:
        def chat(self, messages, temperature, max_tokens):
            return '{"domaine": null, "sous_theme": null, "referentiel": null, "intention": "autre", "langue": "fr", "confiance": 0.1, "besoin_precision": true, "question_sous_themes": ["general"]}'

    monkeypatch.setattr("app.services.classifier.get_llm_provider", lambda: DummyProvider())

    result = classify("raconte-moi une blague")
    assert result.domaine is None
    assert result.besoin_precision is True
