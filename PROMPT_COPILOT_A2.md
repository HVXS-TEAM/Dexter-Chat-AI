# PROMPT_COPILOT — A2 : Écran d'accueil Dexter

**Contexte :** le socle A1 est validé (layout `src/components/Layout.tsx`, tokens deux thèmes dans `src/index.css`, ThemeProvider, routes React Router). Tu réalises **uniquement** l'écran d'accueil (`src/pages/Accueil.tsx`), fidèle aux maquettes fournies. Aucune autre page, aucun autre fichier existant ne doit être modifié (sauf indication ci-dessous).

## Sources de vérité (OBLIGATOIRES — interdiction d'inventer un style, une couleur ou une géométrie)
1. `stitch_dexter_ai_educational_platform/cran_d_accueil_dexter/screen.png` — **autorité finale de géométrie** (sombre).
2. `stitch_dexter_ai_educational_platform/cran_d_accueil_clair_dexter_2/code.html` — référence exécutable (variante claire retenue).
3. `stitch_dexter_ai_educational_platform/cran_d_accueil_clair_dexter_2/cran_d_accueil_clair_dexter_2.json` — spec machine (composants, labels requis, règles de fidélité).
4. Tokens déjà en place dans `frontend/src/index.css` (variables des deux thèmes) — **utilise-les**, ne redéfinis aucune couleur.
5. `stitch_dexter_ai_educational_platform/aether_intelligence/DESIGN.md` + `aether_intelligence_light_2/DESIGN.md` — contrats design system (grille 12 col, gouttière 24, base 8, radius 18 cartes / 12 contrôles / pill, Inter, Material Symbols Outlined 24px).

## Contenu de l'écran (labels conformes aux specs)
1. **Zone de question centrale** : placeholder « Pose ta question à Dexter » + bouton d'envoi.
   - Comportement : à la soumission, **naviguer vers `/chat`** en transmettant la question (via state de navigation React Router — PAS de query string).
2. **Chips de suggestions** sous la barre : reprendre EXACTEMENT les chips des maquettes (labels du `code.html` / JSON spec). Un clic = même navigation vers `/chat` avec la question pré-remplie.
3. **Grille « Tes Matières »** : **7 domaines PRD** chargés depuis le backend — **JAMAIS en dur** :
   - appel `GET /domains` via axios (base URL : lire `import.meta.env.VITE_API_URL` avec fallback `http://localhost:8000`) ;
   - réponse : tableau `[{"id", "label", "keywords", "sous_themes", "referentiels"}, ...]` (7 entrées attendues : comptabilite, finance, marketing, statistique, banque, business, management) ;
   - chaque carte : `label` + (si utile à la carte) nombre de sous-thèmes ; navigation → `/matiere/:id` avec l'`id` du domaine ;
   - **états obligatoires** : chargement (squelette ou spinner sobre), erreur (message explicite + bouton « Réessayer », **jamais silencieux**), liste vide (message explicite).
4. Si la maquette affiche d'autres blocs (en-tête de bienvenue, raccourcis…), reprendre ceux du `code.html`/`screen.png` — rien de plus, rien de moins.

## Règles techniques
- React 19 + TypeScript strict + Tailwind v4 (déjà configuré via `@tailwindcss/vite`).
- Typage : définir une interface `Domain` alignée sur le contrat `GET /domains` ci-dessus.
- Utiliser les classes utilitaires Tailwind **mappées aux variables CSS** des thèmes (ex. `bg-[var(--surface)]`) pour que le toggle sombre/claire fonctionne sans code supplémentaire.
- Icônes : Material Symbols Outlined (déjà chargées par `index.html`), 24px.
- Responsive : suivre les breakpoints du `DESIGN.md` (sidebar 280px desktop → rail tablette → nav basse mobile, déjà gérés par le Layout — ne pas les recoder ici).
- Aucune nouvelle dépendance npm. Aucun appel LLM direct. Aucun `console.log` laissé. Pas d'erreur avalée : en cas d'échec axios, afficher l'état d'erreur prévu.

## Definition of Done
- `src/pages/Accueil.tsx` réécrit, rien d'autre modifié.
- `npm run build` (tsc + vite) passe sans erreur ni warning nouveau.
- En navigation : question → `/chat` (question transmise) ; carte → `/matiere/:id` ; toggle thème fonctionne sur cet écran.
