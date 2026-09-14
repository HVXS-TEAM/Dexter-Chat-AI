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

**Statut : en attente de validation utilisateur (règle 11).**

### Points mineurs signalés (non bloquants)
- `SAWarning` SQLAlchemy dans `rag_service.py` (`document_id.in_(subquery)` → passer un `select()` explicite) — dépréciation SQLAlchemy 2.0, à moderniser en V1
- Avertissement HF Hub « unauthenticated requests » au premier téléchargement du modèle d'embedding — informatif ; prévoir `HF_TOKEN` ou modèle embarqué en V1
- Indexation synchrone dans la requête d'upload (upload lent pour un gros document) — tâche de fond à prévoir en V1

## Module `dexter-calc` — corrections d'intégrité (cycle DSH, 09/09/2026)

> **Important** : le projet a été déplacé de `E:\Projets Edwin\New\Chatbot & Calco\Dexter Chat AI`
> vers `D:\Projets Edwin\New\Chatbot & Calco\Dexter Chat AI` par l'utilisateur.
> L'ancien emplacement n'existe plus ; le workspace VS Code doit être rouvert sur `D:`.

| Correctif | Fichier(s) | Statut |
|---|---|---|
| **Bug critique 1** : doublon `CalculationError` (2 définitions incompatibles — la version de `exceptions.py` sans `code` provoquait un `TypeError` sur le chemin d'erreur) | `core/exceptions.py` (classe canonique avec `code`), `core/calculator.py` (doublon supprimé) | ✅ corrigé |
| **Bug critique 2** : encodage mojibake (« â‚¬ » au lieu de « € », « modÃ¨le ») | `banque/credit_bon.py` | ✅ corrigé |
| **Bug critique 3** : fonction `calcul_van` inexistante (`ImportError` à l'import) | `finance/van.py` (alias historique ajouté) | ✅ corrigé |
| `calculer_ica` : taux 0,1 codé en dur → paramètre `taux_actualisation`, docstring corrigée, investissement nul rejeté explicitement | `finance/van.py` | ✅ corrigé |
| `_tir_simple` (NaN silencieux, code mort) → `calculer_tir_simple` publique, `CalculationError` explicite si pas de changement de signe | `finance/van.py` | ✅ corrigé |
| Imports absolus mélangés aux relatifs → imports relatifs uniformisés | `finance/van.py`, `finance/amortissement.py`, `banque/credit_bon.py` | ✅ corrigé |
| Accents dans identifiants (`calculer_dotation_linéaire`, `valeur_a_ammortir`, `reesiduelle`) → ASCII convention (`calculer_dotation_lineaire`, `valeur_a_amortir`, `residuelle`) | `finance/amortissement.py`, `finance/__init__.py` | ✅ corrigé |
| Fautes dans clés extra (`total_ammorce`, `reste_a_ammorcer`) → `total_amorti`, `reste_a_amortir` | `finance/amortissement.py` | ✅ corrigé |
| Validation implicite par `or 0`/`or 1` (valeurs par défaut masquant les erreurs) → paramètres requis explicitement (`missing_duration`, `missing_period_years`, entiers contrôlés) | `finance/amortissement.py` | ✅ corrigé |
| `_resolve_taux` avec `or` (taux 0 ignoré) → chaîne `is None` explicite | `finance/van.py`, `banque/credit_bon.py` | ✅ corrigé |
| `listCalculators` camelCase → `list_calculators` (synchronisé côté backend) | `core/registry.py`, `backend/app/services/calculator_service.py` | ✅ corrigé |
| Imports CLI cassés (`VANCulator`, `AmortissementLinearCalculator` — classes inexistantes) → noms réels des classes | `dexter-calc/app/cli.py` | ✅ corrigé |
| Import inutilisé `CalculationError` dans `validators.py` ; lignes vides / cosmétique (`core/__init__.py`, lignes collées `credit_bon.py`) | divers | ✅ corrigé |

**Statut : ✅ vérifié par exécution le 13/09/2026** — `backend/tests/test_calculators.py` **11/11 passed**, `dexter-calc/tests/` **7/7 passed** (TVA), non-régression ciblée **28/28** (`test_calculators` + `test_auth_flow` + `test_conversations` + `test_documents`). Étape **validée par l’utilisateur (13/09/2026, règle 11).**

### Correctif routeur calculators — intégration backend (Option A, 13/09/2026)

> Cause racine : `backend/app/main.py` n’incluait pas le routeur calculators (routes `/calculators/*` → 404 sur 10/11 tests), et le routeur déclarait `APIRouter()` sans préfixe.

| Correctif | Fichier(s) | Statut |
|---|---|---|
| Routeur branché : `prefix="/calculators"` + `tags=["calculators"]`, import `Query` inutilisé supprimé | `backend/app/routers/calculators.py` | ✅ appliqué + vérifié |
| Routeur inclus dans l’application FastAPI | `backend/app/main.py` (`import` + `include_router`) | ✅ appliqué + vérifié |
| Dépendance locale rendue importable : `dexter-calc` installé en editable dans `backend/.venv` (`dexter-calc 0.1.0`, validation règle 10 obtenue) | venv (aucun fichier source modifié) | ✅ installé + vérifié |

Note : la suite complète `backend/tests/` a dépassé le timeout de 30 s (tests LLM/embedding lents probables) — résultat non concluant, à relancer module par module si souhaité.

## Phase suivante — Outils de calcul integres au chat (Approche 1, 13/09/2026)

> Branche deterministe sur POST /chat/message : si intention == calcul + domaine connu, extraction explicite -> dexter-calc via calculator_service -> resultat verifie injecte dans le prompt calcul.md -> LLM explique. Params manquants = clarification explicite, jamais de chiffre invente (PRD S6/S10.5).

| Element | Statut |
|---|---|
| chat_calculation.py (extraction TVA/VAN/amortissement/credit + run_deterministic_calculation + build_calculation_context) | applique |
| schemas/chat.py (mode calcul + calcul_result + champs_manquants) | applique |
| routers/chat.py (branche calcul + calcul inline dans chat_message, persistance mode calcul) | applique |
| tests/test_chat_calcul.py (TVA verifiee, clarification sans taux, VAN, 502 LLM) | 4/4 passed |
| Non-regression chat (test_chat_calcul + test_chat_message + test_chat_service) | 8/8 passed |
| dexter-calc/tests/ | 7/7 passed |
| Point signale : test_calculators.py non relance ce cycle (suite DB : PostgreSQL natif instable le 13/09 — connexion refusee 5432 ; SQLite incompatible : colonne matieres_enseignees manquante — pre-existant, non touche regle 8) | signale |

**Statut : ✅ VALIDEE par l'utilisateur (regle 11).**

## Phase quiz / exercices (B, 13/09/2026) — cycle Copilot + analyse DSH

> Analyse du code Copilot sauvegardé (`routers/quiz.py`, `services/quiz_service.py`,
> `schemas/quiz.py`, `models/quiz.py`, migration `202409040000_quiz_attempts`,
> `tests/test_quiz.py`) contre le PRD §5.2/§5.3/§8.1 (table `quiz_attempts`).
> Rapport ✅/⚠️/❌ remis, correctifs appliqués après « Go pour tous » de l'utilisateur.

| Élément | Statut |
|---|---|
| Modèle `QuizAttempt` + relation `User.quiz_attempts` + migration `202409040000` (table, FK cascade, index, downgrade) | ✅ appliqué |
| Routes branchées dans `main.py` (pas de 404) : `POST /quiz/generate` (201, corrigé masqué), `POST /quiz/{id}/submit`, `GET /quiz/{id}`, `GET /users/me/progress` | ✅ appliqué |
| Sécurité : `get_current_user` partout ; `get_attempt` filtre owner (404 inter-utilisateur) ; double soumission → 400 | ✅ appliqué |
| ❌1 corrigé : templates `generation_exercice.md` (compta + finance) imposent `ÉNONCÉ:` / `CORRIGÉ:` + `_split_quiz_response` tolérant (`CORRIGE` sans deux-points, `### CORRIGÉ`) | ✅ appliqué |
| ❌2 corrigé : erreurs LLM logguées (`logger.warning`) et cartographiées (`UnknownDomainError`→400, `QuizGenerationError`→502) ; réponse LLM vide → 502 propre (plus de 500) | ✅ appliqué |
| ❌3 corrigé : réponse vide rejetée (validator schéma + service) | ✅ appliqué |
| ❌4 corrigé : annotations router alignées sur les schémas de réponse | ✅ appliqué |
| `QuizSubmitResponse.corrige` → optionnel (attempt sans corrigé stocké → réponse honnête, pas de 500) | ✅ appliqué |
| Route `GET /quiz/{id}` ajoutée (relecture owner, correction masquée tant que `statut=genere`) | ✅ appliqué |
| `tests/test_quiz.py` | ✅ **12/12 passed** (6 initiaux + 6 ajoutés : LLM vide→502, sans marqueur, déjà soumis→400, inter-utilisateur→404, sans corrigé stocké, détail masqué/révélé) |
| Non-régression chat + quiz (`test_chat_calcul` + `test_chat_message` + `test_chat_service` + `test_quiz`) | ✅ **20/20 passed** |
| `DummySession.refresh` → `datetime.now(timezone.utc)` (`utcnow` déprécié retiré) | ✅ appliqué |
| Restriction de rôle sur `POST /quiz/generate` : **laissée ouverte** (choix utilisateur, 13/09/2026) — les étudiants s'auto-génèrent des exercices (entraînement, PRD §5.2) | ✅ acté |

**Statut : ✅ VALIDÉE par l'utilisateur (13/09/2026, règle 11) — 12/12 quiz + 20/20 non-régression, vérifiés par exécution.**

## Phase C — Classes & adhésion (en cours, 13/09/2026)

> Décision actée avec l'utilisateur : **code d'invitation unique** (champ `code_invitation`
> sur `classes`, écart justifié par PRD §12.5). Périmètre V1 : `POST /classes`,
> `GET /classes`, `POST /classes/{id}/join`. **`GET /classes/{id}/progress` exclu** (V2+, PRD §5.3/§8.3/§11.5).
> Prompt remis à Copilot le 13/09/2026 : `PROMPT_COPILOT_CLASSES.md` — production Copilot analysée puis corrigée le 13/09/2026.

| Élément | Statut |
|---|---|
| Modèles `Classe`/`ClasseMembre` (PRD §8.1 + `code_invitation` unique), migration `202409050000_classes`, `models/__init__.py`, `main.py`, schémas, router 3 routes, code `secrets` 8 car. | ✅ conforme à la production Copilot, vérifié |
| Sécurité : 403 rôles (create prof / join étudiant), 404 classe absente, 400 code invalide / déjà membre ; `code_invitation` jamais exposé à un étudiant | ✅ vérifié |
| Périmètre V1 : **aucun** `GET /classes/{id}/progress` (V2+ PRD §5.3/§8.3/§11.5) | ✅ respecté |
| **SAWarning corrigé** : relations en conflit d'écriture (`classe_membres.classe_id`/`etudiant_id`) → `classes_inscrites_rel` et `ClasseMembre.etudiant` supprimées, `Classe.etudiants`/`User.classes_inscrites` en `viewonly=True` | ✅ 0 SAWarning (prouvé `-W error::sqlalchemy.exc.SAWarning`) |
| Router : handler `ValueError` 400 simplifié (une branche), annotations alignées sur les schémas réels | ✅ appliqué |
| `tests/test_classes.py` (router, mocks) + `tests/test_classes_service.py` (**nouveau**, SQLite en mémoire : code, create, join succès/code invalide/déjà membre, listes) | ✅ **16/16 passed** |
| Non-régression chat + quiz ; import app OK (13 routes), OpenAPI OK (23 paths) | ✅ **20/20 passed** |
| Résidu `models/user (2).py` (fragment mort produit par Copilot) supprimé | ✅ supprimé |

**Statut : correctifs appliqués, vérifiés par exécution — en attente de validation utilisateur (règle 11).**

Écart de traçabilité signalé : `PROMPT_COPILOT_QUIZ.md` annoncé dans un cycle précédent
est **absent du disque** (5 `PROMPT_COPILOT_*.md` seulement) — à recréer si demandé.

### Références visuelles Dexter — 14/09/2026

Les 18 dossiers de `stitch_dexter_ai_educational_platform` disposent désormais
d'un JSON nommé d'après leur dossier. Chaque fichier contient un bloc
`reproduction_spec` décrivant la source de référence, le viewport, la grille,
les tokens visuels, l'arbre de composants, la typographie, les contenus visibles,
les effets et les règles de fidélité. Validation exécutée : **18/18 JSON valides**
et documentés.

## A faire ensuite


- **Ordre acté par l'utilisateur (13/09/2026)** : **B** (quiz — ✅ validé) → **C** (classes — en cours, prompt Copilot remis) → **A** (frontend Dexter depuis les maquettes `stitch_dexter_ai_educational_platform.zip` — variante à trancher : sombre / clair_1 / clair_2)


- **Workspace rouvert sur `D:\Projets Edwin\New\Chatbot & Calco\Dexter Chat AI`** ✅ — vérification par exécution effectuée le 13/09/2026 : pytest backend `tests/test_calculators.py` **11/11 passed** + tests dexter-calc **7/7 passed** (TVA) + non-régression ciblée **28/28**.
- Réparation in situ de Windows (quand l'utilisateur le décide) → reprise Docker

## Frontend - Etape A1 Socle (lancee le 13/09/2026, GO utilisateur)

| Element | Statut |
|---|---|
| Decisions actees : 2 themes avec toggle, 7 domaines PRD sur l'accueil, Tailwind accepte, MVP (recherche croisee simple) | OK |
| Tailwind v4.3.3 + @tailwindcss/vite installes (regle 14, avant tout code) | OK - verifie package.json + node_modules |
| Assets template supprimes (autorisation utilisateur : hero.png, react.svg, vite.svg, App.css) ; favicon.svg/icons.svg intouches | OK - verifie |
| Specs design : dossier stitch_dexter_ai_educational_platform extrait a la racine (18 variantes, JSON reproduction_spec + DESIGN.md + code.html) - sources uniques des tokens | OK |
| PROMPT_COPILOT_A1.md redige (Copilot produit -> agent analyse/corrige -> build -> validation visuelle utilisateur) | ecrit |
| Etat en cours : App.tsx = template Vite (refe. cassees vers assets supprimes, attendu jusqu'a reecriture A1) | en cours |

**Statut A1 : ✅ VALIDEE par l'utilisateur (règle 11, 13/09/2026) — validation visuelle des deux thèmes (toggle), sidebar, routes ; build tsc + vite OK (0 erreur). Code analysé conforme aux contrats DESIGN.md. Étape close.**

### Frontend — Étape A2 Accueil (suivante)
- Périmètre : chat focal + chips suggestions + cartes des 7 domaines PRD.
- Dépendance backend à valider (règle 10) : route `GET /domains` (lecture de `domains.json`) — à créer avant ou pendant A2.
