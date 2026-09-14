# Prompt Copilot — Classes & adhésion (partage professeur → classe)

## Contexte

Projet : Dexter Chat AI — chatbot pédagogique pour étudiants et professeurs.
Stack : Python + FastAPI, SQLAlchemy, Alembic, PostgreSQL + pgvector, React + TypeScript.
Documentation de référence : `Documentation Dexter/dexter-prd.md` (sections §4.3, §5.3, §8.1, §12.5).
Règles projet : `AGENTS.md` et `cline.md`.

## État actuel du code

Le backend est fonctionnel avec :

- Authentification complète (JWT, bcrypt, rôles `etudiant`/`professeur`)
- Routage `/chat/message` (détection domaine/sous-thème/référentiel/intention/langue, branches calcul déterministe et RAG)
- Conversations persistantes (`conversations`, `messages`, `user_domain_referentiels`)
- Documents + RAG (`documents`, `document_chunks`, visibilité `prive`/`partage_classe`, partage réservé professeur via `PATCH /documents/{id}/visibility`)
- Quiz/exercices (`quiz_attempts`, `POST /quiz/generate`, `POST /quiz/{id}/submit`, `GET /quiz/{id}`, `GET /users/me/progress`)
- Migrations Alembic jusqu'à `202409040000` (quiz_attempts)
- Tests pytest (modèle : mock de session SQLAlchemy avec dependency override, `DummySession`)

### Structure existante (backend/app)

```
main.py                        # FastAPI app — inclut auth, users, calculators, chat, conversations, documents, quiz
models/
  __init__.py                  # Base (DeclarativeBase) + exports User, Conversation, Message, UserDomainReferentiel, Document, DocumentChunk, QuizAttempt
  user.py                      # User (+ relations conversations, documents, quiz_attempts)
  conversation.py, document.py, quiz.py
schemas/user.py, chat.py, conversation.py, document.py, quiz.py
services/users.py, classifier.py, chat_service.py, chat_calculation.py, rag_service.py, conversations.py, quiz_service.py, calculator_service.py
routers/auth.py, users.py, calculators.py, chat.py, conversations.py, documents.py, quiz.py
auth/dependencies.py           # get_current_user
db/session.py                  # get_db
alembic/versions/              # 202409010000_initial_users, 202409020000_conversations, 202409030000_documents, 202409040000_quiz_attempts
```

### Conventions existantes (à respecter strictement)

- Code, noms de variables/fonctions/classes et docstrings en **anglais**
- Champs de base de données **en français** (noms imposés par le PRD §8.1)
- Type hints systématiques (`Mapped[...]`, `mapped_column`, `str | None`)
- Modèles dans `app/models/`, schémas Pydantic dans `app/schemas/`, services dans `app/services/`, routers dans `app/routers/`
- Dépendances `get_db` (session) et `get_current_user` (auth)
- Migrations Alembic dans `backend/alembic/versions/`
- Tests pytest dans `backend/tests/`
- Pas de dépendances inutiles — logique minimal but functional
- Ne jamais exposer dans les logs ou les réponses : mots de passe, tokens, `code_invitation` d'une classe non possédée par l'appelant
- Jamais d'`except` silencieux : toute erreur est logguée avec contexte et remontée explicitement

## Décisions actées pour cette étape (ne pas dévier)

1. **Code d'invitation unique** : la table `classes` porte un champ `code_invitation` unique,
   généré aléatoirement à la création et partagé par le professeur aux étudiants.
   Écart assumé par rapport au schéma minimal du PRD §8.1, justifié par §12.5
   (« Post /classes/{id}/join — Rejoindre une classe (étudiant, via code d'invitation à définir) »).
2. **Périmètre V1 uniquement** :
   - `POST /classes` — créer une classe (réservé professeur)
   - `GET /classes` — classes du professeur, ou classes rejointes pour un étudiant
   - `POST /classes/{id}/join` — adhésion d'un étudiant via code
   - **NE PAS implémenter** `GET /classes/{id}/progress` : le suivi de progression de classe
     est **V2+** (PRD §5.3 étape 5, §8.3, §11.5). Aucune route, aucun champ dédié.
3. **Rôles** :
   - Créer une classe → `professeur` uniquement, sinon **403** « Only professors can create classes. »
   - Rejoindre une classe → `etudiant` uniquement, sinon **403** « Only students can join a class. »
4. **Sécurité des codes** :
   - `code_invitation` renvoyé uniquement au professeur propriétaire de la classe
     (réponse de création et `GET /classes` côté professeur)
   - Jamais exposé à un étudiant dans les réponses
5. **Erreurs explicites** (pas de masquage, pas d'idempotence silencieuse) :
   - Classe inconnue → **404** « Class not found. »
   - Code invalide → **400** « Invalid invitation code. »
   - Étudiant déjà membre → **400** « Already a member of this class. »

## Spécification fonctionnelle

### 1. Modèles SQLAlchemy — `backend/app/models/classes.py`

```python
class Classe(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    professeur_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    code_invitation: Mapped[str] = mapped_column(String(12), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    professeur: Mapped["User"] = relationship(back_populates="classes_enseignees")
    membres: Mapped[list["ClasseMembre"]] = relationship(
        back_populates="classe", cascade="all, delete-orphan"
    )


class ClasseMembre(Base):
    __tablename__ = "classe_membres"

    classe_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True
    )
    etudiant_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    classe: Mapped["Classe"] = relationship(back_populates="membres")
```

- Ajouter sur `User` (dans `backend/app/models/user.py`) :
  - `classes_enseignees: Mapped[list["Classe"]] = relationship(back_populates="professeur")`
  - `classes_inscrites: Mapped[list["Classe"]] = relationship(secondary="classe_membres", back_populates="etudiants")`
- Enregistrer les deux modèles dans `backend/app/models/__init__.py` et les exporter dans `__all__`.

### 2. Migration Alembic — `backend/alembic/versions/202409050000_classes.py`

- `revision = "202409050000"`, `down_revision = "202409040000"`
- `upgrade()` :
  - créer `classes` (colonnes ci-dessus + FK `professeur_id` → `users.id`, index sur `id`, `professeur_id`, `code_invitation`)
  - créer `classe_membres` (PK composite `(classe_id, etudiant_id)`, FK `classe_id` → `classes.id` CASCADE, FK `etudiant_id` → `users.id` CASCADE)
  - index sur `classe_membres.classe_id` et `classe_membres.etudiant_id`
- `downgrade()` : supprimer `classe_membres` puis `classes` (ordre inverse).

### 3. Schémas Pydantic — `backend/app/schemas/classes.py`

- `ClassCreate { nom: str }` — `nom` non vide (min_length=1 + strip)
- `ClassRead` (professeur) : `id, nom, professeur_id, code_invitation, created_at`
- `ClassReadStudent` (étudiant) : `id, nom, professeur_id, created_at` (pas de `code_invitation`)
- `ClassJoinRequest { code_invitation: str }` — non vide
- `ClassJoinResponse` : classe vue côté étudiant (sans code)

### 4. Service — `backend/app/services/classes.py`

Fonctions (type hints stricts, docstrings anglaises) :

- `generate_invitation_code() -> str` : 8 caractères, alphabet `ABCDEFGHJKMNPQRSTUVWXYZ23456789`
  (sans `I`, `O`, `0`, `1`), via `secrets.choice` — jamais de code prévisible.
- `create_class(db, professeur: User, nom: str) -> Classe` :
  - génère le code, crée, `commit`, `refresh`, retourne la classe
- `list_classes(db, user: User) -> list[Classe]` :
  - `professeur` → classes dont il est propriétaire
  - `etudiant` → classes dont il est membre (join via `classe_membres`)
- `join_class(db, classe: Classe, etudiant: User, code: str) -> Classe` :
  - si l'étudiant est déjà membre → `ValueError("Already a member of this class.")`
  - si code invalide → `ValueError("Invalid invitation code.")`
  - sinon insère la ligne `ClasseMembre` et retourne la classe
- `get_class(db, classe_id: int) -> Classe | None`

### 5. Router — `backend/app/routers/classes.py`

`router = APIRouter(tags=["classes"])` — **pas de préfixe** (chemins complets) :

| Méthode | Chemin | Comportement |
|---|---|---|
| POST | `/classes` | `current_user.role != "professeur"` → 403 ; sinon `create_class`, 201, réponse `ClassRead` (avec code) |
| GET | `/classes` | `professeur` → `ClassRead` ; `etudiant` → `ClassReadStudent` |
| POST | `/classes/{classe_id}/join` | `current_user.role != "etudiant"` → 403 ; classe absente → 404 ; `ValueError` → 400 avec le message ; succès → 200 `ClassJoinResponse` |

- « One thing at a time » : pas d'endpoint supplémentaire (pas de detail, pas de delete, pas de progress).
- Annotations de retour = schéma de réponse réel (jamais le modèle ORM).

### 6. Enregistrement — `backend/app/main.py`

- `from app.routers.classes import router as classes_router`
- `app.include_router(classes_router)` (ligne aux côtés des autres routers)

### 7. Tests pytest — `backend/tests/test_classes.py`

Même patron que `tests/test_quiz.py` : `TestClient(app)`, overrides `get_current_user`/`get_db`,
`DummySession` factice (les tests ne passent **pas** par une vraie base). Mocker
`app.routers.classes.get_class` / `app.services.classes.create_class` etc. selon le besoin.
Couverture minimale :

1. `test_create_class_as_professor_returns_code` — prof → 201, `code_invitation` présent, nom correct
2. `test_create_class_as_student_is_403` — étudiant → 403
3. `test_list_classes_professor_lists_owned` — prof → ses classes (avec code)
4. `test_list_classes_student_lists_joined` — étudiant → classes rejointes, **sans** `code_invitation`
5. `test_join_class_with_valid_code` — étudiant + bon code → 200, membre ajouté
6. `test_join_class_wrong_code_is_400` — étudiant + mauvais code → 400 « Invalid invitation code. »
7. `test_join_class_already_member_is_400` — déjà membre → 400 « Already a member of this class. »
8. `test_join_class_not_found_is_404` — id inconnu → 404
9. `test_join_class_as_professor_is_403` — prof → 403

## Critères de vérification

- `pytest backend/tests/test_classes.py` → **9/9 passed**
- `pytest backend/tests/test_quiz.py backend/tests/test_chat_calcul.py backend/tests/test_chat_message.py backend/tests/test_chat_service.py` → non-régression, **20/20 passed**
- L'application importe et démarre (`from app.main import app` OK), les routes `/classes` apparaissent dans `/docs`
- Aucun `except` silencieux dans le code produit

## Livrables attendus

- `backend/app/models/classes.py` + mise à jour `models/__init__.py` et `models/user.py`
- `backend/alembic/versions/202409050000_classes.py`
- `backend/app/schemas/classes.py`
- `backend/app/services/classes.py`
- `backend/app/routers/classes.py`
- `backend/app/main.py` (1 ligne d'include)
- `backend/tests/test_classes.py`