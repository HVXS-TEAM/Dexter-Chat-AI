# Prompt Copilot — RAG / Documents

## Contexte

Projet : Dexter Chat AI — chatbot pédagogique pour étudiants et professeurs.
Stack : Python + FastAPI, SQLAlchemy, Alembic, PostgreSQL + pgvector, React + TypeScript.
Documentation de référence : `Documentation Dexter/dexter-prd.md` (sections §4.2, §4.3, §8.1, §9, §12.3).
Règles projet : `AGENTS.md` et `cline.md`.

## État actuel du code

Le backend est fonctionnel avec :
- Authentification complète (JWT, bcrypt, rôles étudiant/professeur)
- Détection générique de domaine / sous-thème / référentiel / intention / langue
- Génération pédagogique spécialisée par domaine (templates markdown)
- Conversations persistantes (tables `conversations`, `messages`, `user_domain_referentiels`)
- Route `/chat/message` avec `conversation_id` optionnel (persistance + contexte conversationnel)
- Résumé `.md` de conversation (champ `resume_md`, route `POST /conversations/{id}/resume`)
- Tests pytest 18/18 passés

### Dépendances RAG déjà installées

- `sentence-transformers` (modèle d'embedding multilingue)
- `PyPDF2` (extraction PDF)
- `python-docx` (extraction DOCX)
- `python-pptx` (extraction PPTX)
- `Pillow` (images)
- `pytesseract` (OCR pour images scannées)

### Structure existante pertinente

```
backend/app/
├── main.py              # FastAPI app, inclut auth_router, users_router, chat_router, conversations_router
├── config.py            # Settings pydantic-settings
├── models/
│   ├── __init__.py      # Base + exports User, Conversation, Message, UserDomainReferentiel
│   ├── user.py          # Modèle User
│   └── conversation.py  # Modèles Conversation, Message, UserDomainReferentiel
├── schemas/
│   ├── chat.py          # ChatMessageRequest (conversation_id optionnel)
│   └── conversation.py  # Schémas conversations
├── services/
│   ├── conversations.py # CRUD conversations, build_conversation_context
│   ├── classifier.py    # Classification de domaine
│   └── chat_service.py  # Génération de réponse pédagogique
├── routers/
│   ├── chat.py          # /chat/classify, /chat/message
│   └── conversations.py # /conversations CRUD + messages + resume
├── domains/
│   ├── domains.json     # Configuration des domaines (comptabilite, finance)
│   └── loader.py        # list_domains, get_domain, domain_prompt_context
└── llm/
    ├── provider.py      # Interface LLMProvider
    └── openai_compatible.py  # Implémentation OpenAI-compatible (httpx)
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
- Accès multi-utilisateurs : toute ressource vérifiée comme appartenant à l'utilisateur (404 sinon)

## Décisions déjà actées (avec l'utilisateur)

1. **Modèle d'embedding** : `intfloat/multilingual-e5-small` (384 dims, open-source, multilingue FR/EN)
2. **Formats de documents** : PDF, DOCX, PPTX, images (OCR via pytesseract), TXT/MD
3. **Fenêtre de contexte** : 5 chunks maximum injectés dans une réponse
4. **Ré-indexation** : remplacer les anciens chunks quand un document est ré-uploadé
5. **Seuil de pertinence** : score ≥ 0.5 (similarité cosinus) pour basculer en mode "Mes cours" ; sinon "Explique-moi"

## Mission

Implémenter la couche RAG / documents :
1. **Modèles SQLAlchemy** : `Document`, `DocumentChunk` (avec embedding pgvector)
2. **Extraction de texte** : service multi-formats (PDF, DOCX, PPTX, images OCR, TXT/MD)
3. **Chunking** : découpage intelligent par paragraphes/sections
4. **Embedding** : vectorisation via `sentence-transformers`
5. **Recherche vectorielle** : récupération des chunks pertinents (pgvector)
6. **Intégration chat** : mode "Mes cours" vs "Explique-moi" avec transparence de source
7. **Routes API** : conformes PRD §12.3

## Spécification fonctionnelle

### 1. Modèles SQLAlchemy

#### `Document` (table `documents`) — conformément à PRD §8.1

```python
class Document(Base):
    """A user-uploaded document attached to a conversation."""
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True, nullable=False)
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    type_fichier: Mapped[str] = mapped_column(String(50), nullable=False)  # pdf, docx, pptx, image, txt, md
    domaine_associe: Mapped[str | None] = mapped_column(String(50), nullable=True)  # détecté par classify
    visibilite: Mapped[str] = mapped_column(String(20), nullable=False, default="prive")  # 'prive' | 'partage_classe'
    fichier_url: Mapped[str] = mapped_column(String(500), nullable=False)
    statut_indexation: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending | indexe | erreur
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    owner: Mapped["User"] = relationship(back_populates="documents")
    conversation: Mapped["Conversation"] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
```

#### `DocumentChunk` (table `document_chunks`) — avec embedding pgvector

```python
from pgvector.sqlalchemy import Vector

class DocumentChunk(Base):
    """A vectorized chunk of a document for RAG retrieval."""
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True, nullable=False)
    contenu_texte: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(384), nullable=False)  # intfloat/multilingual-e5-small
    page_ou_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document: Mapped["Document"] = relationship(back_populates="chunks")
```

#### Mise à jour des modèles existants

- `User` : ajouter `documents: Mapped[list["Document"]] = relationship(back_populates="owner", cascade="all, delete-orphan")`
- `Conversation` : ajouter `documents: Mapped[list["Document"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")`
- `Message` : le champ `sources_rag` (JSON) stocke déjà les ids des chunks utilisés — sera alimenté par le RAG
- `models/__init__.py` : exporter `Document`, `DocumentChunk`

### 2. Schémas Pydantic — `app/schemas/document.py`

```python
class DocumentRead(BaseModel):
    """Document payload returned by the API."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_id: int
    conversation_id: int
    titre: str
    type_fichier: str
    domaine_associe: str | None
    visibilite: str
    fichier_url: str
    statut_indexation: str
    created_at: datetime

class DocumentVisibilityUpdate(BaseModel):
    """Payload to change document visibility."""
    visibilite: Literal["prive", "partage_classe"]

class DocumentIndexStatus(BaseModel):
    """Document detail with indexing status."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    titre: str
    type_fichier: str
    domaine_associe: str | None
    statut_indexation: str
    nombre_chunks: int = 0
    created_at: datetime
```

### 3. Service d'extraction de texte — `app/services/document_extractor.py`

```python
def extract_text(filename: str, file_bytes: bytes) -> str:
    """Extract plain text from a supported document type.

    Supported: .pdf, .docx, .pptx, .png/.jpg/.jpeg (OCR via pytesseract), .txt, .md
    Raises ValueError for unsupported types or extraction failures.
    """
```

Implémentation :
- **PDF** : `PyPDF2.PdfReader` — concaténer le texte de chaque page, suivre le numéro de page
- **DOCX** : `docx.Document` — concaténer les paragraphes + tableaux
- **PPTX** : `pptx.Presentation` — concaténer le texte de chaque slide, suivre le numéro de slide
- **Image** : `PIL.Image.open` + `pytesseract.image_to_string` (OCR)
- **TXT/MD** : décoder `utf-8` (fallback `latin-1`)
- Gérer les erreurs explicitement (jamais de `except` silencieux — règle 6 AGENTS.md)

### 4. Service de chunking — `app/services/document_chunker.py`

```python
def chunk_text(text: str, max_chars: int = 800, overlap: int = 100) -> list[tuple[str, int]]:
    """Split text into coherent chunks by paragraph/section.

    Returns a list of (chunk_text, position) tuples.
    - Split on double newlines (paragraphs) first
    - Merge small paragraphs up to max_chars
    - Split oversized paragraphs at sentence boundaries or max_chars
    - Add overlap between chunks to preserve context
    """
```

Logique :
1. Découper par paragraphes (séparateur `\n\n`)
2. Fusionner les petits paragraphes jusqu'à ~max_chars
3. Si un paragraphe dépasse max_chars, le découper aux limites de phrases (`.`, `!`, `?`) ou à max_chars en dernier recours
4. Chevaucher les chunks de ~overlap caractères pour préserver le contexte
5. Retourner aussi la position (index du chunk) pour `page_ou_position`

### 5. Service d'embedding — `app/services/embedding_service.py`

```python
from sentence_transformers import SentenceTransformer

_model_cache: SentenceTransformer | None = None

def get_embedding_model() -> SentenceTransformer:
    """Load and cache the multilingual E5 small model."""
    global _model_cache
    if _model_cache is None:
        _model_cache = SentenceTransformer("intfloat/multilingual-e5-small")
    return _model_cache

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts into 384-dim vectors."""
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return [embedding.tolist() for embedding in embeddings]

def embed_text(text: str) -> list[float]:
    """Embed a single text."""
    return embed_texts([text])[0]
```

Note : importer `SentenceTransformer` **lazily** (dans la fonction, pas en top-level) pour éviter le chargement du modèle au démarrage de l'application.

### 6. Service RAG — `app/services/rag_service.py`

```python
def index_document(db: Session, document: Document) -> Document:
    """Extract text, chunk it, embed chunks, and store them.

    1. Extract text from the file (document_extractor)
    2. Detect domain from the text (classifier.classify)
    3. Chunk the text (document_chunker)
    4. Embed the chunks (embedding_service)
    5. Delete existing chunks (re-indexation : remplacer les anciens)
    6. Insert new chunks in document_chunks
    7. Update document.domaine_associe and document.statut_indexation
    """

def search_documents(
    db: Session,
    conversation_id: int,
    question: str,
    limit: int = 5,
    min_score: float = 0.5,
) -> list[tuple[DocumentChunk, float]]:
    """Search vectorized chunks similar to the question.

    Returns (chunk, similarity_score) pairs sorted by score desc,
    restricted to chunks of documents belonging to the conversation,
    and only with score >= min_score.
    """

def format_chunks_context(chunks: list[tuple[DocumentChunk, float]]) -> str:
    """Format retrieved chunks for LLM prompt injection with source traceability."""
```

**Recherche vectorielle avec pgvector :**

```python
from pgvector.sqlalchemy import Vector
from sqlalchemy import select

def search_documents(db, conversation_id, question, limit=5, min_score=0.5):
    # 1. Embed the question
    question_vector = embed_text(question)

    # 2. Get documents of this conversation
    doc_ids = db.query(Document.id).filter(Document.conversation_id == conversation_id).subquery()

    # 3. Cosine similarity search on chunks
    chunks = (
        db.query(DocumentChunk, DocumentChunk.embedding.cosine_distance(question_vector).label("distance"))
        .filter(DocumentChunk.document_id.in_(doc_ids))
        .order_by("distance")
        .limit(limit * 2)  # fetch extra, filter on score after
        .all()
    )

    # 4. Convert distance to similarity (1 - distance) and filter by threshold
    results = []
    for chunk, distance in chunks:
        score = 1.0 - float(distance)
        if score >= min_score:
            results.append((chunk, score))
        if len(results) >= limit:
            break
    return results
```

### 7. Intégration avec le chat — `app/routers/chat.py` et `app/services/chat_service.py`

#### Nouveau flux dans `POST /chat/message` (avec `conversation_id` présent) :

1. Classifier la question (comportement actuel)
2. **Nouveau** : si `conversation_id` est fourni → `search_documents(db, conversation_id, question)` :
   - Si des chunks pertinents trouvés (score ≥ 0.5) → **mode "mes_cours"** :
     - Injecter les chunks formatés dans le prompt de génération
     - Stocker les ids des chunks dans `message.sources_rag`
     - `mode_utilise = "mes_cours"` sur le message
   - Sinon → mode "explique_moi" (comportement actuel)
3. Persister les messages avec les métadonnées RAG

#### Transparence de source (PRD §4.2 / §9.3) :

- Le prompt de génération doit indiquer au modèle de signaler la source.
- Mode "mes_cours" : « D'après tes notes de cours... » / "According to your course notes..."
- Mode "explique_moi" : « De manière générale... » / "In general..."
- Les ids des chunks utilisés sont persistés sur le message assistant (`sources_rag`)

#### Template de prompt RAG — `app/prompts/templates/rag_context.md` :

```markdown
You have access to the following excerpts from the user's course documents.
Use them to ground your answer. If the excerpts are not relevant, say so.

## Course excerpts
$chunks

## User's question
$question

Answer in $langue, adapted for a $profil. Explicitly indicate when your answer
is based on the course documents ("D'après tes notes de cours...") vs. general
knowledge ("De manière générale...").
```

Le service `chat_service.generate_answer` doit être étendu pour accepter des chunks RAG optionnels et injecter le template `rag_context.md` dans le prompt si présent.

### 8. Routes API — `app/routers/documents.py`

```
POST   /conversations/{id}/documents        → Upload un document dans une conversation (multipart/form-data)
GET    /conversations/{id}/documents        → Liste des documents de la conversation
GET    /documents/{id}                      → Détail d'un document (statut indexation, nombre chunks, domaine)
PATCH  /documents/{id}/visibility           → Changer visibilité (réservé aux professeurs — 403 pour étudiants)
DELETE /documents/{id}                      → Supprimer un document (et ses chunks)
```

**Contraintes :**
- Toutes les routes protégées par `get_current_user`
- Vérifier l'appartenance : 404 si le document/conversation n'appartient pas à l'utilisateur
- `PATCH /documents/{id}/visibility` : 403 si `current_user.role != "professeur"` (PRD §4.3)
- Upload : accepter `UploadFile`, lire les bytes, valider l'extension supportée, créer le `Document`, puis lancer l'indexation (synchrone pour MVP — tâche asynchrone en V1)
- Stocker le fichier dans `backend/uploads/` (répertoire à créer, gitignoré) avec un nom sécurisé : `{uuid}_{nom_original}`
- Mettre à jour `fichier_url` avec le chemin relatif

### 9. Migration Alembic — `backend/alembic/versions/202409030000_documents.py`

- Table `documents` (id, owner_id FK, conversation_id FK, titre, type_fichier, domaine_associe, visibilite, fichier_url, statut_indexation, created_at)
- Table `document_chunks` (id, document_id FK, contenu_texte, embedding vector(384), page_ou_position, created_at)
- Index sur `documents.owner_id`, `documents.conversation_id`, `document_chunks.document_id`
- Foreign keys avec `ondelete="CASCADE"`
- Exécuter `CREATE EXTENSION IF NOT EXISTS vector` dans la migration (pgvector)

### 10. Configuration

Ajouter à `backend/app/config.py` :
```python
embedding_model: str = "intfloat/multilingual-e5-small"
rag_min_score: float = 0.5
rag_max_chunks: int = 5
upload_dir: str = "uploads"
```

Ajouter à `.env.example` :
```
EMBEDDING_MODEL=intfloat/multilingual-e5-small
RAG_MIN_SCORE=0.5
RAG_MAX_CHUNKS=5
UPLOAD_DIR=uploads
```

### 11. Tests ciblés — `backend/tests/test_documents.py`

1. `test_upload_document_txt` — upload d'un fichier .txt, vérifier le Document créé
2. `test_upload_document_unsupported` — upload d'un type non supporté → 400
3. `test_list_documents` — lister les documents d'une conversation
4. `test_document_detail` — détail d'un document avec statut d'indexation
5. `test_upload_document_access_denied` — 404 si on upload dans la conversation d'un autre utilisateur
6. `test_document_visibility_professor` — professeur peut changer la visibilité → 200
7. `test_document_visibility_student` — étudiant ne peut pas changer la visibilité → 403
8. `test_delete_document` — supprimer un document et ses chunks
9. `test_chunk_text` — unit test du chunker (découpe, fusion, chevauchement)
10. `test_extract_text_txt` — unit test de l'extracteur sur du texte brut
11. `test_search_documents` — mock de l'embedding, vérifier le retour des chunks pertinents
12. `test_chat_message_rag_mode` — mock du RAG : avec chunks pertinents → mode "mes_cours", `sources_rag` rempli
13. `test_chat_message_no_rag` — mock du RAG sans chunks pertinents → mode "explique_moi"

### 12. Mise à jour de `app/main.py`

Inclure le nouveau router :
```python
from app.routers.documents import router as documents_router
app.include_router(documents_router)
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
- Jamais de `except` silencieux ou de `pass` qui avale une exception
- Ne pas déclarer la tâche terminée sans vérification
- Import lazy de `sentence_transformers` (pas au top-level, sinon le modèle se charge au démarrage)

## Livrables attendus

- Modèles SQLAlchemy : `Document`, `DocumentChunk` + relations sur User/Conversation
- Schémas Pydantic : `document.py`
- Services : `document_extractor.py`, `document_chunker.py`, `embedding_service.py`, `rag_service.py`
- Router : `documents.py`
- Migration Alembic : `202409030000_documents.py`
- Template : `prompts/templates/rag_context.md`
- Mise à jour : `chat.py` (mode RAG), `chat_service.py` (injection chunks), `config.py`, `main.py`, `models/__init__.py`
- Répertoire `backend/uploads/` à créer (et ajouter à `.gitignore`)
- Tests : `tests/test_documents.py`
- Validation : pytest 18/18 existants + nouveaux tests passent

## Ordre de travail recommandé

1. Modèles SQLAlchemy + migration Alembic (avec CREATE EXTENSION vector)
2. Schémas Pydantic
3. Service d'extraction de texte (multi-formats)
4. Service de chunking
5. Service d'embedding (sentence-transformers, lazy import)
6. Service RAG (indexation + recherche vectorielle)
7. Router de documents
8. Intégration chat (mode "mes_cours" + transparence source)
9. Tests
10. Validation complète (pytest)