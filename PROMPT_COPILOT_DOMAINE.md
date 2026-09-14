# PROMPT COPLIOT — Phase MVP : Détection de domaine générique (classification)

Copie ce bloc dans GitHub Copilot (VS Code) pour la génération. Contexte : le socle Phase 0 + l'authentification sont en place et validés. PostgreSQL tourne en local.

---

## Contexte

Projet **Dexter** — chatbot tuteur IA (backend FastAPI). État actuel :

- `backend/app/main.py` : FastAPI + `GET /health` + routers auth/users inclus
- `backend/app/config.py` : Settings pydantic-settings lisant le `.env` racine (`settings.db_url`, `settings.jwt_secret`, ...)
- `backend/app/models/` (User), `backend/app/schemas/`, `backend/app/auth/`, `backend/app/services/users.py`, `backend/app/routers/` — fonctionnels et testés
- `backend/.venv` : fastapi, sqlalchemy, alembic, pydantic, pydantic-settings, python-jose, passlib[bcrypt], psycopg2-binary, pgvector, httpx (présent dans le venv), pytest
- PostgreSQL 16.10 local (base `dexter`), pgvector activé

## Tâche : détection de domaine/sous-thème/référentiel/intention/langue — GÉNÉRIQUE et pilotée par configuration

Le PRD (§3.1, §5.4, §7.2, §10.2) impose une détection **automatique et générique** : les domaines sont définis par **configuration/données**, JAMAIS codés en dur dans le code (pas de liste figée des noms de domaines, pas de conditions `if domaine == ...`). Le MVP configure **2 domaines** (Comptabilité, Finance) ; les autres s'ajouteront par configuration.

### 1. Couche d'abstraction LLM (§7.2 — multi-modèles)

- `backend/app/llm/__init__.py` : exporte le provider
- `backend/app/llm/provider.py` : classe abstraite `LLMProvider` avec méthode `chat(messages, temperature, max_tokens) -> str` (interface commune, aucun SDK provider appelé en dur ailleurs)
- `backend/app/llm/openai_compatible.py` : implémentation `OpenAICompatibleProvider` (compatible DeepSeek/OpenAI) utilisant **httpx** (déjà installé) sur l'endpoint `/chat/completions`. Base URL, modèle et clé lus depuis `settings` (jamais en dur).
- Fabrique `get_llm_provider()` retournant le provider configuré (Singleton simple).

### 2. Configuration des domaines (données, pas code)

- `backend/app/domains/domains.json` : structure typée documentée, contenant pour chaque domaine : `id` (ex. "comptabilite"), `label` ("Comptabilité"), `keywords` (liste de termes/expressions de détection), `sous_themes` (liste indicative, NON exhaustive — la détection reste libre au-delà), `referentiels` (ex. comptabilite : ["OHADA", "IFRS", "US GAAP"] ; finance : ["IFRS", "Bâle III"]).
- `backend/app/domains/loader.py` : charge et valide `domains.json` (fichier vide/corrompu → erreur explicite), expose `list_domains()`, `get_domain(domain_id)`, `domain_prompt_context()` (texte injectable dans le prompt système du classifieur).

### 3. Service de classification (étage 1 du routage, PRD §10.2)

- `backend/app/services/classifier.py` : fonction `classify(question: str, history_context: str | None = None) -> ClassificationResult` :
  - Construit un prompt système à partir du contexte des domaines (loader) + consignes (voir §Conventions)
  - Appelle le LLM via `LLMProvider` (pas directement)
  - Demande au modèle de répondre en **JSON strict** : `{"domaine": id|null, "sous_theme": str|null, "referentiel": str|null, "intention": "explication"|"calcul"|"cas_pratique"|"generation_exercice"|"correction"|"autre", "langue": "fr"|"en", "confiance": 0.0-1.0, "besoin_precision": bool, "question_sous_themes": [str]}`
  - Parse le JSON de façon **robuste** (extraction du bloc JSON même si le modèle ajoute du texte ; erreur de parse → `confiance=0`, `besoin_precision=true`, jamais de crash)
  - Règles : si `confiance < seuil` (0.6) ou `besoin_precision` → `domaine=null` et `question_sous_themes` rempli depuis le domaine le plus proche (le front pourra proposer la liste) ; si `referentiel` pertinent pour le domaine mais absent → `besoin_precision=true` (conforme §2.1 : demander le référentiel à la volée) ; langue détectée (fr/en)
- `backend/app/schemas/chat.py` : `ClassifyRequest(question: str, historique: str | None = None)`, `ClassificationResult` (les champs ci-dessus, avec type hints stricts)
- `backend/app/routers/chat.py` : `POST /chat/classify` (public à ce stade MVP) → retourne `ClassificationResult`. Erreurs LLM → 502 explicite avec message, jamais de détail de clé API.

### 4. Configuration

- `backend/app/config.py` : ajouter `llm_api_key: str = ""`, `llm_base_url: str = "https://api.deepseek.com"`, `llm_model: str = "deepseek-chat"` (champs depuis environnement)
- Racine `.env` et `.env.example` : ajouter `LLM_API_KEY=`, `LLM_BASE_URL=`, `LLM_MODEL=`
- `backend/requirements.txt` : **ajouter `httpx`** (actuellement seulement en dev — il devient dépendance runtime pour le provider LLM)

## Conventions impératives

- **Code, variables, fonctions, commentaires en ANGLAIS.** Docstrings courtes. Type hints stricts (Pydantic pour les schémas). Un fichier = une responsabilité.
- **Aucun domaine codé en dur** : tout passe par `domains.json` + loader. Aucun `if` sur les noms de domaines dans le service/route.
- **Secrets jamais en dur** : clé API via `settings.llm_api_key` uniquement. Jamais de log de la clé ou de la réponse LLM complète (coût/confidentialité).
- **Erreurs explicites** : HTTPException (502 erreur LLM, 422 validation), jamais d'exception avalée.
- **Aucune nouvelle dépendance** en dehors de httpx (déjà installé).
- **Ne PAS générer** : prompt pédagogique par domaine (étage 2, phase suivante), quiz, RAG, code frontend.

## Vérification attendue après génération

1. `backend\.venv\Scripts\python.exe -m py_compile` sur tous les nouveaux fichiers + import `app.main` sans erreur
2. `GET /health` répond toujours
3. `POST /chat/classify` avec une question de Comptabilité (ex. « explique-moi le bilan comptable en OHADA ») et une de Finance (ex. « calcule la valeur actuelle nette ») → JSON structuré correct (domaine reconnu, intention, langue)
4. Une question hors domaines (ex. « raconte-moi une blague ») → `domaine=null`, `besoin_precision=true` ou confiance faible
5. Les tests pytest existants passent toujours (`backend\.venv\Scripts\python.exe -m pytest tests/ -v` depuis `backend/`)

---

⚠️ Après génération, SAUVEGARDE tous les fichiers et dis « analyse » à l'agent d'analyse (DeepSeek Harness) qui vérifiera la généricité (aucun domaine en dur), la conformité PRD et la sécurité avant validation.
