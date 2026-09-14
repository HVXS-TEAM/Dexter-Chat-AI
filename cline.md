Bonjour Cline,

Voici le contexte du projet Dexter et la mission à exécuter.

Contexte
- Projet : Dexter Chat AI
- Stack : Python + FastAPI, SQLAlchemy, Alembic, PostgreSQL + pgvector, React + TypeScript
- Objectif produit : chatbot pédagogique pour étudiants et professeurs, multi-domaines, avec détection de domaine, référentiel, RAG, historique de conversation et génération pédagogique.
- Documentation de référence : Documentation Dexter/dexter-prd.md
- Règles projet : AGENTS.md et .github/instructions/dexter.instructions.md

État réel du projet
Le projet est bien avancé :
- authentification complète et validée
- détection générique de domaine / sous-thème / référentiel / intention / langue
- génération pédagogique spécialisée par domaine
- route /chat/message opérationnelle avec logique de clarification si référentiel manquant
- validations backend et tests de base passés

Le cœur technique est donc en place. La prochaine étape prioritaire selon le PRD n’est pas d’ajouter de nouveaux domaines, mais de passer à la persistance des conversations et au contexte conversationnel.

Mission de cette session
Implémenter la couche de persistance pour :
1. conversations
2. messages
3. référentiel actif par conversation
4. historique contextuel
5. reprise du contexte dans les réponses

Contraintes à respecter
- Respecter strictement le PRD et les conventions du projet
- Ne pas hardcoder une liste figée de domaines
- Garder le code et les commentaires en anglais
- Répondre en français dans le chat, mais en anglais dans le code
- Éviter les dépendances inutiles
- Respecter la logique “minimal but functional”
- Ne pas toucher à la documentation sans nécessité
- Ne pas exposer dans les logs : mots de passe, tokens, documents privés

Spécification fonctionnelle attendue
- Créer le modèle de données pour les conversations et les messages
- Relier chaque message à un utilisateur et à une conversation
- Stocker le référentiel actif par conversation
- Récupérer le contexte de la conversation pour les appels LLM suivants
- Faire en sorte que le chatbot mémorise les éléments déjà précisés dans la session
- Ajouter les routes / endpoints nécessaires
- Ajouter les tests ciblés pour :
  - création de conversation
  - ajout de message
  - référentiel actif
  - contexte récupéré
  - comportement sans référentiel
- Vérifier que la suite backend continue à passer

Livrables attendus
- modèles SQLAlchemy
- schémas Pydantic
- service de conversation
- router associé
- migrations Alembic si nécessaire
- tests de validation
- validation via pytest ou commandes pertinentes

Ce qu’il ne faut pas faire
- ne pas implémenter les 7 domaines en dur
- ne pas faire du RAG avant la persistance de conversation
- ne pas ajouter de dépendances inutiles
- ne pas inventer une architecture surdimensionnée
- ne pas déclarer la tâche terminée sans vérification

Travaille de manière méthodique, en une étape à la fois, avec validation après chaque bloc important.

Objectif principal de la prochaine phase
Produire une implémentation propre, stable et alignée avec le PRD pour :
- la persistance de conversation
- le contexte conversationnel
- le référentiel actif
- la base de la suite RAG / documents

Merci de travailler avec cette logique de progression et de te référer au PRD comme source d’autorité.
