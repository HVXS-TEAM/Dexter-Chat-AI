"""Chat classification endpoints."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from app.auth.dependencies import get_current_user
from app.config import settings
from app.db.session import get_db
from app.domains.loader import get_domain, list_domains
from app.models.user import User
from app.rate_limiter import limiter
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
    create_conversation,
    get_conversation,
    set_referentiel_for_domain,
    update_conversation,
)

router = APIRouter(prefix="/chat", tags=["chat"])
api_router = APIRouter(prefix="/api", tags=["chat"])

logger = logging.getLogger(__name__)


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


def _sse_event(payload: dict[str, object]) -> str:
    """Serialize one payload as a Server-Sent Event."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

def _referentiel_clarification(referentiels: list[str]) -> str:
    """Wording of the referential clarification, shared by both routes."""
    return (
        "Quel référentiel souhaites-tu utiliser ? "
        f"Référentiels possibles : {', '.join(referentiels)}."
    )


def _unknown_context_clarification() -> str:
    """Wording of the 'not enough context' clarification, shared by both routes."""
    return (
        "Je n’ai pas assez d’éléments pour comprendre le contexte de ta demande. "
        "Peux-tu préciser ce que tu souhaites faire ?"
    )


def _missing_params_clarification(champs_manquants: list[str]) -> str:
    """Wording of the missing-parameters clarification, shared by both routes."""
    return (
        "Pour faire ce calcul de facon fiable, il me manque : "
        f"{', '.join(champs_manquants)}. Peux-tu preciser ces elements ?"
    )


def _calculator_unavailable_clarification(detail: str) -> str:
    """Wording of the calculator-failure clarification, shared by both routes."""
    return (
        "Je ne peux pas calculer cela de facon fiable "
        f"pour le moment ({detail}). "
        "Peux-tu reformuler avec les montants et le taux ?"
    )


def _persist_clarification(
    db: Session,
    conversation: object | None,
    classification: ClassificationResult,
    clarification: str,
    mode_utilise: str,
) -> int | None:
    """Persist an assistant clarification, returning its id when persisted.

    Both routes must record what the student actually read: without it the
    saved history keeps a dangling question and the next turn cannot rely on
    the clarification (parity ``/chat/stream`` <-> ``/chat/message``).
    """
    if conversation is None:
        return None
    assistant_message = add_message(
        db,
        conversation.id,
        "assistant",
        clarification,
        domaine_detecte=classification.domaine,
        sous_theme_detecte=classification.sous_theme,
        mode_utilise=mode_utilise,
    )
    return assistant_message.id


def _classification_with_inferred_domain(
    question: str,
    classification: ClassificationResult,
) -> ClassificationResult:
    """Fill an empty domain for a calculation request (deterministic fallback).

    A ``calcul`` request without domain cannot reach the deterministic branch:
    it would fall back to free generation with unverified figures (PRD S6).
    When the calculator registry vocabulary identifies a single domain, the
    classification is completed with it; otherwise it is returned unchanged so
    the clarification path stays in charge.
    """
    if classification.intention != "calcul" or classification.domaine:
        return classification
    inferred_domain = chat_calculation.infer_calcul_domain(question, classification)
    if inferred_domain is None:
        return classification
    return classification.model_copy(update={"domaine": inferred_domain})



async def _stream_calcul_events(
    payload: ChatMessageRequest,
    classification: ClassificationResult,
    current_user: User,
    db: Session,
    conversation: object,
    history_context: str | None,
) -> AsyncIterator[str]:
    """Run the deterministic calcul branch of the chat flow as SSE events.

    Mirrors ``_handle_calcul_branch`` (sync route): dexter-calc verifies the
    figures first, then the LLM explains them. A ``meta`` event publishes
    mode/clarification/calcul_result so the UI can render its existing
    panels. Missing parameters or calculator failures are an explicit answer
    streamed as tokens (never a generic error event, regle 6).

    Like the sync route, a clarification is persisted as a real assistant
    message, and both routes build their wording from the same helpers so the
    two contracts cannot drift apart again.
    """
    calc_status, calcul_result, champs_manquants, calc_error = (
        chat_calculation.run_deterministic_calculation(
            payload.question, classification
        )
    )

    if calc_status == "missing_params":
        clarification = _missing_params_clarification(champs_manquants)
    elif calc_status != "ok" or calcul_result is None:
        clarification = _calculator_unavailable_clarification(
            calc_error or "aucun calculateur disponible"
        )
    else:
        clarification = None

    yield _sse_event(
        {
            "type": "meta",
            "mode": "calcul",
            "intention": classification.intention,
            "domaine": classification.domaine,
            "sous_theme": classification.sous_theme,
            # Sub-theme actually resolved by the calculator registry (may
            # differ from the free-text classification above) — decision 2A.
            "sous_theme_effectif": (calcul_result or {}).get("sous_theme"),
            "referentiel": classification.referentiel,
            "clarification_demandee": clarification is not None,
            "champs_manquants": champs_manquants if clarification else [],
            "calcul_result": calcul_result,
        }
    )

    if clarification is not None:
        assistant_message_id = _persist_clarification(
            db, conversation, classification, clarification, "calcul"
        )
        yield _sse_event({"type": "token", "content": clarification})
        yield _sse_event(
            {
                "type": "done",
                "message_id": assistant_message_id,
                "conversation_id": conversation.id,
            }
        )
        return

    calc_context = chat_calculation.build_calculation_context(calcul_result)
    if history_context:
        full_history = f"{history_context}\n{calc_context}"
    else:
        full_history = calc_context

    complete_answer = ""
    async for fragment in chat_service._generate_stream(
        payload.question,
        classification,
        current_user,
        full_history,
        None,
    ):
        complete_answer += fragment
        yield _sse_event({"type": "token", "content": fragment})

    if not complete_answer.strip():
        raise ValueError("LLM returned an empty answer.")

    assistant_message = add_message(
        db,
        conversation.id,
        "assistant",
        complete_answer.strip(),
        domaine_detecte=classification.domaine,
        sous_theme_detecte=classification.sous_theme,
        mode_utilise="calcul",
    )
    yield _sse_event(
        {
            "type": "done",
            "message_id": assistant_message.id,
            "conversation_id": conversation.id,
        }
    )


async def _stream_chat_events(
    payload: ChatMessageRequest,
    current_user: User,
    db: Session,
) -> AsyncIterator[str]:
    """Classify, stream, persist, and serialize one chat response."""
    try:
        conversation = None
        conversation_id = payload.conversation_id
        history_context = payload.historique
        if conversation_id is None:
            conversation = create_conversation(db, current_user.id, "Nouvelle conversation")
            conversation_id = conversation.id
        else:
            conversation = get_conversation(db, conversation_id, current_user.id)
            if conversation is None:
                yield _sse_event({"type": "error", "message": "Conversation introuvable."})
                return
            conversation_context = build_conversation_context(db, conversation)
            history_context = "\n---\n".join(filter(None, [payload.historique, conversation_context]))
        # Classification runs for both paths (brand new or existing conversation),
        # exactly like the sync route: a new conversation must still be classified,
        # otherwise no answer and no "meta" event could ever be produced.
        classification = _classification_with_inferred_domain(
            payload.question,
            classifier.classify(payload.question, history_context),
        )
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

        # Deterministic calcul branch (same contract as /chat/message): dexter-calc
        # verifies the figures, then a "meta" SSE event feeds the UI panels.
        if classification.intention == "calcul" and classification.domaine:
            async for event in _stream_calcul_events(
                payload,
                classification,
                current_user,
                db,
                conversation,
                history_context,
            ):
                yield event
            return

        closest_domain = _closest_domain(payload.question, classification)
        domain_config = get_domain(classification.domaine) if classification.domaine else None
        needs_referentiel = bool(
            domain_config
            and domain_config.get("referentiels")
            and not classification.referentiel
        )
        if classification.besoin_precision or not classification.domaine or needs_referentiel:
            if needs_referentiel:
                referentiels = domain_config.get("referentiels", []) if domain_config else []
                clarification = _referentiel_clarification(referentiels)
            else:
                clarification = _unknown_context_clarification()

            yield _sse_event(
                {
                    "type": "meta",
                    "mode": "explique_moi",
                    "intention": classification.intention,
                    "domaine": classification.domaine,
                    "sous_theme": classification.sous_theme,
                    # Décision 2A : clé présente sur TOUTES les émissions meta,
                    # None ici car aucune résolution de calcul n'a eu lieu.
                    "sous_theme_effectif": None,
                    "referentiel": classification.referentiel,
                    "clarification_demandee": True,
                    "question_sous_themes": classification.question_sous_themes
                    or (closest_domain or {}).get("sous_themes", [])[:3],
                    "referentiels_proposes": (closest_domain or {}).get("referentiels"),
                    "champs_manquants": [],
                    "calcul_result": None,
                }
            )
            yield _sse_event({"type": "token", "content": clarification})
            assistant_message_id = _persist_clarification(
                db, conversation, classification, clarification, "explique_moi"
            )
            yield _sse_event(
                {
                    "type": "done",
                    "message_id": assistant_message_id,
                    "conversation_id": conversation.id,
                }
            )
            return

        rag_context = None
        if conversation is not None:
            rag_chunks = rag_service.search_documents(
                db,
                conversation.id,
                payload.question,
                limit=settings.rag_max_chunks,
                min_score=settings.rag_min_score,
            )
            if rag_chunks:
                rag_context = rag_service.format_chunks_context(rag_chunks)

        # Publish the resolved mode/domain before the tokens so the UI badge and
        # panels stay consistent for every intention (not only "calcul").
        response_mode = "mes_cours" if rag_context else "explique_moi"
        yield _sse_event(
            {
                "type": "meta",
                "mode": response_mode,
                "intention": classification.intention,
                "domaine": classification.domaine,
                "sous_theme": classification.sous_theme,
                # Décision 2A : clé présente sur TOUTES les émissions meta,
                # None ici (aucun calcul — seule la classification s'applique).
                "sous_theme_effectif": None,
                "referentiel": classification.referentiel,
                "clarification_demandee": False,
                "champs_manquants": [],
                "calcul_result": None,
            }
        )

        complete_answer = ""
        async for fragment in chat_service._generate_stream(
            payload.question,
            classification,
            current_user,
            history_context,
            rag_context,
        ):
            complete_answer += fragment
            yield _sse_event({"type": "token", "content": fragment})

        if not complete_answer.strip():
            raise ValueError("LLM returned an empty answer.")

        if conversation is not None:
            assistant_message = add_message(
                db,
                conversation.id,
                "assistant",
                complete_answer.strip(),
                domaine_detecte=classification.domaine,
                sous_theme_detecte=classification.sous_theme,
                mode_utilise=response_mode,
            )
            yield _sse_event(
                {
                    "type": "done",
                    "message_id": assistant_message.id,
                    "conversation_id": conversation.id,
                }
            )
        else:
            yield _sse_event({"type": "done"})
    except Exception:
        # Never swallow the cause (regle 6): the client gets the generic message,
        # the server log gets the question and the full stack trace.
        logger.exception(
            "Stream generation failed (question=%r, conversation_id=%r)",
            payload.question,
            payload.conversation_id,
        )
        yield _sse_event({"type": "error", "message": "La génération de la réponse a échoué."})


def _create_chat_stream_response(
    payload: ChatMessageRequest,
    current_user: User,
    db: Session,
) -> StreamingResponse:
    """Create the shared authenticated SSE response used by chat endpoints."""
    return StreamingResponse(
        _stream_chat_events(payload, current_user, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/stream")
@limiter.shared_limit("20/minute", scope="chat")
def chat_stream(
    request: Request,
    payload: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Stream a chat answer with the legacy path's shared IP limit."""
    return _create_chat_stream_response(payload, current_user, db)


@api_router.post("/chat")
@limiter.shared_limit("20/minute", scope="chat")
def api_chat(
    request: Request,
    payload: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Stream a chat answer from the protected backend API."""
    return _create_chat_stream_response(payload, current_user, db)


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
    classification = _classification_with_inferred_domain(payload.question, classification)
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

    # Deterministic calcul first: a complete calculation must never be blocked
    # by the referential/precision gates below — _handle_calcul_branch asks
    # explicitly for the missing numeric fields instead (PRD S6).
    if classification.intention == "calcul" and classification.domaine:
        response, _ = _handle_calcul_branch(
            payload,
            classification,
            current_user,
            db,
            conversation,
            history_context,
        )
        return response

    if classification.besoin_precision or not classification.domaine or needs_referentiel:
        if needs_referentiel:
            referentiels = domain_config.get("referentiels", []) if domain_config else []
            clarification = _referentiel_clarification(referentiels)
        else:
            clarification = _unknown_context_clarification()
        # Parity with /chat/stream: the clarification is a real assistant turn,
        # so it is persisted and returned instead of leaving "reponse" empty and
        # the saved history without Dexter's question.
        _persist_clarification(
            db, conversation, classification, clarification, "explique_moi"
        )
        return ChatMessageResponse(
            reponse=clarification,
            domaine=classification.domaine,
            sous_theme=classification.sous_theme,
            referentiel=classification.referentiel,
            clarification_demandee=True,
            question_sous_themes=classification.question_sous_themes
            or (closest_domain or {}).get("sous_themes", [])[:3],
            referentiels_proposes=(closest_domain or {}).get("referentiels"),
            conversation_id=payload.conversation_id,
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
) -> tuple[ChatMessageResponse, int | None]:
    """Run the deterministic calcul branch (Approche 1).

    Extraction + dexter-calc first, then LLM explains the verified figures.
    Missing params or calc errors give an explicit answer, never a number
    invented by the model (PRD S6/S10.5).

    Returns the response and the id of the persisted assistant message (``None``
    when no conversation was available, e.g. a request without
    ``conversation_id``). Clarifications are persisted too, exactly like
    ``_stream_calcul_events``, so the saved history mirrors what was displayed.
    """
    calc_status, calcul_result, champs_manquants, calc_error = (
        chat_calculation.run_deterministic_calculation(
            payload.question, classification
        )
    )

    if calc_status == "missing_params":
        clarification = _missing_params_clarification(champs_manquants)
        response = ChatMessageResponse(
            reponse=clarification,
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
        return response, _persist_clarification(
            db, conversation, classification, clarification, "calcul"
        )

    if calc_status != "ok" or calcul_result is None:
        clarification = _calculator_unavailable_clarification(
            calc_error or "aucun calculateur disponible"
        )
        response = ChatMessageResponse(
            reponse=clarification,
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
        return response, _persist_clarification(
            db, conversation, classification, clarification, "calcul"
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

    assistant_message_id: int | None = None
    if payload.conversation_id is not None and conversation is not None:
        assistant_message = add_message(
            db,
            conversation.id,
            "assistant",
            answer,
            domaine_detecte=classification.domaine,
            sous_theme_detecte=classification.sous_theme,
            mode_utilise="calcul",
            sources_rag=None,
        )
        assistant_message_id = assistant_message.id
        if classification.referentiel:
            conversation.referentiel_actif = classification.referentiel
            update_conversation(
                db, conversation, {"referentiel_actif": classification.referentiel}
            )
            if classification.domaine:
                set_referentiel_for_domain(
                    db, current_user.id, classification.domaine, classification.referentiel
                )

    response = ChatMessageResponse(
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
    return response, assistant_message_id