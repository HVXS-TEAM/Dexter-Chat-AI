# TODO LIST — Dexter Chat AI / Module de calculs par domaine

- [ ]Valider l'architecture du module de calculs multi-domaines avant codage
- [ ] Rédiger la note d'intention suite à validation
- [ ] Analyser où intégrer le module dans Dexter (backend vs package dédié)
- [ ] Définir l'interface commune (base calcul, domaine, entrée/sortie normalisées, traçabilité métier)
- [ ] Préparer contrat de test (pytest) avec exemples chiffrés par domaine
- [ ] Coder le squelette avant le premier cycle Copilot/DSH
- [ ] Mettre à jour PROGRESS.md / suite.md une fois live

<note>
État actuel : Discussion d'architecture (plan = vide). Règle AGENTS.md n°4 : présenter l'intention avant l'action.
</note>

# PROGRESS — Dexter Chat AI

Fichier de suivi d'état réel du projet, mis à jour à chaque étape.

## Décisions actées

- **MVP : 2 domaines** — Comptabilité + Finance (exception pilote)
- **Vision produit : 7 domaines** — ajout progressif des 5 autres après le MVP
- Détection de domaine et routage **génériques, pilotés par configuration** (pas de liste figée en dur)
- **Voie B active (TEMPORAIRE)** : la stack tourne en natif (sans Docker) — Docker reste la cible quand Windows sera réparé

## Contexte Docker / Windows (résolu en Voie B)

- Docker Desktop **ne peut pas s'installer** sur cette machine : le pipeline de maintenance Windows (CBS) échoue au boot (`0x800f0922 CBS_E_INSTALLERS_FAILED`) et annule toute activation de fonctionnalité (WSL2).
- Escalier officiel complet tenté : BITS reset ✅, revertpendingactions ✅, sfc /scannow ✅ (propre), dism restorehealth ✅ (réussi), startcomponentcleanup ✅, réinitialisation composants Windows Update ✅, activation WSL2 via DISM ✅ — **annulation au boot à chaque fois**.
- **Solution durable recommandée** : réparation in situ de Windows 11 (Paramètres → Système → Récupération → « Résoudre les problèmes à l'aide de Windows Update » → « Réinstaller maintenant » — conserve fichiers + applications). À faire quand l'utilisateur le souhaite (~30-60 min).
- `docker-compose.yml` et les Dockerfiles **restent la référence** pour reprendre Docker après réparation de Windows.

## Phase 0 — Socle technique

| Élément | Statut |
|---|---|
| docker-compose.yml (postgres, backend, frontend) | créé — YAML validé — **réservé pour après réparation Windows** |
| backend/requirements.txt | créé — bcrypt pincé (==4.0.1) |
| backend/Dockerfile | créé — build à valider plus tard (Docker absent) |
| backend/app/main.py (healthcheck GET /health) | créé — syntaxe validée |
| backend/app/config.py (Settings pydantic-settings) | créé — syntaxe validée |
| Arborescence backend/app (auth, models, schemas, routers, services, db) | créée — syntaxe validée |
| Frontend React + TypeScript (Vite) | créé — build validé (tsc + vite) |
| frontend/package.json (react, react-dom, typescript, vite, react-router-dom, axios) | créé — dépendances installées (58 paquets, 0 vulnérabilité) |
| frontend/Dockerfile (mode développement) | créé — build à valider plus tard (Docker absent) |
| .env.example | créé |
| .gitignore racine | créé (ajout justifié : secrets .env jamais commités) |

## Voie B — Exécution native (TEMPORAIRE)

| Élément | Statut |
|---|---|
| backend/.venv (Python 3.14) | créé |
| Dépendances backend installées dans le venv | ✅ installées (fastapi 0.141, sqlalchemy 2.0.52, psycopg2-binary 2.9.12, pydantic 2.13.5, pgvector 0.5.0, bcrypt 4.0.1) |
| Serveur backend uvicorn natif (`/health`) | ✅ vérifié — HTTP 200 `{"status":"ok"}`, Swagger `/docs` OK |
| Serveur frontend Vite natif (via `node` direct) | ✅ vérifié — HTTP 200 sur http://127.0.0.1:5173/ |
| **PostgreSQL 16.10 natif** (`C:\Users\Edwin Jamel Kouokam\PostgreSQL\pgsql16`) | ✅ installé — serveur actif sur 127.0.0.1:5432, base `dexter`, user `dexter` |
| **pgvector 0.8.6 natif** | ✅ installé — `CREATE EXTENSION vector` OK dans la base `dexter` |
| Connexion SQLAlchemy → PostgreSQL | ✅ vérifiée (settings → .env → DB_URL → SELECT version()) |
| `.env` local (valeurs de dev) | ✅ créé — DB_USER/DB_PASSWORD/DB_NAME/DB_URL/JWT_SECRET |
| `config.py` | ✅ fiabilisé — chemin `.env` résolu depuis le fichier (indépendant du répertoire de lancement) |

**Statut global Phase 0 : en cours (Voie B), en attente de validation utilisateur.**

## Points d'attention (signalés, non résolus d'initiative)

1. **Caractère `&` dans le chemin du projet** (`E:\Projets Edwin\New\Chatbot & Calco\...`) : casse les commandes npm sur l'hôte Windows (`npm run dev/build/lint`). Contournement actif : `node node_modules\vite\bin\vite.js` (vérifié). Alternative durable : renommer le dossier projet sans `&`.
2. **`.env` à créer** pour les phases ultérieures : copier `.env.example` → `.env` et remplir les valeurs (aucune valeur réelle commitée).
3. **Compte « Invité » activé** sur la machine Windows — à désactiver (sécurité, hors périmètre projet).

## Phase MVP — Authentification (générée par Copilot, analysée et corrigée par DSH)

| Élément | Statut |
|---|---|
| Code généré par Copilot (models, schemas, auth, services, routers, alembic, tests) | ✅ généré |
| Analyse DSH (PRD §5.1/§8.1/§12.1, conventions, sécurité) | ✅ conforme — rapport remis |
| Migration Alembic `202409010000_initial_users` | ✅ appliquée — table `users` conforme §8.1 |
| Correctifs appliqués : IntegrityError→400 (race register), `int(subject)` protégé (401), imports nettoyés, alembic.ini nettoyé | ✅ |
| `requirements-dev.txt` (pytest, httpx) | ✅ créé + installés dans le venv |
| Test fonctionnel HTTP réel (10 vérifications) | ✅ 10/10 (register 201, doublon 400, login 200, mauvais mdp 401, /me 200 sans password_hash, sans token 401, PATCH 200, refresh 200, refresh mauvais type 401) |
| Test pytest (`tests/test_auth_flow.py`) | ✅ 1 passed (3,54 s) |
| Base de dev | ✅ nettoyée (0 utilisateur de test) |
| Serveur orphelin sur port 8000 | ✅ supprimé |

**Statut : ✅ VALIDÉE par l'utilisateur (01/09/2026).**

### Reporté (V1) — décisions documentées
- Rotation + révocation des refresh tokens (stateless actuellement, acceptable MVP)
- Base de test dédiée (les tests écrivent actuellement dans la base de dev)
- Champ `annee` gardé (cohérent §5.1, absent de la liste §8.1 — décision validée)

## Phase MVP — Détection de domaine générique (générée par Copilot, analysée et corrigée par DSH)

| Élément | Statut |
|---|---|
| Code généré par Copilot (llm/, domains/, classifier, router, schemas, tests) | ✅ généré |
| Abstraction `LLMProvider` + provider OpenAI-compatible (httpx) | ✅ conforme §7.2 |
| `domains.json` générique (Comptabilité + Finance, keywords/sous_themes/référentiels) + loader | ✅ aucun domaine en dur |
| Correctifs appliqués : modèle `qwen/qwen3.8-27b` (testé), max_tokens 512, domaine conservé si confiance ≥ 0.6 (PRD §2.1), `model_validate` protégé, logs d'échec LLM, `httpx` ajouté à requirements.txt | ✅ |
| Clés API : Groq (principale) + Cerebras + SambaNova (secours) | ✅ vérifiées (200) |
| Tests pytest | ✅ 4 passed |
| **Test réel Groq (4 questions)** | ✅ bilan+OHADA → complet ; VAN → domaine conservé + précision ; blague → hors domaine ; bilan sans réf. → domaine conservé + demande réf. |

**Statut : ✅ VALIDÉE par l'utilisateur (01/09/2026).**

## Phase MVP — Étage 2 : Prompts pédagogiques spécialisés (générée par Copilot, analysée et vérifiée par DSH)

| Élément | Statut |
|---|---|
| Code généré par Copilot (prompts/loader, 12 templates markdown, chat_service, router /chat/message, schemas, tests) | ✅ généré |
| Multi-modèles par tâche (§7.2/§10.4) : classification = `qwen/qwen3.8-27b`, génération = `openai/gpt-oss-120b` (`model` paramétrable dans provider) | ✅ |
| Templates `root.md` + 5 intentions × 2 domaines (comptabilite, finance) — placeholders cohérents (tous fournis par le service) | ✅ |
| Flux `/chat/message` : classifie → si précision nécessaire → clarification (sans LLM) ; sinon → réponse pédagogique du domaine | ✅ conforme §2.1/§5.4/§10.5 |
| Transparence de source (§4.2) + registre par profil (étudiant/professeur) + langue | ✅ (respecté par le modèle en test réel) |
| Tests pytest | ✅ 8 passed |
| **Test réel Groq** | ✅ 401 sans token ; bilan OHADA → réponse pédagogique complète ; VAN → clarification avec référentiels proposés |
| **Validation runtime finale (07/09/2026)** | ✅ 8/8 vérifications — health, register, login, 401 sans token, comptabilité OHADA → réponse générée, finance sans référentiel → clarification (IFRS, Bâle III, PCAOB), hors domaine → clarification, comptabilité sans référentiel → clarification (OHADA, IFRS, US GAAP) |
| **Correctif appliqué** | `chat.py` : forcer la clarification quand le domaine a des référentiels configurés mais qu'aucun n'est fourni (`needs_referentiel`) |
| **Non-régression** | ✅ 8/8 tests pytest après correctif |

**Statut : ✅ VALIDÉE par l'utilisateur (07/09/2026).**

### Points mineurs signalés (non bloquants)
- `$profil` rempli en anglais (« student »/« professor ») dans des templates français (« au profil student ») — correctif cosmétique proposé : « étudiant »/« professeur »
- Templates d'instructions en français uniquement ; le bilinguisme de sortie est géré par `$langue` (le modèle répond dans la langue demandée) — templates EN complets à prévoir en V1
- Pas de log serveur des échecs de génération (le 502 est visible côté client) — à ajouter en V1
- Persistance du référentiel choisi entre messages : hors périmètre (conversations persistantes = phase suivante)

## Phase MVP — Conversations persistantes (générée par Copilot, analysée et corrigée par DSH)

| Élément | Statut |
|---|---|
| Analyse PRD (§5.4, §8.1, §12.2) + code existant | ✅ fait |
| Décisions discutées et actées (rétrocompatibilité, titre auto-généré, référentiel user+domaine, résumé .md) | ✅ fait |
| `PROMPT_COPILOT_CONVERSATIONS.md` | ✅ créé et validé par l'utilisateur (07/09/2026) |
| Code généré par Copilot (modèles, schémas, services, router, tests) | ✅ généré |
| Analyse DSH du code généré | ✅ rapport remis — 3 tests cassés, migration manquante, résumé manquant, titre auto-généré manquant |
| Correctifs appliqués : tests mock corrigés, migration Alembic `202409020000_conversations`, service de résumé + template, route `/resume`, titre auto-généré, `create_all()` retiré de `main.py` | ✅ |
| Migration Alembic `202409020000_conversations` | ✅ appliquée — tables `conversations`, `messages`, `user_domain_referentiels` conformes §8.1 |
| Tests pytest | ✅ 18 passed (8 existants + 10 nouveaux) |
| Base de dev | ✅ nettoyée (26 utilisateurs de test supprimés) |

**Statut : ✅ VALIDÉE par l'utilisateur (08/09/2026).**

## Phase MVP — RAG / Documents (générée par Copilot, analysée et corrigée par DSH)

| Élément | Statut |
|---|---|
| Analyse PRD (§4.2, §4.3, §8.1, §9, §12.3) + code existant | ✅ fait |
| Décisions discutées et actées (embedding open-source, formats PDF/DOCX/PPTX/images/TXT, 5 chunks max, ré-indexation, seuil 0.5) | ✅ fait |
| Dépendances ajoutées à `requirements.txt` | ✅ sentence-transformers, PyPDF2, python-docx, python-pptx, Pillow, pytesseract, python-multipart |
| Dépendances installées dans le venv | ✅ installées, dont `python-multipart` ajouté avec autorisation utilisateur |
| `PROMPT_COPILOT_RAG.md` | ✅ créé et validé par l'utilisateur (08/09/2026) |
| Génération par Copilot (modèles, schémas, services, router, migration, tests) | ✅ implémentation initiale réalisée |
| Modèles `Document` / `DocumentChunk` + relations | ✅ créé, embedding `vector(384)` |
| Extraction multi-formats | ✅ TXT/MD, PDF, DOCX, PPTX, images OCR |
| Chunking + embedding lazy + recherche pgvector | ✅ créé, seuil et limite configurables |
| Routes documents | ✅ upload, liste, détail, visibilité professeur, suppression |
| Intégration `/chat/message` | ✅ mode `mes_cours`, fallback `explique_moi`, sources persistées |
| Migration Alembic `202409030000_documents` | ✅ appliquée — tables `documents` / `document_chunks` opérationnelles (confirmé en runtime) |
| Analyse DSH du code généré | ✅ rapport remis — un étudiant pouvait modifier la visibilité d'un document sans contrôle de rôle |
| Correctif appliqué : `documents.py` (PATCH visibilité réservé au professeur, 403 sinon) | ✅ confirmé par tests dédiés + validation runtime |
| Tests unitaires extraction/chunking | ✅ 2/2 passés |
| Tests pytest complets | ✅ 24/24 passés (suite complète, y compris RAG et visibilité prof/étudiant) — 14,42 s en processus détaché |
| Validation runtime (`validate_rag_runtime.py`) | ✅ 14/14 vérifications réelles passées le 09/09/2026 : health, inscriptions étudiant+professeur, création conversation, upload TXT, statut `indexe` + 1 chunk, question → réponse RAG (mode `mes_cours`, domaine comptabilité), partage prof → 200, étudiant → 403, type non supporté (.exe) → 400 |
| Base de dev | ✅ nettoyée (0 users / conversations / documents / chunks) — dossier uploads et fichiers temporaires supprimés |

**Statut : ✅ VALIDÉE par l'utilisateur (09/09/2026).**

### Points mineurs signalés (non bloquants)
- `SAWarning` SQLAlchemy dans `rag_service.py` (`document_id.in_(subquery)` → passer un `select()` explicite) — dépréciation SQLAlchemy 2.0, à moderniser en V1
- Avertissement HF Hub « unauthenticated requests » au premier téléchargement du modèle d'embedding — informatif ; prévoir `HF_TOKEN` ou modèle embarqué en V1
- Indexation synchrone dans la requête d'upload (upload lent pour un gros document) — tâche de fond à prévoir en V1

## À faire ensuite

- **Phase suivante** : Outils de calcul par domaine (fiabilité chiffrée — PRD §6/§10.5) ou quiz/exercices — en discussion avec l'utilisateur
- Réparation in situ de Windows (quand l'utilisateur le décide) → reprise Docker