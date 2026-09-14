# Prompt Copilot — Conversations persistantes et contexte conversationnel

## Contexte

Projet : Dexter Chat AI — chatbot pédagogique pour étudiants et professeurs.
Stack : Python + FastAPI, SQLAlchemy, Alembic, PostgreSQL + pgvector, React + TypeScript.
Documentation de référence : `Documentation Dexter/dexter-prd.md` (sections §5.4, §8.1, §12.2).
Règles projet : `AGENTS.md` et `cline.md`.

## État actuel du code

Le backend est fonctionnel avec :
- Authentification complète (JWT, bcrypt, rôles étudiant/professeur)
- Détection générique de domaine / sous-thème / référentiel / intention / langue
- Génération pédagogique spécialisée par domaine (templates markdown)
- Route `/chat/message` opérationnelle avec logique de clarification si référentiel manquant
- Tests pytest 8/8 passés

### Structure existante

```
backend/app/
├── main.py              # FastAPI app, inclut auth_router, users_router, chat_router
├── config.py            # Settings pydantic-settings
├── models/
│   ├── __init__.py      # Base (DeclarativeBase) + exports User
│   └── user.py          # Modèle User
├── schemas/
│   ├── __init__.py
│   ├── user.py          # Schémas UserCreate, UserLogin, UserUpdate, UserRead, TokenPair
│   └── chat.py          # Schémas ClassifyRequest, ClassificationResult, ChatMessageRequest, ChatMessageResponse
├── services/
│   ├── __init__.py
│   ├── users.py         # CRUD utilisateurs
│   ├── classifier.py    # Classification de domaine
│   └── chat_service.py  # Génération de réponse pédagogique
├── routers/
│   ├── __init__.py
│   ├── auth.py          # /auth/register, /auth/login, /auth/refresh
│   ├── users.py         # /users/me (GET, PATCH)
│   └── chat.py          # /chat/classify, /chat/message
├── auth/
│   ├── dependencies.py  # get_current_user
│   └── security.py      # hash_password, verify_password, create_access_token, create_refresh_token, decode_token
├── db/
│   └── session.py       # engine, SessionLocal, get_db
├── domains/
│   ├── domains.json     # Configuration des domaines (comptabilite, finance)
│   └── loader.py        # list_domains, get_domain, domain_prompt_context
├── llm/
│   ├── provider.py      # Interface LLMProvider
│   └── openai_compatible.py  # Implémentation OpenAI-compatible
└── prompts/
    ├── loader.py        # build_domain_prompt
    └── templates/       # Templates markdown par domaine et intention
```

### Conventions existantes

- Code et commentaires en **anglais**
- Docstrings en anglais
- Type hints systématiques (`Mapped[...]`, `mapped_column`, `str | None`)
- Modèles SQLAlchemy dans `app/models/`, schémas Pydantic dans `app/schemas/`
- Services dans `app/services/`, routers dans `app/routers/`
- Dépendance `get_db` pour les sessions SQLAlchemy
- Dépendance `get_current_user` pour l'authentification
- Migrations Alembic dans `backend/alembic/versions/`
- Tests pytest dans `backend/tests/`
- Pas de dépendances inutiles
- Logique "minimal but functional"
- Ne pas exposer dans les logs : mots de passe, tokens, documents privés

## Mission

Implémenter la couche de persistance pour :
1. **Conversations** — table `conversations`
2. **Messages** — table `messages`
3. **Référentiel actif** — table `user_domain_referentiels` + champ `referentiel_actif` sur `conversations`
4. **Historique contextuel** — récupération du contexte de conversation pour les appels LLM
5. **Résumé `.md`** — champ `resume_md` sur `conversations` pour le résumé du contexte

## Spécification fonctionnelle

### 1. Modèles SQLAlchemy

#### `Conversation` (table `conversations`)

```python
class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    titre: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    referentiel_actif: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resume_md: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relations
    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
```

#### `Message` (table `messages`)

```python
class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' | 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    domaine_detecte: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sous_theme_detecte: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mode_utilise: Mapped[str] = mapped_column(String(20), nullable=False, default="explique_moi")
    sources_rag: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
```

#### `UserDomainReferentiel` (table `user_domain_referentiels`)

```python
class UserDomainReferentiel(Base):
    __tablename__ = "user_domain_referentiels"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True, nullable=False)
    domaine_id: Mapped[str] = mapped_column(String(50), primary_key=True, nullable=False)
    referentiel: Mapped[str] = mapped_column(String(50), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

#### Mise à jour du modèle `User`

Ajouter la relation inverse :
```python
conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")
```

#### Mise à jour de `app/models/__init__.py`

Exporter `Conversation`, `Message`, `UserDomainReferentiel` en plus de `User`.

### 2. Schémas Pydantic

#### `app/schemas/conversation.py`

```python
class ConversationCreate(BaseModel):
    titre: str | None = None  # Si None, auto-généré à partir du premier message

class ConversationUpdate(BaseModel):
    titre: str | None = None
    referentiel_actif: str | None = None

class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    titre: str
    referentiel_actif: str | None
    resume_md: str | None
    created_at: datetime
    updated_at: datetime

class MessageCreate(BaseModel):
    role: str  # 'user' | 'assistant'
    content: str
    domaine_detecte: str | None = None
    sous_theme_detecte: str | None = None
    mode_utilise: str = "explique_moi"
    sources_rag: list[str] | None = None

class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    conversation_id: int
    role: str
    content: str
    domaine_detecte: str | None
    sous_theme_detecte: str | None
    mode_utilise: str
    sources_rag: list[str] | None
    created_at: datetime

class ConversationDetailRead(ConversationRead):
    messages: list[MessageRead] = []

class UserDomainReferentielRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    domaine_id: str
    referentiel: str
    updated_at: datetime
```

#### Mise à jour de `app/schemas/chat.py`

Ajouter `conversation_id` optionnel à `ChatMessageRequest` :
```python
class ChatMessageRequest(BaseModel):
    question: str = Field(..., min_length=1)
    historique: str | None = None
    conversation_id: int | None = None  # Nouveau : optionnel pour rétrocompatibilité
```

### 3. Service de conversation — `app/services/conversations.py`

```python
def create_conversation(db: Session, user_id: int, titre: str | None = None) -> Conversation
def get_conversation(db: Session, conversation_id: int, user_id: int) -> Conversation | None
def list_conversations(db: Session, user_id: int) -> list[Conversation]
def update_conversation(db: Session, conversation: Conversation, updates: ConversationUpdate) -> Conversation
def delete_conversation(db: Session, conversation: Conversation) -> None
def add_message(db: Session, conversation_id: int, role: str, content: str, **kwargs) -> Message
def list_messages(db: Session, conversation_id: int) -> list[Message]
def get_referentiel_for_domain(db: Session, user_id: int, domaine_id: str) -> str | None
def set_referentiel_for_domain(db: Session, user_id: int, domaine_id: str, referentiel: str) -> UserDomainReferentiel
def build_conversation_context(db: Session, conversation: Conversation) -> str
```

#### `build_conversation_context`

Construit le contexte à injecter dans le prompt LLM :
1. Si `conversation.resume_md` existe → l'utiliser comme contexte principal
2. Sinon → récupérer les N derniers messages (ex. 10) et les formater
3. Ajouter le `referentiel_actif` si présent

Format du contexte :
```
[Conversation context]
Referentiel actif: OHADA
Resume: <resume_md ou messages précédents formatés>
[/Conversation context]
```

### 4. Router — `app/routers/conversations.py`

```
GET    /conversations                     → Liste des conversations de l'utilisateur
POST   /conversations                     → Créer une nouvelle conversation
GET    /conversations/{id}                → Détail d'une conversation (avec messages)
PATCH  /conversations/{id}                → Modifier (titre, referentiel_actif)
DELETE /conversations/{id}                → Supprimer une conversation
GET    /conversations/{id}/messages       → Historique des messages
POST   /conversations/{id}/messages       → Envoyer un message dans une conversation
POST   /conversations/{id}/resume         → Générer le résumé .md (manuel)
```

Toutes les routes doivent être protégées par `get_current_user` et vérifier que la conversation appartient bien à l'utilisateur connecté (404 si non trouvée ou non autorisée).

#### `POST /conversations/{id}/messages`

Ce endpoint doit :
1. Vérifier que la conversation appartient à l'utilisateur
2. Appeler la même logique que `/chat/message` (classification + génération ou clarification)
3. Persister le message utilisateur et la réponse assistant dans la conversation
4. Mettre à jour `referentiel_actif` si la classification a déterminé un référentiel
5. Mettre à jour `user_domain_referentiels` avec le référentiel choisi
6. Si le titre est vide, le générer à partir du premier message (tronqué à 50 caractères)
7. Retourner la même réponse que `/chat/message` + `conversation_id`

### 5. Intégration avec `/chat/message`

Modifier `app/routers/chat.py` :
- Si `payload.conversation_id` est fourni :
  - Vérifier que la conversation appartient à l'utilisateur (404 si non)
  - Récupérer le contexte de la conversation (`build_conversation_context`)
  - Passer ce contexte à `classify` et `generate_answer` comme `historique`
  - Persister le message utilisateur et la réponse
  - Mettre à jour `referentiel_actif` et `user_domain_referentiels`
  - Si le titre est vide, le générer à partir du premier message
- Si `payload.conversation_id` est absent : comportement actuel (sans persistance)

### 6. Génération du résumé `.md`

Créer `app/services/resume_service.py` :

```python
def generate_resume(db: Session, conversation: Conversation) -> str:
    """Generate a markdown summary of the conversation context."""
    # Récupérer tous les messages de la conversation
    # Construire un prompt de résumé avec un LLM dédié
    # Le résumé doit contenir :
    #   - Les principaux points de la discussion
    #   - La situation de départ
    #   - La suite logique
    #   - Le référentiel actif
    #   - Le domaine / sous-thème en cours
    #   - Les sources RAG utilisées (si mode "Mes cours")
    #   - La langue de la conversation
    # Mettre à jour conversation.resume_md
    # Retourner le résumé
```

Le prompt de résumé doit être un template markdown dans `app/prompts/templates/resume.md` :
```markdown
You are a conversation summarizer for Dexter, an educational chatbot.
Summarize the following conversation in a structured markdown format.

## Conversation Summary

### Situation de départ
<what was the initial context>

### Principaux points
- <key point 1>
- <key point 2>
- ...

### Suite logique
<what should happen next>

### Métadonnées
- Référentiel actif: <referentiel or "Non spécifié">
- Domaine: <domaine or "Non spécifié">
- Sous-thème: <sous_theme or "Non spécifié">
- Langue: <langue>
- Sources RAG: <sources or "Aucune">

## Messages
<conversation messages>
```

### 7. Migration Alembic

Créer `backend/alembic/versions/202409020000_conversations.py` :
- Table `conversations` (id, user_id FK, titre, referentiel_actif, resume_md, created_at, updated_at)
- Table `messages` (id, conversation_id FK, role, content, domaine_detecte, sous_theme_detecte, mode_utilise, sources_rag JSON, created_at)
- Table `user_domain_referentiels` (user_id FK, domaine_id, referentiel, updated_at, PK composite)
- Index sur `conversations.user_id`, `messages.conversation_id`
- Foreign keys avec `ondelete="CASCADE"` pour les relations

### 8. Tests ciblés

Créer `backend/tests/test_conversations.py` avec les tests suivants :

1. `test_create_conversation` — créer une conversation, vérifier le titre auto-généré
2. `test_list_conversations` — lister les conversations de l'utilisateur
3. `test_get_conversation_detail` — récupérer une conversation avec ses messages
4. `test_update_conversation` — modifier titre et référentiel_actif
5. `test_delete_conversation` — supprimer une conversation
6. `test_add_message_to_conversation` — ajouter un message à une conversation
7. `test_conversation_belongs_to_user` — 404 si la conversation n'appartient pas à l'utilisateur
8. `test_chat_message_with_conversation_id` — envoyer un message avec conversation_id, vérifier la persistance
9. `test_chat_message_without_conversation_id` — comportement actuel sans persistance
10. `test_referentiel_actif_updated` — vérifier que le référentiel actif est mis à jour après une réponse
11. `test_user_domain_referentiel` — vérifier la table user_domain_referentiels
12. `test_generate_resume` — générer le résumé .md (mock LLM)

### 9. Mise à jour de `app/main.py`

Inclure le nouveau router :
```python
from app.routers.conversations import router as conversations_router
app.include_router(conversations_router)
```

## Contraintes

- Respecter strictement le PRD et les conventions du projet
- Ne pas hardcoder une liste figée de domaines
- Garder le code et les commentaires en anglais
- Répondre en français dans le chat, mais en anglais dans le code
- Éviter les dépendances inutiles
- Respecter la logique "minimal but functional"
- Ne pas toucher à la documentation sans nécessité
- Ne pas exposer dans les logs : mots de passe, tokens, documents privés
- Ne pas implémenter le RAG avant la persistance de conversation
- Ne pas ajouter de dépendances inutiles
- Ne pas inventer une architecture surdimensionnée
- Ne pas déclarer la tâche terminée sans vérification

## Livrables attendus

- Modèles SQLAlchemy : `Conversation`, `Message`, `UserDomainReferentiel`
- Schémas Pydantic : `conversation.py`
- Service de conversation : `conversations.py`
- Service de résumé : `resume_service.py`
- Router : `conversations.py`
- Migration Alembic : `202409020000_conversations.py`
- Mise à jour de `chat.py` pour l'intégration avec `conversation_id`
- Mise à jour de `chat.py` pour la persistance des messages
- Mise à jour de `models/__init__.py` et `models/user.py`
- Mise à jour de `schemas/chat.py` (ajout `conversation_id`)
- Template de résumé : `prompts/templates/resume.md`
- Tests : `tests/test_conversations.py`
- Validation : pytest 8/8 existants + nouveaux tests passent

## Ordre de travail recommandé

1. Modèles SQLAlchemy + migration Alembic
2. Schémas Pydantic
3. Service de conversation
4. Router de conversation
5. Intégration avec `/chat/message`
6. Service de résumé + template
7. Tests
8. Validation complète (pytest)