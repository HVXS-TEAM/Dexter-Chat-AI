# PROMPT_COPILOT_A3.md — Étape A3 : Chat IA (Dexter)

## 🎯 Objectif unique
Implémenter l'écran `/` → `/chat` du Dexter Chat AI, fidèle aux maquettes `stitch_dexter_ai_educational_platform/chat_ia_dexter/` (sombre, autorité géométrie) et `chat_ia_clair/*. DESIGN.md` (clair, design tokens).

**Règle d'or (règle 3 des AGENTS.md du projet) :** aucune UI inventée. Tout ce qui n'est pas couvert par les specs/production spec → tu ne le fais pas, tu le signales.

## 📁 Sources de vérité (à lire, pas à deviner)
- **Sombre** (autorité géométrie) : `stitch_dexter_ai_educational_platform/chat_ia_dexter/screen.png` + le JSON annexe.
- **Clair** : `stitch_dexter_ai_educational_platform/chat_ia_clair_dexter_2/code.html` + `chat_ia_clair_dexter_2/DESIGN.md` (et clair_1 si contradicting).
- **Contrat A2 déjà implémenté** : `frontend/PROMPT_COPILOT_A2.md`, `frontend/src/components/DomainCard.tsx`, `frontend/src/theme/ThemeProvider.tsx`, `frontend/src/index.css`.

Ne pas utiliser tes connaissances génériques sur les interfaces de chat comme source de vérité ; utiliser uniquement ces fichiers.

## 🧪 Contraintes techniques (vérifiable par build)
- Stack **existant** à conserver : React 19, TypeScript, Vite, `react-router-dom` 7, `axios` (déjà configuré pour `http://localhost:8000`). **Pas de nouvelle dépendance npm** pour A3.
- Tokens exacts à réutiliser directement depuis `frontend/src/index.css` (variables `--color-*`, `--space-*`, `--radius-*`, `--font-*`, thèmes `light`/`dark`), **pas de recopier à la main**.
- Fichier à éditer : `src/pages/Chat.tsx` (si inexistant, le créer). Nouveaux composants internes : uniquement si justifiés par les specs, et dans le même `src/pages/` ou `src/components/`.
- Route préexistante `/chat` (voir `frontend/src/App.tsx`) → ton composant `Chat` est le handler.

## 📐 Production spec de l'écran
Implémenter dans l'ordre suivant, chacun vérifiable visuellement :

1. **Zone de saisie** : `<textarea>` stylé selon specs (tokens, radius, placeholder « Pose ta question à Dexter… »), bouton d'envoi, état `loading`.
2. **Bulles conversation** : liste des messages, avec **role=user** (alignée droite ou selon specs) et **role=assistant** (alignée gauche). Typographie, padding, radius, couleurs, icônes selon specs.
3. **Modes affichés** : si le backend retourne `mode` dans la réponse (`explique_moi`, `calcul`, `mes_cours`), afficher un indicateur visuel (chip/pill) selon la palette, avec le label lisible (ex. « Explication », « Calcul vérifié », « Mes cours »). Utiliser la traduction utilisateur, pas le code interne.
4. **Clarification** : si `clarification_demandee === true`, affichage du message de clarification + les champs manquants listés (ex. « taux de TVA »). Conformité au comportement PRD §2.1 : rien de calculé inventé.
5. **Calcul vérifié** (lorsque `calcul_result` est présent dans la réponse) : afficher les figures vérifiées remontées (résultat principal + détails issus du calculateur). Format lisible, selon specs, **sans recalculer**.
6. **Historique** : navigation vers `/historique` ou équivalent, si l'UI le prévoit (sidebar + lien).
7. **UX réaliste** : état de chargement pendant l'appel `/chat/message`, gestion des erreurs 502, traitement du `conversation_id` retourné si pertinent pour le bouton ou le titre de la discussion.

## 🔌 Contrat backend (source : `backend/app/routers/chat.py`)
Écouter l'endpoint :
- `POST /chat/message` avec JSON `{ question: string }`.
- Entêtes d'auth : l'utilisateur doit être connecté côté frontend (token stocké). Pour A3, **simuler l'authentifié** si l'appel backend échoue sans token : accepter que l'appel retourne 401/403 et gérer l'état UX en conséquence. Ne pas implémenter l'auth dans A3.
- Réponse type :
  - `reponse` (string | null)
  - `mode` ("explique_moi" | "calcul" | "mes_cours")
  - `domaine`, `sous_theme`, `referentiel`
  - `clarification_demandee` (bool)
  - `champs_manquants` (string[])
  - `calcul_result` (object | null)
  - `conversation_id` (number | null)

Implémentation minimale acceptable pour A3 :
- Un objet state `messages` (initial : peut être vide ou prérempli de 1 exemple pédagogique minimal chez toi, si les specs l'autorisent — sinon vide).
- Fonction `sendQuestion(question)` qui POST le message, ajoute un message utilisateur local, puis ajoute la réponse après réception.
- Affichage des modes + clarification + calcul selon le contrat ci-dessus.
- Pas de gestion de stream, pas de résumé, pas de suivi des conversations multiples — cela vient plus tard.

## 🚫 Ce que A3 ne fait PAS (éviter les dérives)
- Ne pas implémenter la barre d'accueil (c'est A2).
- Ne pas implémenter `GET /domains` dans Chat (c'est A2 + backend).
- Ne pas ajouter de nouvelles polices, icônes, couleurs hors specs.
- Ne pas brancher le bouton Nouvelle discussion sur un flux backend non préparé (comportement UI réaliste acceptable : vide la liste + reset si cohérent avec specs, sinon placeholder).

## ✅ Gating pour validation
Après ton implémentation, lance `npm.cmd run build` (ou `npm run build`) dans `frontend/` et inclus la preuve (0 erreur tsc + vite) dans ton message de fin. Si tu rencontres un problème de build lié à des tokens/absence de fichier, tu le signales avant de t'en sortir.

## 📤 Rédaction de la réponse attendue
Tu me renvoies :
1. Le contenu final de `Chat.tsx` (et tout nouveau composant dans `pages/` ou `components/`).
2. La liste exacte des fichiers créés/modifiés.
3. Le résultat du build (`tsc -b` + `vite build`) avec preuve.
4. Tout point où les specs ne couvrent pas une décision, listé.
