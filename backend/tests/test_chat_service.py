from types import SimpleNamespace

from app.schemas.chat import ClassificationResult
from app.services import chat_service


def test_generate_answer_uses_domain_template_and_generation_model(monkeypatch):
    calls = []

    class DummyProvider:
        def chat(self, messages, temperature, max_tokens, model=None):
            calls.append((messages, model))
            return "Generated answer"

    monkeypatch.setattr(chat_service, "get_llm_provider", lambda: DummyProvider())
    monkeypatch.setattr(chat_service.settings, "llm_model_generation", "generation-model")

    result = chat_service.generate_answer(
        "Explain the balance sheet",
        ClassificationResult(
            domaine="comptabilite",
            sous_theme="bilan",
            referentiel="OHADA",
            intention="explication",
            langue="fr",
            confiance=0.95,
            besoin_precision=False,
        ),
        SimpleNamespace(role="etudiant", langue_preferee="fr"),
    )

    assert result == "Generated answer"
    assert calls[0][1] == "generation-model"
    prompt = calls[0][0][0]["content"]
    assert "Explain the balance sheet" in prompt
    assert "OHADA" in prompt
    assert "$question" not in prompt
