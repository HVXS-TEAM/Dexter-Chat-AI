# Instructions de projet — Dexter

## Contexte du projet

Dexter est un chatbot éducatif IA multi-domaines (comptabilité, marketing,
finance, statistique, banque, business, management) pour étudiants et
professeurs d'université. Le cadrage complet (vision, architecture, modèle
de données, stratégie RAG, roadmap) se trouve dans `documentation/dexter-prd.md`
— consulte-le avant toute génération de code structurante, mais ne modifie
jamais aucun fichier du dossier `documentation/`.

## Périmètre actuel (important)

Le développement démarre sur **2 domaines seulement** (à définir), pas les 7.
Ne génère pas de code prévoyant déjà les 7 domaines en dur (pas de liste
figée des 7 noms de domaines dans le code) — le système de détection de
domaine et de routage doit être générique et piloté par configuration/données,
pas par des conditions codées en dur par domaine.

## Stack technique imposée

- **Backend** : Python + FastAPI, SQLAlchemy (ORM), Alembic (migrations),
  Pydantic (validation)
- **Base de données** : PostgreSQL + extension pgvector pour les embeddings
- **Frontend** : React + TypeScript
- **Conteneurisation** : Docker + docker-compose pour l'environnement local
- **Authentification** : JWT (access + refresh token)
- Ne propose jamais une alternative à cette stack sans que je le demande
  explicitement.

## Conventions de code

- Code, noms de variables/fonctions/classes et commentaires **en anglais**,
  même si l'interface utilisateur finale est bilingue français/anglais
- Typage strict partout : type hints Python (avec Pydantic pour les schémas
  API), TypeScript strict côté frontend — jamais de `any` implicite
- Docstrings courtes sur toute fonction/service non trivial
- Un fichier = une responsabilité claire ; éviter les fichiers fourre-tout
- Variables sensibles (clés API, secrets JWT, identifiants DB) toujours via
  variables d'environnement (`.env`), jamais en dur dans le code — mets à
  jour `.env.example` à chaque nouvelle variable introduite

## Architecture à respecter

- **Détection domaine/sous-thème** et **référentiel normatif** : logique
  générique et réutilisable, pas de taxonomie figée en dur (cf. PRD §3.1) —
  le sous-thème est un texte libre détecté dynamiquement, jamais une clé
  étrangère vers une liste prédéfinie
- **Routage LLM multi-modèles** : passer par une interface/abstraction
  commune (ex. classe `LLMProvider`) — jamais d'appel direct en dur à un
  SDK de provider dans les services métier
- **RAG** : pas d'isolation stricte par domaine — la recherche vectorielle
  peut croiser plusieurs documents de matières différentes si pertinent
  (cf. PRD §4.3, §9)
- **Documents** : privés par défaut, visibilité `partage_classe` uniquement
  sur action explicite d'un professeur — ne jamais rendre un document
  visible à d'autres utilisateurs par défaut
- Respecter strictement les entités et noms de champs du modèle de données
  du PRD §8 (users, conversations, messages, documents, document_chunks,
  classes, classe_membres, quiz_attempts) sauf si je demande explicitement
  un changement

## Sécurité

- Ne jamais logger ou exposer de mot de passe, token, ou contenu de document
  utilisateur dans les logs applicatifs
- Toute route qui touche aux données d'un utilisateur doit vérifier
  l'appartenance de la ressource (pas de faille d'autorisation horizontale)
- Chiffrement au repos pour les documents uploadés (cf. PRD §6)

## Ce que je veux de toi (Copilot)

- Génère du code minimal mais fonctionnel — des implémentations claires et
  simples plutôt que des abstractions prématurées pour un futur besoin
  hypothétique (projet solo, périmètre volontairement restreint pour l'instant)
- Si une de mes demandes contredit une règle ci-dessus ou le PRD, signale-le
  avant de générer le code, ne l'applique pas silencieusement
- Pas de dépendance ajoutée sans nécessité claire — demande avant d'introduire
  une nouvelle librairie qui n'est pas déjà listée dans ce fichier
- Écris en français dans tes réponses de chat, mais garde le code et les
  commentaires en anglais (cf. conventions ci-dessus)