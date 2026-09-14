# PROMPT COPLIOT — Phase MVP : Authentification

Copie ce bloc dans GitHub Copilot (VS Code) pour la génération. Contexte : le socle Phase 0 est en place et vérifié, PostgreSQL + pgvector tournent en local.

---

## Contexte

Projet **Dexter** — chatbot tuteur IA (backend FastAPI + frontend React). Le socle Phase 0 est déjà en place et fonctionnel :

- `backend/app/main.py` (FastAPI + `GET /health`), `backend/app/config.py` (Settings pydantic-settings lisant `.env` à la racine via `settings.db_url`, `settings.jwt_secret`)
- Packages vides avec `__init__.py` : `backend/app/auth/`, `models/`, `schemas/`, `routers/`, `services/`, `db/`
- Dépendances déjà installées dans `backend\.venv` : fastapi, uvicorn[standard], sqlalchemy, alembic, pydantic, pydantic-settings, python-jose[cryptography], passlib[bcrypt] (bcrypt==4.0.1), psycopg2-binary, pgvector, python-dotenv
- **PostgreSQL 16.10 tourne en local** : hôte `localhost:5432`, base `dexter`, utilisateur `dexter` (mot de passe `dexter_dev`), extension `vector` activée. `.env` racine fourni (DB_URL, JWT_SECRET en valeurs de dev).
- Python du venv : `backend\.venv\Scripts\python.exe` (utilise-le pour alembic et les tests)

## Tâche : implémenter l'authentification complète

Endpoints REST (convention PRD §12.1) :

1. **POST /auth/register** — inscription : email, mot de passe, rôle (`etudiant` | `professeur`), champs optionnels selon rôle (étudiant : filiere, annee ; professeur : matieres_enseignees, etablissement). Hachage du mot de passe (passlib/bcrypt). Email dupliqué → 400 explicite.
2. **POST /auth/login** — vérifie email + mot de passe → retourne `access_token` (durée courte, 30 min) + `refresh_token` (durée longue, 7 jours), JWT (python-jose).
3. **POST /auth/refresh** — échange un refresh token valide contre une nouvelle paire de tokens.
4. **GET /users/me** — profil de l'utilisateur connecté (protégé par access token Bearer).
5. **PATCH /users/me** — mise à jour des champs optionnels du profil (langue_preferee, filiere, matieres_enseignees, etablissement, etc.).

## Modèle de données (PRD §8.1 — noms de champs imposés)

Table `users` : `id` (PK), `email` (unique, index), `password_hash`, `role` ('etudiant' | 'professeur'), `langue_preferee`, `filiere`, `matieres_enseignees`, `etablissement`, `created_at`.

## Structure à générer

- `backend/app/models/user.py` + mise à jour `backend/app/models/__init__.py` : Base SQLAlchemy (déclarative) et modèle User
- `backend/app/db/session.py` : moteur SQLAlchemy depuis `settings.db_url` + `SessionLocal` + fonction `get_db()` (dépendance FastAPI)
- `backend/app/schemas/user.py` : schémas Pydantic (UserCreate, UserLogin, UserUpdate, UserRead, TokenPair) avec validation (email, longueur mot de passe min 8)
- `backend/app/auth/security.py` : hachage/vérification bcrypt + création/vérification JWT (python-jose, access + refresh)
- `backend/app/auth/dependencies.py` : dépendance `get_current_user` (extrait et valide le Bearer token, charge l'utilisateur depuis la DB)
- `backend/app/services/users.py` : logique métier (créer, récupérer par email, récupérer par id, mettre à jour)
- `backend/app/routers/auth.py` : register / login / refresh
- `backend/app/routers/users.py` : GET + PATCH /users/me
- `backend/app/main.py` : inclure les deux routers (ne pas casser `GET /health`)
- **Alembic** : `alembic.ini`, `backend/alembic/env.py` (import du modèle User + `settings.db_url`), `backend/alembic/versions/xxxx_initial.py` (création table `users`). Prévois aussi la commande à exécuter avec le venv : `backend\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head` (depuis `backend/`).

## Conventions impératives

- **Code, variables, fonctions, commentaires en ANGLAIS.** Docstrings courtes sur toute fonction non triviale. Type hints stricts partout (Pydantic pour les schémas API). Un fichier = une responsabilité.
- **Secrets jamais en dur** : tout vient de `.env` via `app/config.py` (settings.jwt_secret, settings.db_url…).
- **Aucune nouvelle dépendance** : utiliser uniquement les paquets déjà installés (liste ci-dessus).
- **Sécurité** : jamais de mot de passe renvoyé ni loggé ; vérifier l'appartenance de la ressource (pas de faille d'autorisation horizontale) ; rôles en minuscules.
- **Erreurs explicites** : HTTPException avec codes clairs (400 email déjà utilisé, 401 identifiants invalides / token invalide ou expiré, 422 validation).
- **Ne PAS générer** : logique métier hors authentification, domaines métier (compta/finance), quiz, documents/RAG, code frontend.

## Vérification attendue après génération

1. Le backend démarre : `backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload` (depuis `backend/`) → `GET /health` répond toujours `{"status":"ok"}`
2. La migration Alembic s'applique sans erreur (table `users` créée)
3. Cycle complet fonctionnel : register → login → `GET /users/me` avec le token → PATCH /users/me → refresh

---

⚠️ Après génération, SAUVEGARDE tous les fichiers et dis « analyse » à l'agent d'analyse (DeepSeek Harness) qui vérifiera la conformité au PRD, les conventions et la sécurité avant toute validation.
