# PROMPT COPILOT — Écran « Mes classes » (frontend, fin de C)

Copilot : produis l'écran **« Mes classes »** de Dexter Chat AI (React 19 + TypeScript + Vite + Tailwind v4 + react-router-dom 7 + axios). **Lis d'abord** :

- `stitch_dexter_ai_educational_platform/stitch_dexter_ai_classroom_portal/stitch_dexter_ai_classroom_portal.json` — spécification de reproduction (3 variantes, tokens, contenu exact, **10 dispositions de données validées**) ;
- les 3 `screen.png` du même dossier (autorité géométrie) ;
- `frontend/src/pages/Profil.tsx` — pattern de page à suivre (axios + états + Tailwind avec `var()`) ;
- `frontend/src/components/Layout.tsx` et `frontend/src/App.tsx` — points de branchement ;
- `frontend/src/auth/AuthContext.tsx` — authentification (ne pas réinventer).

## Périmètre exact — 5 fichiers, rien d'autre

1. **NOUVEAU** `frontend/src/classes/types.ts`
2. **NOUVEAU** `frontend/src/classes/api.ts`
3. **NOUVEAU** `frontend/src/pages/Classes.tsx`
4. **MODIF** `frontend/src/App.tsx` — route `/classes` dans le groupe protégé « compte requis » (comme `/profil`, SANS `allowGuest`)
5. **MODIF** `frontend/src/components/Layout.tsx` — une seule entrée de navigation ajoutée : `Mes classes`, icône `groups`, insérée après `Mes matières` (les classes CSS existantes `navigation-link` s'appliquent d'elles-mêmes)

**Interdits** : toute autre modification (backend, autres pages, `index.css`, thème) ; toute nouvelle dépendance ; tout champ de données absent du backend ; tout code de gestion d'invité (la redirection est déjà assurée par `ProtectedRoute`).

## Contrat backend V1 — aucune modification autorisée

- `GET /classes` → 200 : **professeur** = `ClassRead[]` `{id, nom, professeur_id, code_invitation, created_at}` ; **étudiant** = `ClassReadStudent[]` `{id, nom, professeur_id, created_at}` (jamais de `code_invitation`).
- `POST /classes` (professeur) body `{nom}` → 201 `ClassRead` ; 403 si rôle ≠ professeur.
- `POST /classes/{id}/join` (étudiant) body `{code_invitation}` → 200 `ClassJoinResponse` (= ClassReadStudent) ; **400** code invalide ou déjà membre (message dans `detail`) ; **404** classe absente ; **403** si rôle ≠ étudiant.
- **Auth** : n'envoie pas le Bearer toi-même. Utilise `axios` nu — l'instance globale porte déjà `Authorization` (posé dans `axios.defaults` par `AuthContext`) et l'intercepteur 401 → refresh silencieux → retry. `baseURL` = `import.meta.env.VITE_API_URL || 'http://localhost:8000'`.

## Types attendus (`classes/types.ts`)

```ts
export interface ClassRead { id: number; nom: string; professeur_id: number; code_invitation: string; created_at: string }
export interface ClassReadStudent { id: number; nom: string; professeur_id: number; created_at: string }
export type ClassJoinResponse = ClassReadStudent
export interface ClassCreatePayload { nom: string }
export interface ClassJoinPayload { code_invitation: string }
```

## Fonctions attendues (`classes/api.ts`, axios nu, comme Profil.tsx)

```ts
listClasses(): Promise<Array<ClassRead | ClassReadStudent>>
createClass(payload: ClassCreatePayload): Promise<ClassRead>          // POST /classes
joinClass(classeId: number, payload: ClassJoinPayload): Promise<ClassJoinResponse>  // POST /classes/{id}/join
```

## Spécification écran — `frontend/src/pages/Classes.tsx`

Une seule page ; **deux vues selon `user.role`** (`useAuth()` importé depuis `../auth`). Le thème clair/sombre est géré par les variables CSS existantes : les variantes sombre/clair de la maquette deviennent **une** implémentation.

**Structure commune** : H1 « Mes classes » + sous-titre — étudiant : « Rejoignez une classe ou retrouvez celles où vous êtes inscrit. » ; professeur : « Créez vos classes et partagez le code d'invitation avec vos étudiants. »

**Vue étudiant** (`user.role === 'etudiant'`) :
- Carte bordée violette « Rejoindre une nouvelle classe » : texte d'aide « Entrez le code communiqué par votre professeur pour accéder aux cours et travaux. » ; champ « Code d'invitation » (placeholder « EX. A7XK2M9P », `maxLength={8}`, valeur mise en majuscules à la saisie) ; bouton primaire « Rejoindre ».
- Rejoindre : à la réussite → message de confirmation inline + rechargement de la liste ; à l'échec → afficher le `detail` renvoyé par le backend (400/404), lisible et explicite.
- Section « Classes actuelles » + chip pilule compteur « N classes actives ».
- Grille de cartes : pastille arrondie avec icône `groups`, nom de la classe, ligne « Professeur » (générique, sans nom — disposition 1), séparateur, « Créée le {date} » (disposition 2) + icône `check_circle`. Aucun bouton/CTA sur les cartes.

**Vue professeur** (`user.role === 'professeur'`) :
- Eyebrow « Espace enseignant » (petites majuscules, sans année — disposition 8).
- Carte bordée violette « Créer une nouvelle classe » : champ « Nom de la classe » (placeholder « Ex. Terminale — Comptabilité », requis, `trim`) ; bouton primaire « Créer une classe » (icône `add`). À la réussite (201) → rechargement de la liste ; le code apparaît sur la nouvelle carte.
- Grille de cartes : nom, **panneau inset « CODE D'INVITATION »** (fond sombre type `var(--surface-secondary)`, label en petites capitales, code en `font-mono`, bouton icône `content_copy` → `navigator.clipboard.writeText`), « Créée le {date} ».

**Omis conformément aux dispositions 3-7** (ne pas les inventer) : nombre d'inscrits, lieu, description de carte, chips de catégorie, contrôle de tri.

**États** (micro-états absents de la maquette — réutiliser les patterns `Profil.tsx`, ne pas créer de design neuf) :
- Chargement : skeleton (`animate-pulse`, blocs aux mêmes formes).
- Erreur réseau : message explicite + bouton « Réessayer ».
- Liste vide : message simple « Aucune classe pour le moment. »
- Date : `new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })` (comme Profil.tsx).

## Conventions de style (Tailwind v4 + variables existantes UNIQUEMENT)

- Utilise les classes arbitraires avec `var()` comme Profil.tsx : `bg-[var(--surface)]`, `border-[var(--border-default)]`, `text-[var(--text-primary)]`, `text-[var(--text-secondary)]`.
- Boutons pleins : `bg-[var(--primary-container)]` avec texte blanc (`hover:brightness-110`) — Profil.tsx l.172.
- Cartes : `rounded-[20px]` + bordure `border` + `bg-[var(--glass-background)]` ; cartes mises en avant (rejoindre/créer) : bordure violette (`border-[var(--primary)]/40`) + `bg-[var(--glass-background)]`.
- Champs et boutons : `rounded-[12px]` ; grilles : `grid gap-6 md:grid-cols-2 lg:grid-cols-3` ; conteneur de page : `w-full max-w-[1100px]` (comme Profil.tsx).
- Icônes : `<span className="material-symbols-outlined" aria-hidden="true">nom</span>` (24px, déjà chargées dans l'app).
- **Aucun hex littéral nouveau**, aucun ajout à `index.css`, aucune classe de design hors celles-ci.

## Vérifications avant de dire « terminé »

- `npx tsc --noEmit -p tsconfig.app.json` → **0 erreur** (obligatoire ; signale toute erreur au lieu de la contourner).
- Aucun `console.log` laissé ; erreurs réseau jamais avalées silencieusement (message visible à l'utilisateur).
- Ne touche à aucun autre fichier que les 5 du périmètre.