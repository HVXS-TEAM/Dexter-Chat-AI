"""Document indexing and vector retrieval service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.services import classifier
from app.services.document_chunker import chunk_text
from app.services.document_extractor import extract_text
from app.services.embedding_service import embed_text, embed_texts


def index_document(db: Session, document: Document, file_bytes: bytes) -> Document:
    """Extract, chunk, embed, and persist a document."""
    document.statut_indexation = "pending"
    text = extract_text(document.titre, file_bytes)
    classification = classifier.classify(text[:4000])
    chunks = chunk_text(text)
    embeddings = embed_texts([chunk for chunk, _ in chunks])
    document.chunks.clear()
    document.domaine_associe = classification.domaine
    document.statut_indexation = "indexe"
    for (content, position), embedding in zip(chunks, embeddings, strict=True):
        document.chunks.append(
            DocumentChunk(contenu_texte=content, embedding=embedding, page_ou_position=position)
        )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def search_documents(
    db: Session,
    conversation_id: int,
    question: str,
    limit: int = 5,
    min_score: float = 0.5,
) -> list[tuple[DocumentChunk, float]]:
    """Return relevant chunks from documents attached to a conversation."""
    document_ids = db.query(Document.id).filter(Document.conversation_id == conversation_id).subquery()
    if db.query(document_ids.c.id).first() is None:
        return []
    question_vector = embed_text(question)
    rows = (
        db.query(DocumentChunk, DocumentChunk.embedding.cosine_distance(question_vector).label("distance"))
        .filter(DocumentChunk.document_id.in_(document_ids))
        .order_by("distance")
        .limit(limit * 2)
        .all()
    )
    results: list[tuple[DocumentChunk, float]] = []
    for chunk, distance in rows:
        score = 1.0 - float(distance)
        if score >= min_score:
            results.append((chunk, score))
        if len(results) >= limit:
            break
    return results


def format_chunks_context(chunks: list[tuple[DocumentChunk, float]]) -> str:
    """Format retrieved chunks with source identifiers."""
    return "\n\n".join(
        f"[Source chunk {chunk.id}, position {chunk.page_ou_position}, score {score:.3f}]\n{chunk.contenu_texte}"
        for chunk, score in chunks
    )
