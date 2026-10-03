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

**Statut global Phase 0 (actualisé le 02/10/2026 — traçabilité) : Voie B en service et acceptée de fait** —
aucune validation explicite n'avait été tracée, mais toutes les phases validées depuis (Auth 01/09/2026, etc.)
s'y appuient ; Docker reste reporté après réparation Windows (voir « Contexte Docker / Windows » ci-dessus).

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

**Statut (actualisé le 02/10/2026 — traçabilité) : aucune validation explicite de cette phase n'a été tracée** —
prompt validé le 08/09/2026, vérifications runtime 14/14 le 09/09/2026, volet frontend « documents dans le Chat »
validé visuellement le 21/09/2026 (voir plus bas) ; validation formelle toujours ouverte si vous souhaitez la confirmer.

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

## Phase C — Classes & adhésion (validée, 13/09/2026)

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

**Statut : correctifs appliqués, vérifiés par exécution — validation actée par l'utilisateur le 13/09/2026 (voir « A faire ensuite ») ; statut aligné le 20/09/2026.**

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


- **Ordre acté par l'utilisateur (13/09/2026)** : **B** (quiz) ✅ validé → **C** (classes) ✅ validé → **A** (frontend Dexter depuis les maquettes `stitch_dexter_ai_educational_platform`) — **étapes A1 → A5 ✅ validées** (socle, accueil, chat, détail matière + recherche, profil). **Prochaine décision : branchement de `DexterWelcome` (réparé, mais 0 référence dans l'app).**


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

## Session du 20/09/2026 — réparation frontend + scripts npm (cycle DSH)

### Constat d'entrée (preuves par exécution, pas des suppositions)
- `frontend/src/components/MagicRings.tsx` (composant React Bits `MagicRings`, issu de la maquette `DexterWelcome.jsx`) : **amputé** — blocs manquants dans le `useEffect` (`renderer`, garde `mount`, `scene`, `camera`, `resize()`, `ResizeObserver`, handlers souris + `addEventListener`) → 12+ erreurs TS.
- `frontend/src/components/DexterWelcome.tsx` : **corrompu** — 262 lignes mortes (duplicata du composant `MagicRings` collé en fin de fichier) → 3 erreurs tsc (lignes 369 / 461 / 463).
- `frontend/src/auth/AuthContext.tsx` : **3 erreurs TS réelles** (ligne 82 : `Promise<TokenPair>` incompatible avec le `null` renvoyé par le `.catch` ; lignes 151-155 : `error.config` typé sans `headers`, puis affectation d'un objet littéral à `AxiosRequestHeaders`).
- `MagicRings.tsx` et `DexterWelcome.tsx` n'étaient **importés par personne** → `vite build` passait alors que `tsc` échouait : build trompeur.

### Correctifs appliqués (fichiers sauvegardés, analysés puis corrigés)
| Fichier | Correctif | Vérification |
|---|---|---|
| `frontend/src/components/MagicRings.tsx` | blocs manquants restaurés + `console.warn` explicites au lieu des `return` muets (règle 6) → **295 lignes** | tsc 0 erreur |
| `frontend/src/components/DexterWelcome.tsx` | troncature au composant valide (**462 → 200 lignes**) ; importe et utilise `MagicRings` (l. 3 / l. 54) | tsc 0 erreur |
| `frontend/src/auth/AuthContext.tsx` | `useRef<Promise<TokenPair \| null> \| null>`, `error.config as InternalAxiosRequestConfig & { _retry?: boolean }`, refresh via `AxiosHeaders.from(...).set(...)` → **209 lignes** | tsc 0 erreur |
| `frontend/package.json` | scripts **`dev:node`** et **`build:node`** ajoutés (appel direct `node`, `node_modules` intouché) — option B1 validée par l'utilisateur | voir ci-dessous |

### Vérifications réelles exécutées
- `tsc --noEmit -p tsconfig.app.json` → **0 erreur**
- `tsc -b --force` → **0 erreur**
- `vite build` → ✅ 94 modules, bundle généré
- `npm run dev:node` → ✅ vite 8.2.2 démarre
- `npm run build:node` → ✅ **EXIT 0 en 13,2 s**, bundle généré

### Point d'outillage (bloquant, non résolu par le code)
`npm run dev` et `npm run build` restent **inutilisables** : les shims `node_modules/.bin/*.cmd` générés par npm cassent sur le `&` du chemin du projet
(`Error: Cannot find module 'D:\Projets Edwin\New\vite\bin\vite.js'`). Contournement retenu (option B1) : scripts `dev:node` / `build:node`.
Écartés : patch des shims `.cmd` (perdu au prochain `npm install`, donc correctif temporaire) et renommage du dossier racine (casse les chemins existants).

### En attente (règle 11)
- **`DexterWelcome` n'était branché nulle part** (0 référence dans l'app) — **tranché et résolu par l'étape A6** ci-dessous : route publique `/bienvenue` (choix utilisateur, 20/09/2026).
- Ce fichier `PROGRESS.md`, supprimé du disque **et** du dépôt par le commit `e977586`, a été **restauré depuis git le 20/09/2026**, puis mis à jour.

### Points signalés, non touchés (règle 8)
- `frontend/Dockerfile (2)` — doublon résiduel.
- `backend/test_auth.db` (modifié, résidu de test) et `backend/pytest_stream_out.txt` (non suivi).
- `stitch_dexter_ai_educational_platform/DexterWelcome.jsx` (maquette source, non suivie).

### Étape A6 — Écran d'ouverture + essai sans connexion (option G1, 20/09/2026)

Périmètre validé par l'utilisateur : `DexterWelcome` devient l'**écran d'ouverture public** avec deux choix — « Se connecter » ou « Essayer sans connexion » — l'essai restant limité à ce que le backend expose publiquement. **Aucun changement backend, aucune dépendance nouvelle.**

| Élément | Contenu | Statut |
|---|---|---|
| `frontend/vite.config.ts` | serveur dev forcé sur **4173** (`strictPort`) — seul port autorisé par le CORS backend (`app/main.py`), sinon **aucun appel API ne passait en dev** | ✅ vérifié (HTTP 200 sur `http://localhost:4173/`, titre « Dexter », `lang="fr"`) |
| `frontend/src/auth/guestMode.ts` (nouveau) | indicateur « essai sans connexion » (sessionStorage) : activé par le bouton, désactivé dès une connexion réussie | ✅ |
| `frontend/src/auth/ProtectedRoute.tsx` | props `allowGuest` / `redirectTo` — un visiteur en essai accède aux écrans publics, sinon renvoi vers `/bienvenue` | ✅ |
| `frontend/src/App.tsx` | route publique `/bienvenue` ; groupe « essai » : `/`, `/chat`, `/recherche`, `/matieres`, `/matiere/:id`, `/historique` ; `/profil` reste protégé (renvoi `/login`) | ✅ |
| `frontend/src/components/DexterWelcome.tsx` | deux boutons (« Se connecter » / « Essayer sans connexion ») + « Continuer » si déjà connecté ; styles **repris de l'existant** (pill de la maquette `DexterWelcome.jsx` + style des contrôles de `Login.tsx`) — aucune UI inventée (règle 3) | ✅ |
| `frontend/src/auth/AuthContext.tsx` | sortie du mode invité dès qu'une connexion réussit | ✅ |

**Périmètre réel de l'essai sans connexion (vérifié ligne par ligne côté backend)** : `GET /domains` et `/calculators/*` sont publics → Accueil, Matières, Détail matière fonctionnent ; `/chat/*`, `/users/*`, `/quiz/*`, `/classes/*`, `/conversations/*`, `/documents/*` exigent un compte. Le chat invité affiche donc le message **déjà existant** « Vous devez être connecté pour utiliser le chat Dexter. » — aucun message inventé.

### BUG corrigé (bloquant, découvert pendant l'analyse de cette étape)
| Fichier | Constat | Correctif | Vérification |
|---|---|---|---|
| `frontend/src/pages/Chat.tsx` (l. 114-118 d'origine) | l'appel streaming `fetch('/chat/stream')` n'envoyait **aucun header `Authorization`** (l'intercepteur d'`axios` ne s'applique pas à `fetch`) → **401 même pour un utilisateur connecté** : le chat était inutilisable | envoi explicite du jeton via `getAccessToken()` (`Authorization: Bearer …`) | tsc 0 erreur + build OK |

### Vérifications réelles de l'étape A6
- `npm run build:node` → ✅ **EXIT 0** ; **99 modules** (94 avant) : `DexterWelcome` et `MagicRings` sont désormais **réellement inclus dans le bundle** — preuve du branchement effectif.
- `npm run dev:node` → ✅ serveur prêt sur **`http://localhost:4173/`** ; `GET /` → HTTP 200, titre « Dexter », `lang="fr"` ; serveur arrêté proprement ensuite (aucun processus résiduel).
- Avertissement de build signalé (non bloquant) : bundle principal ≈ 870 Ko / 236 Ko gzip à cause de `three` — piste : chargement différé de `MagicRings` (hors périmètre de cette étape).

**Statut : validé visuellement par l'utilisateur le 20/09/2026 (règle 11).** — Lancement : backend uvicorn natif port 8000 + `npm run dev:node`, ouvrir `http://localhost:4173/`.

### Étape A7 — Salutation dynamique de l'accueil (demande utilisateur, 20/09/2026)

Demande : « En quoi puis-je aider aujourd'hui ? » pour l'essai gratuit, et une formule d'accueil **variée avec le prénom** pour un compte connecté.

Constat préalable : **aucun champ « prénom » n'existe** (ni table `users`, ni `UserRead`, ni type `User` frontend) ; `Register.tsx` ne collecte pas de nom et `Profil.tsx` n'a pas de formulaire d'édition. Option retenue par l'utilisateur : **A — prénom déduit de l'email, côté frontend** (0 backend, 0 migration), avec formules de repli.

| Élément | Contenu | Statut |
|---|---|---|
| `frontend/src/pages/accueilGreetings.ts` (nouveau) | 7 formules avec prénom, 4 formules de repli, sous-titre de la maquette, `GUEST_GREETING` = « En quoi puis-je aider aujourd'hui ? », `extractFirstName()` (email → prénom, préfixes génériques écartés) | ✅ |
| `frontend/src/pages/Accueil.tsx` | titre = formule tirée à l'ouverture (invité : texte fixe) ; **sous-titre de la maquette affiché uniquement pour un compte connecté** (sinon deux questions redondantes) | ✅ |

Écart assumé à la maquette (signalé) : « Bonjour, David 👋 » provient de `cran_d_accueil_clair_dexter_2/code.html` (l. 294-295) — la demande utilisateur remplace expressément ce texte d'exemple, il n'y a donc plus conformité littérale au `content_contract`. Aucune UI ni style modifié (le `gradient-text` du prénom n'existe que dans la variante clair_1, non retenue).

Vérifications réelles :
- Test fonctionnel du module (exécution Node 24 directement sur le `.ts`) : `edwin.kouokam@exemple.com` → « Edwin » ; `Edwin.Jamel@…` → « Edwin » ; `contact@…`, `e.k@…`, `etudiant123@…`, `null` → repli « Bonjour 👋 » ; tirage 0 → « Bonjour Edwin 👋 » ; tirage max → « Edwin, prêt pour une nouvelle session ? » ; invité → « En quoi puis-je aider aujourd'hui ? » — **10/10 conformes**.
- `npm run build:node` → ✅ **EXIT 0** (tsc 0 erreur + bundle généré).

#### Suite A7 (20/09/2026) — 8e formule + stabilité par session
Décisions utilisateur : (a) la 8e formule « Que veux-tu apprendre aujourd'hui, {prénom} ? » est **réintégrée** (pool passé à 8 + 5 formules de repli) ; (b) formule **stable par session d'onglet** (`sessionStorage`, clé par email) plutôt que tirée à chaque ouverture — choix confié à l'agent, qui a opté pour la stabilité (moins de surprise, formule constante pendant la navigation).
Règle anti-redondance : quand la formule tirée est la question « Que veux-tu apprendre aujourd'hui… », le sous-titre de la maquette (« Que souhaites-tu étudier aujourd'hui ? ») est **masqué** (`isLearningQuestion()`), pour éviter deux questions qui se suivent.
Vérifications réelles : `tsc --noEmit` 0 erreur + `npm run build:node` ✅ **EXIT 0**.

**Statut : validé visuellement par l'utilisateur le 20/09/2026 (règle 11).**


## Session du 20/09/2026 (suite) — lancement du chantier « Classes frontend » (fin de C)

- Validation visuelle **A6 + A7 reçue** de l'utilisateur (règle 11) — statuts mis à jour ci-dessus.
- Statut **Phase C aligné** sur « validée » (décision actée le 13/09/2026, voir « A faire ensuite »).
- **Chantier suivant acté : Classes côté frontend** (fin de C). Périmètre V1 backend confirmé par lecture du code :
  `POST /classes` (professeur uniquement, 403 sinon), `GET /classes` (liste — `code_invitation` visible du seul
  professeur), `POST /classes/{id}/join` (étudiant uniquement, 403 sinon) ; `GET /classes/{id}/progress` exclu (V2+,
  PRD §5.3/§8.3/§11.5).
- **Règle 3 — bloquant constaté puis tranché** : aucun des 18 dossiers de maquettes (`stitch_dexter_ai_educational_platform/`)
  ni `Documentation Dexter/` ne couvre un écran « Classes ». Choix utilisateur (20/09/2026) : **l'utilisateur fournit
  une maquette Stitch « Classes »** — **en attente de la maquette avant toute production**. Aucune ligne de code
  Classes écrite à ce stade.
- Analyse des dépendances (règle 14) : **0 nouvelle dépendance npm** (axios et react-router-dom déjà présents).
  Contraintes structurelles prévisibles : page protégée (compte requis — le mode invité n'a pas de rôle), différenciation
  étudiant/professeur via `User.role`, entrée de navigation à ajouter dans `Layout.tsx`.

### Maquette Classes déposée, analysée et validée (20/09/2026)

- Dépôt utilisateur : `stitch_dexter_ai_educational_platform/stitch_dexter_ai_classroom_portal/` — 3 écrans PNG
  (`mes_classes_vue_tudiant_sombre`, `mes_classes_vue_professeur_sombre`, `mes_classes_vue_tudiant_clair`)
  + `nocturne_scholar/DESIGN.md` (système « Nocturne Scholar »). Pas de `code.html` (non bloquant : PNG = autorité
  géométrie ; styles réutilisés depuis les variables existantes de l'app).
- Analyse contre le backend V1 et les tokens de l'app : sidebar/tokens conformes ; périmètre V1 couvert
  (rejoindre par code 8 car., créer + copier le code, liste sans CTA de détail — `GET /classes/{id}` n'existe pas).
- **10 dispositions de données validées par l'utilisateur (GO, sans modification backend)** : nom du professeur →
  libellé générique (« Professeur ») ; « Rejoint le » → « Créée le » (created_at) ; inscrits, lieu, description,
  chips, contrôle de tri, année scolaire → omis ; sidebar et bloc utilisateur inchangés hors entrée « Mes classes »
  (carte plan = chantier « badge plan » séparé ; prénom affiché = chantier « prenom » différé).
- Défauts maquette signalés et assumés : bandeau violet illisible en variante claire (structure sombre = autorité) ;
  variante professeur claire absente (dérivée des tokens clairs existants de l'app).
- **`stitch_dexter_ai_classroom_portal.json` créé** (reproduction_spec + data_dispositions + 3 variantes) à la racine
  du dossier maquette.
- Mode de production **acté : Copilot** (protocole habituel) ; note d'intention de reproduction présentée et couverte par le GO utilisateur.
- **`PROMPT_COPILOT_CLASSES_FRONTEND.md` créé à la racine** (contexte, périmètre 5 fichiers, contrat backend exact, spécification
  écran avec les 10 dispositions, conventions Tailwind v4 + `var()`, vérifications attendues).
- Écart de traçabilité constaté : **aucun `PROMPT_COPILOT_*.md` n'existe plus sur le disque** (recherche récursive vide) —
  les prompts des cycles antérieurs ont disparu (comme `PROGRESS.md` avec le commit `e977586`). Signalé, non reconstitué.
- **En attente** : l'utilisateur fait produire le prompt par Copilot, sauvegarde les fichiers, puis signale « Copilot terminé »
  → analyse en 1 passe (lecture + `tsc --noEmit` + `npm run build:node`), rapport ✅/⚠️/❌, correctifs après validation,
  validation visuelle (règle 11).

### Cycle Copilot « Mes classes » — production analysée en 1 passe (20/09/2026)

- Production Copilot reçue puis analysée (lecture intégrale) : `classes/types.ts` (24 l.), `classes/api.ts` (19 l.),
  `pages/Classes.tsx` (303 l.), `App.tsx` (route `/classes` dans le groupe « compte requis »), `Layout.tsx`
  (entrée « Mes classes », icône groups, après « Mes matières »).
- **Vérifications réelles** : `node node_modules\typescript\bin\tsc --noEmit -p tsconfig.app.json` → **0 erreur** ;
  `npm.cmd run build:node` → **EXIT 0**, **102 modules** (99 avant → +3, preuve d'intégration au bundle).
  Note outillage : `npx`/`npm` (shims `.ps1`) sont bloqués par la politique d'exécution PowerShell → utiliser
  `node ...` direct ou `npm.cmd`.
- **Conformité** : types/API exacts (axios nu, sans Bearer manuel — pattern AuthContext) ; route protégée correcte ;
  entrée nav unique ; contenus français contractuels ; dispositions 1, 2, 8 appliquées ; dispositions 3-7 respectées
  (rien d'inventé) ; erreurs jamais avalées (règle 6) ; Tailwind v4 + `var()` uniquement.
- **❌ Bug bloquant (Classes.tsx l. 75)** : `joinClass(classes[0]?.id ?? 0, …)` — le join n'est pas lié au code saisi.
  Cause racine = **écart de conception V1** : aucun endpoint backend ne résout un code d'invitation en id de classe
  (la maquette et le prompt DSH supposaient un flux « code seul » ; PRD §12.5 « code à définir »). Flux étudiant
  inopérant en l'état (400 « déjà membre » ou 404).
- **⚠️ Mineurs** : `check_circle` sur cartes professeur (maquette : étudiant) ; titre « Classes actuelles » + chip
  affichés aussi côté professeur (maquette prof : cartes directes) ; bouton copie `rounded-[10px]` (≠ 12px) ; icône
  `person` vs pictogramme éducation de la maquette ; guillemets anglais dans le message de succès.
- **En attente de décision utilisateur** : Option A (extension backend minimale `POST /classes/join` par code — lève
  le « sans backend ») / Option B (sans backend : masquer le flux join, V1 étudiant amputé) + lot de micro-corrections.

### Correctifs appliqués — Option A + micro-corrections (20/09/2026) — EN ATTENTE DE VALIDATION

Décision utilisateur : **Option A** (extension backend minimale) + micro-corrections frontend.

**Backend** (périmètre étendu validé explicitement) :
- `app/services/classes.py` : `find_class_by_code()` (résolution du code, insensible à la casse, vide → None) +
  `join_class_by_code()` (réutilise `join_class` existant ; `ValueError("Invalid invitation code.")` si code inconnu/vide).
- `app/routers/classes.py` : **`POST /classes/join`** (body `{code_invitation}` seul ; étudiant uniquement, 403 sinon ;
  400 code invalide ; réponse `ClassJoinResponse` sans code exposé) — déclarée avant `/classes/{id}/join` (paths
  distincts, aucun conflit de routage) ; réutilise `ClassJoinRequest`. L'ancienne route `{id}/join` conservée.
- Tests : +3 router (succès 200 avec code minuscule, sans `code_invitation` exposé / 400 code inconnu / 403 professeur)
  +3 service (succès code minuscule avec membership persisté / code inconnu / code vide) → **pytest 22/22 passed**
  (`tests/test_classes.py` + `tests/test_classes_service.py`, exit 0).

**Frontend** :
- `classes/api.ts` : `joinClass(classeId, …)` remplacée par `joinClassByCode({code_invitation})` → `POST /classes/join`.
- `pages/Classes.tsx` : join branché sur le code réellement saisi (**bug `classes[0]?.id ?? 0` corrigé**) ; message de
  succès nommant la classe avec guillemets français (« Classe « X » rejointe. » / « créée. ») ; `check_circle` déplacé
  sur les cartes **étudiant** (bas de carte, à côté de « Créée le », comme la maquette) et retiré des cartes
  professeur ; icône `school` pour la ligne « Professeur » ; bouton copie `rounded-[12px]` ; titre « Classes
  actuelles » + chip compteur réservés à l'étudiant (prof = cartes directes, conforme maquette).
- Erreur relevée et corrigée pendant le correctif (traçabilité honnête) : une icône `visibility` avait été introduite
  par erreur sur les cartes professeur (invention hors maquette) → **supprimée** (les cartes prof n'ont aucun
  pictogramme en haut à droite ; badge « inscrits » omis — disposition 3).

**Vérifications réelles après correctifs** : pytest backend **22/22 passed** ; `tsc --noEmit` **0 erreur** ;
`npm.cmd run build:node` **EXIT 0** (102 modules). Les 8 échecs pytest préexistants (test_auth/test_chat) restent
hors périmètre, non touchés.

**Statut : en attente de validation visuelle de l'utilisateur (règle 11)** — lancer uvicorn (port 8000) +
`npm run dev:node` → http://localhost:4173/classes : compte étudiant (rejoindre par code, insensible à la casse ;
codes invalides → message backend explicite) et compte professeur (créer une classe, copier le code).

### Blocage connexion résolu — PostgreSQL arrêté + comptes de test (21/09/2026)

- **Cause racine de l'échec de connexion** (diagnostic par exécution, pas de supposition) : **PostgreSQL était arrêté**
  (`connection refused` sur localhost:5432 ; log : « database system was interrupted; last known up at 2026-09-13 »).
  Aucun bug applicatif : register 201, login 200, `/users/me` 200 après redémarrage.
- **Procédure de démarrage PostgreSQL natif** (à refaire après chaque redémarrage machine — Voie B) :
  1. Vérifier : `Get-Process -Name postgres` ; sinon démarrer **détaché** (pg_ctl garde la console sous PowerShell →
     timeout de l'outil) : `Start-Process -FilePath 'C:\Users\Edwin Jamel Kouokam\PostgreSQL\pgsql16\bin\pg_ctl.exe'
     -ArgumentList '-D "C:\Users\Edwin Jamel Kouokam\PostgreSQL\data" -l "…\pg_start_<date>.log" start' -WindowStyle Hidden`
     (guillemets obligatoires autour des chemins espacés, passés en une seule chaîne).
  2. Patienter (~40 s : récupération WAL) puis contrôler `pg_isready -h localhost -p 5432` → « acceptation des connexions ».
  - Pièges rencontrés et documentés : `postmaster.pid` résiduel à supprimer si arrêt forcé ; violation de partage
    sur le fichier de log si pg_ctl et le serveur l'ouvrent simultanément (le serveur retente 30 s — laisser finir).
  - **Piste permanente proposée, non appliquée (règle 1)** : enregistrer PostgreSQL comme service Windows
    (`pg_ctl register -N PostgreSQL-Dexter`) pour démarrage automatique — décision utilisateur.
- **Comptes de test créés en base de dev** (via `backend/scripts/diagnostic_auth.py`, ré-exécutable — idempotent partiel :
  renvoie « Email already registered. » si déjà créés) :
  | Rôle | Email | Mot de passe |
  |---|---|---|
  | Étudiant | `etudiant.test@dexter.dev` | `Etudiant2026!` |
  | Professeur | `professeur.test@dexter.dev` | `Professeur2026!` |
  (ids 137/138 ; prof : matières Comptabilité/Finance. Contraintes : mot de passe ≥ 8 caractères — le login échoue
  en 422 si plus court, côté schéma `UserLogin`.)
- Script de diagnostic créé : `backend/scripts/diagnostic_auth.py` (register + login + /users/me via l'API réelle).

### Feature différée — « Se souvenir de moi » (finalisation, fin de projet)

Demandée le 21/09/2026 : case « Se souvenir de moi » sur l'écran de connexion, effet **côté navigateur** (persistance
des jetons : localStorage vs sessionStorage) **et côté serveur** (durée de vie du refresh token variable selon
l'option, ex. claim `remember` dans le JWT → refresh long durée). **Reportée volontairement par l'utilisateur à la
phase de finalisation du projet** — à ne pas entamer sans son GO. Point de départ technique : `AuthContext.tsx`
(clés `dexter-access-token`/`dexter-refresh-token` en localStorage, refresh silencieux existant) et
`app/auth/security.py` (durées `access_token_expire_minutes` / `refresh_token_expire_days`).

### Script `start-dev.ps1` — environnement lancé en un coup (21/09/2026)

- **`start-dev.ps1` créé à la racine** : ① PostgreSQL démarré si arrêté (détaché, suppression `postmaster.pid`
  résiduel, attente jusqu'à 90 s via `pg_isready` — test sur le **code de sortie**, le message étant localisé en
  français) ; ② backend uvicorn (port 8000) dans une fenêtre dédiée — **via `python.exe -m uvicorn`** (le lanceur
  `uvicorn.exe` du venv échoue silencieusement, piége documenté) ; ③ frontend Vite (port 4173, `node` direct)
  dans une fenêtre dédiée. Idempotent : vérifie ce qui tourne déjà (health 8000, HTTP 4173).
- **Vérifié par exécution** : script **EXIT 0** ; `GET /health` → **HTTP 200 `{"status":"ok"}`** ; `GET /` :4173 →
  **HTTP 200**. Fichiers de diagnostic temporaires supprimés (`uvicorn_diag.txt`, `uvicorn_err/out.txt`).
- Usage : `powershell -ExecutionPolicy Bypass -File .\start-dev.ps1` (ou clic droit → Exécuter avec PowerShell).
  Arrêt : fermer les fenêtres backend/frontend ; PostgreSQL reste actif.
- Service Windows **non enregistré** (alternatif, nécessite droits admin) : `pg_ctl register -N PostgreSQL-Dexter`
  — sur décision utilisateur ; le script couvre le besoin courant.
- **Comptes de test en base de dev** (créés le 21/09, vérifiés register 201 / login 200 / me 200) :
  étudiant `etudiant.test@dexter.dev` / `Etudiant2026!` ; professeur `professeur.test@dexter.dev` / `Professeur2026!`.

### Chantier RAG/documents frontend — Phase 1 « documents dans le Chat » (21/09/2026)

- Analyse effectuée (règle 3) : le contrat backend documents est complet (upload/indexation synchrone, liste par
  conversation, statut, visibilité prof, suppression) — **aucune modification backend nécessaire**. Les documents sont
  rattachés aux **conversations** (pas aux matières). Maquette : le **trombone du Chat** (`chat_ia_dexter/screen.png`)
  couvre l'affordance ; le trombone existant dans `Chat.tsx` (l. 278) est décoratif. L'onglet « Ressources » du détail
  matière est visible sur la maquette mais **aucune variante n'en montre le contenu** → Phase 2 impossible en l'état
  (pas d'endpoint backend global/par domaine + pas de maquette) → **différée**.
- Décision utilisateur : **Phase 1 validée** (adaptation UI acceptée : trombone fonctionnel + présentation des
  documents de la conversation). Mode de production : **Copilot** (protocole établi).
- **`PROMPT_COPILOT_CHAT_DOCUMENTS.md` créé à la racine** : périmètre 3 fichiers (`documents/types.ts`,
  `documents/api.ts` nouveau ; `Chat.tsx` modifié), contrat backend exact, statuts `pending|indexe|erreur`,
  conditions d'activation du trombone (compte requis + conversation existante), chips de documents au-dessus de la
  barre de saisie (nom, statut, suppression, visibilité prof).
- **En attente** : production Copilot → « Copilot terminé » → analyse en 1 passe (lecture + `tsc` + `build:node`) →
  rapport ✅/⚠️/❌ → correctifs après validation → validation visuelle (règle 11).

### Validation visuelle « Mes classes » reçue + features graphiques différées (21/09/2026)

- **Écran « Mes classes » validé visuellement par l'utilisateur (règle 11)** — étape C frontend close (backend + frontend
  fonctionnels : connexion comptes de test, création + copie de code, rejoindre par code).
- **2 features graphiques demandées, différées volontairement par l'utilisateur (à planifier plus tard)** :
  1. **Sidebar auto-repliante** : se referme automatiquement quand la souris n'est pas dessus, en ne laissant
     apparaître que les icônes (mode rail).
  2. **Responsive général** : l'app doit s'adapter à tout type d'écran et d'environnement de lancement (navigateur),
     en particulier la **page d'accueil** et l'écran **« welcome Dexter »** (`DexterWelcome`).
- Aucune modification UI réalisée à ce stade (volonté utilisateur : « en attendant, on continue avec la route déjà
  prévue »). Points d'entrée techniques futurs : `Layout.tsx` + classes CSS `.sidebar` (index.css) pour le repli ;
  `DexterWelcome.tsx` / `Accueil.tsx` pour le responsive.

### Cycle Copilot « documents du Chat » — production analysée en 1 passe (21/09/2026)

- Lecture des 3 fichiers produits (`frontend/src/documents/types.ts`, `frontend/src/documents/api.ts`,
  `frontend/src/pages/Chat.tsx`) + vérifications réelles : `tsc --noEmit` → **0 erreur** ; `npm run build:node` →
  **EXIT 0** (103 modules, +1 attendu ; bundle 884,90 KB, +5 KB ; avertissement `three` préexistant inchangé).
- ✅ Conforme : contrat backend exact (4 routes, FormData `file`, payload `{visibilite}` aligné sur
  `DocumentVisibilityUpdate` Literal `prive|partage_classe`, statuts `pending|indexe|erreur`, extensions
  `.pdf,.docx,.pptx,.png,.jpg,.jpeg,.txt,.md` identiques au backend) ; conditions trombone (compte + conversation
  existante + pas d'upload en cours) ; bande de chips au-dessus de la saisie (spinner d'upload, icône type
  image/description, icône statut colorée, suppression, bascule visibilité **prof uniquement**) ; messages d'erreur
  français par code (400/403/404/422) ; **SSE du chat intacte** ; style `var(--*)` uniquement ; **0 nouvelle
  dépendance** (`package.json` : modification héritée d'un cycle antérieur — statut git cumulatif depuis le dernier
  commit) ; reset de l'input file permettant de re-joindre le même fichier.
- Auth vérifiée pendant l'analyse : `documents/api.ts` n'envoie pas d'en-tête explicite, mais `AuthContext.tsx` pose
  `axios.defaults.headers.common.Authorization` à la connexion (l. 86/110/175) + intercepteur 401 → refresh — même
  schéma que `classes/api.ts`, déjà validé visuellement. Conforme.
- ⚠️ Point mineur signalé (non bloquant) : le wording des erreurs 404 est générique (« Conversation introuvable. »)
  y compris pour suppression/bascule de visibilité, où le 404 du backend signifie « **document** introuvable ».
  Proposition : message par handler. **Correctif non appliqué** — en attente de décision utilisateur.
- **En attente (règle 11)** : validation visuelle — scénarios : connexion, premier message → conversation créée,
  upload `.pdf`/`.txt` → chip passe à « indexé », upload `.exe` → « Type de fichier non supporté », suppression de
  chip, bascule visibilité côté prof.

### Validation documents reçue + chantier « Chat riche » — décisions et prompt (21/09/2026)

- **Validation visuelle documents reçue avec 2 demandes** : ① trombone actif nativement (comme ChatGPT) ;
  ② réponses Dexter riches (style ChatGPT/Gemini) + menu après clic sur le trombone.
- **Décisions utilisateur actées** : dépendances `react-markdown` + `remark-gfm` validées (règle 10) ; menu
  2 items (« Document de cours » / « Image ») ; échec d'upload = tout-ou-rien ; trombone actif pour l'invité ;
  Option B (instructions markdown dans les 7 `root.md`) ; carte calcul + horodatages + **pouces de feedback**
  (l'utilisateur surmonte ma réserve : feedback = nouveau besoin backend).
- **BUG racine découvert (préexistant, bloquant)** : la voie streaming `/chat/stream` (`_stream_chat_events`) ne
  crée JAMAIS de conversation (si `conversation_id` null → rien de créé/persisté ; aucun événement SSE ne renvoie
  `conversation_id`) → `conversationId` du Chat reste toujours null → trombone jamais actif, et les conversations
  streamées ne sont pas persistées (écart au PRD « conversations persistantes » ; la voie synchrone persiste et
  retitre, elle). Correctif : le frontend crée la conversation (`POST /conversations`) au premier envoi, avant le
  stream ; + auto-titre ajouté à la voie streaming (miroir de la synchrone) ; + événement `done` enrichi de
  `message_id` (nécessaire au feedback).
- **Feedback (pouces)** : colonne `Message.feedback` (`String(10)`, `up`/`down`) + migration Alembic
  `202409060000_message_feedback` + endpoint `PATCH /messages/{message_id}/feedback` (ownership par jointure
  conversation) + `MessageRead.feedback`.
- **Invité** : trombone/menu actifs, fichiers attachables (staged local) ; l'envoi requiert un compte →
  CTA connexion à l'envoi (le backend exige l'auth pour chat/upload ; aucune voie anonyme créée). Interprétation
  honnête signalée à l'utilisateur.
- **`PROMPT_COPILOT_CHAT_RICHE.md` créé** (172 lignes, protocole habituel : Copilot produit → DSH analyse) :
  partie A backend (7 items) + partie B frontend (5 items) + garde-fous (SSE inchangée hors `message_id`,
  `var()` uniquement, 2 dépendances max, périmètre fermé) + vérifications obligatoires (alembic upgrade, pytest
  ciblés, tsc, build:node).
- **En attente** : production Copilot → « Copilot terminé » → analyse en 1 passe → rapport ✅/⚠️/❌ → correctifs
  après validation → validation visuelle (règle 11).

### Production Copilot partielle constatée + addendum v2 (21/09/2026)

- « Copilot terminé » reçu, mais **vérification disque : production INCOMPLÈTE**.
- ✅ Présent (Partie A, presque complète) : colonne `Message.feedback`, migration `202409060000_message_feedback`
  (style conforme au modèle classes), `MessageRead.feedback` + `MessageFeedbackUpdate` (Literal up/down), routeur
  `messages.py` (`PATCH /messages/{id}/feedback`, ownership par jointure, 404) enregistré dans `main.py`,
  auto-titre dans la voie streaming, `done` avec `message_id`, instruction markdown dans les **7** `root.md`.
- **Déviation du prompt** : Copilot fait créer la conversation **par le backend** dans la voie streaming
  (`create_conversation` si `conversation_id` null) au lieu du frontend — déviation acceptable (filet de sécurité,
  persistance systématique), **MAIS l'identifiant n'est jamais renvoyé** (aucun événement SSE ne transporte
  `conversation_id`) → le trombone serait resté inactif. → **A8 ajouté** : `done` transporte désormais
  `message_id` **et** `conversation_id` ; design acté : le frontend crée toujours la conversation en amont, la
  création backend ne sert qu'à `conversation_id=null`.
- ❌ Absent : `backend/tests/test_messages_feedback.py` (A7) ; **toute la Partie B** (B1-B5 : deps npm,
  `ChatMarkdown.tsx`, `AttachMenu.tsx`, `conversations/api.ts`, refonte `Chat.tsx`) — aucun marqueur trouvé.
- État de la migration en base : vérif `alembic current` non concluante (quirk PowerShell stderr, exit 1) —
  l'addendum fait re-appliquer `alembic upgrade head` (idempotent).
- **`PROMPT_COPILOT_CHAT_RICHE.md` mis à jour avec ADDENDUM v2** (état disque, A8, rappels A7 et B1-B5).
- **En attente** : reprise Copilot (même fichier, depuis l'ADDENDUM v2) → « Copilot terminé » → analyse en 1 passe.

### Cycle « Chat riche » — production complète analysée en 1 passe (21/09/2026)

- Production vérifiée sur disque : **Partie A (A1-A8) + Partie B (B1-B5) complètes**.
- ✅ Conforme : modèle/schéma/migration/routeur feedback ; `done` avec `message_id` **et** `conversation_id` (A8,
  couvert par `test_chat_stream.py` l. 70-72) ; auto-titre streaming ; 7 `root.md` ; `ChatMarkdown.tsx` (var()
  uniquement, blockquote panneau « Analogy: », tables GFM) ; `AttachMenu.tsx` (2 items, ESC + clic-extérieur) ;
  `conversations/api.ts` ; refonte `Chat.tsx` conforme au spécifié : trombone actif pour tous (disabled UNIQUEMENT
  pendant upload), chips staged pointillées retirables, création conversation en amont, upload séquentiel
  **tout-ou-rien** (échec → message non envoyé, question restaurée), SSE : seule clé `message_id` ajoutée, rendu
  assistant via `<ChatMarkdown/>`, carte « Calcul vérifié », horodatages (user droite / « Dexter • hh:mm »), pouces
  (connecté + `messageId` + hors stream, `aria-pressed`, rollback sur échec), interception invité **avant tout
  appel réseau** (carte CTA register/login).
- Vérifications réelles : `alembic upgrade head` → EXIT 0 ; pytest ciblé → **17 passed** ; suite complète →
  **85 passed / 8 failed** (les 8 préexistants `test_auth`/`test_chat`, hors périmètre, intacts) ; `tsc --noEmit` →
  0 erreur ; `build:node` → EXIT 0 (354 modules, 1 047 KB / 287.7 KB gz — +48 KB gz, conforme à l'estimation
  validée).
- ❌ **BUG majeur (règles 6 et 7) — correctif requis** : Copilot a introduit des fallbacks par duck-typing dans
  `backend/app/services/conversations.py` (`_session_supports_persistence`, `_session_supports_query`, ids factices
  `conversation.id = 1` / `message.id = 1`, persistance silencieusement ignorée) et
  `backend/app/services/rag_service.py` (`hasattr(db, "query")` → `return []`). Cause : le harnais de
  `test_chat_stream.py` remplace la base par `SimpleNamespace()` vide (l. 27-28) — au lieu de corriger le harnais,
  Copilot a masqué le problème dans le code de production. Conséquence : les 3 premiers tests du fichier valident
  le **chemin factice**, pas le comportement réel ; toute session non-SQLAlchemy produirait des ids faux en
  silence. **Correctif proposé (en attente de GO)** : ① revert des 2 services vers du SQLAlchemy pur ; ② réécriture
  des 3 premiers tests par monkeypatch au niveau routeur (pattern du test 4 existant du même fichier :
  `create_conversation` id=42, `add_message` compteur user id=10 / assistant id=22, `build_conversation_context`,
  `update_conversation`, `search_documents`) avec assertions sur les valeurs des fakes (prouve le flux, pas des
  constantes) ; ③ suppression du résidu `backend/test_chat_stream.db` ; ④ re-run pytest + grep de contrôle.
- ⚠️ Mineurs frontend (non bloquants, correctifs au choix) : double habillage du bloc code (`pre` **et** `code`
  stylés → double padding) ; rôle ARIA invalide `menuitembutton` → `menuitem` ; sous-titre sans accents
  « OCR integre ». Noté sans changement : envoi de pièces jointes sans texte impossible (question exigée par le
  contrat backend).
- **En attente** : GO utilisateur sur les correctifs ❌/⚠️ → application → re-vérification → validation visuelle
  (règle 11).

### Diagnostic des 2 symptômes signalés sur l'écran Chat (23/09/2026) — EN ATTENTE DE GO

Méthode : diagnostic **par exécution** contre l'API réelle (uvicorn), pas par lecture de code.
Harnais : `backend/scripts/upload_test.py` (httpx — volontairement PAS un `TestClient`, pour mesurer exactement ce
que voit le navigateur). Rappel d'un piège déjà rencontré : `diagnostic_auth.py` utilise un `TestClient` en processus
et ne prouve donc rien sur le port 8000 réellement utilisé par le frontend.

**Preuves mesurées (backend Dexter lancé sur le port 8001, base `dexter`) :**

| Appel | Résultat observé |
|---|---|
| `GET /health` | HTTP 200 `{"status":"ok"}` |
| `POST /auth/register` | HTTP 400 « Email already registered. » (compte existant) |
| `POST /auth/login` | HTTP 200 + access_token (auth fonctionnelle) |
| `POST /conversations` | HTTP 201 (conversations fonctionnelles) |
| `POST /conversations/{id}/documents` (PNG) | **HTTP 422 « Document indexing failed. »** |
| `POST /conversations/{id}/documents` (TXT) | HTTP 201 en 2,7 s (modèle chaud) |
| `POST /chat/message` | HTTP 200, réponse LLM complète (`domaine=comptabilite`) |
| `POST /chat/stream` — « Explique-moi le bilan comptable » | 200, 1 117 événements `token` puis `done` |
| `POST /chat/stream` — « Quelle est la formule de la TVA ? » | **`{"type":"error","message":"Une précision est nécessaire avant de répondre."}`** |
| `POST /chat/stream` — « Comment calculer la TVA sur 1000 euros ? » | **`{"type":"error","message":"Le mode calcul reste synchrone."}`** |

**❌ BUG 1 — Upload d'images : 422 systématique.** Cause racine :
`document_extractor.extract_text()` (`backend/app/services/document_extractor.py`, l. 37-41) s'appuie sur `pytesseract`
pour `.png/.jpg/.jpeg`, mais le **binaire Tesseract OCR n'est pas installé** : `Get-Command tesseract` → rien,
`C:\Program Files\Tesseract-OCR\` et `C:\Program Files (x86)\Tesseract-OCR\` absents,
`pytesseract.get_tesseract_version()` → `TesseractNotFoundError: tesseract is not installed or it's not in your PATH`.
Toute image lève donc une exception → `index_document` propage → `documents.py` (l. 72-83) répond 422.
Confirmé en base : les 2 PNG de test ont `documents.statut_indexation = "erreur"` et **0 chunk**.

**✅ Statut A1 au 03/10/2026 — CAUSE RACINE CORRIGÉE ET VÉRIFIÉE (détail et preuves : section « Checkpoints de
revue » en fin de fichier).** Tesseract a été installé **hors dépôt** le 23/09/2026 (`.env` :
`TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe`, `TESSDATA_DIR=C:\Tools\tessdata`) → la cause décrite
ci-dessus (« binaire non installé ») est **périmée sur ce point**. Le 422 persistait néanmoins : `_ocr_arguments()`
passait `--tessdata-dir "<dir>"` à pytesseract, dont `shlex.split(config, posix=False)` (Windows) **conserve les
guillemets** → `Error opening data file "<dir>"/fra.traineddata`. Correctif retenu : la variable `TESSDATA_PREFIX`
(remède explicitement recommandé par le message d'erreur de Tesseract).


**❌ BUG 2 — « Impossible de converser » (3 causes cumulées, toutes reproduites).**
1. **Tout-ou-rien des pièces jointes** (`frontend/src/pages/Chat.tsx`, l. 316-334) : si l'upload d'une pièce jointe
   échoue, le code retire le message utilisateur ET la bulle assistant, restaure la question puis `return` → le
   message n'est **jamais** envoyé à `/chat/stream`. Comme l'upload d'image échoue **toujours** (BUG 1), joindre une
   image bloque **l'intégralité** de la conversation : les 2 symptômes signalés ont donc **une cause commune**.
   (Le tout-ou-rien est bien le comportement **spécifié** dans `PROMPT_COPILOT_CHAT_RICHE.md` l. 132 — il est correct,
   c'est la cause amont qui est fautive.)
2. **Clarification sans issue dans le flux SSE** (`backend/app/routers/chat.py`, l. 84-86) : quand le classifieur met
   `besoin_precision=True`, ou ne détecte pas de domaine, ou qu'un référentiel est requis, le flux émet
   `{"type":"error","message":"Une précision est nécessaire avant de répondre."}`. Le frontend (l. 401-406) supprime
   alors la bulle assistant et n'affiche qu'un texte discret au-dessus de la zone de saisie. L'événement d'erreur ne
   transporte **ni** `question_sous_themes` **ni** `referentiels_proposes` (contrairement à `/chat/message`, l. 226-237) :
   **l'utilisateur n'a aucun moyen de répondre à la demande de précision** → conversation bloquée. Aggravant :
   `classifier.classify` est **non déterministe** — la même question « Quelle est la formule de la TVA ? » a donné
   `domaine=null` / `besoin_precision=true` via `/chat/classify`, mais une réponse complète via `/chat/message`.
3. **Mode calcul jamais servi en streaming** (`backend/app/routers/chat.py`, l. 75-77) : toute question classée
   `intention="calcul"` émet `{"type":"error","message":"Le mode calcul reste synchrone."}`. Or le frontend n'appelle
   **que** `/chat/stream` (l. 346) et n'a **aucun repli** vers `/chat/message` — qui, lui, traite correctement le calcul.
   Ces questions n'obtiennent donc **jamais** de réponse dans l'interface.


**⚠️ CAUSE ENVIRONNEMENTALE MAJEURE — conflit de port 8000.** `netstat` : `127.0.0.1:8000 LISTENING` appartient à un
**autre projet** — `D:\Projets Edwin\BTS Projects\Sentinelle AIOPS\venv_env\...\python.exe -m uvicorn main:app --port 8000`.
`GET http://127.0.0.1:8000/` répond `{"status":"online","service":"Sentinelle AIOps","version":"1.0.0"}`, tandis que
`/health` et `/openapi.json` y répondent **404**. Comme il n'existe **aucun `frontend/.env`**, toutes les pages du
frontend appellent `http://localhost:8000` en dur (`Chat.tsx` l. 55, `AuthContext.tsx` l. 30, `Accueil.tsx`,
`Matiere.tsx`, `Profil.tsx`, `Recherche.tsx`, et les 4 `api.ts`) : si Sentinelle AIOps occupe 8000, **le frontend
Dexter parle à un autre backend** (auth/upload/chat en échec) et `start-dev.ps1` ne peut pas lier le port pour Dexter
(il teste `/health`, obtient 404 → tente de démarrer → port déjà pris). Dexter lui-même a été validé comme
**pleinement fonctionnel** en le lançant sur le **port 8001** (voir tableau ci-dessus).
**Action requise (règles 1 et 8 : aucun processus tiers arrêté d'initiative)** : arrêter le serveur Sentinelle AIOps,
ou convenir d'un `VITE_API_URL` / port dédié pour Dexter.

**⚠️ Mineur — latence d'indexation à froid.** Le **premier** upload après démarrage du backend dépasse 60-90 s
(import de `torch` / `sentence-transformers` + chargement de `intfloat/multilingual-e5-small`), alors que le modèle
est bien présent en cache local (`~/.cache/huggingface/hub`). À chaud : 2,7 s puis 9,9 s. Le document finit bien en
`indexe` côté serveur (vérifié en base : `diag_note.txt` → `indexe`, 1 chunk), mais le client a déjà abandonné →
l'utilisateur voit un échec. Piste (décision utilisateur) : précharger le modèle au démarrage, ou détacher
l'indexation de la requête HTTP.

**⚠️ Mineur (relevé, non touché — règle 8)** : `run_backend.bat` (racine) pointe encore vers une lettre de lecteur
obsolète (`cd /d "E:\Projets Edwin\...`), alors que le projet est sur `D:`. Sans effet sur `start-dev.ps1`, mais le
script est inutilisable en l'état.

**✅ Conforme (aucun écart constaté)** : authentification (register/login/token), CRUD conversations, génération LLM
réelle (`/chat/message` et `/chat/stream` pour une question hors clarification/calcul), chaîne RAG d'indexation des
documents texte, affichage des erreurs côté frontend (`errorMessage` l. 527, `documentsError` l. 569 — aucune erreur
n'est silencieuse).

**Statut : diagnostic terminé — AUCUN correctif appliqué (règle 1). En attente du GO utilisateur.**


### Libération du port 8000 + validation sur le port réel (23/09/2026) — GO utilisateur

Action demandée et autorisée explicitement : « détruire les émissions de Sentinelle pour libérer le port 8000 ».

- **Constat avant action** : plus aucun processus `*Sentinelle*` n'était vivant et **le port 8000 était déjà libre**
  (ils avaient quitté d'eux-mêmes entre-temps). **Aucun processus tiers n'a donc eu à être arrêté** par mes soins.
- **Nettoyage effectué** : arrêt du backend de diagnostic que j'avais lancé sur le port 8001 (PID 12612 et 21588) —
  c'étaient **mes propres** processus de diagnostic, pas ceux d'un autre projet.
- **Démarrage** : `start-dev.ps1` lancé détaché (`Start-Process … -ExecutionPolicy Bypass -File S:\start-dev.ps1`),
  ce qui démarre PostgreSQL (déjà actif), le backend sur **8000** et le frontend Vite sur **4173**.
- **Vérifications réelles après démarrage** :
  - `GET http://127.0.0.1:8000/health` → **200 `{"status":"ok"}`**
  - `GET http://127.0.0.1:8000/openapi.json` → **`"title": "Dexter API"`, version 0.1.0** → c'est bien **Dexter** qui
    occupe 8000 (plus Sentinelle AIOps), et la route `/conversations/{conversation_id}/documents` est présente.
  - `netstat` : `127.0.0.1:8000 LISTENING` (PID 17148, `S:\backend\.venv\Scripts\python.exe -m uvicorn app.main:app`)
    et `[::1]:4173 LISTENING` (Vite).
- **Diagnostic complet relancé sur le port 8000** (`C:\Tools\diag8000.py`, httpx) — **résultats identiques** à ceux du
  port 8001 : `LOGIN` 200 ; `UPLOAD_PNG` **422 « Document indexing failed. »** ; `UPLOAD_TXT` **201** ;
  `POST /chat/stream` « Explique-moi le bilan comptable » → 200 avec **1 101** événements `token` + `done` ;
  `POST /chat/stream` « Quelle est la formule de la TVA ? » → 200 avec **1 seul** événement `error`
  « Une précision est nécessaire avant de répondre. ». Le bug est donc bien **déterministe et reproductible** sur le
  port que le navigateur utilise réellement.

**⚠️ Nouvel enseignement (robustesse) — le chargement à froid bloque TOUT le backend.** Un premier run de diagnostic tué
au bout de 30 s (pendant le chargement de `torch` / `sentence-transformers`) a laissé le backend occupé : le
`POST /auth/login` du run suivant a alors **expiré** (aucune réponse en 60-180 s). Une fois le modèle chargé, le même
`/auth/login` répond en **0,6 s**. Cause : l'import de `torch` monopolise le GIL et les routes synchrones (`def`)
tournent dans le threadpool → **toutes** les requêtes sont retardées, pas seulement l'upload. C'est un argument
supplémentaire pour précharger le modèle au démarrage **ou** sortir l'indexation de la requête HTTP.

**Statut : environnement conforme (backend Dexter sur 8000 + frontend sur 4173) — diagnostic clos et reproductible.
Aucun correctif de code appliqué : GO attendu sur les options présentées.**


### Modernisation des tests + teardown SQLite sous Windows (28/09/2026) — Option A validée

Contexte : la suite pytest s'arrêtait sur `test_auth.py` (contrat obsolète) avant même d'atteindre les correctifs.
L'utilisateur a choisi l'**option A : adapter les tests au contrat réel de l'API** (aucun changement de l'API).

**Fait :**
- **`backend/tests/conftest.py` (nouveau)** : chaque session pytest utilise une base SQLite temporaire propre
  (env `DB_URL` posé avant import de l'app), fixture `isolated_test_database` (drop/create par test + override
  `get_db`). Teardown corrigé pour Windows : `app_engine.dispose()` en plus de l'engine local (l'engine de l'app
  pointe sur la même base temp et verrouille le fichier), puis suppression avec **10 retries × 0,3 s**, puis
  **`warnings.warn` visible avec le chemin** si le verrou persiste (règle 6 : rien de masqué).
- **`test_auth.py` réécrit** (7/7 ✅) : `POST /auth/register` → 201 **sans token** (contrat `UserRead`),
  tokens uniquement via `POST /auth/login`, profil sur **`GET`/`PATCH /users/me`** (l'ancien test appelait
  `/auth/me` → 404), mot de passe erronné de 12 caractères (≥ 8 imposé par `UserLogin` → sinon 422 au lieu de 401),
  suppression du hack `os.environ["DB_URL"]`/`create_all` en tête de fichier.
- **`test_chat.py` réécrit** (4/4 ✅) : diagnostic live prouvé que **le classifieur LLM est non déterministe**
  (même question « TVA 1000€ à 20% » → `domaine="comptabilite"` dans un run, `domaine=None` → clarification dans un
  autre). Réécriture selon le **pattern établi** (`test_chat_stream.py` / `test_chat_calcul.py`) : mock du
  classifieur + de `generate_answer`, **logique réelle conservée** (routing, extraction, dexter-calc).
  Assertions sur le contrat réel (`reponse`/`mode`/`domaine`/`calcul_result`, pas les clés legacy `domain`/`question`) :
  TVA → `calcul_result.result == 200.0` ; crédit → `13200.0` (intérêt `1200.0`) ; général → `mode == "explique_moi"`.
- **`test_chat_stream.py` / `test_calculators.py`** : suppression des hacks `os.environ["DB_URL"]` résiduels
  (no-ops trompeurs depuis l'arrivée du conftest) ; `test_auth.db`, `test_chat.db` (anciens) n'alimentent plus rien.
- **Artefact orphelin `%TEMP%\dexter_test_*.db` supprimé** : issu d'un run **tué à 30 s** (timeout outil) — un kill
  brutal exécute naturellement aucun teardown ; les 4 runs suivants (sortie normale) n'en ont laissé **aucun** (0 résidu).

**Vérifications réelles :** ciblé `test_chat + test_chat_stream + test_calculators` → **19/19** ; **suite complète →
93 passed / 0 failed (87 s)** ; `%TEMP%` → 0 fichier `dexter_test_*` ; PostgreSQL dev intact (override `get_db` partout).

**Signalements (règle 8 — constatés, non touchés, décision utilisateur) :**
1. `backend/test_auth.db` est **tracké par git** (modifié) et `backend/test_chat_stream.db` existe en non-tracké :
   artefacts de tests à supprimer + `.gitignore` dédié.
2. **Fragilité produit** : en live, le classifieur renvoie parfois `domaine=None` (TVA → clarification au lieu du
   calcul) et pour le crédit `sous_theme="analyse de crédit"` alors que le registry dexter-calc exige `sous_theme=="credit"`
   → `NoCalculatorFoundError` probable en production. À arbitrer côté produit (mapping sous_thèmes ou fuzz du registry).
3. `run_backend.bat` pointe toujours vers une lettre de lecteur obsolète (déjà signalé).

**Statut : suite backend 93/93 verts — cycle VALIDÉ par l'utilisateur le 28/09/2026 (règle 11). Les signalements
1 à 3 ci-dessus restent ouverts (décision utilisateur en attente).**

---

### Signalement n° 2 — branchement déterministe du calcul dans le stream (28/09/2026) — option 1+2+3B2 validée

Contexte : « calcule la TVA 1000 € à 20 % » répondait parfois par une clarification ou par des chiffres non
vérifiés, alors que la branche déterministe existait côté `/chat/message`. Diagnostic : `Chat.tsx` n'appelle QUE
`/chat/stream`, et cette route n'avait **jamais** branché le calcul déterministe (chemin LLM pur → risque de
chiffres inventés, PRD S6). Trois bugs identifiés ; périmètre **1 + 2 + 3B2** validé par l'utilisateur.

**Bugs corrigés :**
- **A (déterministe)** — `/chat/message` : le gate référentiel/`besoin_precision` était évalué **avant** la branche
  calcul → question de calcul bloquée en clarification. Le gate passe désormais **après** la branche calcul :
  l'autorité devient `champs_manquants`, qui est explicite.
- **B (déterministe)** — vocabulaire divergent : le classifieur renvoie `sous_theme="régularisation"` (TVA) ou
  `"analyse de crédit"` (crédit) alors que le registry dexter-calc exige `"tva"`/`"credit"` → `NoCalculatorFoundError`.
  Ajout d'un **repli domaine-seul** dans `chat_calculation.run_deterministic_calculation` : résolution sans
  `sous_theme` **uniquement si le domaine n'a qu'un seul outil enregistré** (comptabilité → TVA, banque → crédit),
  avec `logger.warning` visible ; `finance` (VAN + amortissement = 2 outils) reste un **échec explicite**, aucun
  choix arbitraire (règle 6).
- **C (racine architecturale)** — `/chat/stream` : branche calcul déterministe enfin branchée (nouveau
  `_stream_calcul_events`), placée avant le RAG, avec parité stricte du contrat sync : dexter-calc vérifie → les
  chiffres vérifiés sont injectés dans l'historique du LLM → réponse persistée en `mode_utilise="calcul"` ;
  paramètres manquants ou calculateur absent → **réponse explicite streamée en tokens** (jamais un événement d'erreur
  générique) et **non persistée** (parité sync). Nouvel événement SSE **`meta`** (`mode`, `domaine`, `sous_theme`,
  `referentiel`, `clarification_demandee`, `champs_manquants`, `calcul_result`). Code mort `needs_referentiel` du
  stream supprimé.

**Fichiers modifiés :**
- `backend/app/routers/chat.py` : réordonnancement sync ; `_stream_calcul_events` + branchement dans
  `_stream_chat_events` ; suppression du `needs_referentiel` mort.
- `backend/app/services/chat_calculation.py` : repli registry mono-outil (warnings visibles).
- `backend/tests/test_chat_calcul.py` : +3 tests (référentiel absent **et** `besoin_precision=True` → calcul ;
  sous-thème « régularisation » → `200.0` via repli ; `finance` ambigu → échec explicite **sans appel LLM**).
- `backend/tests/test_chat_stream.py` : +2 tests (`meta` + tokens vérifiés + `done` avec `message_id` ; paramètres
  manquants → `champs_manquants` explicites, aucun appel LLM, `done` sans `message_id`).
- `frontend/src/pages/Chat.tsx` : type d'événement `meta` + handler (~20 lignes) alimentant les panneaux **déjà
  codés** « Calcul vérifié » / « Précision nécessaire » (aucune maquette nouvelle, règle 3).

**Dépendances :** aucune nouvelle (règle 14 satisfaite : Python pur + pytest/TestClient + TypeScript déjà en place).

**Vérifications réelles :** ciblé `test_chat_calcul + test_chat_stream + test_chat_message` → **16/16** ;
**suite complète → 98 passed / 0 failed (70,3 s)** ; frontend `npm run build:node` → `tsc -b` **sans erreur** puis build
Vite OK (5,8 s) ; `%TEMP%` → aucun résidu de cette session (seul un `.db-journal` daté 20:34, antérieur à ce cycle,
subsiste et n'a pas été touché).

**Statut : correctifs appliqués et vérifiés automatiquement — VALIDATION UTILISATEUR EN ATTENTE (règle 11),
notamment le contrôle visuel du stream dans l'UI (mode « Calcul vérifié », panneaux chiffrés, clarifications).**


---

### Points de suite du 28/09/2026 — nettoyage, lanceurs, `meta` non-calcul, vérification live

Note d'intention (règle 4) présentée avant action : 5 points (redémarrage backend + vérification live,
résidu `%TEMP%`, signalement n° 1 `gitignore`/untrack, signalement n° 3 lanceurs obsolètes, limite
« `meta` émis seulement pour le calcul »).

**1. Résidu `%TEMP%`** — `dexter_test_*.db-journal` supprimé ; contrôle `Get-ChildItem %TEMP%\dexter_*` → **0** résidu
de base de test.

**2. Signalement n° 1 — artefacts de tests** — `.gitignore` racine complété (section « Tests » :
`backend/test_*.db`, `backend/test_*.db-journal`) ; `git rm --cached backend/test_auth.db backend/test_calculators.db`
(ces 2 fichiers étaient **trackés**) ; suppression physique de `test_auth.db`, `test_calculators.db`,
`test_chat_stream.db`. Contrôles : `git check-ignore -v` → les 3 fichiers ignorés (`backend/test_*.db`) ; plus aucun
`*.db` dans `backend/` ; `git status` → `D backend/test_auth.db` + `D backend/test_calculators.db` (index mis à
jour, **commit laissé à l'utilisateur**, règle 1). Sûreté vérifiée avant suppression : aucun code ni test ne lit
ces fichiers (grep : seules mentions documentaires dans `PROGRESS.md`).

**3. Signalement n° 3 — lanceurs obsolètes** — `run_backend.bat` **et** `run_backend.ps1` pointaient tous les deux
vers `E:\Projets Edwin\New\Chatbot & Calco\Dexter Chat AI\backend` (lettre de lecteur obsolète). Corrigés en chemins
**relatifs au script** : `cd /d "%~dp0backend"` et `Join-Path $PSScriptRoot 'backend'` ; flags d'origine conservés
(`--host 127.0.0.1 --port 8000 --reload`). Preuve réelle : le backend de cette session a été démarré **par ce
`.bat` corrigé** → `GET /health` → 200.

**4. Limite signalée — `meta` pour les intentions non-calcul** — `_stream_chat_events` émet désormais le `meta`
**avant les tokens** pour tout le chemin non-calcul : `mode` = `mes_cours` si un document RAG est trouvé sinon
`explique_moi`, `domaine`/`sous_theme`/`referentiel` issus de la classification, `clarification_demandee=False`,
`champs_manquants=[]`, `calcul_result=None`. La persistance du message assistant utilise la **même** variable
`response_mode` (plus aucune divergence entre le `meta` et `mode_utilise` en base). `Chat.tsx` gérait déjà ce cas
(handler `meta` du cycle précédent, `event.mode ?? …`) → **aucune retouche front**. Tests : 3 tests d'ordre de
`test_chat_stream.py` mis à jour (`meta` en tête ; cas d'erreur → `[meta, error]`) + **1 test neuf**
(`test_chat_stream_meta_reports_mes_cours_when_rag_finds_chunks`).

**Vérifications réelles :**
- Ciblé `test_chat_stream + test_chat_calcul + test_chat + test_chat_message` → **21 passed**.
- **Suite complète → 99 passed / 0 failed (69,6 s)** (98 précédents + 1 test neuf).
- `%TEMP%` → aucun résidu de base de test ; PostgreSQL natif redémarré (crash recovery après arrêt du 23/09) ;
  backend `:8000` + frontend `:4173` relancés et joignables (200/200).
- **Contrôle live du contrat SSE** (`%TEMP%\dexter_stream_live_check.py`, script de diagnostic hors dépôt,
  4 questions réelles + événements d'erreur affichés) :
  - **TVA complète** — passe 1 : `meta{mode=calcul, domaine=comptabilite, result=200.0}` + explication streamée ✓.
  - **Crédit complet** — passes 1 et 2 : `meta{mode=calcul, domaine=banque, sous_theme='analyse de crédit',
    result=13200.0}` + explication (2 723 / 2 919 chars) ✓ → le **repli registry mono-outil** fonctionne en live.
  - **Question générale** — passes 1 et 2 : `meta{mode=explique_moi, domaine=comptabilite, sous_theme=bilan,
    calcul_result=None}` + explication (3 726 / 3 643 chars) ✓ → point 5 validé en live.

**Signalements (règle 8 — constatés, non touchés, décision utilisateur) :**
1. **Classifieur live instable sur la TVA (le plus important)** — en passe 2, la même question TVA renvoie
   `domaine=None` (avec `sous_theme='calcul de la TVA'` ou `'régularisation'`) → la condition
   `classification.intention == "calcul" and classification.domaine` est fausse → **la branche déterministe est
   sautée** et la question repart en LLM pur (risque de chiffres non vérifiés, PRD S6). Le repli mono-outil du
   registry ne peut pas aider ici : il exige un `domaine` renseigné. Options (à arbitrer, règle 13) :
   **A** exposer `intention` (et le `sous_theme` brut) dans le `meta` pour rendre la cause visible dans l'UI ;
   **B** si `intention == "calcul"` et `domaine is None` : demander une précision au lieu de générer ;
   **C** repli déterministe `sous_theme` → `domaine` par mots-clés (`tva`, `calcul de la tva` → comptabilité) ;
   **D** ne rien changer.
2. **Cause des erreurs de stream non journalisée (règle 6)** — `routers/chat.py` (`except Exception:` l. 271, chemin
   unique des deux helpers de stream) renvoie `{"type": "error", "message": "La génération de la réponse a
   échoué."}` **sans aucun log**. Observé en live : les 2 questions TVA de la passe 2 ont renvoyé cet événement
   avec **0 token** (échec du provider LLM) et aucune trace exploitable côté serveur. Correctif proposé (1 ligne
   par `except`) : `logger.exception("Stream generation failed (question=%r)", payload.question)` avant le `yield`
   d'erreur — ajout de `logger = logging.getLogger(__name__)` dans le module (aucun `logging` importé aujourd'hui).
3. `backend/pytest_stream_out.txt` (non suivi, antérieur à ce cycle) et `stitch_dexter_ai_educational_platform/`
   restent hors périmètre.

**Statut : 5 points traités et vérifiés automatiquement (règle 11) — VALIDATION UTILISATEUR EN ATTENTE.** Backend et
frontend sont **lancés** (`:8000` / `:4173`) pour le contrôle visuel : question TVA → panneau « Calcul vérifié »,
crédit → idem, question générale → badge « Explication » correct, TVA sans taux → « Précision nécessaire ».
Les 2 signalements ci-dessus peuvent affecter ce contrôle visuel (TVA dépendante du classifieur) et restent
**ouverts** faute d'arbitrage.

---

## Cycle 2 du 28/09/2026 — régression « nouvelle conversation » corrigée + journalisation des erreurs de stream

**Contexte / traçabilité de l'état du dépôt.** Pendant cette session, `backend/app/routers/chat.py` **et**
`backend/tests/test_chat_stream.py` ont été réécrits par un **rédacteur externe** (copie de travail VS Code) à
`22:52:34`, soit **après** mes propres écritures de fin de cycle 1 (`PROGRESS.md`, `22:38:59`) et **avant** mes
correctifs (`22:57:36`). Ce travail externe ajoute notamment : branches de clarification dans le stream
(`besoin_precision` / `referentiel`), **persistance** des clarifications, helper de test
`_patch_stream_dependencies`, et ~80 lignes supplémentaires dans `chat.py` (553 → 635 lignes).

**❌ Régression prouvée (bloquante, chemin « nouvelle conversation »).** Dans la version externe de
`_stream_chat_events`, `history_context` et `classification = classifier.classify(...)` n'étaient assignés que dans
la branche `else` (conversation existante). Conséquence : toute requête **sans `conversation_id`** levait
`UnboundLocalError` à la première utilisation de `classification` (persistance du message utilisateur), capturée par
le `except Exception` → un seul événement `{"type": "error", "message": "La génération de la réponse a échoué."}`,
**aucune réponse, aucun `meta`**. Le front crée la conversation avant d'envoyer (`createConversation`), ce qui
**masquait** le bug dans l'UI, mais l'API et ma vérification live (qui poste sans `conversation_id`) étaient cassées.
Preuve : `pytest tests/test_chat_stream.py tests/test_auth.py` → **7 failed / 9 passed** (7 tests stream rouges ;
`test_chat_stream_sends_tokens_and_done` recevait `events[0] == {"type": "error"}` au lieu du `meta` attendu).
⚠️ Ce constat **invalide rétroactivement** le chiffre « **99 passed / 0 failed** » du cycle 1 ci-dessus : il a été
obtenu sur l'état de fichier **antérieur** à l'édition externe de `22:52:34`, qui a cassé ce chemin après coup.

**✅ Correctif 1 — structure du flux (`routers/chat.py`, l. 186-202).** `history_context = payload.historique`
initialisé avant le `if`, et `classification = classifier.classify(payload.question, history_context)` **sorti du
`else`** : le classifieur s'exécute désormais pour les deux chemins, en **parité stricte avec la route synchrone**
(`chat_message`, l. 384-393). Aucune autre logique modifiée.

**✅ Correctif 2 — plus d'erreur masquée (règle 6), signalement n° 2 du cycle 1 (`routers/chat.py`).**
`import logging` (l. 6) + `logger = logging.getLogger(__name__)` (l. 37) + dans le `except Exception` qui produit
l'événement d'erreur générique (l. 347-355) :
`logger.exception("Stream generation failed (question=%r, conversation_id=%r)", payload.question, payload.conversation_id)`.
Le client garde le message générique, le serveur obtient la question **et** la stacktrace complète. Cette cause
était bien celle observée en live au cycle 1 : le `raise ValueError("LLM returned an empty answer.")` explicite
(`_stream_calcul_events` l. 159, `_stream_chat_events` l. 326) produisait un « 0 token + error » non traçable.

**Vérifications réelles (protocole, point 4).**
- `python -m py_compile app/routers/chat.py` → **OK**.
- Ciblé `pytest tests/test_chat_stream.py` → **9 passed / 0 failed** (deux exécutions : 4,59 s et 5,46 s), contre
  **7 failed / 9 passed** avant correctif (mesure de référence prise avant toute modification).
- Suite complète `pytest -q` → **101 passed / 0 failed (83,51 s)**.
  *Transparence* : une exécution intermédiaire a produit `99 passed / 2 failed`
  (`test_chat_stream_asks_for_clarification_when_context_is_insufficient`,
  `test_chat_stream_calcul_missing_params_asks_explicitly`, `KeyError` sur `events[2]["message_id"]`). Non reproduit
  par les 3 exécutions suivantes (fichier seul x2 + suite complète) → attribué à une **course** entre l'écriture
  externe des fichiers (`22:57:36`) et l'import du module par pytest, **pas** au code.
- **Contrôle live** (`%TEMP%\dexter_stream_live_check.py`, script de diagnostic hors dépôt, 4 questions réelles,
  envoyées **sans `conversation_id`** — c'est-à-dire sur le chemin exact que le correctif 1 répare ; les événements
  `error` sont affichés) → **17/17 vérifications passées**, **aucun événement `error`** :
  - **TVA complète** : `meta{mode=calcul, domaine=comptabilite, sous_theme='régularisation',
    clarification_demandee=False}` + `calcul_result.result=200.0` (« TVA collectée sur HT ») + explication
    **3 105 caractères** ✓ (au cycle 1 ce cas renvoyait « error + 0 token »).
  - **TVA sans taux** : `meta{mode=calcul, clarification_demandee=True, champs_manquants=['taux de TVA'],
    calcul_result=None}` + réponse explicite streamée ✓.
  - **Crédit complet** : `meta{mode=calcul, domaine=banque, sous_theme='analyse de crédit'}` +
    `calcul_result.result=13200.0` + explication 2 356 caractères ✓ (repli registry mono-outil toujours bon en live).
  - **Question générale** : `meta{mode=explique_moi, domaine=comptabilite, sous_theme=bilan, calcul_result=None}` +
    explication 3 915 caractères ✓ (point 5 du cycle 1 confirmé).
- Frontend `http://localhost:4173/` → **200** (le serveur Vite répond sur `localhost`, **pas** sur `127.0.0.1`) ;
  backend `:8000/health` → `{"status":"ok"}`. Uvicorn tourne bien en `--reload` (`run_backend.bat`), donc le code
  corrigé est celui servi aux vérifications live.
- `%TEMP%` : **0 résidu** `dexter_test_*.db` (voir signalement 7).

**Nouveaux signalements (règle 8 — constatés, non touchés, décision utilisateur).**
4. **Docstring fausse + divergence de contrat sur les clarifications.** `_stream_calcul_events` l. 85 affirme
   encore « clarifications are not persisted, exactly like the sync route » alors que le code juste en dessous
   (l. 121-139) puis le chemin non-calcul (l. 268-276) **persistent** désormais la clarification. Conséquence réelle :
   `/chat/stream` persiste la clarification, `/chat/message` (route synchrone, l. 434-445) **ne la persiste pas** —
   les deux voies ne racontent plus la même histoire. À corriger (docstring) et à arbitrer (aligner la synchrone, ou
   ne rien persister côté stream).
5. **Un rédacteur externe écrit dans le dépôt pendant les sessions.** `chat.py` + `test_chat_stream.py` réécrits à
   `22:52:34` en plein cycle, `git status` montre ~30 fichiers modifiés (classes, messages/feedback, documents,
   frontend, prompts…) sans lien avec ce cycle. C'est la cause probable des 2 échecs transitoires et de la première
   capture de `UnboundLocalError`. Confirmation du mode de travail (qui écrit quoi, quand) souhaitée avant la suite.
6. `test_auth.py::test_register` et `test_auth.py::test_login_wrong_password` figurent dans
   `.pytest_cache/v/cache/lastfailed` (exécution antérieure non attribuée) mais **passent** dans mes 3 exécutions
   complètes → non reproduits, à surveiller.
7. Le dernier résidu `%TEMP%\dexter_test_*.db` observé a **disparu tout seul** entre deux mesures (23:08 → 23:10)
   sans intervention de ma part → indice supplémentaire d'un **processus de test externe** en cours d'exécution
   (cohérent avec le signalement 5).

**Statut : correctifs 1 et 2 appliqués et vérifiés automatiquement — VALIDATION UTILISATEUR EN ATTENTE (règle 11).**
Restent ouverts : signalement 1 (classifieur live instable sur la TVA — options A/B/C/D), signalement 4
(parité des clarifications + docstring), signalement 5 (mode de travail).

---

## Cycle 3 du 28/09/2026 — arbitrage utilisateur exécuté : option A (+ B) sur le signalement n° 1

**Décision utilisateur (règle 13)** : option **« A + B »** — exposer `intention` dans le `meta`, et si
`intention == "calcul"` sans `domaine` reconnu, **demander une précision au lieu de générer** (aucun chiffre non
vérifié, PRD S6).

**A — `intention` publiée dans les trois `meta` du stream (`routers/chat.py`).** Ajout de
`"intention": classification.intention` dans : le `meta` de la branche calcul (l. 112), le `meta` de clarification
non-calcul (l. 257) et le `meta` du chemin non-calcul standard (l. 307). Aucune autre clé modifiée.
Côté front, **aucune modification nécessaire** : `Chat.tsx` (l. 382-395) ne lit que les clés qu'il déclare et
ignore les clés supplémentaires ; **l'affichage** de `intention` dans l'UI reste à arbitrer séparément (règle 3 :
pas d'interface inventée sans maquette validée).

**B — `intention=calcul` + `domaine=None` ⇒ clarification, jamais de génération.** Analyse préalable : la condition
existante `besoin_precision or not classification.domaine or needs_referentiel` (`_stream_chat_events`, l. 239)
couvrait **déjà** ce cas côté code, mais **aucun test ne le verrouillait** pour `intention="calcul"` (le test
existant utilisait `intention="autre"` + `besoin_precision=True`). Verrouillage par un **test de non-régression
neuf** : `test_chat_stream_calcul_without_domain_asks_for_clarification`
(`tests/test_chat_stream.py` l. 382-445) — classification `intention="calcul"`, `domaine=None`,
`besoin_precision=False` ; le LLM ne doit **jamais** être appelé (le faux `_generate_stream` lève une
`AssertionError` s'il est atteint) ; attentes : `[meta, token, done]`, `meta{intention:'calcul', domaine=None,
clarification_demandee=True, calcul_result=None}`, réponse contenant « préciser », clarification **persistée**
(`message_id == 12`).
Réutilisation de l'UI existante (aucun composant inventé) : `Chat.tsx` affiche déjà « Précision nécessaire avant de
continuer. » dès que `clarification_demandee` est vraie (l. 507).

**Vérifications réelles.**
- `py_compile` sur `app/routers/chat.py` + `tests/test_chat_stream.py` → **OK**.
- Ciblé `pytest tests/test_chat_stream.py` → **10 passed / 0 failed** (les 9 précédents + le test B neuf).
- Suite complète `pytest -q` → **102 passed / 0 failed (75,19 s)**.
- **⚠️ Découverte opérationnelle majeure — le serveur `:8000` servait du code périmé.** Les processus uvicorn
  (PID 20108 watcher / 6516 worker / 22156 spawn) dataient du cycle 1 : le `--reload` **n'a rechargé ni les
  modifications externes de `22:52:34` ni mes correctifs de `22:57:36`**. Preuve : le `meta` servi ne contenait ni
  `intention` ni les clés de la branche de clarification, et la question TVA avec `domaine=None` partait encore en
  génération libre (`clarification_demandee: False`). *Conséquence : les vérifications live faites avant ce
  redémarrage ne testaient pas le code courant et ne doivent pas être comptées comme preuve.* Le serveur a été
  **arrêté puis relancé** avec la même commande que `run_backend.bat`
  (`python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`) et les logs capturés dans
  `%TEMP%\uvicorn_8000.log` / `uvicorn_8000_err.log`.
- **Contrôle live sur le serveur redémarré** (4 questions réelles, toujours **sans `conversation_id`**) :
  - **A validé** : `intention` est présent dans les trois formes de `meta`
    (`'intention': 'calcul'` et `'intention': 'explication'`).
  - **B validé en live** : TVA complète → classifieur instable (`intention='calcul'`, `domaine=None`,
    `sous_theme='calcul fiscal'`) → `meta{mode=explique_moi, intention:'calcul', domaine=None,
    clarification_demandee=True}` + demande de précision, **aucun événement `error`, aucune génération libre**.
    C'est exactement la protection visée (auparavant : `error` + 0 token, ou réponse libre non vérifiée).
  - TVA sans taux → `meta{mode=calcul, domaine=comptabilite, clarification_demandee=True,
    champs_manquants=['taux de TVA']}` ✓ ; crédit → `meta{mode=calcul, domaine=banque, result=13200.0}` ✓ ;
    question générale → `meta{mode=explique_moi, intention='explication', domaine=comptabilite}` ✓.
  - **Aucun `[SSE error]`** sur cette exécution ; logs serveur sans `Traceback` ni « Stream generation failed ».
  - Le script de diagnostic `%TEMP%\dexter_stream_live_check.py` (hors dépôt) compte **13/17** parce que ses
    attentes pour la question 1 sont **obsolètes** : il exige `mode=calcul` + `result=200.0`, alors que l'instabilité
    du classifieur conduit désormais (voulu) à une clarification. À réécrire au prochain cycle si on veut un
    harnais live 100 % vert.

**Signalements (règle 8 — constatés, non touchés).**
8. **`--reload` inopérant sur ce poste** : le processus backend a servi du code périmé pendant plus de 20 minutes
   sans aucun avertissement. Toute vérification live doit donc désormais être **précédée d'un redémarrage explicite**
   du backend (ou d'un contrôle qu'un marqueur de version est bien présent dans les réponses).
9. **La cause racine de l'instabilité du classifieur reste entière** : B protège (jamais de chiffres non vérifiés)
   mais l'utilisateur reçoit une **demande de précision** là où il attendait un calcul. L'option **C** (repli
   déterministe `sous_theme`/mots-clés → `domaine`, ex. « calcul fiscal » / « calcul de la TVA » → comptabilité)
   reste disponible, de même qu'un travail sur le prompt de classification — décision utilisateur.


### Correctif Chat — contexte des suivis et clarifications (28/09/2026)

Demande utilisateur : corriger l'échec visible après le suivi « Imagine les » et permettre à Dexter de comprendre le
contexte de la conversation et d'agir. Approche validée : fournir le contexte sauvegardé au classifieur, traiter
explicitement l'incertitude, puis consigner le résultat ici.

**Cause confirmée par tests de régression :**
- La voie `/chat/stream` classait la question avec seulement `payload.historique`, avant de charger les messages de la
  conversation. Un suivi court ne bénéficiait donc pas de l'échange précédent.
- Quand le classifieur ne trouvait pas de domaine exploitable, le flux poursuivait jusqu'au générateur LLM, qui
  échouait et produisait l'erreur générique visible à l'écran.
- Les textes de clarification (classification incertaine ou paramètres de calcul manquants) étaient streamés mais
  pas sauvegardés comme messages assistant. Le tour suivant ne pouvait donc pas les relire.

**Correctifs appliqués :**
- `backend/app/routers/chat.py` : résolution de la conversation et combinaison du contexte client avec l'historique
  sauvegardé avant l'appel au classifieur ; clarification SSE structurée quand le domaine/référentiel reste
  incertain ; persistance des clarifications de classification et de calcul ; `done` retourne l'identifiant du
  message assistant sauvegardé.
- `backend/tests/test_chat_stream.py` : tests de régression prouvant que le classifieur reçoit les deux sources de
  contexte et que les clarifications sont persistées et renvoyées avec leur `message_id`.
- `frontend/src/pages/Chat.tsx` : le panneau de précision affiche aussi les pistes de sous-thèmes et référentiels
  proposées dans l'événement SSE.

**Vérifications exécutées :** `tests/test_chat_stream.py` → **9 passed** ; TypeScript frontend
`tsc --noEmit -p tsconfig.app.json` → **0 erreur**. Le lancement des tests des autres modules depuis certains
terminaux a pris le Python global ou perdu le répertoire actif ; résultat de cette commande combinée non confirmé.

**Point produit restant à clarifier avant extension :** pour « Imagine les » après une demande de paramètres VAN,
le calcul déterministe ne dispose toujours d'aucune valeur numérique à extraire. Faut-il autoriser Dexter à proposer
des hypothèses fictives clairement étiquetées puis calculer leur résultat avec `dexter-calc`, ou doit-il continuer
à demander les valeurs réelles ? Aucun chiffre fictif n'est généré implicitement.

**Statut : correctif du flux de contexte et des clarifications appliqué ; validation visuelle et décision sur les
hypothèses fictives en attente.**

---

## Cycle 4 du 28/09/2026 (suite) — correctifs n° 4 et n° 9 (option C) + parité des clarifications

Demande utilisateur : « applique toutes les correctifs ; on fera les corrections visuelles plus tard ». Aucune
retouche front dans ce cycle (règle 3 respectée : `Chat.tsx` inchangé). **Aucune nouvelle dépendance** (règle 14) :
tout est fait avec `unicodedata` / `re` (bibliothèque standard) et l'existant.

**✅ Correctif 3 — signalement n° 4, docstrings fausses (`app/routers/chat.py`).**
`_stream_calcul_events` n'affirme plus « clarifications are not persisted, exactly like the sync route » (faux :
le stream les persistait déjà) et `_handle_calcul_branch` ne prétend plus que « the streaming route » consomme son
`message_id` (le stream ne l'appelle pas). Les deux docstrings décrivent désormais le comportement réel.

**✅ Correctif 4 — signalement n° 9, option C (repli déterministe du domaine calculable).**
- `app/services/chat_calculation.py` : `_normalize_for_matching` (minuscules + accents retirés via NFKD),
  `_matches_vocabulary` (correspondance **en début de mot** : `van` ne matche pas `avant`) et
  `infer_calcul_domain(question, classification)`.
- Source de vérité : le **vocabulaire du registre des calculateurs** (`tva`, `credit`, `van`, `amortissement`) — et
  **non** `domains.json`, car `tva` n'y figure pas (constat vérifié : un repli par mots-clés de domaines aurait raté
  le cas TVA). Un domaine n'est renvoyé que s'il **gagne seul** ; sinon `None` → on continue de demander une
  précision (règle 6).
- `app/routers/chat.py` : `_classification_with_inferred_domain` complète la classification (via `model_copy`)
  **uniquement** si `intention == "calcul"` et `domaine` vide, et il est appelé par **les deux routes**
  (`/chat/stream` l. 276, `/chat/message` l. 486) → parité.
- Contrôle unitaire hors test : TVA → `comptabilite` ; question sans vocabulaire → `None` ; « avant remise » →
  `None` ; `crédit` → `banque` ; `amortissement` → `finance` ; « VAN + crédit » → `None` (ambiguïté journalisée en
  `warning`).

**✅ Correctif 5 — signalement n° 4, fin de la divergence `/chat/stream` ↔ `/chat/message`.**
- Les textes de clarification ne sont plus dupliqués : `_referentiel_clarification`,
  `_unknown_context_clarification`, `_missing_params_clarification`, `_calculator_unavailable_clarification` sont
  partagés par les deux routes (c'est la duplication qui avait produit la divergence).
- `_persist_clarification` devient **l'unique voie de persistance** d'une clarification (utilisée par les 3 points
  de persistance du stream et par les 2 de la route synchrone).
- Direction retenue : **parité par persistance**. L'option inverse (ne plus persister côté stream) contredit le
  correctif validé au cycle précédent (« les textes de clarification étaient streamés mais pas sauvegardés »).
  Conséquence assumée : `/chat/message` renvoie désormais le texte de clarification dans `reponse` au lieu de
  `null` (1 assertion de `test_chat_message.py` mise à jour). Aucun impact visuel : le front n'appelle que
  `/chat/stream` (vérifié par recherche dans `frontend/src`).

**Tests (règle 5 : un correctif à la fois, chacun couvert).** `test_chat_stream.py` : le test B (cycle 3) devient le
**filet de sécurité** des questions sans vocabulaire calculable (question changée en « Peux-tu calculer un montant
pour ce dossier ? ») et **1 test neuf** couvre l'option C (TVA sans domaine → `comptabilite` + `result=200.0`, et le
domaine déduit est aussi celui sauvegardé). `test_chat_message.py` : **1 test neuf** de parité de persistance
(`user` puis `assistant` avec le même texte que le stream). `test_chat_calcul.py` : **1 test** de l'option C sur la
route synchrone + **3 tests unitaires** de `infer_calcul_domain` (vocabulaire du registre, accents/débuts de mot,
ambiguïté).

**Vérifications réelles (protocole, point 4).**
- `py_compile` sur `app/routers/chat.py`, `app/services/chat_calculation.py` et les 3 fichiers de test → **OK**.
- Ciblé `test_chat_stream + test_chat_message + test_chat_calcul + test_chat` → **30 passed / 0 failed**
  (deux fois : à 23:48, puis **rejoué après l'édition externe de `chat.py` à 23:54:17** → 30 passed en 17,77 s).
- Suite complète → **108 passed / 1 failed** : le seul échec est `tests/test_chat_rate_limit.py`, fichier
  **non suivi par git, créé par le rédacteur externe à 23:38:59** (encore modifié à 23:52:38) ; il vérifie un 429
  sur `/api/chat` (nouvelle route `api_router` du même rédacteur) et **n'exécute aucun de mes chemins**
  (`_stream_chat_events` y est intégralement remplacé) → échec hors périmètre, signalement 11.
- Backend `:8000/health` → `{"status":"ok"}`. Le serveur a été démarré à **23:19:36**, donc il sert **encore le code
  antérieur** à mes correctifs : les contrôles live restent à refaire après un redémarrage explicite (signalement 8).
- Frontend `http://localhost:4173/` → **inaccessible** (serveur Vite non lancé). Sans conséquence : ce cycle ne
  contient aucun changement front, et `Chat.tsx` n'est pas modifié.

**❌ Blocages constatés (aucun correctif appliqué : hors périmètre ou autorisation requise).**
10. **Venv inutilisable en l'état — toute la suite de tests échoue à la collecte.**
    `ModuleNotFoundError: No module named 'pkg_resources'` : `requirements.txt` **l. 20 pin `setuptools<82`**
    (précisément pour garder `pkg_resources`), or `setuptools 84.0.0` est installé, et **`limits` a été remplacé
    aujourd'hui à 23:38:53 par la version 2.4.0** (`limits/util.py` l. 8 `import pkg_resources`) — seule version de
    la série à en dépendre. Les tests passaient encore une heure plus tôt : la régression vient donc de
    l'installation externe, pas du code.
    *Mesure temporaire explicitement étiquetée (règle 7), hors dépôt* : shim de diagnostic
    `%TEMP%\dexter_pkg_resources_shim\pkg_resources.py` (implémente `resource_string`) + `PYTHONPATH` sur ce
    dossier. Les vérifications ci-dessus l'utilisent. **Correctif définitif à valider (règle 10)** : soit
    `pip install "setuptools<82"` (restaure le pin déclaré), soit `pip install -U limits` (version sans
    `pkg_resources`). Aucun des deux n'a été exécuté.
11. **`tests/test_chat_rate_limit.py` (nouveau, non suivi) échoue** — attend `429` sur `/api/chat` après 20
    requêtes, obtient `200`. Travail en cours du rédacteur externe ; non touché (règle 8).
12. **`S:\` est un `subst` de `D:\Projets Edwin\New\Chatbot & Calco\Dexter Chat AI`** (`subst` → `S:\: => D:\...`).
    Les deux chemins désignent **un seul et même dépôt et un seul venv** : les processus de l'éditeur (jedi,
    `pip list` relancés depuis `d:\...\backend\.venv`) écrivent donc dans mon périmètre de travail.
13. **Signalement 5 confirmé par horodatage** : pendant ce cycle, le rédacteur externe a installé `limits`/`slowapi`
    (23:38:53), créé `app/rate_limiter.py` (23:42:45), créé `tests/test_chat_rate_limit.py` (23:38:59, modifié
    23:52:38) et **modifié `app/routers/chat.py` à 23:54:17, soit après ma suite complète**. Mes correctifs sont
    intacts dans cette version (marqueurs vérifiés par recherche, l. 71-678), mais deux rédacteurs concurrents sur
    le même fichier rendent toute vérification fragile : un couple « correctif → suite verte » peut être invalidé
    dans les minutes qui suivent.
14. **Signalement 8 précisé** : `S:` est un disque **local NTFS** (`subst` de `D:`) et `watchfiles` est **installé**
    → l'incohérence du `--reload` n'est pas expliquée par un disque réseau. À défaut d'explication, la règle
    « redémarrage explicite du backend avant toute vérification live » reste appliquée (aucun correctif de code
    proposé ici : `main.py` hors périmètre, règle 8).

**Statut : correctifs 3, 4 et 5 appliqués et vérifiés automatiquement (30 passed / 0 failed sur les 4 fichiers
concernés, rejoués après la dernière édition externe) — VALIDATION UTILISATEUR EN ATTENTE (règle 11).**
Vérifications live **bloquées** : le venv est cassé (signalement 10) et un redémarrage du backend échouerait à
l'import ; arbitrage demandé sur la réparation de l'environnement et sur la cohabitation avec le rédacteur externe.

### Complément du cycle 4 — environnement réparé (option 2 retenue par l'utilisateur)

1. **Réparation demandée explicitement** : `pip install "limits==5.8.0"` (version qui fonctionnait avant
   l'installation externe). pip a ajouté **2 dépendances transitives obligatoires** : `deprecated 3.0.0` et
   `wrapt 2.5.0`. Aucune autre installation n'a été faite (pas de `pip install -r`, pas de contrainte ajoutée).
2. **Vérifications d'intégrité** : `import app.main` → **OK sans le shim temporaire** ; `pip check` →
   *No broken requirements found*. Le shim de diagnostic `%TEMP%\dexter_pkg_resources_shim` a été **supprimé**
   (mesure temporaire de la règle 7 refermée).
3. **Suite complète sans shim → 110 passed / 0 failed (84 s)**. `tests/test_chat_rate_limit.py` (fichier du
   rédacteur externe, signalement 11) **passe désormais** : son échec précédent était donc bien causé par
   `limits 2.4.0` et non par du code. Découverte utile : la version de `limits` conditionne réellement l'émission
   du `429`, donc toute anomalie de limitation d'API doit être imputée à l'environnement avant le code.
4. **Backend redémarré explicitement** (les processus de 23:19:36 servaient encore le code antérieur) ;
   `GET /health` → `{"status":"ok"}` sur le code courant.
5. **Contrôle live toujours impossible — cause désormais identifiée et hors code (signalement 15)** :
   PostgreSQL n'écoute plus sur `localhost:5432` (`DB_URL=postgresql+psycopg2://***:***@localhost:5432/dexter`),
   `POST /auth/login` → **500** et le harnais `%TEMP%\dexter_stream_live_check.py` a été interrompu par
   `httpx.ReadError: [WinError 10054]`. Aucun service PostgreSQL n'est déclaré sur la machine, `pg_ctl` est absent
   du `PATH` et **le démon Docker n'est pas démarré** (`docker ps` → « failed to connect to the docker API ») —
   or `docker-compose.yml` déclare le service `postgres` (`pgvector/pgvector:pg16`, port 5432). Le contrôle live
   exige donc de démarrer Docker Desktop puis le service `postgres` : décision utilisateur (action sur la machine,
   hors dépôt).
6. Aucun fichier `app/**/*.py` n'a été modifié par le rédacteur externe depuis **00:00** : mes correctifs sont
   donc, de fait, figés dans la version actuellement testée et servie.

### Clôture du cycle 4 (décision utilisateur)

Décision enregistrée : **on s'arrête là pour cette session** — la vérification automatique (**110 passed /
0 failed**) est jugée suffisante ; **le contrôle live et les corrections visuelles sont reportés à une prochaine
session** (aucun harnais live supplémentaire n'a donc été exécuté, signalement 15 laissé ouvert).

**Statut du cycle 4 : correctifs 3, 4 et 5 appliqués, compilés, testés et servis par le backend redémarré —
VALIDATION UTILISATEUR EN ATTENTE (règle 11).** À confirmer ou veto :
- direction retenue pour la **parité** des clarifications : **persistance** côté `/chat/message` (son champ
  `reponse` n'est plus `null` en cas de clarification ; l'option inverse contredisait le correctif validé au
  cycle précédent) ;
- **option C** : une demande de calcul à `domaine=None` dont la question contient le vocabulaire du registre
  reçoit désormais un **calcul vérifié** ; le test B du cycle 3 est devenu le filet de sécurité des questions sans
  vocabulaire calculable.

### Validation de l'utilisateur — cycle 4 clôturé

Validation explicite reçue : **correctifs 3, 4 et 5 acceptés**, ainsi que la **parité par persistance**
(`/chat/message` persiste et renvoie sa clarification) et l'**option C** (repli déterministe du domaine via le
registre des calculateurs). Le cycle 4 est clos ; les vérifications automatiques font foi
(**110 passed / 0 failed**, `py_compile` OK).

État constaté à l'ouverture de la session suivante :
- le mappage `subst S:` n'est **plus actif** (`subst` vide) → le dépôt est travaillé via
  `D:\Projets Edwin\New\Chatbot & Calco\Dexter Chat AI` (chemin réel, `PROGRESS.md` = même fichier qu'au cycle 4) ;
- les marqueurs des correctifs 3/4/5 sont toujours présents dans `backend/app/routers/chat.py`
  (lignes 152, 162, 298, 512, 515, 617, 634) et `py_compile` passe → code intact ;
- **le backend n'est plus lancé** (aucun processus `uvicorn`, `GET /health` injoignable) : les processus de la
  session précédente ont été arrêtés entre-temps ;
- `docker` et `postgresql:5432` toujours hors service (signalement 15 inchangé).

**Prochaine étape proposée (règles 1 et 5, en attente d'autorisation)** : remise en route live — démarrage de
Docker Desktop, `docker compose up -d postgres`, redémarrage explicite du backend, rejeu de
`%TEMP%\dexter_stream_live_check.py`. Action machine hors dépôt : je ne la lance pas sans accord explicite.

**À faire ensuite (ordre proposé, une étape à la fois)** : arbitrer les signalements 5 / 12 / 13 (cohabitation
avec le rédacteur externe) ; décider des corrections visuelles (exposer `intention` dans l'UI, règle 3).

### Remise en route live — cycle 4 (étapes 1 à 3 du plan, autorisées « A »)

Démarrage et vérifications réalisés le 02/10/2026 (ordre respecté, une étape à la fois) :

1. **Docker Desktop démarré** (moteur 29.8.0 prêt). Aléas rencontrés et résolus sans modifier le dépôt :
   - le pull de `pgvector/pgvector:pg16` est resté bloqué à 0 B à trois reprises (le registre et le CDN
     répondaient en TCP) ; une erreur DNS transitoire dans la VM Docker a été observée au passage
     (`lookup registry-1.docker.io: no such host`), puis `hello-world` a été tiré avec succès — **quatrième
     essai de pull = succès** ; rien à installer ni à reconfigurer ;
   - le conteneur `dexterchatai-postgres-1` est apparu **déjà Running/healthy** au `compose up` (politique de
     redémarrage) — il tourne depuis le démarrage de Docker Desktop avec reprise automatique
     (`database system was not properly shut down; automatic recovery in progress` → prêt).
2. **Backend redémarré explicitement** (anciens processus uvicorn arrêtés, puis `uvicorn app.main:app
   --host 127.0.0.1 --port 8000` sans `--reload`) → `GET /health` = `200 {"status":"ok"}`.
3. **Cause racine du 500 sur `/auth/login` trouvée et corrigée par la procédure documentée** : la base `dexter`
   contenait **0 table** (`relation "users" does not exist` dans les logs) — c'est la vraie raison du 500,
   Postgres n'étant que l'outil de stockage. `python -m alembic upgrade head` appliqué (README ligne 188) :
   **6 migrations → 10 tables**, `alembic current` = `202409060000` (head). Base préalablement vide → aucune
   donnée perdue. Aucun code modifié.
4. **Harnais `%TEMP%\dexter_stream_live_check.py` rejoué → 18/18 vérifications passées** :
   - 1) TVA complète : meta en tête, `intention=calcul` (option A), `mode=calcul`, `domaine=comptabilite`,
     `result=200.0`, pas de clarification, explication non vide ;
   - 2) TVA sans taux : `clarification_demandee=True`, `champs_manquants=['taux de TVA']`, aucun
     `calcul_result` (filet de sécurité intact) ;
   - 3) Crédit : `mode=calcul`, `result=13200.0` ;
   - 4) Question générale : `mode=explique_moi`, `intention=explication`, aucun `calcul_result`.
   - **Signalement 15 : CLOS** (contrôle live de bout en bout : login → SSE → persistance).
5. Observations **signalées, non corrigées** (règle 8, hors périmètre) :
   - `calcul_result.unit` = `'€'` alors que la question exprime des **FCFA** (l'explication LLM, elle, affiche
     FCFA) — divergence unité monétaire entre le résultat chiffré et le texte ; idem `unit='€'` côté crédit ;
   - `sous_theme='régularisation'` en meta pour une question de TVA courante (le `calcul_result.sous_theme`
     correct, `'tva'`, est lui cohérent) — le meta suit un autre signal que le calcul ;
   - l'affichage mojibake (`rÃ©gularisation`) dans les sorties PowerShell est un **artefact de console**
     (encodage de la fenêtre), pas un défaut du backend : le harnais force UTF-8 et les vérifications passent.

**Statut : remise en route live terminée — 18/18 au harnais. VALIDATION UTILISATEUR EN ATTENTE (règle 11)**
pour ces étapes ; signalements restants ouverts : 5 / 12 / 13 (cohabitation rédacteur externe) + les deux
observations d'unité/sous_theme ci-dessus à arbitrer.

### Validation de l'utilisateur — remise en route live (étapes 1 à 3)

Validation explicite reçue pour les étapes 1 à 3 ci-dessus (Docker + postgres, backend, migrations, harnais
18/18). **Signalement 15 clos et acté.** Consigne complémentaire de l'utilisateur : *« le reste prend des
décisions adéquates mais présente-les moi avant »* → les décisions restantes (observations unité/sous_theme,
signalements 5/12/13, exposition d'`intention` dans l'UI) font l'objet d'une **feuille de décisions à présenter
avant toute application** ; aucune correction n'est appliquée sans validation explicite (règles 1 et 13).

### Arbitrage utilisateur — feuille des 4 décisions, puis application (cycle 5)

Arbitrage reçu : **« Prend toutes les actions que tu recommande »** → actées les options recommandées :
**1A** (devise détectée dans la question), **2A** (clé `sous_theme_effectif`), **3C+A** (base git de référence
puis discipline de cohabitation), **4A** (report de l'affichage `intention`). Actions réalisées dans l'ordre,
une chose à la fois :

1. **Décision 3C — base git de référence** : commit local `9fe5374` (« Base de reference: etat du depot avant
   correctifs unites/sous_theme », 77 fichiers, aucun secret — `.env` et `Documentation Dexter/API Key.txt`
   sont ignorés), arbre propre constaté ensuite. Tout écart externe futur apparaîtra en `git diff` (pas de
   push effectué).
2. **Décision 1A — la devise de la question prime sur `unit="€"`** (`backend/app/services/chat_calculation.py`) :
   table `_CURRENCY_LABELS` (FCFA, XAF, XOF, EUR/€, $/USD, ordre de priorité) + `_extract_currency_label()`,
   appliquée dans `run_deterministic_calculation()` juste avant le `return "ok"` — **les deux chemins de succès**
   (calcul direct et repli domaine-seul) sont couverts. Sans devise explicite, le défaut du calculateur est
   conservé. Les calculateurs dexter-calc ne sont **pas** modifiés (périmètre : seul `calcul_result.unit` change,
   ce qui aligne figure, bloc prompt `build_calculation_context()` et panneau UI `Chat.tsx:521`).
3. **Décision 2A — `sous_theme_effectif` dans le `meta` du branch calcul** (`backend/app/routers/chat.py`,
   `_stream_calcul_events`) : clé additive = `calcul_result.sous_theme` (registre dexter-calc), `None` quand il
   n'y a pas de résultat. `meta.sous_theme` (classifieur) est laissé tel quel — sources volontairement
   distinctes. **Périmètre** : seul l'événement `meta` de la branche calcul porte la clé ; les `meta`
   `explique_moi`/`mes_cours` (où `calcul_result` est toujours `None`) ne l'ont pas — signalé, pas étendu de
   ma propre initiative (règle 8).
4. **Décision 4A — report** : l'affichage de l'`intention` dans l'UI reste reporté faute de maquette dans
   `documentation/` (règle 3). Aucun fichier front touché.
5. **Signalement 12 : CLOS** — le mappage `subst S:` est obsolète (constaté : `subst` vide, dépôt travaillé via
   `D:\Projets Edwin\New\Chatbot & Calco\Dexter Chat AI`), il ne désigne plus aucun chemin actif.
6. **Signalements 5 et 13** : la partie outillage (C) est faite (base git) ; la partie discipline (A) engage
   le comportement du rédacteur externe et n'est pas un correctif technique — ils restent ouverts comme
   relais de vigilance (`git status` = nouveau réflexe avant chaque cycle).

**Vérifications réelles (aucun « ça devrait marcher ») :**
- `py_compile` sur `chat_calculation.py`, `chat.py`, `test_chat_calcul.py`, `test_chat_stream.py` → **OK** ;
- **suite complète `pytest -q` → 113 passed / 0 failed (76 s)** (110 précédents + 3 nouveaux tests : table de
  devise, question FCFA → `unit == "FCFA"`, absence de devise → défaut `€` conservé ; le test stream existant
  `sous_theme="régularisation"` asserte maintenant `sous_theme_effectif == "tva"`) ;
- serveur redémarré (l'exécution uvicorn tourne **sans `--reload`**, les éditions n'étaient pas servies) →
  `GET /health = 200 {"status":"ok"}` ;
- **harnais `%TEMP%\dexter_stream_live_check.py` rejoué → 18/18 vérifications passées**, en live :
  - TVA : `unit: 'FCFA'` (était `'€'`) + `sous_theme: 'régularisation'` / `sous_theme_effectif: 'tva'` ;
  - crédit : `unit: 'FCFA'` (était `'€'`) + `sous_theme_effectif: 'credit'` ;
  - TVA sans taux : `sous_theme_effectif: None`, filet de clarification intact ;
  - question générale : meta `explique_moi` inchangé (clé non présente, périmètre assumé).

**Observations résiduelles signalées, non corrigées (règle 8) :**
- la `pedagogical_note` du crédit contient encore « 1200.0 € sur 12 mois » (texte interne généré par
  dexter-calc) — 1A porte sur `calcul_result.unit`, pas sur les notes des calculateurs ;
- `sous_theme_effectif` absent des `meta` non-calcul (voir point 3).

**Statut (actualisé le 02/10/2026 — traçabilité) : cycle 5 appliqué et vérifié (113 tests + harnais 18/18), accepté de fait
via l'arbitrage « Les deux » du 02/10/2026 qui a fondé le cycle 6** (clôture de ses 2 observations résiduelles) ; signalement 12 clos, 5/13 en discipline de suivi, décision 4A reportée.

---

## Cycle 6 — 02/10/2026 : clôture des 2 observations résiduelles du cycle 5 (notes € + `sous_theme_effectif`)

**Périmètre validé (arbitrage utilisateur « Les deux » pour l'observation 1)** : (1) la `pedagogical_note`
du crédit en « € » → correctif **racine dexter-calc** ET **filet backend** ; (2) `sous_theme_effectif`
absent des `meta` non-calcul → clé ajoutée avec valeur `None`. Aucune nouvelle dépendance (règle 14).

### Lot A — correctif racine dexter-calc (installé en éditable, mods actives sans réinstallation)

- `core\calculator.py` : champ `display_currency: str | None = None` ajouté à `CalculationInput` ;
- `banque\credit_bon.py` : 2 notes (`run` + `derive`) → `devise = input_.display_currency or self.unit`
  inséré dans le texte (« Interet simple : {interet} {devise} sur … ») ;
- `finance\amortissement.py` : 2 notes (`run` + `derive`) → 4 occurrences `{devise}` ;
- `finance\van.py` : 1 note (`run`) → « VAN = {van} {devise} » ;
- `comptabilite\tva.py` : 2 `unit` (`calc` + `derive`) → `devise` (sa note ne porte pas de devise) ;
- **nouveau test** `dexter-calc\tests\test_display_currency.py` : 6 tests (credit run/derive, tva unit,
  van, amortissement run/derive, défaut « € » préservé sans devise explicite).

### Lot B — passage de la devise au calculateur + filet backend

- `calculator_service.py` : `display_currency=payload.get("display_currency")` transmis à `CalculationInput` ;
- `chat_calculation.py` (`run_deterministic_calculation`) : `_extract_currency_label(question)` extrait AVANT
  l'appel → `payload["display_currency"]` (la devise atteint le calculateur) ; puis filet de sécurité après
  calcul : `unit` forcé à la devise ET `pedagogical_note` débarrassée de tout « € » restant (couvre les
  calculateurs qui ignoreraient `display_currency`) ;
- **nouveau test** `test_chat_calcul_credit_note_follows_question_currency` : question crédit FCFA →
  note contient « FCFA », pas « € », `unit == "FCFA"` (couvre exactement l'observation 1382).

### Lot C — `sous_theme_effectif: None` dans les 2 `meta` non-calcul

- `chat.py` : clé ajoutée avec commentaire décision 2A dans le meta de clarification (l.~335) ET dans le
  meta général `explique_moi`/`mes_cours` (l.~382) ;
- `test_chat_stream.py` : `_EXPLIQUE_META` enrichi (égalité stricte des 3 tests qui l'utilisent) +
  assertion `sous_theme_effectif is None` dans le test clarification ET dans le test `mes_cours`.

### Lot D — vérifications réelles

- `py_compile` : **80 fichiers backend OK** + 6 fichiers dexter-calc OK ;
- **suite backend `pytest tests -q` → 114 passed / 0 failed (80,9 s)** (113 + 1 nouveau test note crédit) ;
- **dexter-calc `pytest dexter-calc\tests -q` → 13 passed** (7 TVA existants + 6 nouveaux) — lancé depuis
  `backend/` (voir menaces ci-dessous) ;
- uvicorn **redémarré** (anciens PID 2580/20880 arrêtés, nouveau PID 20052, sans `--reload`, PID dans
  `%TEMP%\dexter_uvicorn_pid.txt`) → `GET /health = 200 {"status":"ok"}` ;
- **harnais `%TEMP%\dexter_stream_live_check.py` étendu à 21 vérifications → 21/21 passées** en live :
  - crédit : `pedagogical_note = 'Interet simple : 1200.0 FCFA sur 12 mois. Taux : 10.0%.'` + `unit: 'FCFA'`
    → **observation 1382 CLOS** (avait « 1200.0 € sur 12 mois ») ;
  - meta clarification (TVA sans taux) : `sous_theme_effectif` présent = `None` ;
  - meta général (question générale) : `sous_theme_effectif` présent = `None` → **observation 1384 CLOS** ;
  - 15 vérifications précédentes toujours au vert (filets de clarification, order meta→tokens→done, etc.).

### Menaces et observations signalées (règles 6 et 8 — rien de masqué, rien hors périmètre)

> **Mise à jour cycle 7 (02/10/2026)** : les 4 observations de cette section ont été arbitrées par
> l'utilisateur (option A) et traitées — voir « Cycle 7 » plus bas.

- **Générateurs one-shot** : `dexter-calc\write_modules.py` et `dexter-calc\write_credit_bon.py` contiennent
  encore des notes « € » hardcodées et un chemin absolu `E:\` mort — **non modifiés** (règle 8 : aucune
  référence dans le code actif, exécution impossible). **Risque** : si quelqu'un les relançait, ils
  régénéreraient des modules sans `display_currency` et annuleraient le Lot A ;
- `dexter-calc\write_credit_bon.py` / `van_addition.py` : `van_addition.py` n'est pas enregistré dans le
  registre → hors périmètre, non modifié ;
- **Dossier `dexter_calc/` en doublon à la racine du dépôt** (tracké par git : `dexter_calc/core/exceptions.py`,
  sans `__init__.py`) : il interfère avec la collecte pytest **quand on lance depuis la racine**
  (`ModuleNotFoundError: dexter_calc.core.calculator`). La suite passe en lançant depuis `backend/` (cwd des
  cycles précédents). **Non supprimé** (règle 8) — à arbitrer par l'utilisateur ;
- **Nouveau (constat live)** : `calcul_result.display_currency` reste `None` dans le meta alors que la devise
  est FCFA — le champ `CalculationOutput.display_currency` (préexistant) n'est jamais renseigné par les
  calculateurs. Cosmétique (unité et note sont correctes) mais potentiellement trompeur à la lecture ;
  **non corrigé** (hors périmètre validé) — à arbitrer.

**Statut : cycle 6 appliqué et vérifié (114 tests backend + 13 dexter-calc + harnais 21/21) —
commité `79c206b` (arbre propre)** ; arbitrage utilisateur reçu le 02/10/2026 sur les 4 observations
ci-dessous → traitées au cycle 7.

---

## Cycle 7 — 02/10/2026 : clôture des 4 observations du cycle 6 (arbitrage « A »)

**Périmètre validé (règle 1 : autorisation explicite « Je valide l'action sur les points signalés » ;
arbitrage option A = tout supprimer)** : les 4 observations résiduelles du cycle 6 — (1) doublon
`dexter_calc/` racine ; (2) `calcul_result.display_currency` toujours `None` ; (3) générateurs one-shot
dangereux ; (4) `van_addition.py` mort. Aucune nouvelle dépendance (règle 14), rien hors de ce périmètre
touché (règle 8).

### Lot 1 — suppression du doublon `dexter_calc/` racine

- **Preuves avant suppression** : unique fichier `dexter_calc\core\exceptions.py` = **ancienne copie** des
  exceptions (sans le paramètre `code` exigé par le code actif), tracké uniquement par le commit initial
  `a326273`, sans `__init__.py` donc jamais importable comme paquet, et il prenait le dessus sur le vrai
  package quand pytest tournait depuis la racine ;
- `git rm -r dexter_calc` → l'import depuis la racine résout désormais le canonique
  `dexter-calc\dexter_calc\...` (vérifié : construction `CalculationError(..., code=...)` OK) ;
- **Vérification** : `pytest dexter-calc\tests` lancé **depuis la racine** (cassé au cycle 6) → **13 passed**.

### Lot 2 — `display_currency` renseigné (racine + filet, même duo que le cycle 6)

- **Racine — 7 sites `unit=devise` (exhaustivité vérifiée par recherche, zéro 8ᵉ site)** :
  `banque\credit_bon.py` ×2 (`calc` + `derive`), `comptabilite\tva.py` ×2, `finance\amortissement.py` ×2,
  `finance\van.py` ×1 (`run`) → `display_currency=devise` ajouté à chaque `CalculationOutput` — la devise
  réellement affichée est désormais lisible dans le champ dédié (défaut « € » sans devise explicite).
  `van.derive` (ICA, `unit=None`) reste `None` : indice sans devise, cohérent ;
- **Filet backend** : `chat_calculation.py` → `calcul_result["display_currency"] = currency_label` ajouté
  au filet décision 1A existant (commentaire mis à jour — le filet reste explicite, règle 7) ;
- **Tests** : assertions `display_currency` ajoutées dans `dexter-calc\tests\test_display_currency.py` (7 :
  devise explicite sur credit/tva/van/amortissement + défaut « € » sur credit et tva),
  `backend\tests\test_chat_calcul.py` (3 : crédit FCFA, TVA FCFA, défaut « € ») et
  `backend\tests\test_chat_stream.py` (1 : meta stream en « € ») — aucun test ajouté ni supprimé.

### Lot 3 — arbitrages option A : suppressions des débris

- `git rm` : `dexter-calc\write_modules.py` et `dexter-calc\write_credit_bon.py` (générateurs one-shot à
  notes « € » hardcodées et chemin `E:\` mort ; risque : une relance après correction du chemin aurait
  régénéré les calculateurs **sans** `display_currency`, annulant les Lots A du cycle 6 et 2 du cycle 7) ;
- `git rm` : `dexter-calc\dexter_calc\finance\van_addition.py` (débris **non importable** : aucune ligne
  d'import → `NameError` à l'import ; doublon du nom de classe `VANChatCalculator` de `van.py` ; s'il avait
  été « réparé et enregistré », il aurait créé un second outil « finance/van » ambigu dans le registre —
  `resolve()` choisit alors le premier inscrit, résultat aléatoire à la lecture) ;
- l'historique git conserve les 3 fichiers ; vérifié après suppression :
  `find_spec('dexter_calc.finance.van_addition') → None`, `van` et `credit_bon` importent OK.

### Lot 4 — vérifications réelles

- `py_compile` : **8 fichiers édités OK** ;
- **suite backend `pytest tests -q` → 114 passed / 0 failed** (relancée après les éditions, puis après les
  suppressions — 2 passes au vert, ~87 s) ;
- **dexter-calc → 13 passed**, lancé **depuis la racine** (nouveau, suite au Lot 1) **et depuis `backend/`** ;
- uvicorn **redémarré** (PID 20052 → **PID 21284**, sans `--reload`, PID dans `%TEMP%\dexter_uvicorn_pid.txt`)
  → `GET /health = 200 {"status":"ok"}` ;
- **harnais `%TEMP%\dexter_stream_live_check.py` étendu à 22 vérifications → 22/22 passées** :
  - TVA : `calcul_result.display_currency = 'FCFA'` (était `None`) ;
  - crédit : `calcul_result.display_currency = 'FCFA'` (était `None`) + note toujours en FCFA →
    **observation « display_currency = None » CLOS** ;
  - les 21 vérifications précédentes toujours au vert (`sous_theme_effectif`, filets, ordre des events…).

### Observations restantes signalées (règles 6 et 8 — rien de masqué)

> **Mise à jour cycle 8 (02/10/2026)** : cette liste a été intégralement traitée (arbitrage A) —
> voir « Cycle 8 » plus bas.

- **Les 4 observations du cycle 6 sont CLOSSES** (doublon racine supprimé, `display_currency` renseigné,
  générateurs et `van_addition.py` supprimés sur arbitrage A) ;
- `dexter-calc\dexter_calc.egg-info\SOURCES.txt` (tracké) référence encore `van_addition.py` : artefact
  **généré** par un build antérieur, déjà périmé (ne liste pas les tests récents) — régénéré automatiquement
  au prochain build ; **non édité à la main** ici (règle 8) ;
- hors périmètre, non touchés : `dexter-calc\check_registry.py`, `create_dirs.py`, `test_full.py`,
  `check_result.txt`, `test_write.txt` (utilitaires/trace trackés, sans référence dans le code actif) —
  à arbitrer si souhaité.

**Statut : cycle 7 appliqué et vérifié (114 tests backend + 13 dexter-calc + harnais 22/22) —
VALIDATION UTILISATEUR LE 02/10/2026 (règle 11)** ; commit de clôture effectué dans ce même commit
(hash visible dans `git log`, non auto-référençable ici).

---

## Cycle 8 — 02/10/2026 : nettoyage des résidus (5 utilitaires/trace + artefacts `egg-info`)

**Périmètre validé (règle 1 : autorisation « continuons avec les résidus » ; arbitrage utilisateur
« A » = tout supprimer + ligne gitignore)** : la liste des restants tracée en fin de cycle 7. Aucune
nouvelle dépendance (règle 14), aucun code exécutable de produit touché (règle 8).

### Enquête préalable (lecture seule, avant toute suppression)

- **Zéro référence dans le code actif** pour les 5 fichiers (recherche sur 388 fichiers : seules
  occurrences = cette note PROGRESS et `check_result.txt` qui mentionne `check_registry.py`) ;
- tous trackés **depuis le commit initial `a326273` uniquement**, jamais modifiés depuis ;
- constats individuels : `create_dirs.py` → chemin absolu mort `E:\…` (autre drive) qui recréerait des
  `__init__.py` vides ; `test_full.py` → doublon de démo **et buggé** (ligne 3 joint
  `…\dexter-calc\dexter-calc`, path inexistant) ; `check_result.txt` → trace d'`ImportError` ancienne ;
  `test_write.txt` → « test » ; `check_registry.py` → redondant avec la suite pytest (+ son
  `sys.path.insert` maison) ;
- **6 fichiers** `dexter_calc.egg-info/` étaient trackés (pas seulement `SOURCES.txt`) : artefacts
  setuptools périmés (ne listent ni les tests ni les fichiers supprimés au cycle 7) ;
- install éditable **moderne** confirmée dans `backend\.venv` (`__editable__.dexter_calc-0.1.0.pth` +
  finder, aucun `*.egg-link`) → le dossier `egg-info/` n'est pas requis pour les imports.

### Exécution

- `git rm` des 5 fichiers + `git rm -r dexter-calc\dexter_calc.egg-info` → **11 fichiers** retirés du
  suivi et du disque (historique git conservé) ;
- `.gitignore` racine : ligne `*.egg-info/` ajoutée à la section `# Python` (l. 16) — ajout de structure
  soumis avec l'option A et accepté (règle 10) : le prochain build régénérera l'egg-info **hors suivi**.

### Vérifications réelles

- `Test-Path dexter-calc\dexter_calc.egg-info → False` + `git check-ignore -v → .gitignore:16:*.egg-info/`
  → artefact absent du disque **et** désormais ignoré ;
- import venv backend : `find_spec('dexter_calc.finance.van_addition') → None`, `credit_bon` / `van`
  importent OK ;
- **suite backend `pytest tests -q` → 114 passed / 0 failed (78,9 s)** (après suppressions) ;
- **dexter-calc → 13 passed**, lancé depuis la racine ;
- uvicorn **inchangé** (aucun code édité → pas de redémarrage superflu ; PID 21284 toujours en service)
  → `GET /health = 200 {"status":"ok"}` ;
- **harnais live → 22/22** (`display_currency: 'FCFA'` toujours au vert) ;
- exhaustivité : `git ls-files` ne montre **aucun** cache/pyc/env tracké ; `git ls-files dexter-calc` ne
  contient plus que du code, des tests, `README.md` et `pyproject.toml`.

### Observations restantes signalées (règles 6 et 8)

- **la liste des résidus du cycle 7 est intégralement traitée** — plus aucun résidu connu ;
- hors périmètre et non touché : `dexter-calc\app\cli.py` — **pas un résidu** : déclaré comme console
  script officiel dans `pyproject.toml` (`dexter-calc = "app.cli:app"`, l. 12), donc potentiellement actif.

**Statut : cycle 8 appliqué et vérifié (114 tests backend + 13 dexter-calc + harnais 22/22) —
VALIDATION UTILISATEUR LE 02/10/2026 (règle 11)** ; commit de clôture effectué dans ce même commit
(hash visible dans `git log`, non auto-référençable ici).

---

## Checkpoints de revue « reste à faire » — 02-03/10/2026

Revue conduite **par checkpoints**, chacun marqué par l'utilisateur après correction d'un événement vérifiable.
Ordre arbitré avec l'utilisateur (règle 13) : traçabilité (F) → **A1** OCR → A3/A4 + 4A → features différées (C) / V1.

### CheckPoint 1 — traçabilité — VALIDÉ PAR L'UTILISATEUR (02/10/2026)

3 statuts périmés de ce fichier actualisés, sans inventer aucune validation (lecture seule, aucun code touché) :
l. 49-51 (Phase 0 → « Voie B en service et acceptée de fait »), l. 156-158 (RAG → « aucune validation explicite
tracée » + jalons datés), l. 1390-1391 (cycle 5 → « accepté de fait via l'arbitrage "Les deux" du 02/10/2026
fondant le cycle 6 »). Consigne utilisateur : **pas de commit à ce stade** (commit groupé, à sa demande — règle 11).

Découverte signalée hors périmètre, **non touchée** (règles 8 et 13) : 6 statuts « VALIDATION UTILISATEUR EN
ATTENTE » historiques (l. 873/943/1030/1227/1263/1294) — deux disposent d'une validation postérieure tracée
(l. 1271/1333), les cycles 1-3 étant probablement implicites → **checkpoint 1-bis en attente d'arbitrage**.

### CheckPoint 2 — A1 « upload d'images » — CORRIGÉ, VÉRIFIÉ ET VALIDÉ PAR L'UTILISATEUR (03/10/2026)

Arbitrage utilisateur (règle 13) : **option A** — variable `TESSDATA_PREFIX` posée par le service (robuste aux
espaces dans le chemin) **+** test de non-régression.

**État réel constaté par exécution (règle 2), avant toute édition :**
- Tesseract **est installé** : `pytesseract.get_tesseract_version()` → `5.4.0.20240606` ; `C:\Tools\tessdata`
  contient `fra.traineddata` (14 213 351 o), `eng`, `osd` ; `.env` modifié le **23/09/2026 22:16:44** ;
- le tessdata **par défaut** (`C:\Program Files\Tesseract-OCR\tessdata`) ne contient **pas** `fra` → aucun repli
  possible sans `TESSDATA_DIR` ;
- backend en service redémarré le **02/10/2026 22:23:09** (donc `.env` bien pris en compte) ;
- **bug toujours actif** : `extract_text()` sur une image valide levait `TesseractError (1, 'Error opening data file
  "C:\Tools\tessdata"/fra.traineddata … Failed loading language fra')` ;
- **cause racine** : `pytesseract/pytesseract.py` l. 267 → `shlex.split(config, posix=not_windows)` ; sous Windows
  `posix=False` **conserve les guillemets** produits par `_ocr_arguments()` → chemin invalide pour Tesseract.

**Correctif appliqué (option A) :**
- `backend/app/services/document_extractor.py` : `_configure_tesseract()` exporte désormais
  `os.environ["TESSDATA_PREFIX"] = settings.tessdata_dir` (commentaire du piège de quoting) ; `_ocr_arguments()`
  supprimée et `config=_ocr_arguments()` retiré de l'appel `image_to_string()` ;
- `backend/tests/test_document_extractor_ocr.py` (**nouveau**) : 2 tests — export de `TESSDATA_PREFIX` et OCR réel
  d'un PNG généré en mémoire, avec *skip* explicite et motivé si le moteur ou les données de langue sont absents.
Aucune dépendance nouvelle (règle 14) ; aucune zone hors périmètre modifiée (règle 8).

**Vérifications réelles :**
- `py_compile` des 2 fichiers → OK ;
- `pytest tests/test_document_extractor_ocr.py tests/test_documents.py -q` → **8 passed** (2 nouveaux non skippés) ;
- **suite backend complète → 116 passed / 0 failed (80,2 s)** (114 précédents + 2 nouveaux) ;
- **preuve live avant/après sur l'API réelle** (backend redémarré — uvicorn **PID 14364** en écoute, `/health` → 200 ;
  `Start-Process` avait rapporté le PID du lanceur 20912), PNG **contenant du texte** généré en mémoire et envoyé
  en httpx :
  - *avant* (ancien code) : `POST /conversations/21/documents` → **HTTP 422** `Document indexing failed.`
    (document #1 : `statut_indexation="erreur"`) ;
  - *après* (code corrigé) : `POST /conversations/23/documents` → **HTTP 201**, corps
    `{"id":3,…,"statut_indexation":"indexe"}` (documents #2 et #3 : `indexe`).

**Découverte complémentaire (explique une partie du rapport initial) :** le PNG 1×1 de
`backend/scripts/upload_test.py` est **corrompu** (CRC IHDR invalide) → journal backend
`OSError: broken data stream when reading image file`. Le symptôme « image → 422 » du 23/09 avait donc **deux
causes** : ce harnais (artefact de diagnostic) **et** le vrai bug de quoting (toute image valide échouait).

**Observations signalées, non corrigées (règle 8) :**
- message HTTP générique (`Document indexing failed.`) alors que la cause réelle n'existe que dans le journal
  (`_logger.exception`) → **piste A4** ;
- `backend/scripts/upload_test.py` embarque toujours son PNG corrompu (correctif de harnais non demandé) ;
- données créées dans la base de dev par la vérification : utilisateur 6 (`etudiant.test@dexter.dev`),
  conversations 21/22/23, documents 1-4, + 4 fichiers dans `backend/uploads/` (dossier ignoré par git) —
  **nettoyage non fait**, à la demande ;
- au premier appel à froid, la réponse d'upload n'est pas revenue dans la limite de 30 s de l'outil (chargement du
  modèle d'embedding) → **indice concret pour A2** (freeze à froid), non traité ici.

**Statut : correctif appliqué et vérifié par exécution — VALIDATION UTILISATEUR LE 03/10/2026 (règle 11).**
Consigne permanente à ce stade : **aucun commit** (commit groupé, à la demande de l'utilisateur) — l'état reste
`M PROGRESS.md`, `M backend/app/services/document_extractor.py`, `?? backend/tests/test_document_extractor_ocr.py`.
Suite de la revue actée par l'utilisateur : **CheckPoint 3 = A3 / A4 + décision 4A** (note d'intention à présenter,
GO à obtenir avant toute édition — règles 1, 4 et 13).


### CheckPoint 3 — A3 / A4 + décision 4A — APPLIQUÉ, VÉRIFIÉ ET VALIDÉ PAR L'UTILISATEUR (03/10/2026)

Arbitrage utilisateur (règle 13) : **GO sur le périmètre complet, options recommandées** — A3 par **discriminateur
explicite** (passeur de contexte React), A4 par **exception typée** (« fichier illisible » distinct d'une erreur
technique), puis choix du **code HTTP** comme discriminant (422 contenu / 500 serveur).

**Cadrage (constat de départ) :** `A3`/`A4` n'étaient définis nulle part dans ce fichier ; la note d'intention a donc
été présentée avec l'interprétation retenue (A3 = les 3 ⚠️ frontend de la revue l. 664-666 ; A4 = l'erreur masquée au
sens de la règle 6, piste déjà tracée en CP2 l. 1669) et validée par l'utilisateur **avant toute édition** (règle 1).

**A3 — état réel prouvé avant correction (règle 2) : deux observations sur trois étaient des faux positifs.**
- rôle ARIA : le code portait **déjà** `role="menuitem"` (`frontend/src/components/AttachMenu.tsx` l. 33) —
  `git log -S 'menuitembutton'` → **0 commit** : la chaîne invalide n'a jamais existé sur disque. Elle vient du
  **document** `PROMPT_COPILOT_CHAT_RICHE.md` l. 101, qui prescrit `role="menuitembutton"` ;
- accents : le code portait **déjà** « OCR intégré » (`AttachMenu.tsx` l. 82) — `git log -S 'OCR integre'` → **0 commit** ;
- **double habillage du bloc code : réel, mais plus étroit que décrit.** Sonde `node` sur `react-markdown@10.1.0`
  (rendu réel des 3 cas) : une clôture ``` **sans langage** produit un `code` aux props **identiques** à celles du
  code inline (`className === undefined`) **à l'intérieur** d'un `pre` déjà stylé → seule cette configuration cumulait
  les deux habillages (`bg` + `px-1` du `code` dans le `bg` + `p-4` du `pre`). `className` était donc inexploitable
  comme discriminant.

**Correctif A3 (1 fichier, `frontend/src/components/ChatMarkdown.tsx`) :** passeur de contexte
(`InsideCodeBlockContext`) posé par `pre` et lu par `code` → discrimination exacte, sans heuristique ; le `code` d'un
bloc ne porte plus que `block font-mono text-sm` (le `pre` reste seul propriétaire du visuel) et la classe
`language-*` est **conservée** pour un futur coloriseur. Aucune dépendance nouvelle (règle 14).

**Correctif A4 (3 fichiers + tests) — un échec serveur n'est plus présenté comme la faute de l'utilisateur :**
- `backend/app/services/document_extractor.py` : nouvelle exception typée `UnreadableDocumentError` (contenu que
  l'utilisateur peut corriger) ; extraction éclatée en `_extract_pdf` / `_extract_docx` / `_extract_pptx` /
  `_extract_image_text`, chacune convertissant **explicitement** ses échecs de contenu (`PyPdfError`,
  `OSError`/`ValueError`, `zipfile.BadZipFile`, `PackageNotFoundError`, absence de texte) ; `image.load()` force le
  décodage **avant** l'OCR — c'est là qu'un PNG tronqué échoue (constat de CP2) ; `pytesseract.TesseractError`
  (moteur ou langue manquants) est **laissé propager** = erreur serveur, jamais « fichier illisible » ;
- `backend/app/routers/documents.py` : deux branches distinctes — `UnreadableDocumentError` → **422**
  `"The document content is unreadable."` (`_logger.warning` portant la cause exacte) ; toute autre exception →
  **500** `"Document indexing failed."` (`_logger.exception`) ; statut `erreur` factorisé dans `_mark_indexing_failed()` ;
- `frontend/src/pages/Chat.tsx` : 422 → « Le contenu du fichier est illisible (fichier corrompu ou vide). Vérifiez le
  fichier puis réessayez. », 500 → « L'indexation a échoué côté serveur. Réessayez dans un instant. » ; le `switch`
  sur le code HTTP reste le **seul** point de décision (aucun couplage par chaîne) ;
- `backend/tests/test_documents.py` : **3 tests** ajoutés — contenu indécodable → 422 + statut `erreur` relu via
  l'API ; fichier sans texte → 422 ; échec serveur simulé (`embed_texts` défaillant) → 500.

**Vérifications réelles (aucun « ça devrait marcher ») :**
- `py_compile` (3 fichiers backend) → **EXIT 0** ;
- `pytest tests/test_documents.py tests/test_document_extractor_ocr.py -q` → **11 passed** ;
- **suite backend complète → 119 passed / 0 failed (82,06 s)** (116 de CP2 + 3 nouveaux, aucune régression) ;
- frontend : `tsc -b` → **EXIT 0** ; `vite build` → **EXIT 0** (354 modules) ;
- **sonde avant/après du correctif A3** (mêmes 3 cas rendus par `react-markdown`) : fence sans langage
  `INLINE(bg + px-1) dans BLOC(bg + p-4)` **avant** → `BLOC seul` **après** ; code inline inchangé ; `language-js`
  conservé ;
- **preuve live sur l'API réelle** (backend redémarré — launcher PID **18264**, worker en écoute port 8000 PID
  **23088** ; `/health` → 200) : PNG corrompu → **422** `{"detail":"The document content is unreadable."}` ;
  TXT sans texte → **422** même message ; TXT valide → **201** `statut_indexation="indexe"` ; statuts relus en base :
  `ok.txt=indexe`, `vide.txt=erreur`, `corrompu.png=erreur` ; journal serveur portant les causes exactes
  (« image file cannot be read: cannot identify image file », « does not contain extractable text »).

**Décision 4A :** report **maintenu** — affichage de l'`intention` dans l'UI impossible sans maquette dans
`documentation/` (règle 3). **Aucun fichier front touché pour 4A.**

**Observations signalées, non corrigées (règle 8) :**
- le **document** `PROMPT_COPILOT_CHAT_RICHE.md` l. 101 prescrit toujours `role="menuitembutton"` (rôle ARIA
  inexistant) : c'est le document qui est fautif, pas le code — correctif non demandé ;
- `status.HTTP_422_UNPROCESSABLE_ENTITY` est **déprécié** par Starlette (avertissement présent dans les journaux :
  « Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead ») — usage **préexistant**, non modifié ici ;
- `backend/scripts/upload_test.py` embarque toujours son PNG corrompu (harnais de diagnostic) ;
- **contrat d'API modifié** : un échec d'indexation *technique* d'upload répond désormais **500** (au lieu de 422) —
  tout consommateur externe doit en être informé ; seul le frontend du projet consomme cette route et il est à jour ;
- données créées dans la base de dev par la preuve live : utilisateur **7** (`a4-live-d7b699b4@dexter.dev`),
  conversation **24**, documents 5-7, fichiers dans `backend/uploads/` → **nettoyage non fait**, à la demande
  (s'ajoute à la liste CP2 : utilisateur 6, conversations 21/22/23, documents 1-4).

**Statut : correctifs appliqués et vérifiés par exécution — VALIDATION UTILISATEUR LE 03/10/2026 (règle 11)** ;
l'observation « nettoyage non fait, à la demande » a été traitée le même jour (voir la section suivante).
Périmètre git touché (aucun commit, consigne maintenue) : `PROGRESS.md`, `backend/app/routers/documents.py`,
`backend/app/services/document_extractor.py`, `backend/tests/test_documents.py`,
`frontend/src/components/ChatMarkdown.tsx`, `frontend/src/pages/Chat.tsx`,
`?? backend/tests/test_document_extractor_ocr.py`.
Prochaine étape de l'ordre arbitré : **features différées (C) / V1** (l. 1613), ou le **checkpoint 1-bis**.

### Nettoyage de la base de dev et des uploads — 03/10/2026 (demande explicite de l'utilisateur, règle 1)

**Périmètre demandé** : « Nettoie la base ». Inventaire **avant** action (lecture seule) sur PostgreSQL `dexter`
(conteneur Docker `dexterchatai-postgres-1`, image `pgvector/pgvector:pg16`) : la base ne contenait **que des
artefacts de harnais** — utilisateurs `live-*@test.com` (ids 1-5, harnais de stream du 02/10),
`etudiant.test@dexter.dev` (id 6, preuve live CP2), `a4-live-d7b699b4@dexter.dev` (id 7, preuve live CP3) ;
25 conversations (ids 1-25), 44 messages, 7 documents (`erreur` / `indexe`), 3 chunks ; **0** classe, **0** membre,
**0** quiz, **0** référentiel. Aucun compte ni contenu réel → périmètre de nettoyage retenu : **toutes les données**,
**schéma exclu**.

**Filet de sécurité** : `pg_dump` complet **avant** l'effacement →
`%TEMP%\dexter_dev_backup_avant_nettoyage.sql` (109 124 octets, copié depuis le conteneur puis vérifié sur disque ;
restauration possible par `psql -f`).

**Action** : `TRUNCATE TABLE document_chunks, documents, messages, conversations, quiz_attempts, classe_membres,
classes, user_domain_referentiels, users RESTART IDENTITY CASCADE;` (données seules, séquences remises à 1) ; puis
suppression des **99 fichiers** de `backend/uploads/` (7,05 Mo : 87 `.txt`, 11 `.png`, 1 `.jpg`), **dossier
conservé** (requis par `settings.upload_dir`).

**Vérifications réelles (exécutées, jamais « ça devrait marcher »)** :
- comptages après nettoyage : `users=0`, `conversations=0`, `messages=0`, `documents=0`, `document_chunks=0`,
  `classes=0`, `classe_membres=0`, `quiz_attempts=0`, `user_domain_referentiels=0` ;
- schéma intact : `\dt` → **les 10 tables** toujours présentes ; `alembic_version = 202409060000` **inchangé** ;
- `backend/uploads/` → **0 fichier**, `Test-Path backend\uploads` → **True** ;
- backend toujours en service après l'opération (uvicorn **PID 23088** en écoute sur `:8000`) →
  `GET /health` → **200 `{"status":"ok"}`**.

**Conséquence tracée** : l'observation CP2/CP3 « nettoyage non fait, à la demande » est **CLOSE**. Restent ouverts et
inchangés à ce stade (règle 8) : PNG corrompu du harnais `backend/scripts/upload_test.py`, latence à froid (indice
**A2**, tracé l. 785-790), `status.HTTP_422_UNPROCESSABLE_ENTITY` déprécié par Starlette,
`role="menuitembutton"` prescrit par `PROMPT_COPILOT_CHAT_RICHE.md` l. 101, et le **checkpoint 1-bis** (6 statuts
historiques « VALIDATION UTILISATEUR EN ATTENTE »).

**Statut : nettoyage exécuté et vérifié (règles 4 et 9) — reprise des correctifs demandée par l'utilisateur le
03/10/2026 ; prochaine correction à arbitrer avec lui avant toute édition (règles 1 et 13).**
