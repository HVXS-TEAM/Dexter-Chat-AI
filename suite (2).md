# État actuel du projet Dexter

## Résumé exécutif

Le projet est dans un état fonctionnel sur les fondations et les couches métier principales :

- Authentification complète et validée en conditions réelles.
- Détection de domaine / sous-thème / référentiel / intention / langue mise en place et validée sur des cas réels.
- Étage 2 de génération pédagogique implémenté et validé : tests pytest 8/8 et validation runtime 8/8 effectués le 07/09/2026.
- Conversations persistantes validées (18/18 tests pytest, migration Alembic appliquée) le 08/09/2026.
- RAG / Documents implémenté, analysé, corrigé et validé runtime (24/24 tests pytest, 14/14 vérifications runtime) le 09/09/2026.

## Ce qui est réellement validé

### 1) Base technique et exécution native

- Backend FastAPI structuré et démarrable.
- Route health OK.
- Configuration centralisée via variables d'environnement.
- PostgreSQL local opérationnel avec pgvector.
- Exécution native Windows validée comme voie de travail courante.
- Docker reste prévu comme cible future, mais n'est pas la voie actuellement utilisée sur cette machine.

### 2) Authentification complète

Fonctionnalités implémentées :

- Modèle utilisateur SQLAlchemy.
- Migration initiale.
- Inscription avec rôles étudiant / professeur.
- Hashage bcrypt.
- JWT access token + refresh token.
- Protection des routes via bearer token.
- Profil utilisateur consultable et modifiable.
- Validation des entrées et gestion explicite des erreurs.

État de validation :

- Cycle réel HTTP validé : inscription, login, profil, patch, refresh.
- Test fonctionnel authentification validé lors des livraisons précédentes.
- Aucune donnée sensible n'est renvoyée dans le profil.

### 3) Détection de domaine générique et pilotée par configuration

Fonctionnalités implémentées :

- Provider LLM générique OpenAI-compatible.
- Chargement des domaines depuis une configuration JSON externe.
- Classification générique sans branchement métier codé en dur.
- Détection de domaine, sous-thème, référentiel, intention et langue.
- Fallback explicite lors d'échec de classification.
- Route publique de classification ajoutée.

État de validation :

- Cas réels testés sur comptabilité, finance et hors domaine.
- Comportement de clarification validé quand le référentiel est absent ou ambigu.
- Tests de classification passés dans des livraisons antérieures.