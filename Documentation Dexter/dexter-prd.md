# Dexter — Documentation de cadrage (PRD)

**Version :** 0.1 — Draft de travail
**Statut :** En cours de définition, section par section

---

## 1. Vision & positionnement

Dexter est un **chatbot tuteur intelligent** couvrant sept domaines : comptabilité, marketing, finance, statistique, banque, business et management.

**Positionnement :** ni un moteur de recherche, ni un simple générateur de texte — un assistant pédagogique capable de :
- Expliquer un concept avec le bon niveau de rigueur métier
- S'ancrer sur les documents/cours propres de l'étudiant quand ils existent (RAG)
- Fournir des exemples chiffrés fiables (pas d'hallucination sur des calculs)
- Suivre la progression de l'étudiant dans le temps

**Ce que Dexter EST :** un chatbot visant à aider **étudiants et professeurs** à comprendre, se cultiver, maîtriser et s'exercer sur les 7 domaines.

**Ce que Dexter n'est PAS (à ce stade) :**
- Un outil de conseil financier réel ou de gestion comptable en production
- Un correcteur automatique certifiant officiellement des notes/diplômes
- Un outil temps réel de trading ou de reporting bancaire

---

## 2. Public cible

| Critère | Détail |
|---|---|
| Cible primaire | **Deux profils** : étudiants (niveau université) ET professeurs |
| Niveau d'études | Université |
| Zone géographique | **Cross-zone** — pas de référentiel normatif unique |
| Langue(s) | À préciser (français seul, ou bilingue français/anglais ?) |
| Niveau d'autonomie numérique | Public universitaire — UI standard, pas de simplification excessive nécessaire |

### 2.1 Implications du cross-zone

Un contenu "cross-zone" signifie que Dexter doit être capable de :
- Détecter ou demander le référentiel normatif pertinent (ex. compta : OHADA, IFRS, US GAAP...)
- Adapter ses réponses en conséquence, plutôt que de supposer un référentiel par défaut
- Signaler explicitement quand une notion est universelle (théorie de gestion, stats) vs spécifique à une zone (droit bancaire, fiscalité)

**Décision : le référentiel normatif se précise question par question**, intégré nativement dans le flux de conversation — pas de réglage figé dans le profil. Dexter doit donc être capable de :
- Détecter si la question implique un référentiel spécifique (compta, droit bancaire, fiscalité...)
- Demander la précision à la volée si elle manque et qu'elle change la réponse ("Tu es sur quel référentiel comptable — OHADA, IFRS, autre ?")
- Ne PAS redemander à chaque fois dans une même conversation si déjà précisé (mémoriser le contexte de session)
- Rester neutre/signaler l'ambiguïté quand la notion est universelle et ne nécessite aucune précision

### 2.2 Deux profils, deux besoins différents

| Besoin | Étudiant | Professeur |
|---|---|---|
| Comprendre un concept | ✅ Cœur d'usage | ✅ Pour préparer un cours |
| S'exercer (quiz, exercices) | ✅ Cœur d'usage | Génère des exercices pour sa classe |
| Suivi de progression | Suivi individuel | Suivi d'une classe/groupe (V2+ probable) |
| Upload de documents (RAG) | Ses notes de cours | Ses supports de cours / corrigés |

**Décision : interface unique, fonctionnalités différenciées par profil.** Étudiant et professeur se connectent à la même application ; le profil (choisi à l'inscription ou détecté) déverrouille des fonctionnalités spécifiques plutôt qu'une interface séparée. Concrètement :
- Socle commun : chat, upload de documents (RAG), historique, sélection de domaine/référentiel
- Fonctionnalités étudiant : quiz personnels, suivi de progression individuelle
- Fonctionnalités professeur : génération d'exercices/corrigés pour une classe, (V2+) suivi d'un groupe d'étudiants

Cette approche simplifie le code (une seule UI, gestion par rôles/permissions) et pourra évoluer sans refonte si le profil professeur prend plus d'ampleur en V2.

---

## 3. Domaines fonctionnels couverts

1. **Comptabilité**
2. **Marketing**
3. **Finance**
4. **Statistique**
5. **Banque**
6. **Business**
7. **Management**

**Décision révisée : le MVP se limite à 2 domaines**, choisis en priorité, avec les 5 autres ajoutés progressivement après le lancement pilote. Décision qui remplace le choix initial "7 domaines à profondeur égale dès le MVP" — revirement assumé après un constat simple : viser les 7 domaines à profondeur égale en développement solo, sans échéance, risquait de repousser indéfiniment un premier lancement testable par de vrais utilisateurs. Mieux vaut une preuve de valeur rapide sur un périmètre restreint mais solide, puis un enrichissement itératif nourri par les retours réels.

*Point à trancher : lesquels des 7 domaines choisir pour ce MVP restreint ?*

### 3.1 Granularité des sous-thèmes : approche dynamique, pas de liste figée

**Décision :** on ne pré-liste pas exhaustivement les sous-thèmes de chaque domaine dans cette documentation. Les 7 domaines restent volontairement généraux ici ; le sous-thème précis est déterminé **au moment de la conversation**, selon la même logique que la détection de domaine (§5.4) :

- Dexter analyse la question et/ou les documents fournis par l'utilisateur pour identifier le sous-thème concerné
- Si l'identification est incertaine ou trop large, Dexter **propose une liste de sous-thèmes** du domaine concerné pour que l'utilisateur précise et reste dans le cadre attendu
- Cette approche évite de figer une taxonomie rigide dans le produit et laisse la détection s'affiner avec l'usage réel

*Conséquence technique à garder en tête pour l'architecture (§ à venir) : le système de détection de domaine devra être conçu comme un mécanisme réutilisable à deux niveaux — domaine, puis sous-thème à l'intérieur du domaine — plutôt que deux logiques séparées.*

---

## 4. Modes d'usage

### 4.1 Les deux modes

- **Mode "Explique-moi"** : connaissances générales du domaine, pédagogique, avec exemples. S'appuie sur la détection dynamique de domaine et sous-thème (§3.1) et le référentiel normatif actif (§2.1/§5.4).
- **Mode "Mes cours"** : RAG sur documents uploadés par l'utilisateur (cours, syllabus, notes pour un étudiant ; supports de cours, corrigés pour un professeur), réponses ancrées et sourcées.

### 4.2 Bascule entre les modes

- **Automatique par défaut** : si des documents pertinents au sujet de la question ont été uploadés, Dexter privilégie le mode "Mes cours" ; sinon, bascule sur "Explique-moi"
- **Transparence systématique** : Dexter indique toujours explicitement la source de sa réponse ("D'après tes notes de cours..." vs "De manière générale...") — jamais d'ambiguïté sur l'origine de l'information
- Cohérent avec la logique déjà actée pour le référentiel normatif (§5.4) : détection automatique, mais l'utilisateur garde la main pour forcer un mode explicitement s'il le souhaite

### 4.3 Décisions actées

- **Portée du RAG :** pas d'isolation stricte par domaine/sous-thème. Dexter peut croiser plusieurs documents de matières différentes dans une même réponse, tant que ça reste pertinent au contexte de la question et que ça aide à une réponse plus consistante (ex. une question de business qui bénéficie de croiser un cours de finance et un cours de marketing).
- **Documents du professeur :** privés par défaut (usage personnel de préparation). Partage avec les étudiants uniquement sur décision explicite du professeur — jamais automatique.
- **Durée de vie des documents :** conservés au niveau de la discussion/conversation. *Point à affiner plus tard* : faut-il aussi une bibliothèque personnelle persistante en dehors des conversations (pour retrouver un document uploadé il y a des semaines sans avoir à le re-uploader), ou chaque conversation reste-t-elle son propre silo de documents ? On y reviendra à un stade plus avancé.

---

## 5. Parcours utilisateur

### 5.1 Inscription / connexion

1. L'utilisateur crée un compte (email + mot de passe, ou SSO à définir)
2. Choix du profil : **Étudiant** ou **Professeur**
3. (Étudiant) Informations optionnelles : filière, année d'étude
4. (Professeur) Informations optionnelles : matière(s) enseignée(s), établissement
5. Aucun réglage de référentiel normatif à cette étape — géré dynamiquement en conversation (voir §2.1)

### 5.2 Parcours étudiant

1. Connexion → écran d'accueil avec les 7 domaines visibles
2. Question libre ou upload de documents — Dexter détecte automatiquement le domaine concerné (demande une précision seulement en cas de doute)
3. (Optionnel) Upload de documents de cours pour ce domaine → active le mode RAG
4. Conversation avec Dexter : questions, explications, précision de référentiel à la volée si besoin
5. Demande de quiz/exercices sur le sujet en cours → Dexter génère, corrige, explique les erreurs
6. Consultation de l'historique de progression (par domaine)

### 5.3 Parcours professeur

1. Connexion → écran d'accueil avec les 7 domaines visibles + accès aux outils "classe" (si activés)
2. Sélection d'un domaine et d'un sujet à préparer
3. (Optionnel) Upload de ses supports de cours existants → RAG pour rester cohérent avec son propre contenu
4. Génération d'exercices/corrigés/études de cas alignés sur son référentiel et son niveau de classe
5. (V2+) Partage avec un groupe d'étudiants / suivi de leur progression

### 5.4 Décisions actées

- **Détection du domaine :** automatique, à partir de l'analyse de la question posée et/ou des documents fournis. Si Dexter ne parvient pas à identifier le domaine avec confiance, il demande explicitement à l'utilisateur de préciser plutôt que de deviner et risquer une réponse hors-sujet.
- **Persistance du référentiel normatif :** une fois précisé (ex. "je suis en IFRS"), il est retenu par défaut pour la suite de la conversation — et idéalement pour les conversations suivantes du même utilisateur/domaine — sauf demande explicite de changement ("en fait je veux la version OHADA"). Implication technique : le référentiel actif doit être stocké au niveau utilisateur (ou utilisateur+domaine), pas seulement au niveau du message.
- **Fréquence d'usage :** ponctuelle ET régulière. Dexter doit donc bien fonctionner en usage "coup de feu avant examen" (réponses rapides, quiz de révision intensifs) autant qu'en usage installé dans la durée (suivi de progression, historique exploitable, pas de friction à revenir).

---

## 6. Exigences non-fonctionnelles

| Aspect | Exigence |
|---|---|
| Plateformes | Web d'abord → Android + iPhone ensuite (API commune) |
| Performance | Réponses en streaming, latence perçue faible |
| Fiabilité des calculs | Pas d'hallucination sur les chiffres (compta/stats/finance) — nécessite un outil de calcul dédié, pas juste le LLM seul |
| Sécurité des données | Documents uploadés = données potentiellement sensibles (cours, infos perso, supports pédagogiques de profs) |
| Scalabilité | Architecture pensée multi-utilisateurs dès le départ |
| Accessibilité | À définir (contraste, lecteur d'écran, etc.) |

### 6.1 Décisions actées

- **Langue(s) :** bilingue français/anglais dès le MVP. Implication technique : prompts système et détection de langue dès la conception, pas une couche ajoutée après coup.
- **Sécurité des documents uploadés :** chiffrement au repos suffisant pour le pilote. Pas de mécanisme avancé de droit à l'oubli/anonymisation exigé à ce stade — à réévaluer si la volumétrie ou le type d'établissements partenaires l'imposent plus tard (ex. établissements publics avec obligations RGPD strictes).
- **Volumétrie cible à 6-12 mois :** dizaines d'utilisateurs (phase test/pilote). Ça autorise une architecture simple au départ (pas besoin de scalabilité horizontale agressive dès le MVP), tout en gardant les choix techniques du §2 (Docker, API découplée) qui permettent de scaler plus tard sans réécriture complète.
- **Budget/coût IA :** contrainte modérée à surveiller, sans bloquer les choix. Ça laisse la liberté de choisir le modèle le plus adapté à la qualité voulue plutôt que le moins cher par défaut, tout en gardant un œil sur le coût (ex. caching de réponses fréquentes, pas d'appels redondants).
- **Accessibilité :** bonnes pratiques web basiques (contraste suffisant, navigation clavier) — pas d'exigence RGAA/WCAG formelle pour le pilote.

---

## 7. Architecture technique

### 7.1 Backend : recommandation

**Python + FastAPI**, pour trois raisons concrètes vu ton contexte (multi-modèles, RAG, calculs fiables) :
- Écosystème RAG/IA le plus mature (LangChain, LlamaIndex, bibliothèques d'embeddings) — utile pour le routage multi-modèles et la construction du pipeline RAG
- Écosystème scientifique/calcul (pandas, numpy) directement exploitable pour la fiabilité des calculs en compta/finance/stats (§6, exigence "pas d'hallucination sur les chiffres")
- FastAPI expose nativement une API REST bien typée et documentée (OpenAPI/Swagger) — condition pour brancher les futures apps Android/iPhone sans réécriture

*Frontend web reste React + TypeScript comme évoqué en amont — combinaison Python (backend) / React (frontend) est un des couples les plus courants et bien outillés pour ce type de produit.*

### 7.2 Multi-modèles : architecture de routage

Le choix "multi-modèles avec routage selon la tâche" implique une **couche d'abstraction LLM** dans le backend, plutôt que d'appeler un fournisseur en dur partout dans le code :

- Un **routeur de modèles** décide quel modèle appeler selon le type de tâche : ex. un modèle plus rapide/économique pour la détection de domaine et de sous-thème (§3.1), un modèle plus capable pour les explications pédagogiques complexes, potentiellement un modèle spécialisé code/calcul pour les vérifications chiffrées (§6, fiabilité des calculs)
- Cette couche facilite aussi le contrôle du coût (§6, contrainte modérée) : les tâches simples n'utilisent pas systématiquement le modèle le plus cher
- Techniquement : interface commune (ex. classe abstraite `LLMProvider`) implémentée par provider, pour ajouter/retirer un fournisseur sans toucher au reste du code

*Point à trancher plus tard, une fois qu'on rentrera dans le détail du routage par domaine (section à venir) : quels fournisseurs precis intégrer en premier.*

### 7.3 Hébergement pilote

**Hébergeur simplifié type Railway/Render** confirmé — cohérent avec la cible "dizaines d'utilisateurs" (§6) : pas besoin de la complexité d'un cloud généraliste (AWS/GCP/Azure) pour un pilote de cette taille. Avantages concrets pour ce projet :
- Déploiement rapide depuis Git, sans gestion d'infra manuelle
- Bases de données managées disponibles (Postgres notamment) en quelques clics
- Coût prévisible et bas pour un volume pilote
- Migration vers un cloud généraliste reste possible plus tard si la volumétrie grandit, sans que ça remette en cause les choix d'architecture applicative (Docker déjà prévu §2 facilite cette portabilité)

### 7.4 Composants de l'architecture (vue d'ensemble)

```
┌─────────────────┐
│  Frontend React  │  (web → puis React Native pour mobile)
└────────┬─────────┘
         │ API REST (OpenAPI)
┌────────▼─────────┐
│  Backend FastAPI  │
│  ┌──────────────┐ │
│  │  Auth (JWT)  │ │
│  ├──────────────┤ │
│  │  Détection   │ │  → domaine + sous-thème (§3.1) + langue (§6)
│  │  domaine/    │ │
│  │  référentiel │ │
│  ├──────────────┤ │
│  │  Routeur LLM │ │  → multi-modèles selon la tâche (§7.2)
│  ├──────────────┤ │
│  │  Pipeline    │ │  → RAG cross-documents (§4.3)
│  │  RAG         │ │
│  └──────────────┘ │
└────────┬──────┬────┘
         │      │
┌────────▼──┐ ┌─▼──────────┐
│ PostgreSQL │ │ Vector DB  │
│ (données   │ │ (embeddings│
│ relation.) │ │ documents) │
└────────────┘ └────────────┘
```

### 7.5 Décisions actées

- **Vector DB :** **pgvector** (extension PostgreSQL) — la solution la plus simple, confirmée. Tout reste dans une seule base de données, ce qui colle parfaitement avec l'hébergement simplifié (§7.3) : une seule base managée à opérer plutôt que deux systèmes séparés (Postgres + Vector DB dédié). Suffisant pour la volumétrie pilote visée (§6, dizaines d'utilisateurs) ; une migration vers une solution dédiée (Qdrant, Pinecone) reste possible plus tard si le volume de documents/recherches vectorielles devient un goulot d'étranglement — mais ce n'est pas un sujet à ce stade.
- **Providers LLM concrets :** à trancher au moment de détailler le routage par domaine (section à venir) — reste ouvert pour l'instant.

---

## 8. Modèle de données

### 8.1 Entités principales

```sql
-- Utilisateurs et rôles (§2.2 : interface unique, fonctionnalités par profil)
users (
  id, email, password_hash,
  role                -- 'etudiant' | 'professeur'
  langue_preferee,     -- 'fr' | 'en' (§6 bilingue)
  filiere,             -- nullable, info optionnelle étudiant
  matieres_enseignees, -- nullable, info optionnelle professeur
  etablissement,        -- nullable
  created_at
)

-- Conversations (unité de persistance des documents, §4.3)
conversations (
  id, user_id, titre,
  referentiel_actif,   -- ex. 'OHADA', 'IFRS', null si non applicable
  created_at, updated_at
)

-- Messages (historique du chat)
messages (
  id, conversation_id, role,        -- 'user' | 'assistant'
  content,
  domaine_detecte,      -- nullable, un des 7 domaines (§3)
  sous_theme_detecte,   -- nullable, texte libre (§3.1, pas de taxonomie figée)
  mode_utilise,          -- 'explique_moi' | 'mes_cours' | 'hybride' (§4)
  sources_rag[],          -- ids des document_chunks utilisés, si mode RAG
  created_at
)

-- Documents uploadés (§4.3 : privés par défaut, partage explicite pour profs)
documents (
  id, owner_id, conversation_id,   -- rattaché à une conversation (§4.3)
  titre, type_fichier,
  domaine_associe,       -- nullable, détecté ou déclaré
  visibilite,             -- 'prive' | 'partage_classe' (défaut: prive, §4.3)
  fichier_url,
  created_at
)

-- Chunks vectorisés pour le RAG (pgvector, §7.5)
document_chunks (
  id, document_id,
  contenu_texte,
  embedding vector(1536),  -- dimension selon le modèle d'embedding choisi
  page_ou_position,
  created_at
)

-- Groupes/classes (support du partage professeur → étudiants, §4.3, §5.3)
classes (
  id, professeur_id, nom, created_at
)

classe_membres (
  classe_id, etudiant_id, joined_at
)

-- Suivi pédagogique (quiz/exercices, §5.2/§5.3)
quiz_attempts (
  id, user_id, domaine, sous_theme,
  score, questions[], reponses[],
  created_at
)
```

### 8.2 Points de cohérence avec les décisions déjà actées

- **`referentiel_actif` au niveau conversation, pas message** : cohérent avec la persistance par défaut du référentiel (§5.4) — évite de le redemander à chaque message tant que la conversation ne change pas explicitement.
- **`documents.conversation_id`** : traduit la décision "documents conservés au niveau de la discussion" (§4.3). *Point resté ouvert dans le PRD (bibliothèque persistante hors conversation) : si tranché plus tard, il suffira de rendre `conversation_id` nullable et d'ajouter une notion de bibliothèque personnelle — pas de refonte du modèle.*
- **`documents.visibilite`** : traduit directement la règle "privé par défaut, partage sur décision explicite du professeur" (§4.3).
- **`messages.sources_rag[]` sans restriction de domaine** : permet le croisement multi-documents multi-matières acté en §4.3 (pas d'isolation stricte).
- **Pas de table `sous_themes`** : cohérent avec la décision de ne pas figer de taxonomie (§3.1) — le sous-thème est stocké comme texte libre détecté à la volée, pas une clé étrangère vers une liste prédéfinie.

### 8.3 Points à trancher

- **Dimension des embeddings** : dépend du modèle d'embedding choisi (à trancher avec le choix des providers LLM, §7.5) — impacte la définition exacte de `vector(N)` dans pgvector.
- **Anonymisation/pseudonymisation des données étudiants** dans `quiz_attempts` si un professeur consulte le suivi de sa classe (V2+, §5.3) : accès complet aux réponses individuelles, ou vue agrégée uniquement ?

---

## 9. Stratégie RAG

### 9.1 Pipeline d'ingestion des documents

1. **Upload** : l'utilisateur (étudiant ou professeur) dépose un document (PDF, DOCX, PPTX...) dans une conversation (§4.3, §8.1 `documents.conversation_id`)
2. **Extraction du texte** : parsing selon le format (texte natif, ou OCR si document scanné)
3. **Chunking** : découpage en segments cohérents (par paragraphe/section plutôt que taille fixe aveugle, pour préserver le sens — important pour des documents structurés comme des cours avec titres/sous-titres)
4. **Détection de domaine/sous-thème du document** : réutilise la même logique de détection que pour les questions (§3.1), appliquée cette fois au contenu du document — alimente `documents.domaine_associe` (§8.1)
5. **Embedding** : chaque chunk est vectorisé et stocké dans `document_chunks` (pgvector, §7.5/§8.1)

### 9.2 Pipeline de récupération (retrieval) au moment d'une question

1. La question de l'utilisateur est analysée (détection domaine/sous-thème/référentiel, §3.1/§5.4)
2. **Recherche vectorielle** dans les chunks des documents accessibles à l'utilisateur dans le contexte courant :
   - Ses propres documents uploadés dans la conversation
   - Les documents de classe partagés par son professeur, si applicable (§4.3, `visibilite = 'partage_classe'`)
3. **Croisement multi-documents autorisé** (§4.3 acté) : la recherche n'est pas limitée à un seul document ni à un seul domaine si plusieurs chunks pertinents de sources différentes améliorent la réponse
4. **Décision du mode** (§4.2) : si des chunks suffisamment pertinents sont trouvés → mode "Mes cours" ; sinon → bascule "Explique-moi" sur connaissances générales
5. **Génération de la réponse** avec les chunks pertinents injectés en contexte au LLM, en conservant la traçabilité (quels chunks/documents ont servi) pour respecter l'exigence de transparence de la source (§4.2)

### 9.3 Qualité et fiabilité

- **Seuil de pertinence** : une recherche vectorielle qui ne retourne que des chunks faiblement pertinents ne doit pas être utilisée artificiellement — mieux vaut basculer proprement sur "Explique-moi" que de forcer une réponse mal ancrée (cohérent avec l'exigence de fiabilité du §6)
- **Pas de mélange silencieux** : quand une réponse combine RAG et connaissances générales, Dexter le signale clairement plutôt que de présenter un mélange comme une source unique (renforce la transparence déjà actée en §4.2)
- **Calculs chiffrés** : le RAG fournit le contexte/les données, mais les calculs eux-mêmes doivent passer par l'outil de calcul dédié évoqué en §6 (fiabilité), pas être « lus » depuis un chunk et recopiés tel quel sans vérification

### 9.4 Points à trancher

- **Modèle d'embedding** : à choisir en cohérence avec le choix des providers LLM (§7.5) — impacte directement la dimension définie dans pgvector (§8.3)
- **Taille de fenêtre de contexte pour les chunks croisés** : combien de chunks maximum injecter dans une même réponse quand plusieurs documents de matières différentes sont pertinents (§4.3), pour ne pas diluer la réponse ni dépasser le budget de tokens ?
- **Ré-indexation** : si un professeur met à jour un support de cours déjà uploadé, faut-il ré-indexer automatiquement (remplacer les anciens chunks), ou traiter chaque upload comme une nouvelle version conservée à part ?

---

## 10. Routage par domaine et prompts spécialisés

### 10.1 Pourquoi un routage dédié

Avec 7 domaines traités à profondeur égale (§3) et un vocabulaire/méthodes très différents (compta ≠ marketing ≠ stats), un seul prompt système générique donnerait des réponses molles ou approximatives. Le routage par domaine est ce qui transforme Dexter d'un chatbot générique en véritable expert multi-domaines.

### 10.2 Architecture en deux étages

**Étage 1 — Classification (déjà actée en §3.1/§5.4/§9.1)**
Un premier passage (rapide, modèle économique — cohérent avec la contrainte de coût modérée du §6) détermine :
- Domaine (parmi les 7)
- Sous-thème (texte libre, détecté dynamiquement — §3.1)
- Référentiel normatif actif ou à préciser (§5.4)
- Intention de la question : *définition/explication*, *calcul*, *cas pratique*, *génération d'exercice*, *correction*
- Langue de la question (§6, bilingue FR/EN)

**Étage 2 — Génération avec prompt spécialisé**
Une fois la classification faite, la question part vers un **prompt système propre à ce domaine**, injecté avec le contexte de classification (référentiel, intention, langue) et les chunks RAG pertinents s'il y en a (§9.2).

### 10.3 Contenu des prompts spécialisés par domaine

Chaque prompt domaine encode :
- **Vocabulaire et normes propres** : ex. compta → normes OHADA/IFRS/US GAAP selon le référentiel actif, structure bilan/compte de résultat ; banque → réglementation prudentielle, produits bancaires ; stats → rigueur méthodologique (tests, hypothèses)
- **Registre pédagogique adapté au profil** (§2.2) : ton et niveau différents si la question vient d'un étudiant (explication progressive) ou d'un professeur (préparation de contenu, formulation d'énoncés)
- **Consignes spécifiques par intention** : un prompt "calcul" en compta/finance/stats déclenche l'appel à l'outil de calcul dédié (§6, §9.3) plutôt que de laisser le LLM produire un chiffre non vérifié

### 10.4 Lien avec le routage multi-modèles (§7.2)

Le routage par domaine et le routage multi-modèles sont deux décisions complémentaires, pas redondantes :
- Le **routage domaine** décide *quel prompt/contexte métier* utiliser
- Le **routage multi-modèles** décide *quel modèle* traiter la requête (classification légère vs génération complexe vs vérification de calcul)

Concrètement, une question de calcul en finance peut : passer par un modèle rapide pour la classification → un modèle capable pour l'explication pédagogique → un outil de calcul déterministe (pas un LLM) pour le chiffre final vérifié.

### 10.5 Décisions actées

- **Granularité des prompts : variantes par intention à l'intérieur de chaque domaine** (ex. compta-calcul vs compta-explication vs compta-cas-pratique). Recommandation retenue plutôt qu'un prompt unique par domaine : la précision gagnée est significative pour un chatbot qui se veut expert (pas générique), et le surcoût de maintenance reste gérable si les prompts d'un même domaine partagent un socle commun (vocabulaire, référentiel) avec seulement les consignes spécifiques à l'intention qui varient. Concrètement : un prompt "racine" par domaine (normes, ton, référentiel) + des blocs additionnels par intention, plutôt que 7×5 prompts totalement indépendants à maintenir.
- **Outil de calcul : bibliothèques/outils dédiés par domaine**, plutôt qu'une sandbox de code générique. Cohérent avec la fiabilité recherchée (§6, §9.3) : des formules et méthodes métier vérifiées (finance, statistique, comptabilité) plutôt qu'un LLM qui génère du code à la volée pour chaque calcul. *Point connexe (hors périmètre de Dexter, noté pour mémoire) : un projet séparé de calculatrice Python (standard + une par domaine) est envisagé en parallèle — pourrait à terme constituer une base pour ces outils de calcul dédiés, mais reste un projet distinct pour l'instant, pas encore intégré au périmètre de Dexter.*
- **Providers LLM à intégrer en premier** : reste ouvert — se précisera une fois l'architecture de routage validée dans son ensemble.

---

## 11. Roadmap

### 11.1 Un point de vigilance qui a fait évoluer la roadmap

**Décision initiale (§3, désormais révisée) :** les 7 domaines à profondeur égale dès le MVP posaient un risque concret pour un développement solo sans échéance — celui de repousser indéfiniment un premier lancement testable. **Décision retenue : le MVP se limite à 2 domaines**, les 5 autres étant ajoutés progressivement après le lancement pilote, au rythme des retours réels d'usage. La roadmap ci-dessous reflète ce périmètre resserré.

### 11.2 Phase 0 — Socle technique

- Setup du repo (backend FastAPI + frontend React), Docker, CI basique
- Base de données PostgreSQL + pgvector (§7.5/§8) sur l'hébergeur simplifié (§7.3)
- Authentification (inscription, connexion, choix du profil étudiant/professeur — §5.1)
- Couche d'abstraction multi-modèles (§7.2), même avec un seul provider branché au départ

### 11.3 Phase MVP — Cœur fonctionnel sur 2 domaines

- Chat conversationnel avec détection automatique domaine + sous-thème (§3.1, §5.4), sur les 2 domaines retenus pour le MVP
- Prompts spécialisés pour ces 2 domaines, avec variantes par intention (§10.5) — explication/définition en priorité, calcul/cas pratique pourront être affinés en continu
- Gestion du référentiel normatif dynamique, persistant par conversation (§5.4)
- Bilingue français/anglais (§6)
- Upload de documents + RAG hybride basique (§9) — croisement multi-documents, transparence de source
- Interface unique étudiant/professeur avec fonctionnalités de base différenciées (§2.2) : chat + upload pour les deux profils
- Historique des conversations

*Volontairement exclu du MVP (repoussé en V1) : outils de calcul dédiés par domaine (§10.5), génération de quiz/exercices, partage de documents prof→classe. Le MVP prouve la valeur du chat expert sur un périmètre restreint mais solide, avant d'élargir aux autres domaines et aux couches pédagogiques actives.*

### 11.4 Phase V1 — Extension des domaines et couche pédagogique active

- **Ajout progressif des 5 domaines restants**, un par un ou par petits groupes, au rythme des retours d'usage réels du pilote — chaque nouveau domaine reprend le même travail de conception de prompts spécialisés déjà rodé sur les 2 premiers (§10)
- Outils de calcul dédiés par domaine (§10.5) — fiabilise les réponses chiffrées en compta/finance/stats
- Génération de quiz/exercices personnalisés (§5.2), avec correction et suivi individuel (`quiz_attempts`, §8.1)
- Partage de documents professeur → classe (`visibilite = 'partage_classe'`, §4.3, §8.1) et notion de classes (`classes`, `classe_membres`, §8.1)
- Génération d'exercices/corrigés pour les professeurs (§5.3)
- Affinement continu des prompts par intention à partir des retours d'usage réels du pilote

### 11.5 Phase V2 — Mobile et suivi avancé

- Applications Android et iPhone (§6, plateformes) — l'API REST stabilisée en amont (FastAPI, §7.1) rend cette étape une consommation de l'API existante plutôt qu'une réécriture
- Suivi de progression de classe pour les professeurs (§5.3, §8.3 — vue agrégée ou détaillée à trancher à ce stade)
- Bibliothèque de documents persistante hors conversation, si le besoin est confirmé par l'usage (§4.3, point resté ouvert)
- Optimisations de coût/performance à la lumière de la charge réelle observée en pilote (§6)

### 11.6 Décisions actées

- **Équipe : développement solo.** Implication concrète sur la roadmap : les phases doivent rester réalistes pour un rythme individuel — privilégier un socle simple et robuste (§7.1, hébergeur simplifié, Docker) plutôt que des optimisations prématurées, et accepter que les 7 prompts spécialisés (§10) s'affinent progressivement plutôt que d'être parfaits dès le premier jour.
- **Pas d'échéance externe** : rythme libre, sans date de lancement pilote imposée. Ça laisse la priorité à la qualité du MVP (les 7 domaines bien traités, §3) plutôt qu'à la vitesse.
- **Critère de passage MVP → V1 : nombre d'utilisateurs actifs atteint.** *Point à préciser plus tard, une fois le pilote lancé et un premier ordre de grandeur observé* : quel seuil concret viser (ex. combien d'utilisateurs actifs sur combien de temps) — pas urgent à trancher avant d'avoir des premières données réelles.

---

## 12. Spécification API (endpoints)

Convention REST, exposée via FastAPI (§7.1) avec documentation OpenAPI/Swagger auto-générée — condition posée pour que les futures apps mobiles (§11.5) consomment la même API sans réécriture.

### 12.1 Authentification & profil

| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Inscription — email, mot de passe, choix du profil `etudiant`/`professeur` (§5.1) |
| POST | `/auth/login` | Connexion — retourne JWT (access + refresh) |
| POST | `/auth/refresh` | Rafraîchissement du token |
| GET | `/users/me` | Profil de l'utilisateur connecté |
| PATCH | `/users/me` | Mise à jour du profil (filière, matières enseignées, langue préférée — §8.1) |

### 12.2 Conversations & messages

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/conversations` | Liste des conversations de l'utilisateur |
| POST | `/conversations` | Créer une nouvelle conversation |
| GET | `/conversations/{id}` | Détail d'une conversation (messages, référentiel actif, documents liés) |
| PATCH | `/conversations/{id}` | Modifier (ex. changer explicitement le référentiel normatif — §5.4) |
| DELETE | `/conversations/{id}` | Supprimer une conversation |
| POST | `/conversations/{id}/messages` | Envoyer un message — déclenche détection domaine/sous-thème (§3.1), routage (§10), retrieval RAG si pertinent (§9.2). Réponse en streaming (§6, performance) |
| GET | `/conversations/{id}/messages` | Historique des messages de la conversation |

### 12.3 Documents & RAG

| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/conversations/{id}/documents` | Upload d'un document dans une conversation (§4.3, §9.1) — déclenche extraction/chunking/embedding en tâche asynchrone |
| GET | `/conversations/{id}/documents` | Liste des documents d'une conversation |
| GET | `/documents/{id}` | Détail d'un document (statut d'indexation, domaine associé détecté) |
| PATCH | `/documents/{id}/visibility` | Changer la visibilité `prive`/`partage_classe` — réservé aux professeurs (§4.3) |
| DELETE | `/documents/{id}` | Supprimer un document (et ses chunks associés) |

### 12.4 Domaines & quiz (V1, §11.4)

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/domains` | Liste des 7 domaines disponibles (référentiel statique côté produit) |
| POST | `/quiz/generate` | Générer un quiz sur un domaine/sous-thème donné (§5.2, §5.3) |
| POST | `/quiz/{id}/submit` | Soumettre les réponses — correction + stockage dans `quiz_attempts` (§8.1) |
| GET | `/users/me/progress` | Suivi de progression individuel par domaine (§5.2) |

### 12.5 Classes (V1, §11.4)

| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/classes` | Créer une classe — réservé aux professeurs (§8.1) |
| GET | `/classes` | Liste des classes du professeur, ou de la classe rejointe pour un étudiant |
| POST | `/classes/{id}/join` | Rejoindre une classe (étudiant, via code d'invitation à définir) |
| GET | `/classes/{id}/progress` | Suivi agrégé ou détaillé des étudiants de la classe (§8.3, granularité à trancher) |

### 12.6 Points à trancher

- **Pagination et filtres** : convention à définir pour les listes (conversations, documents, historique) — offset/limit classique ou curseur ?
- **Rate limiting** : nécessaire dès le pilote (dizaines d'utilisateurs, §6) ou seulement à partir de la V1/V2 quand la volumétrie grandira ?
- **Versionning de l'API** : préfixe `/v1/` dès le départ (facilite l'évolution sans casser les futures apps mobiles), ou pas de versionning tant qu'on reste en pilote ?

---

## 13. Statut des sections

- [x] Vision & positionnement (draft)
- [x] Public cible (étudiants + professeurs, université, cross-zone)
- [x] Domaines fonctionnels (draft)
- [x] Modes d'usage (draft)
- [x] Parcours utilisateur (étudiant + professeur, draft)
- [x] Exigences non-fonctionnelles (draft)
- [x] Architecture technique (draft — pgvector retenu ; providers LLM concrets à préciser au routage par domaine)
- [x] Modèle de données (draft — dimension embeddings et vue prof/classe à préciser plus tard)
- [x] Stratégie RAG (draft — modèle d'embedding et politique de ré-indexation à préciser)
- [x] Routage par domaine / prompts spécialisés (draft — variantes par intention retenues ; outils de calcul dédiés par domaine)
- [x] Roadmap (draft — équipe solo, rythme libre, critère MVP→V1 acté ; seuil chiffré à préciser après lancement)
- [x] Spécification API (endpoints) (draft — pagination, rate limiting et versionning à trancher)

---

**Toutes les sections du cadrage sont désormais actées.** Le PRD est complet dans sa première version — les quelques points laissés ouverts (modèle d'embedding, granularité de certaines vues, conventions API mineures) sont des détails d'implémentation qui se trancheront naturellement en construisant, sans remettre en cause la cohérence d'ensemble du document.

---

*Document vivant — on avance section par section et on l'enrichit ensemble.*
