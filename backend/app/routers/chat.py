"""Chat classification endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import settings
from app.db.session import get_db
from app.domains.loader import get_domain, list_domains
from app.models.user import User
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ClassifyRequest,
    ClassificationResult,
)
from app.services import chat_service, classifier, rag_service
from app.services import chat_calculation
from app.services.conversations import (
    add_message,
    build_conversation_context,
    get_conversation,
    set_referentiel_for_domain,
    update_conversation,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/classify", response_model=ClassificationResult)
def classify_question(payload: ClassifyRequest) -> ClassificationResult:
    """Classify a user question by domain, sub-theme, intention, and language."""
    try:
        return classifier.classify(payload.question, payload.historique)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="LLM classification failed.") from exc


def _closest_domain(question: str, classification: ClassificationResult) -> dict | None:
    """Find the closest configured domain for clarification metadata."""
    if classification.domaine:
        return get_domain(classification.domaine)

    question_text = question.lower()
    candidates: list[tuple[int, dict]] = []
    for domain in list_domains():
        score = sum(keyword.lower() in question_text for keyword in domain.get("keywords", []))
        score += sum(theme.lower() in question_text for theme in domain.get("sous_themes", []))
        score += sum(theme.lower() in classification.question_sous_themes for theme in domain.get("sous_themes", []))
        if score > 0:
            candidates.append((score, domain))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None
@router.post("/message", response_model=ChatMessageResponse)
def chat_message(
    payload: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatMessageResponse:
    """Classify a question and generate or request clarification."""
    conversation = None
    history_context = payload.historique
    if payload.conversation_id is not None:
        conversation = get_conversation(db, payload.conversation_id, current_user.id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
        conversation_context = build_conversation_context(db, conversation)
        history_context = "\n---\n".join(filter(None, [payload.historique, conversation_context]))

    try:
        classification = classifier.classify(payload.question, history_context)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="LLM classification failed.") from exc
    closest_domain = _closest_domain(payload.question, classification)
    domain_config = get_domain(classification.domaine) if classification.domaine else None
    needs_referentiel = bool(
        domain_config
        and domain_config.get("referentiels")
        and not classification.referentiel
    )

    if payload.conversation_id is not None and conversation is not None:
        add_message(
            db,
            conversation.id,
            "user",
            payload.question,
            domaine_detecte=classification.domaine,
            sous_theme_detecte=classification.sous_theme,
            mode_utilise="explique_moi",
        )
        if conversation.titre in ("", "Nouvelle conversation"):
            auto_title = payload.question.strip()[:50]
            if len(payload.question.strip()) > 50:
                auto_title += "..."
            update_conversation(db, conversation, {"titre": auto_title})

    if classification.besoin_precision or not classification.domaine or needs_referentiel:
        return ChatMessageResponse(
            reponse=None,
            domaine=classification.domaine,
            sous_theme=classification.sous_theme,
            referentiel=classification.referentiel,
            clarification_demandee=True,
            question_sous_themes=classification.question_sous_themes
            or (closest_domain or {}).get("sous_themes", [])[:3],
            referentiels_proposes=(closest_domain or {}).get("referentiels"),
            conversation_id=payload.conversation_id,
        )

    if classification.intention == "calcul" and classification.domaine:
        return _handle_calcul_branch(
            payload,
            classification,
            current_user,
            db,
            conversation,
            history_context,
        )

    rag_chunks: list[tuple[object, float]] = []
    rag_context: str | None = None
    if payload.conversation_id is not None and conversation is not None:
        try:
            rag_chunks = rag_service.search_documents(
                db,
                conversation.id,
                payload.question,
                limit=settings.rag_max_chunks,
                min_score=settings.rag_min_score,
            )
            if rag_chunks:
                rag_context = rag_service.format_chunks_context(rag_chunks)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Document retrieval failed.") from exc

    response_mode = "mes_cours" if rag_chunks else "explique_moi"
    source_ids: list[str] | None = [str(chunk.id) for chunk, _ in rag_chunks] or None

    try:
        if rag_context:
            answer = chat_service.generate_answer(
                payload.question,
                classification,
                current_user,
                history_context,
                rag_context=rag_context,
            )
        else:
            answer = chat_service.generate_answer(
                payload.question,
                classification,
                current_user,
                history_context,
            )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="LLM generation failed.") from exc

    if payload.conversation_id is not None and conversation is not None:
        add_message(
            db,
            conversation.id,
            "assistant",
            answer,
            domaine_detecte=classification.domaine,
            sous_theme_detecte=classification.sous_theme,
            mode_utilise=response_mode,
            sources_rag=source_ids,
        )
        if classification.referentiel:
            conversation.referentiel_actif = classification.referentiel
            update_conversation(db, conversation, {"referentiel_actif": classification.referentiel})
            if classification.domaine:
                set_referentiel_for_domain(db, current_user.id, classification.domaine, classification.referentiel)

    return ChatMessageResponse(
        reponse=answer,
        mode=response_mode,
        domaine=classification.domaine,
        sous_theme=classification.sous_theme,
        referentiel=classification.referentiel,
        clarification_demandee=False,
        question_sous_themes=classification.question_sous_themes,
        referentiels_proposes=None,
        conversation_id=payload.conversation_id,
    )


def _handle_calcul_branch(
    payload: ChatMessageRequest,
    classification: ClassificationResult,
    current_user: User,
    db: Session,
    conversation: object | None,
    history_context: str | None,
) -> ChatMessageResponse:
    """Run the deterministic calcul branch (Approche 1).

    Extraction + dexter-calc first, then LLM explains the verified figures.
    Missing params or calc errors give an explicit answer, never a number
    invented by the model (PRD S6/S10.5).
    """
    calc_status, calcul_result, champs_manquants, calc_error = (
        chat_calculation.run_deterministic_calculation(
            payload.question, classification
        )
    )

    if calc_status == "missing_params":
        joined = ", ".join(champs_manquants)
        return ChatMessageResponse(
            reponse=(
                "Pour faire ce calcul de facon fiable, il me manque : "
                f"{joined}. Peux-tu preciser ces elements ?"
            ),
            mode="calcul",
            domaine=classification.domaine,
            sous_theme=classification.sous_theme,
            referentiel=classification.referentiel,
            clarification_demandee=True,
            question_sous_themes=classification.question_sous_themes,
            referentiels_proposes=None,
            conversation_id=payload.conversation_id,
            calcul_result=None,
            champs_manquants=champs_manquants,
        )

    if calc_status != "ok" or calcul_result is None:
        detail = calc_error or "aucun calculateur disponible"
        return ChatMessageResponse(
            reponse=(
                "Je ne peux pas calculer cela de facon fiable "
                f"pour le moment ({detail}). "
                "Peux-tu reformuler avec les montants et le taux ?"
            ),
            mode="calcul",
            domaine=classification.domaine,
            sous_theme=classification.sous_theme,
            referentiel=classification.referentiel,
            clarification_demandee=True,
            question_sous_themes=classification.question_sous_themes,
            referentiels_proposes=None,
            conversation_id=payload.conversation_id,
            calcul_result=None,
            champs_manquants=[],
        )

    calc_context = chat_calculation.build_calculation_context(calcul_result)
    if history_context:
        full_history = f"{history_context}\n{calc_context}"
    else:
        full_history = calc_context

    try:
        answer = chat_service.generate_answer(
            payload.question,
            classification,
            current_user,
            full_history,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM generation failed.",
        ) from exc

    if payload.conversation_id is not None and conversation is not None:
        add_message(
            db,
            conversation.id,
            "assistant",
            answer,
            domaine_detecte=classification.domaine,
            sous_theme_detecte=classification.sous_theme,
            mode_utilise="calcul",
            sources_rag=None,
        )
        if classification.referentiel:
            conversation.referentiel_actif = classification.referentiel
            update_conversation(
                db, conversation, {"referentiel_actif": classification.referentiel}
            )
            if classification.domaine:
                set_referentiel_for_domain(
                    db, current_user.id, classification.domaine, classification.referentiel
                )

    return ChatMessageResponse(
        reponse=answer,
        mode="calcul",
        domaine=classification.domaine,
        sous_theme=classification.sous_theme,
        referentiel=classification.referentiel,
        clarification_demandee=False,
        question_sous_themes=classification.question_sous_themes,
        referentiels_proposes=None,
        conversation_id=payload.conversation_id,
        calcul_result=calcul_result,
        champs_manquants=[],
    )