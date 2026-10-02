


import json
import logging
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
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


def _classification():
    return ClassificationResult(
        domaine="comptabilite",
        sous_theme="bilan",
        referentiel="OHADA",
        intention="explication",
        langue="fr",
        confiance=0.95,
        besoin_precision=False,
        question_sous_themes=["bilan"],
    )


_EXPLIQUE_META = {
    "type": "meta",
    "mode": "explique_moi",
    "intention": "explication",
    "domaine": "comptabilite",
    "sous_theme": "bilan",
    "sous_theme_effectif": None,
    "referentiel": "OHADA",
    "clarification_demandee": False,
    "champs_manquants": [],
    "calcul_result": None,
}


def _events(response):
    return [json.loads(line.removeprefix("data: ").strip()) for line in response.text.splitlines() if line.startswith("data: ")]


def test_chat_stream_sends_tokens_and_done(monkeypatch):
    conversation = SimpleNamespace(id=42, titre="Nouvelle conversation")
    added_messages = iter([SimpleNamespace(id=10), SimpleNamespace(id=22)])
    updates: list[dict] = []

    monkeypatch.setattr("app.services.classifier.classify", lambda question, history: _classification())
    monkeypatch.setattr("app.routers.chat.create_conversation", lambda db, user_id, title: conversation)
    monkeypatch.setattr("app.routers.chat.build_conversation_context", lambda db, item: "")
    monkeypatch.setattr("app.routers.chat.add_message", lambda *args, **kwargs: next(added_messages))
    monkeypatch.setattr("app.routers.chat.update_conversation", lambda db, item, values: updates.append(values))
    monkeypatch.setattr("app.routers.chat.rag_service.search_documents", lambda *args, **kwargs: [])

    async def generate_stream(*args, **kwargs):
        yield "Bonjour "
        yield "Dexter."

    monkeypatch.setattr("app.services.chat_service._generate_stream", generate_stream)
    app.dependency_overrides[get_current_user] = _override_user
    try:
        response = client.post("/chat/stream", json={"question": "Explique le bilan en OHADA"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"
    events = _events(response)
    assert events[0] == _EXPLIQUE_META
    assert events[1] == {"type": "token", "content": "Bonjour "}
    assert events[2] == {"type": "token", "content": "Dexter."}
    assert events[3]["type"] == "done"
    assert events[3]["message_id"] == 22
    assert events[3]["conversation_id"] == 42
    assert updates == [{"titre": "Explique le bilan en OHADA"}]


def test_chat_stream_classifies_follow_up_with_conversation_context(monkeypatch):
    conversation = SimpleNamespace(id=42, titre="Calcul de VAN")
    stored_context = "Previous user question: Calcule la VAN. Previous assistant answer: Il manque des donnees."
    classification_contexts = []
    added_messages = iter([SimpleNamespace(id=10), SimpleNamespace(id=22)])

    def classify(question, history):
        classification_contexts.append(history)
        return _classification()

    monkeypatch.setattr("app.services.classifier.classify", classify)
    monkeypatch.setattr("app.routers.chat.get_conversation", lambda db, conversation_id, user_id: conversation)
    monkeypatch.setattr("app.routers.chat.build_conversation_context", lambda db, item: stored_context)
    monkeypatch.setattr("app.routers.chat.add_message", lambda *args, **kwargs: next(added_messages))
    monkeypatch.setattr("app.routers.chat.rag_service.search_documents", lambda *args, **kwargs: [])

    async def generate_stream(*args, **kwargs):
        yield "Voici la suite contextualisee."

    monkeypatch.setattr("app.services.chat_service._generate_stream", generate_stream)
    app.dependency_overrides[get_current_user] = _override_user
    try:
        response = client.post(
            "/chat/stream",
            json={
                "question": "Imagine les",
                "conversation_id": conversation.id,
                "historique": "Client-provided context",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(classification_contexts) == 1
    assert "Client-provided context" in classification_contexts[0]
    assert stored_context in classification_contexts[0]


def test_chat_stream_asks_for_clarification_when_context_is_insufficient(monkeypatch):
    conversation = SimpleNamespace(id=42, titre="Conversation")
    persisted_messages = []
    ambiguous_classification = ClassificationResult(
        domaine=None,
        sous_theme=None,
        referentiel=None,
        intention="autre",
        langue="fr",
        confiance=0.2,
        besoin_precision=True,
        question_sous_themes=["VAN"],
    )

    monkeypatch.setattr("app.services.classifier.classify", lambda question, history: ambiguous_classification)
    monkeypatch.setattr("app.routers.chat.get_conversation", lambda db, conversation_id, user_id: conversation)
    monkeypatch.setattr("app.routers.chat.build_conversation_context", lambda db, item: "Previous calculation context")
    def add_message(db, conversation_id, role, content, **kwargs):
        persisted_messages.append((role, content))
        return SimpleNamespace(id=10 + len(persisted_messages))

    monkeypatch.setattr("app.routers.chat.add_message", add_message)

    async def generate_stream(*args, **kwargs):
        raise AssertionError("Generation must not run without a classified domain")
        yield "unreachable"

    monkeypatch.setattr("app.services.chat_service._generate_stream", generate_stream)
    app.dependency_overrides[get_current_user] = _override_user
    try:
        response = client.post(
            "/chat/stream",
            json={"question": "Imagine les", "conversation_id": conversation.id},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    events = _events(response)
    assert [event["type"] for event in events] == ["meta", "token", "done"]
    assert events[0]["clarification_demandee"] is True
    # Décision 2A : la clé est aussi exposée par le meta de clarification.
    assert events[0]["sous_theme_effectif"] is None
    assert "préciser" in events[1]["content"].lower()
    assert events[2]["conversation_id"] == conversation.id
    assert persisted_messages[-1] == ("assistant", events[1]["content"])
    assert events[2]["message_id"] == 12


def test_chat_stream_returns_error_for_empty_stream(monkeypatch):
    conversation = SimpleNamespace(id=7, titre="Nouvelle conversation")

    monkeypatch.setattr("app.services.classifier.classify", lambda question, history: _classification())
    monkeypatch.setattr("app.routers.chat.create_conversation", lambda db, user_id, title: conversation)
    monkeypatch.setattr("app.routers.chat.build_conversation_context", lambda db, item: "")
    monkeypatch.setattr("app.routers.chat.add_message", lambda *args, **kwargs: SimpleNamespace(id=11))
    monkeypatch.setattr("app.routers.chat.update_conversation", lambda db, item, values: None)
    monkeypatch.setattr("app.routers.chat.rag_service.search_documents", lambda *args, **kwargs: [])

    async def generate_stream(*args, **kwargs):
        if False:
            yield ""

    monkeypatch.setattr("app.services.chat_service._generate_stream", generate_stream)
    app.dependency_overrides[get_current_user] = _override_user
    try:
        response = client.post("/chat/stream", json={"question": "Explique le bilan en OHADA"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert _events(response) == [
        _EXPLIQUE_META,
        {"type": "error", "message": "La génération de la réponse a échoué."},
    ]


def test_chat_stream_returns_error_when_llm_fails(monkeypatch, caplog):
    conversation = SimpleNamespace(id=7, titre="Nouvelle conversation")

    monkeypatch.setattr("app.services.classifier.classify", lambda question, history: _classification())
    monkeypatch.setattr("app.routers.chat.create_conversation", lambda db, user_id, title: conversation)
    monkeypatch.setattr("app.routers.chat.build_conversation_context", lambda db, item: "")
    monkeypatch.setattr("app.routers.chat.add_message", lambda *args, **kwargs: SimpleNamespace(id=11))
    monkeypatch.setattr("app.routers.chat.update_conversation", lambda db, item, values: None)
    monkeypatch.setattr("app.routers.chat.rag_service.search_documents", lambda *args, **kwargs: [])

    async def generate_stream(*args, **kwargs):
        raise RuntimeError("provider unavailable")
        yield "unreachable"

    monkeypatch.setattr("app.services.chat_service._generate_stream", generate_stream)
    app.dependency_overrides[get_current_user] = _override_user
    try:
        with caplog.at_level(logging.ERROR):
            response = client.post("/chat/stream", json={"question": "Explique le bilan en OHADA"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert _events(response) == [
        _EXPLIQUE_META,
        {"type": "error", "message": "La génération de la réponse a échoué."},
    ]
    # The generic message is for the client only: the server log must carry the
    # real cause (regle 6 — no hidden error).
    assert "Stream generation failed" in caplog.text
    assert "provider unavailable" in caplog.text


def test_chat_stream_auto_titles_new_conversation(monkeypatch):
    conversation = SimpleNamespace(id=7, titre="Nouvelle conversation")
    updates = []

    monkeypatch.setattr("app.services.classifier.classify", lambda question, history: _classification())
    monkeypatch.setattr("app.routers.chat.create_conversation", lambda db, user_id, title: conversation)
    monkeypatch.setattr("app.routers.chat.build_conversation_context", lambda db, item: "")
    monkeypatch.setattr("app.routers.chat.add_message", lambda *args, **kwargs: SimpleNamespace(id=22))
    monkeypatch.setattr("app.routers.chat.update_conversation", lambda db, item, values: updates.append(values))
    monkeypatch.setattr("app.routers.chat.rag_service.search_documents", lambda *args, **kwargs: [])

    async def generate_stream(*args, **kwargs):
        yield "Réponse"

    monkeypatch.setattr("app.services.chat_service._generate_stream", generate_stream)
    app.dependency_overrides[get_current_user] = _override_user
    try:
        response = client.post("/chat/stream", json={"question": "Explique le bilan comptable"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert updates == [{"titre": "Explique le bilan comptable"}]


def _calcul_classification(**overrides):
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


def _patch_stream_dependencies(monkeypatch, conversation, classification, added_messages):
    """Patch the stream I/O around the branch under test."""
    monkeypatch.setattr("app.services.classifier.classify", lambda question, history: classification)
    monkeypatch.setattr("app.routers.chat.create_conversation", lambda db, user_id, title: conversation)
    monkeypatch.setattr("app.routers.chat.build_conversation_context", lambda db, item: "")
    monkeypatch.setattr("app.routers.chat.add_message", lambda *args, **kwargs: next(added_messages))
    monkeypatch.setattr("app.routers.chat.update_conversation", lambda db, item, values: None)
    monkeypatch.setattr("app.routers.chat.rag_service.search_documents", lambda *args, **kwargs: [])


def test_chat_stream_calcul_sends_meta_before_verified_tokens(monkeypatch):
    """Le stream branche la branche calcul deterministe (signalement n° 2).

    Sous-theme non enregistre ("régularisation") et aucun referentiel : le
    calcul reste verifie par dexter-calc, le LLM ne recoit que les chiffres
    verifies, et l'evenement ``meta`` alimente les panneaux de l'UI.
    """
    conversation = SimpleNamespace(id=42, titre="Nouvelle conversation")
    added_messages = iter([SimpleNamespace(id=10), SimpleNamespace(id=22)])
    seen = {}

    _patch_stream_dependencies(
        monkeypatch,
        conversation,
        _calcul_classification(sous_theme="régularisation", referentiel=None),
        added_messages,
    )

    async def generate_stream(question, classification, user, history, rag_context=None):
        seen["history"] = history
        yield "TVA de 200 EUR."

    monkeypatch.setattr("app.services.chat_service._generate_stream", generate_stream)
    app.dependency_overrides[get_current_user] = _override_user
    try:
        response = client.post(
            "/chat/stream",
            json={"question": "Calcule la TVA pour 1000 EUR HT a 20%"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    events = _events(response)
    assert events[0]["type"] == "meta"
    assert events[0]["mode"] == "calcul"
    assert events[0]["intention"] == "calcul"
    assert events[0]["domaine"] == "comptabilite"
    # Decision 2A : meta expose aussi le sous-theme effectivement calcule.
    assert events[0]["sous_theme"] == "régularisation"
    assert events[0]["sous_theme_effectif"] == "tva"
    assert events[0]["clarification_demandee"] is False
    assert events[0]["champs_manquants"] == []
    assert events[0]["calcul_result"]["result"] == 200.0
    assert events[1] == {"type": "token", "content": "TVA de 200 EUR."}
    assert events[2] == {"type": "done", "message_id": 22, "conversation_id": 42}
    assert "Resultat de calcul verifie" in seen["history"]


def test_chat_stream_calcul_missing_params_asks_explicitly(monkeypatch):
    """Parametres incomplets -> clarification explicite, sans appel LLM."""
    conversation = SimpleNamespace(id=7, titre="Nouvelle conversation")
    persisted_messages = []

    _patch_stream_dependencies(
        monkeypatch,
        conversation,
        _calcul_classification(),
        iter([SimpleNamespace(id=11)]),
    )

    def add_message(db, conversation_id, role, content, **kwargs):
        persisted_messages.append((role, content))
        return SimpleNamespace(id=10 + len(persisted_messages))

    monkeypatch.setattr("app.routers.chat.add_message", add_message)

    async def generate_stream(*args, **kwargs):
        raise AssertionError("LLM must not run when params are missing")
        yield "unreachable"

    monkeypatch.setattr("app.services.chat_service._generate_stream", generate_stream)
    app.dependency_overrides[get_current_user] = _override_user
    try:
        response = client.post(
            "/chat/stream",
            json={"question": "Calcule la TVA pour 1000 EUR HT"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    events = _events(response)
    assert [event["type"] for event in events] == ["meta", "token", "done"]
    assert events[0]["mode"] == "calcul"
    assert events[0]["clarification_demandee"] is True
    assert events[0]["calcul_result"] is None
    assert "taux de TVA" in events[0]["champs_manquants"]
    assert "taux de TVA" in events[1]["content"]
    assert events[2]["conversation_id"] == 7
    assert events[2]["message_id"] == 12
    assert persisted_messages[-1] == ("assistant", events[1]["content"])


def test_chat_stream_calcul_without_domain_asks_for_clarification(monkeypatch):
    """Option B (filet de securite) : calcul sans domaine ni vocabulaire calculable.

    Le classifieur live peut renvoyer ``intention="calcul"`` avec
    ``domaine=None``. Le repli deterministe du registre des calculateurs
    (option C) n'a alors aucune prise : la question ne contient aucun
    vocabulaire de calculateur. La branche deterministe ne peut donc pas
    s'executer, et la question ne doit JAMAIS partir en generation LLM libre
    (chiffres non verifies, PRD S6). L'utilisateur recoit une demande de
    precision explicite, et le ``meta`` expose ``intention`` pour rendre la
    cause visible (option A).
    """
    conversation = SimpleNamespace(id=42, titre="Conversation")
    persisted_messages = []
    calcul_without_domain = ClassificationResult(
        domaine=None,
        sous_theme="calcul divers",
        referentiel=None,
        intention="calcul",
        langue="fr",
        confiance=0.35,
        besoin_precision=False,
        question_sous_themes=["régularisation"],
    )

    monkeypatch.setattr(
        "app.services.classifier.classify",
        lambda question, history: calcul_without_domain,
    )
    monkeypatch.setattr(
        "app.routers.chat.get_conversation",
        lambda db, conversation_id, user_id: conversation,
    )
    monkeypatch.setattr("app.routers.chat.build_conversation_context", lambda db, item: "")

    def add_message(db, conversation_id, role, content, **kwargs):
        persisted_messages.append((role, content))
        return SimpleNamespace(id=10 + len(persisted_messages))

    monkeypatch.setattr("app.routers.chat.add_message", add_message)

    async def generate_stream(*args, **kwargs):
        raise AssertionError("LLM must not run when the calcul domain is unknown")
        yield "unreachable"

    monkeypatch.setattr("app.services.chat_service._generate_stream", generate_stream)
    app.dependency_overrides[get_current_user] = _override_user
    try:
        response = client.post(
            "/chat/stream",
            json={
                "question": "Peux-tu calculer un montant pour ce dossier ?",
                "conversation_id": conversation.id,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    events = _events(response)
    assert [event["type"] for event in events] == ["meta", "token", "done"]
    assert events[0]["mode"] == "explique_moi"
    assert events[0]["intention"] == "calcul"
    assert events[0]["domaine"] is None
    assert events[0]["clarification_demandee"] is True
    assert events[0]["calcul_result"] is None
    assert "préciser" in events[1]["content"].lower()
    assert events[2]["message_id"] == 12
    assert persisted_messages[-1] == ("assistant", events[1]["content"])




def test_chat_stream_calcul_without_domain_uses_registry_fallback(monkeypatch):
    """Option C : calcul sans domaine + vocabulaire du registre des calculateurs.

    Le classifieur live renvoie ``intention="calcul"`` avec ``domaine=None``.
    ``tva`` n'appartenant pas aux mots-cles de ``domains.json``, le repli
    s'appuie sur le sous-theme du registre ``dexter-calc`` : le domaine est
    complete, donc le calcul verifie s'execute au lieu d'une simple demande de
    precision.
    """
    conversation = SimpleNamespace(id=42, titre="Conversation")
    persisted_messages = []
    calcul_without_domain = ClassificationResult(
        domaine=None,
        sous_theme="calcul de la TVA",
        referentiel=None,
        intention="calcul",
        langue="fr",
        confiance=0.35,
        besoin_precision=False,
        question_sous_themes=["TVA"],
    )

    monkeypatch.setattr(
        "app.services.classifier.classify",
        lambda question, history: calcul_without_domain,
    )
    monkeypatch.setattr(
        "app.routers.chat.get_conversation",
        lambda db, conversation_id, user_id: conversation,
    )
    monkeypatch.setattr("app.routers.chat.build_conversation_context", lambda db, item: "")

    def add_message(db, conversation_id, role, content, **kwargs):
        persisted_messages.append((role, content, kwargs.get("domaine_detecte")))
        return SimpleNamespace(id=10 + len(persisted_messages))

    monkeypatch.setattr("app.routers.chat.add_message", add_message)

    async def generate_stream(question, classification, user, history, rag_context=None):
        yield "TVA de 200 EUR."

    monkeypatch.setattr("app.services.chat_service._generate_stream", generate_stream)
    app.dependency_overrides[get_current_user] = _override_user
    try:
        response = client.post(
            "/chat/stream",
            json={
                "question": "Calcule la TVA pour 1000 EUR HT a 20%",
                "conversation_id": conversation.id,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    events = _events(response)
    assert [event["type"] for event in events] == ["meta", "token", "done"]
    assert events[0]["mode"] == "calcul"
    assert events[0]["intention"] == "calcul"
    assert events[0]["domaine"] == "comptabilite"
    assert events[0]["clarification_demandee"] is False
    assert events[0]["champs_manquants"] == []
    assert events[0]["calcul_result"]["result"] == 200.0
    assert events[1] == {"type": "token", "content": "TVA de 200 EUR."}
    # Le domaine deduit est aussi celui sauvegarde avec les messages.
    assert {message[2] for message in persisted_messages} == {"comptabilite"}


def test_chat_stream_meta_reports_mes_cours_when_rag_finds_chunks(monkeypatch):
    """Document retrouve -> le meta annonce mes_cours avant les tokens."""
    conversation = SimpleNamespace(id=42, titre="Nouvelle conversation")
    added_messages = iter([SimpleNamespace(id=10), SimpleNamespace(id=22)])

    _patch_stream_dependencies(
        monkeypatch,
        conversation,
        _classification(),
        added_messages,
    )
    monkeypatch.setattr(
        "app.routers.chat.rag_service.search_documents",
        lambda *args, **kwargs: [(SimpleNamespace(id=5), 0.91)],
    )
    monkeypatch.setattr(
        "app.routers.chat.rag_service.format_chunks_context",
        lambda chunks: "[Source 1] Extrait du cours.",
    )

    async def generate_stream(question, classification, user, history, rag_context=None):
        assert rag_context == "[Source 1] Extrait du cours."
        yield "D'apres ton cours..."

    monkeypatch.setattr("app.services.chat_service._generate_stream", generate_stream)
    app.dependency_overrides[get_current_user] = _override_user
    try:
        response = client.post(
            "/chat/stream",
            json={"question": "Explique le bilan en OHADA"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    events = _events(response)
    assert events[0]["type"] == "meta"
    assert events[0]["mode"] == "mes_cours"
    assert events[0]["domaine"] == "comptabilite"
    assert events[0]["calcul_result"] is None
    # Décision 2A : la clé est aussi exposée par le meta du mode général.
    assert events[0]["sous_theme_effectif"] is None
    assert events[1] == {"type": "token", "content": "D'apres ton cours..."}
    assert events[2]["type"] == "done"
    assert events[2]["message_id"] == 22
