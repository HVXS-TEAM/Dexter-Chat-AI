# Dexter Chat AI

Dexter est une plateforme éducative assistée par IA pour les étudiants et les
enseignants. Elle permet de poser des questions, obtenir des explications
pédagogiques, utiliser des calculateurs vérifiés, exploiter ses documents de
cours avec une recherche RAG, générer des exercices et suivre ses échanges.

Le projet associe une API FastAPI, une interface React/Vite, PostgreSQL avec
pgvector et une couche LLM compatible OpenAI. L'architecture est configurée par
les données : les domaines, mots-clés, sous-thèmes et référentiels sont chargés
depuis des fichiers de configuration plutôt que codés dans les services métier.

## Fonctionnalités

### Backend

- inscription, connexion, JWT access/refresh et profil utilisateur ;
- rôles étudiant et professeur avec contrôle d'accès aux ressources ;
- classification générique du domaine, du sous-thème, de l'intention et du référentiel ;
- chat pédagogique via `POST /chat/message` ;
- clarification explicite lorsqu'un référentiel ou un paramètre manque ;
- calculs déterministes vérifiés avant leur explication par le LLM ;
- conversations persistantes, titres automatiques, messages et résumés ;
- upload et indexation de fichiers PDF, DOCX, PPTX, TXT, Markdown et images OCR ;
- recherche vectorielle pgvector intégrée au chat ;
- partage de documents réservé aux professeurs propriétaires ;
- génération, soumission, correction et progression des quiz ;
- création de classes, code d'invitation et adhésion des étudiants ;
- catalogue public des domaines via `GET /domains` ;
- calculateurs exposés par domaine via `/calculators`.

### Frontend

- React 19 + TypeScript strict + Vite ;
- routage avec `react-router-dom` ;
- thème sombre et thème clair issus des maquettes Dexter ;
- persistance du thème avec la clé `dexter-theme` ;
- layout responsive avec sidebar desktop, rail tablette et navigation mobile ;
- écran d'accueil avec suggestions, chargement des domaines et états d'erreur ;
- écran de chat avec bulles utilisateur/assistant, modes, clarification, calcul
	vérifié et gestion des erreurs d'authentification ;
- logo Dexter et icône navigateur depuis `DexterIcons.ico` ;
- aucune dépendance frontend ajoutée pour les étapes A1-A3 au-delà de la stack prévue.

## Architecture

```text
Dexter Chat AI/
├── backend/
│   ├── app/
│   │   ├── auth/             # JWT, sécurité et dépendances d'authentification
│   │   ├── db/               # sessions SQLAlchemy
│   │   ├── domains/          # catalogue piloté par domains.json
│   │   ├── llm/              # abstraction LLM et provider compatible OpenAI
│   │   ├── models/           # utilisateurs, conversations, documents, quiz, classes
│   │   ├── routers/          # routes HTTP FastAPI
│   │   ├── schemas/          # contrats Pydantic
│   │   └── services/         # logique métier, RAG, calculs et quiz
│   ├── alembic/              # migrations PostgreSQL
│   ├── tests/                # tests unitaires et fonctionnels
│   ├── requirements.txt
│   └── Dockerfile
├── dexter-calc/              # bibliothèque de calculateurs métier
├── frontend/
│   ├── src/
│   │   ├── components/       # layout partagé
│   │   ├── pages/            # écrans React
│   │   └── theme/            # ThemeProvider
│   ├── public/               # icônes et assets publics
│   ├── package.json
│   └── Dockerfile
├── stitch_dexter_ai_educational_platform/ # références visuelles et JSON
├── docker-compose.yml
├── .env.example
└── PROGRESS.md
```

## Stack technique

| Couche | Technologie |
|---|---|
| API | Python, FastAPI, Uvicorn |
| Validation | Pydantic 2 |
| ORM et migrations | SQLAlchemy 2, Alembic |
| Base de données | PostgreSQL 16 + pgvector |
| Authentification | JWT, `python-jose`, bcrypt |
| LLM | Provider OpenAI-compatible via HTTPX |
| RAG | Sentence Transformers, pgvector, extraction multi-format |
| Calculs | Bibliothèque locale `dexter-calc` |
| Interface | React 19, TypeScript, Vite 8 |
| Styles | Tailwind CSS 4 + variables CSS Dexter |
| Icônes | Material Symbols Outlined et `DexterIcons.ico` |

## Domaines

Le système est conçu pour supporter sept domaines de la vision produit :

- comptabilité ;
- finance ;
- marketing ;
- statistique ;
- banque ;
- business ;
- management.

Le catalogue actuellement configuré dans
`backend/app/domains/domains.json` contient le périmètre MVP actif :
**Comptabilité** et **Finance**. Les autres domaines peuvent être ajoutés par
configuration sans modifier le routeur ni les services métier.

## Routes principales

### Santé et catalogue

| Méthode | Route | Accès | Description |
|---|---|---|---|
| `GET` | `/health` | public | état de l'API |
| `GET` | `/domains` | public | domaines configurés |
| `GET` | `/docs` | public | documentation Swagger |

### Authentification et utilisateurs

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/auth/register` | créer un compte |
| `POST` | `/auth/login` | obtenir les tokens JWT |
| `POST` | `/auth/refresh` | renouveler un access token |
| `GET` | `/users/me` | lire son profil |
| `PATCH` | `/users/me` | modifier son profil |
| `GET` | `/users/me/progress` | lire sa progression quiz |

### Chat et conversations

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/chat/classify` | classifier une question |
| `POST` | `/chat/message` | obtenir une réponse pédagogique ou une clarification |
| `POST` | `/conversations` | créer une conversation |
| `GET` | `/conversations` | lister ses conversations |
| `GET` | `/conversations/{id}` | lire une conversation |
| `PATCH` | `/conversations/{id}` | modifier une conversation |
| `DELETE` | `/conversations/{id}` | supprimer une conversation |
| `GET` | `/conversations/{id}/resume` | générer/lire un résumé |

### Documents, quiz, classes et calculateurs

- Documents : upload par conversation, liste, statut d'indexation, visibilité
	professeur et suppression.
- Quiz : `/quiz/generate`, `/quiz/{id}`, `/quiz/{id}/submit` et progression.
- Classes : `POST /classes`, `GET /classes` et `POST /classes/{id}/join`.
- Calculateurs : `GET /calculators/`, `GET/POST /calculators/{domain}/calculate`
	et `POST /calculators/resolve`.

## Configuration

Copier le modèle d'environnement avant un lancement local :

```powershell
Copy-Item .env.example .env
```

Variables principales :

```dotenv
DB_USER=dexter
DB_PASSWORD=change_me
DB_NAME=dexter
DB_URL=postgresql+psycopg2://dexter:change_me@localhost:5432/dexter
JWT_SECRET=change_me
LLM_API_KEY=change_me
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=qwen/qwen3.8-27b
```

Ne jamais versionner `.env`, les tokens, les mots de passe ou les fichiers
uploadés. Le `.gitignore` racine les exclut.

## Installation native Windows

### Backend

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API : <http://127.0.0.1:8000>  
Swagger : <http://127.0.0.1:8000/docs>

### Frontend

```powershell
Set-Location frontend
npm.cmd install
node node_modules\vite\bin\vite.js --host 127.0.0.1 --port 4173
```

Interface : <http://127.0.0.1:4173>

Dans ce chemin Windows, le caractère `&` peut casser les wrappers `.cmd` de
npm. L'exécution directe des binaires Node est la commande validée dans cet
environnement. Un chemin de projet sans `&` permet de revenir aux scripts npm
classiques.

## Lancement Docker

La stack Docker comprend PostgreSQL avec pgvector, le backend FastAPI et le
frontend Vite :

```powershell
Copy-Item .env.example .env.docker
docker compose up --build
```

Services prévus :

- PostgreSQL/pgvector : `localhost:5432` ;
- backend : `localhost:8000` ;
- frontend : `localhost:5173`.

Le code et les Dockerfiles sont prêts pour cette exécution. Sur la machine de
développement Windows utilisée pour le projet, Docker Desktop/WSL2 est bloqué
par une erreur de maintenance Windows (`0x800f0922`). Le mode natif est donc le
mode de validation courant ; cela ne change pas l'architecture de la stack.

## Tests et validation

Tests backend ciblés :

```powershell
Set-Location backend
pytest
pytest tests/test_auth_flow.py
pytest tests/test_quiz.py
pytest tests/test_classes.py tests/test_classes_service.py
```

Validation de la bibliothèque de calcul :

```powershell
Set-Location dexter-calc
pytest
```

Build frontend :

```powershell
Set-Location frontend
node node_modules\typescript\bin\tsc -b
node node_modules\vite\bin\vite.js build
```

Les cycles de validation documentés dans `PROGRESS.md` couvrent notamment
l'authentification, le chat, le RAG, les calculateurs, les quiz et les classes.

## Sécurité et règles métier

- les routes utilisateur vérifient la propriété de la ressource ;
- les mots de passe sont hachés et ne sont jamais renvoyés ;
- les documents sont privés par défaut ;
- seul le professeur propriétaire peut partager un document ;
- les codes d'invitation de classe ne sont pas exposés aux étudiants ;
- les quiz masquent le corrigé avant soumission ;
- les calculs sont réalisés par `dexter-calc` avant explication par le LLM ;
- les paramètres manquants déclenchent une clarification explicite, jamais un
	résultat inventé ;
- les erreurs d'authentification, de LLM, d'indexation et de validation sont
	renvoyées avec un statut HTTP adapté.

## Références visuelles

Le dossier `stitch_dexter_ai_educational_platform/` contient les maquettes
Dexter sombres et claires, les `DESIGN.md`, les `code.html`, les captures
`screen.png` et les JSON de reproduction. Ces références définissent les
tokens, la grille, les rayons, la typographie, les composants et les règles de
fidélité visuelle du frontend.

## État du projet

Le socle fonctionnel est opérationnel sur son périmètre MVP : API, base de
données, authentification, chat, calculs, documents/RAG, quiz, classes et
frontend sont intégrés. Les extensions prévues concernent principalement
l'élargissement du catalogue aux sept domaines, l'authentification frontend
complète, les évolutions UX des écrans restants, l'indexation asynchrone des
documents et la reprise Docker après réparation de l'environnement Windows.

Pour le suivi détaillé des décisions, validations et écarts connus, consulter
[`PROGRESS.md`](PROGRESS.md) et [`RESUME_PROJET.md`](RESUME_PROJET.md).
