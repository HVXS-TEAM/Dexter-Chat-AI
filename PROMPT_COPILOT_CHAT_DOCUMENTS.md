# PROMPT COPILOT — Documents dans le Chat (RAG frontend, Phase 1)

Copilot : rends fonctionnel le **trombone du Chat** (joindre un document à la conversation, indexation RAG) et affiche les **documents de la conversation**. Stack : React 19 + TypeScript + Vite + Tailwind v4 + axios. **Lis d'abord** :

- `stitch_dexter_ai_educational_platform/chat_ia_dexter/screen.png` — maquette : le trombone dans la barre de saisie « Ask Dexter anything… » est l'autorité visuelle de l'affordance ;
- `frontend/src/pages/Chat.tsx` — page à modifier (le trombone `attach_file` y est **décoratif**, l. 278) ;
- `backend/app/routers/documents.py` + `backend/app/schemas/document.py` — contrat exact ;
- `frontend/src/classes/api.ts` — pattern des modules API (axios nu, sans Bearer manuel).

## Périmètre exact — 3 fichiers, rien d'autre

1. **NOUVEAU** `frontend/src/documents/types.ts`
2. **NOUVEAU** `frontend/src/documents/api.ts`
3. **MODIF** `frontend/src/pages/Chat.tsx`

**Interdits** : backend, `App.tsx`, `Layout.tsx`, `index.css`, autres pages, toute nouvelle dépendance, tout hex littéral. Le flux SSE (`sendQuestion`, fetch + Bearer) ne doit **pas** être modifié.

## Contrat backend V1 — aucune modification autorisée

- `POST /conversations/{conversation_id}/documents` — multipart `file` → **201** `DocumentRead` (indexation RAG synchrone) ; **404** conversation absente ; **400** type non supporté ; **422** indexation échouée.
- `GET /conversations/{conversation_id}/documents` → `DocumentRead[]` (du propriétaire, tri desc).
- `GET /documents/{document_id}` → `DocumentIndexStatus` (`nombre_chunks`).
- `PATCH /documents/{document_id}/visibility` — body `{visibilite: 'prive' | 'partage_classe'}` — **professeur uniquement** (403 sinon) → `DocumentRead`.
- `DELETE /documents/{document_id}` → 204 (fichier + chunks supprimés).
- Extensions acceptées : `.pdf, .docx, .pptx, .png, .jpg, .jpeg, .txt, .md`.
- `statut_indexation` : **`pending` | `indexe` | `erreur`** (l'upload est synchrone : une réponse 201 est déjà `indexe`).
- Auth : utilise `axios` **nu** (le jeton global + l'intercepteur 401 s'appliquent ; multipart géré automatiquement — ne met PAS Content-Type toi-même). `baseURL` = `import.meta.env.VITE_API_URL || 'http://localhost:8000'`.

## Types attendus (`documents/types.ts`)

```ts
export interface DocumentRead {
  id: number
  owner_id: number
  conversation_id: number
  titre: string
  type_fichier: string
  domaine_associe: string | null
  visibilite: 'prive' | 'partage_classe'
  fichier_url: string
  statut_indexation: 'pending' | 'indexe' | 'erreur'
  created_at: string
}

export type DocumentVisibility = 'prive' | 'partage_classe'
```

## Fonctions attendues (`documents/api.ts`, axios nu)

```ts
listConversationDocuments(conversationId: number): Promise<DocumentRead[]>
uploadDocument(conversationId: number, file: File): Promise<DocumentRead>   // FormData('file', file)
updateDocumentVisibility(documentId: number, visibilite: DocumentVisibility): Promise<DocumentRead>
deleteDocument(documentId: number): Promise<void>                            // DELETE, 204
```

## Spécification UI — `frontend/src/pages/Chat.tsx`

### Trombone fonctionnel
- Remplacer le `<span>` décoratif `attach_file` (l. 278) par un **`<button type="button">`** englobant l'icône, associé à un **`<input type="file" hidden>`** (`accept=".pdf,.docx,.pptx,.png,.jpg,.jpeg,.txt,.md"`, `aria-label="Joindre un document"`).
- **Conditions d'activation** (le trombone reste toujours visible, comme la maquette, mais `disabled` + `title` explicite) :
  1. invité (`user` null via `useAuth()`) → `title="Connectez-vous pour joindre des documents"` ;
  2. `conversationId === null` → `title="Envoyez d'abord un message pour démarrer une conversation"` (la conversation est créée par le premier échange, l'id revient dans le flux SSE) ;
  3. upload en cours → `disabled` tant que l'upload n'est pas terminé.
- À la sélection de fichier : **upload immédiat** via `uploadDocument(conversationId, file)` (aucun champ de texte supplémentaire).

### Présentation des documents de la conversation (adaptation validée)
- Une **bande de chips** au-dessus de la barre de saisie, dans le conteneur `fixed bottom-0` existant, visible uniquement si `conversationId` est défini (chargée via `listConversationDocuments`) :
  - icône selon le type : `description` pour les documents (pdf/docx/pptx/txt/md), `image` pour png/jpg/jpeg ;
  - titre du fichier **tronqué** (`truncate max-w-[160px]`), tooltip natif complet ;
  - **statut** : `indexe` → icône `check_circle` (vert doux via opacité, SANS hex) ; `pending` → icône `progress_activity` animée ; `erreur` → icône `error` ;
  - **suppression** : bouton icône `delete` (suppression immédiate, sans confirmation, V1) puis rechargement de la liste ;
  - **professeur uniquement** : bouton bascule de visibilité — icône `lock` si `prive`, `group` si `partage_classe` — appelant `updateDocumentVisibility` puis rechargement de la liste.
- Pendant un upload : une chip temporaire « upload en cours » (nom du fichier + `progress_activity` animée) ; la vraie chip remplace via le rechargement.
- Chips : `rounded-full border border-[var(--border-default)] bg-[var(--surface-secondary)] px-3 py-1.5 text-xs` — cohérentes avec les chips existantes de l'app. Bande : `flex flex-wrap gap-2`.
- Accessibilité : chaque bouton a un `aria-label` explicite (« Supprimer le document X », « Visibilité du document X »).

### Gestion des erreurs (jamais silencieuses — règle 6)
Affichées inline au-dessus des chips (même pattern que l'`errorMessage` existant) :
- 400 → « Type de fichier non supporté (pdf, docx, pptx, png, jpg, jpeg, txt, md). »
- 422 → « L'indexation du document a échoué. »
- 404 → « Conversation introuvable. »
- 403 (visibilité par un non-prof) → « Seuls les professeurs peuvent partager des documents. »
- autre → « Impossible de traiter le document. Vérifiez la connexion au serveur et réessayez. »

### Garde-fous
- Ne modifie PAS `sendQuestion` ni la logique SSE ; les documents sont indépendants du flux de chat.
- Ne toucher à aucun autre fichier ; aucun `console.log` ; Tailwind + `var()` uniquement.

## Vérifications avant de dire « terminé »

- `node node_modules/typescript/bin/tsc --noEmit -p tsconfig.app.json` → **0 erreur**.
- `npm.cmd run build:node` → **EXIT 0**.
- Scénario mental vérifié : invité → trombone désactivé ; 1er message → conversation créée → trombone actif ; upload .pdf → 201 → chip `indexe` ; upload .exe → 400 → message ; suppression → 204 → chip disparue ; prof → bascule visibilité.