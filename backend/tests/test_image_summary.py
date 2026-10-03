"""Image OCR summary (ChatGPT style) via the configured text LLM.

The summary is prepended to the OCR text before chunking: no new dependency
(no vision model), no database migration, no schema change. A provider
failure never blocks indexing — it is logged and the raw OCR text is kept.
"""

from __future__ import annotations

from types import SimpleNamespace

from app.schemas.chat import ClassificationResult
from app.services import rag_service


def _classification_result() -> ClassificationResult:
    return ClassificationResult(
        domaine="comptabilite",
        sous_theme="general",
        referentiel="OHADA",
        confiance=0.9,
    )


class _SummaryProvider:
    """Fake LLM provider recording the prompt it received."""

    def __init__(self, answer: str = "") -> None:
        self.answer = answer
        self.calls: list[list[dict[str, str]]] = []

    def chat(self, messages, temperature, max_tokens, model=None):
        self.calls.append(messages)
        return self.answer


class _FakeChunks:
    def __init__(self) -> None:
        self.stored: list = []

    def clear(self) -> None:
        self.stored.clear()

    def append(self, chunk) -> None:
        self.stored.append(chunk)


class _FakeDb:
    def add(self, _item) -> None:
        return None

    def commit(self) -> None:
        return None

    def refresh(self, _item) -> None:
        return None


def _index_png(monkeypatch, tmp_path, provider, ocr_text: str, titre: str):
    """Index a fake PNG through ``rag_service`` with a controlled provider."""
    from PIL import Image

    monkeypatch.setattr("app.services.image_summary.get_llm_provider", lambda: provider)
    monkeypatch.setattr(
        rag_service.classifier, "classify", lambda text, historique=None: _classification_result()
    )
    monkeypatch.setattr(rag_service, "embed_texts", lambda texts: [[0.0] * 384 for _ in texts])
    monkeypatch.setattr(
        "app.services.rag_service.extract_text", lambda filename, file_bytes: ocr_text
    )

    image_path = tmp_path / titre
    Image.new("RGB", (10, 10), "white").save(image_path, format="PNG")
    chunks = _FakeChunks()
    document = SimpleNamespace(
        titre=titre, chunks=chunks, statut_indexation="pending", domaine_associe=None
    )
    result = rag_service.index_document(_FakeDb(), document, image_path.read_bytes())
    return result, chunks.stored



def test_image_summary_is_prepended_as_chunk_zero(monkeypatch, tmp_path):
    """The structured summary becomes chunk 0, ahead of the raw OCR text."""
    provider = _SummaryProvider(
        answer="Description : facture.\nEntites : Dexter.\nChiffres cles : 20%."
    )
    _result, stored = _index_png(
        monkeypatch, tmp_path, provider, "TVA 20% sur 1000 euros le 12/03/2026", "facture.png"
    )

    assert provider.calls, "le LLM de resume aurait du etre appele pour une image"
    prompt = " ".join(message["content"] for message in provider.calls[0])
    assert "TVA 20%" in prompt, "le texte OCR doit etre envoye au LLM"
    assert stored, "aucun chunk persiste"
    first = stored[0].contenu_texte
    assert first.startswith("Resume de l'image :"), first[:120]
    assert "TVA 20%" in first, "le texte OCR brut doit suivre le resume"
    assert stored[0].page_ou_position == 0


def test_image_summary_failure_keeps_ocr_alone(monkeypatch, tmp_path):
    """A provider failure never blocks indexing: OCR alone is chunked."""

    class _FailingProvider:
        def chat(self, messages, temperature, max_tokens, model=None):
            raise RuntimeError("LLM indisponible")

    result, stored = _index_png(
        monkeypatch, tmp_path, _FailingProvider(), "TVA 20% sur 1000 euros", "panne.png"
    )

    assert result.statut_indexation == "indexe"
    assert stored, "l'OCR seul aurait du etre indexe malgre la panne LLM"
    assert all("Resume de l'image" not in chunk.contenu_texte for chunk in stored)
    assert "TVA 20%" in stored[0].contenu_texte


def test_txt_document_never_calls_summary_llm(monkeypatch):
    """Non-image documents keep the previous path: no summary LLM call."""
    provider = _SummaryProvider(answer="ne doit jamais servir")
    monkeypatch.setattr("app.services.image_summary.get_llm_provider", lambda: provider)
    monkeypatch.setattr(
        rag_service.classifier, "classify", lambda text, historique=None: _classification_result()
    )
    monkeypatch.setattr(rag_service, "embed_texts", lambda texts: [[0.0] * 384 for _ in texts])
    monkeypatch.setattr(
        "app.services.rag_service.extract_text", lambda filename, file_bytes: "Balance sheet"
    )

    chunks = _FakeChunks()
    document = SimpleNamespace(
        titre="lesson.txt", chunks=chunks, statut_indexation="pending", domaine_associe=None
    )
    rag_service.index_document(_FakeDb(), document, b"Balance sheet")

    assert provider.calls == [], "le LLM de resume ne doit pas etre appele pour un TXT"