# PROMPT COPLIOT — Phase MVP : Étage 2 — Prompts pédagogiques spécialisés par domaine

Copie ce bloc dans GitHub Copilot (VS Code) pour la génération. Contexte : classification (étage 1) fonctionnelle et validée.

---

## Contexte

Projet **Dexter** — chatbot tuteur IA (backend FastAPI). État actuel (tout est validé et testé) :

- **Étage 1 — Classification** : `POST /chat/classify` → `ClassificationResult {domaine, sous_theme, referentiel, intention, langue, confiance, besoin_precision, question_sous_themes}` via `app/services/classifier.py` (LLM qwen3.8-27b sur Groq, générique, piloté par `app/domains/domains.json` : comptabilite + finance)
- **Abstraction LLM** : `app/llm/provider.py` (`LLMProvider.chat(messages, temperature, max_tokens)`), `app/llm/openai_compatible.py` (httpx, singleton `get_llm_provider()`), config via `settings` (LLM_API_KEY=Groq, LLM_BASE_URL, LLM_MODEL=qwen/qwen3.8-27b)
- **Auth** : `get_current_user` (Bearer JWT) → User (rôle `etudiant`/`professeur`, `langue_preferee`)
- `.env` : LLM_API_KEY (Groq), LLM_BASE_URL, LLM_MODEL (classification), + clés Cerebras/SambaNova (inutilisées pour l'instant)

## Tâche : ÉTAGE 2 — génération de réponses pédagogiques spécialisées par domaine (PRD §10)

Après la classification, la question part vers un **prompt système propre au domaine**, injecté avec le contexte de classification (référentiel, intention, langue) — PRD §10.2 étage 2.

### 1. Multi-modèles par tâche (PRD §7.2, §10.4)

- `backend/app/config.py` : ajouter `llm_model_generation: str = "openai/gpt-oss-120b"` (modèle de génération, plus capable ; la classification reste sur le modèle rapide `llm_model`)
- `backend/app/llm/provider.py` : `chat(..., model: str | None = None)` — si `model` est fourni, il remplace le modèle par défaut du provider (les deux modèles sont testés et accessibles sur le compte Groq)
- `backend/app/llm/openai_compatible.py` : implémenter le paramètre `model` dans la requête
- `.env` + `.env.example` : ajouter `LLM_MODEL_GENERATION=openai/gpt-oss-120b`

### 2. Templates de prompts par domaine (socle + variantes par intention, PRD §10.5)

Créer `backend/app/prompts/templates/` avec des fichiers **markdown** (placeholders `$question`, `$referentiel`, `$profil`, `$sous_theme`, `$langue`, `$historique` — utiliser `string.Template` de Python) :

- `templates/comptabilite/root.md` : socle commun — vocabulaire et normes (référentiels OHADA/IFRS/US GAAP, structure bilan/compte de résultat), registre pédagogique selon le profil (étudiant : explication progressive ; professeur : préparation de contenu), consignes de transparence de source (PRD §4.2 : « De manière générale… »), bilinguisme
- `templates/comptabilite/explication.md`, `calcul.md`, `cas_pratique.md`, `generation_exercice.md`, `correction.md` : blocs additionnels par intention (variantes d'instructions, exemples attendus)
- Même structure pour `templates/finance/` (root + 5 intentions : vocabulaire finance, valorisation, VAN, risque, portefeuille, référentiels IFRS/Bâle III)
- `backend/app/prompts/loader.py` : charge les templates (fichier manquant/corrompu → erreur explicite), fonction `build_domain_prompt(domain_id, intention) -> str` qui concatène root + bloc intention
- `backend/app/prompts/__init__.py`

### 3. Service de génération pédagogique

- `backend/app/services/chat_service.py` :
  - `generate_answer(question, classification: ClassificationResult, user, history_context=None) -> str` :
    - choisit le template (domain_id + intention depuis la classification, fallback intention « explication »)
    - construit le prompt avec `string.Template` (profil étudiant/professeur depuis `user.role`, langue depuis `classification.langue` ou `user.langue_preferee`)
    - appelle le LLM via le provider **avec le modèle de génération** (`settings.llm_model_generation`)
    - consignes système : transparence de la source (« De manière générale… » — jamais de mélange silencieux, PRD §4.2/§9.3), réponse dans la langue demandée, rigueur métier
    - si l'appel LLM échoue → lever une erreur explicite (pas de réponse silencieuse), jamais de log de clé

### 4. Endpoint conversationnel complet (étage 1 + étage 2)

- `backend/app/schemas/chat.py` : ajouter `ChatMessageRequest(question: str, historique: str | None = None)` et `ChatMessageResponse` : `{reponse: str | None, mode: Literal["explique_moi"], domaine: str | None, sous_theme: str | None, referentiel: str | None, clarification_demandee: bool, question_sous_themes: list[str], referentiels_proposes: list[str] | None}`
- `backend/app/routers/chat.py` : ajouter `POST /chat/message` **protégé par `get_current_user`** :
  1. Classifie la question (étage 1)
  2. **Si `besoin_precision`** (référentiel manquant ou domaine incertain) → NE PAS générer : répondre `clarification_demandee=true`, `question_sous_themes` (domaine le plus proche), `referentiels_proposes` (référentiels du domaine détecté, ex. comptabilite → [OHADA, IFRS, US GAAP]) — sans appel LLM (PRD §2.1/§5.4)
  3. **Sinon** → générer la réponse pédagogique (étage 2) avec le prompt du domaine, `mode="explique_moi"`
  4. Erreurs : 401 (auth), 502 (LLM), 422 (validation)
- `backend/app/main.py` : aucun changement nécessaire (router déjà inclus)

## Conventions impératives

- **Code, variables, fonctions, commentaires en ANGLAIS.** Docstrings courtes. Type hints stricts. Un fichier = une responsabilité.
- **Aucun domaine codé en dur dans le code métier** : les templates sont des fichiers par domaine ; le service ne fait aucun `if` sur les noms de domaines.
- **Secrets jamais en dur** : clés via `settings` uniquement, jamais loggées.
- **Erreurs explicites** : jamais d'exception avalée (sauf le repli de classification existant, déjà loggé).
- **Hors périmètre (NE PAS générer)** : outils de calcul dédiés (V1), RAG/documents (V1), quiz/exercices interactifs (V1), conversations persistantes, code frontend.
- **Aucune nouvelle dépendance** (string.Template est stdlib).

## Vérification attendue après génération

1. Import `app.main` OK, `GET /health` OK, tests existants toujours verts (4 pytest)
2. `POST /chat/message` avec un token valide (register + login) :
   - « explique-moi le bilan comptable en OHADA » (profil étudiant) → réponse pédagogique structurée en français, mode explique_moi, domaine comptabilite, référentiel OHADA
   - « calcule la valeur actuelle nette d'un projet » → `clarification_demandee=true` avec référentiels proposés (pas de génération)
   - « raconte-moi une blague » → clarification (hors domaines)
3. Nouveaux tests pytest : `tests/test_chat_message.py` (provider mocké) — clarification sans appel LLM, génération avec le bon template, erreur LLM → 502
