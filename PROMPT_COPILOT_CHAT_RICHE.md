# PROMPT COPILOT — Chat : trombone natif + réponses riches + feedback

Tu interviens sur le projet **Dexter Chat AI** (React 19 + TypeScript + Tailwind v4 + Vite ; FastAPI + SQLAlchemy + Alembic + PostgreSQL).
Lis d'abord ces fichiers pour comprendre les conventions et le contrat existant — n'écris rien avant :

**Frontend** : `frontend/src/pages/Chat.tsx`, `frontend/src/documents/api.ts`, `frontend/src/documents/types.ts`,
`frontend/src/auth/AuthContext.tsx`, `frontend/src/auth/guestMode.ts`, `frontend/src/theme/` (tokens CSS), `frontend/src/index.css`.
**Backend** : `backend/app/routers/chat.py`, `backend/app/services/chat_service.py`, `backend/app/services/conversations.py`,
`backend/app/models/conversation.py`, `backend/app/schemas/conversation.py`, `backend/app/routers/conversations.py`,
`backend/app/routers/documents.py` (pattern d'ownership), `backend/app/main.py`,
`backend/alembic/versions/202409050000_classes.py` (MODÈLE de révision à imiter), `backend/app/prompts/templates/finance/root.md`,
`backend/tests/test_chat_stream.py`, `backend/tests/test_conversations.py`, `backend/tests/test_documents.py` (pattern de tests).

## Contexte : le bug racine à corriger

Aujourd'hui, `POST /chat/stream` (voie `_stream_chat_events`) **ne crée jamais de conversation** : si `conversation_id`
est null, rien n'est créé ni persisté, et aucun événement SSE ne renvoie `conversation_id`. Résultat : le state
`conversationId` du Chat reste **toujours null**, le trombone ne s'active jamais, et les conversations streamées ne
sont pas persistées (la voie synchrone `/chat/message`, elle, persiste et retitre automatiquement).

**Décisions actées par l'utilisateur (ne pas contester, ne pas réinterpréter)** :
1. Dépendances frontend autorisées : **`react-markdown` + `remark-gfm`** — c'est tout. Pas de syntax highlighting
   (rehype-highlight interdit dans ce cycle).
2. Menu du trombone à **2 items** (« Document de cours » / « Image »).
3. Échec d'upload = **tout-ou-rien** : le message n'est pas envoyé.
4. **Option B** : instructions de format markdown ajoutées aux 7 `templates/<domaine>/root.md`.
5. Carte calcul stylée + horodatages + **pouces de feedback** (nouvelle colonne + endpoint + migration Alembic).
6. Trombone **actif nativement pour tous, invité inclus** ; l'invité peut attacher (staged local) mais l'envoi
   requiert un compte → CTA de connexion à l'envoi (le backend exige l'auth ; ne pas créer d'upload anonyme).

## PARTIE A — BACKEND

### A1. Colonne feedback sur Message
Dans `backend/app/models/conversation.py`, classe `Message`, ajouter :
`feedback: Mapped[str | None] = mapped_column(String(10), nullable=True)` (valeurs admises : `'up'`, `'down'`).

### A2. Migration Alembic
Créer `backend/alembic/versions/202409060000_message_feedback.py` en imitant EXACTEMENT le style de
`202409050000_classes.py` (docstring, identifiants, upgrade/downgrade) :
`revision = "202409060000"`, `down_revision = "202409050000"` ;
upgrade : `op.add_column("messages", sa.Column("feedback", sa.String(length=10), nullable=True))` ;
downgrade : `op.drop_column("messages", "feedback")`.

### A3. Schéma
Dans `backend/app/schemas/conversation.py` : `MessageRead` gagne `feedback: str | None = None`.

### A4. Endpoint feedback
Créer `backend/app/routers/messages.py` (nouveau routeur, tags `["messages"]`, pas de préfixe) :
`PATCH /messages/{message_id}/feedback` — body `{"feedback": "up" | "down"}` (Pydantic Literal, nouveau schéma
`MessageFeedbackUpdate` dans `schemas/conversation.py`). Auth requise (`get_current_user`). Propriété vérifiée par
jointure message → conversation → `user_id` (même logique d'ownership que `documents.py`) : 404 si introuvable ou
pas au propriétaire. Retour : `MessageRead` du message mis à jour. Enregistrer le routeur dans `main.py` (import +
include_router), en respectant l'ordre existant.

### A5. Corrections dans `_stream_chat_events` (`routers/chat.py`) — 2 ajouts minimes
1. **Auto-titre** (miroir de la voie synchrone, l. 202-206) : quand `conversation` existe et que
   `conversation.titre in ("", "Nouvelle conversation")`, le remplacer par le début de la question
   (`payload.question.strip()[:50]`, + `"..."` si tronqué) via `update_conversation`.
2. **`done` enrichi** : récupérer le message assistant retourné par `add_message` (le service retourne l'objet
   Message) et émettre `yield _sse_event({"type": "done", "message_id": assistant_message.id})`.
   ⚠️ Ne modifie AUCUNE autre partie du flux (classification, RAG, tokens, gestion d'erreurs : intacts).

### A6. Instructions markdown dans les 7 templates
Ajouter à la fin de la partie instructions (avant la ligne `Question : $question`) de CHACUN des
`backend/app/prompts/templates/{comptabilite,finance,management,marketing,statistique,banque,business}/root.md` :

```
Structure ta réponse en Markdown lisible : titres courts (###), **gras** sur les notions clés, listes à puces
quand cela aide la compréhension, bloc de citation (>) pour les analogies ou les encadrés « Exemple », et du
code formaté si pertinent. Jamais de mur de texte : aère avec des paragraphes courts.
```

### A7. Tests backend
- Mettre à jour `test_chat_stream.py` : l'événement `done` contient `message_id` (entier) ; auto-titre vérifié
  après un stream sur conversation titrée « Nouvelle conversation ».
- Nouveau `test_messages_feedback.py` : 200 (feedback persisté), 401 sans token, 404 message d'un autre utilisateur.
  Imiter le pattern de `test_documents.py`/`test_conversations.py` (création user + conversation via les services).
- Les 8 échecs pytest préexistants (`test_auth.py`/`test_chat.py`) sont HORS périmètre : ne pas les toucher.

## PARTIE B — FRONTEND

### B1. Dépendances (les seules autorisées)
Dans `frontend/` : `npm install react-markdown remark-gfm`. Aucune autre dépendance.

### B2. `frontend/src/components/ChatMarkdown.tsx` (nouveau)
Wrapper `react-markdown` (+ plugin `remark-gfm`) qui rend le contenu assistant. **Tous les éléments stylés via
classes Tailwind + variables CSS existantes (`var(--...)`) — aucun hex, aucune nouvelle couleur** :
- `p` : `leading-6` normal ; `strong` : `font-semibold text-[var(--text-primary)]` ;
- `h1-h4` : tailles maîtrisées dans la bulle (ex. h3 ≈ `text-base font-semibold mt-4 mb-1`), jamais plus grand que le texte de bulle ;
- `ul`/`ol`/`li` : `list-disc`/`list-decimal`, `pl-5`, espacement `my-1` ;
- `blockquote` : **panneau interne** comme la maquette (fond `var(--surface)`, bordure gauche 3px `var(--primary)`,
  `rounded-[12px]`, `p-4`, `my-3`) — c'est le rendu du bloc « Analogy: » de la maquette ;
- `table` (GFM) : conteneur `overflow-x-auto`, cellules bordées `var(--border-default)`, en-tête `var(--surface)` ;
- `code` inline : fond `var(--surface)`, `rounded-[6px]`, `px-1`, police monospace ;
- `pre > code` : bloc fond `var(--background)`, `rounded-[12px]`, `p-4`, `overflow-x-auto`.
Pas de rehype-highlight. Le composant doit être stable pendant le streaming (re-render à chaque token : acceptable).

### B3. `frontend/src/components/AttachMenu.tsx` (nouveau)
Menu popup ouvert au clic sur le trombone, positionné au-dessus de la barre de saisie (aligné à gauche du trombone),
style ChatGPT : fond `var(--surface)`, bordure `var(--border-default)`, `rounded-[12px]`, ombre douce,
`role="menu"`. Deux items (`role="menuitembutton"`) :
1. Icône `description` — « Document de cours » — sous-titre « PDF, Word, PowerPoint, TXT, Markdown » →
   `<input type="file" multiple accept=".pdf,.docx,.pptx,.txt,.md">` ;
2. Icône `image` — « Image » — sous-titre « PNG, JPG — OCR intégré » → `<input type="file" multiple accept=".png,.jpg,.jpeg">`.
Fermeture : clic extérieur **et** touche Échap (listeners `useEffect` nettoyés). Icônes Material Symbols.
Accessibilité : `aria-haspopup`, `aria-expanded` sur le trombone, focus visible.

### B4. `frontend/src/conversations/api.ts` (nouveau)
- Type `ConversationRead` (champs du schéma backend `ConversationRead`) et
  `setMessageFeedback(messageId: number, feedback: 'up' | 'down'): Promise<void>` →
  `PATCH {apiUrl}/messages/{messageId}/feedback`.
- `createConversation(payload: { titre?: string } = {}): Promise<ConversationRead>` → `POST {apiUrl}/conversations`.
- Appels axios nus (l'en-tête Authorization global de `AuthContext` s'applique — même pattern que `classes/api.ts`).

### B5. `frontend/src/pages/Chat.tsx` — refonte guidée (le reste de la page ne bouge pas)
**États ajoutés** : `stagedFiles: { id: string; file: File }[]` (pièces jointes en attente, retirables) ;
`attachMenuOpen: boolean` ; `AssistantMessage` gagne `messageId?: number` (id serveur reçu via `done`) et
`feedback?: 'up' | 'down'` + `sentAt: string` (heure locale au moment de l'envoi, format fr 24 h).

**Trombone** : toujours actif (`disabled` UNIQUEMENT pendant un upload en cours). Invité inclus : le menu s'ouvre.
Info-bulle : « Joindre un document » (connecté) / « Connectez-vous pour joindre des documents à vos échanges » (invité).

**Chips au-dessus de la barre (bande existante)** — 3 états visuellement distincts :
1. chips **staged** : icône + nom tronqué + croix (`close`) de retrait, style « en attente » (bordure pointillée) ;
2. chip **upload en cours** (spinner, existant) ;
3. chips **documents réels** (statut + suppression + visibilité prof — existants, inchangés).

**Envoi (connecté)** — ordre strict :
1. Si `conversationId === null` → `createConversation({ titre: 'Nouvelle conversation' })` → `setConversationId(id)` ;
2. Upload **séquentiel** de chaque staged via `uploadDocument(conversationId, file)` ; chaque chip staged devient un
   document réel (rafraîchir la liste) ;
3. **Tout-ou-rien** : si un upload échoue → le message n'est PAS envoyé ; erreur explicite affichée
   (`getDocumentErrorMessage` existant) ; la chip en échec est retirée, les autres staged sont conservés ;
4. Sinon → `POST /chat/stream` (SSE existante, corps `{ question, conversation_id }`) ; à l'événement `done`, lire
   `message_id` (clé optionnelle dans l'union du type d'événement — SEUL changement autorisé au parsing SSE) et
   l'attacher au message assistant.

**Envoi (invité)** — intercepter AVANT tout appel réseau : carte d'incitation (fond `var(--surface)`, bordure
`var(--border-default)`, `rounded-[12px]`, `role="alert"`) : « Créez un compte pour envoyer vos documents et
recevoir des réponses de Dexter. » + bouton primaire « Créer un compte » → `navigate('/register')` + lien
secondaire « J'ai déjà un compte » → `navigate('/login')`. Le chat invité ne doit plus déclencher d'appel API
en échec 401 : l'interception remplace l'erreur brute.

**Rendu des réponses (cœur de la demande)** : la bulle assistant remplace
`<p className="whitespace-pre-wrap">{message.content}</p>` par `<ChatMarkdown content={message.content} />`.
La bulle user garde `whitespace-pre-wrap` (texte simple).

**Carte calcul** : remplacer le `<pre>` JSON brut par une carte « Calcul vérifié » : en-tête (icône `calculate` +
titre « Calcul vérifié »), corps = le JSON indenté existant (`formatCalculation`) en monospace sur fond
`var(--background)`, `rounded-[12px]`, bordure `var(--border-default)`. Même donnée, présentation soignée.

**Horodatages** (maquette) : sous la bulle user, à droite, l'heure locale ; sous la bulle assistant,
« Dexter • hh:mm ». Format 24 h français.

**Pouces de feedback** : à côté de « Dexter • hh:mm », 2 boutons Material Symbols `thumb_up` / `thumb_down`
(visibles UNIQUEMENT si connecté ET `messageId` défini — jamais pendant le streaming). Clic →
`setMessageFeedback(messageId, 'up'|'down')` ; état local optimiste (`aria-pressed`, couleur `var(--primary)` sur
le pouce sélectionné) ; re-clic sur le pouce déjà sélectionné = renvoi idempotent de la même valeur (pas de
désélection — contrat Literal). En cas d'échec : retour à l'état précédent + message discret.

**Inchangé (garde-fous)** : boucle de lecture SSE (hors clé `message_id`), badge mode + bloc clarification,
liste/chargement des documents par conversation, mode `mes_cours`, disclaimer, style global.

## Vérifications obligatoires (exécution réelle, pas de supposition)
1. Backend (PostgreSQL démarré — sinon `powershell -ExecutionPolicy Bypass -File .\start-dev.ps1`) :
   `cd backend ; .\.venv\Scripts\python.exe -m alembic upgrade head` (migration appliquée) ;
   `.\.venv\Scripts\python.exe -m pytest tests/test_messages_feedback.py tests/test_chat_stream.py tests/test_conversations.py -q` → tous pass.
2. Frontend : `npm install` puis `node node_modules\typescript\bin\tsc --noEmit -p tsconfig.app.json` → 0 erreur ;
   `npm run build:node` → exit 0.
3. Ne modifie AUCUN autre fichier que ceux listés ; ne touche pas à `Layout.tsx`, `App.tsx`, aux autres pages ni aux
   8 tests cassés préexistants. En cas de blocage : arrête-toi et documente le blocage dans ta réponse au lieu de
   contourner.

## ADDENDUM v2 — production reprise après arrêt (21/09/2026)

La production a été interrompue. État constaté sur disque : Partie A presque complète, **sauf A7**
(`backend/tests/test_messages_feedback.py` absent). **Partie B entièrement absente** : `ChatMarkdown.tsx`,
`AttachMenu.tsx`, `conversations/api.ts`, modifications de `Chat.tsx`, `npm install react-markdown remark-gfm` —
rien n'existe. Reprends exactement là.

### A8 (nouveau) — `conversation_id` dans l'événement `done`
Ton implémentation fait créer la conversation par le backend (l. 91-93) — accepté, filet de sécurité cohérent.
MAIS l'identifiant n'est jamais communiqué au frontend : aucun événement SSE ne le transporte, donc le frontend
ne peut jamais activer le trombone ni charger les documents. Corrige la ligne `done` :

`yield _sse_event({"type": "done", "message_id": assistant_message.id, "conversation_id": conversation.id})`

(la branche `else` sans conversation garde `{"type": "done"}` tel quel).
**Design acté** : le frontend crée TOUJOURS la conversation en amont (`POST /conversations`) avant l'upload des
pièces jointes et avant le stream — même sans pièce jointe ; la création côté backend ne s'applique qu'à
`conversation_id=null` (aucun double-creation possible).

### A7 — rappel (toujours absent)
Créer `backend/tests/test_messages_feedback.py` (200 feedback persisté / 401 sans token / 404 message d'un autre
utilisateur) et mettre à jour `test_chat_stream.py` : `done` contient `message_id` **et** `conversation_id` ;
auto-titre vérifié. Re-applique la migration si besoin : `.\.venv\Scripts\python.exe -m alembic upgrade head`.

### B1 → B5 — rappel (entièrement à produire)
Tels que spécifiés ci-dessus, sans changement. Deux précisions :
- Le parsing SSE existant lit déjà `conversation_id` s'il est présent dans un événement
  (`if (event.conversation_id !== undefined) setConversationId(...)`) — ajoute seulement la clé `message_id`
  (optionnelle) à l'union du type d'événement.
- `createConversation` est appelé au premier envoi quel que soit le cas (avec ou sans pièces jointes) ; le
  `conversation_id` reçu dans `done` sert de filet de sécurité (si défini et différent du state, l'adopter).

Vérifications obligatoires inchangées : alembic upgrade head ; pytest ciblés → tous pass ; `tsc --noEmit` →
0 erreur ; `npm run build:node` → exit 0.