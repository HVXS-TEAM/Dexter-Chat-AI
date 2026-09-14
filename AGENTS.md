---
description: 'Règles de discipline de travail — sûreté, validation, méthode'
applyTo: '**'
---

# Règles de discipline de travail

## Règles fondamentales (non négociables)

1. **Aucune génération sans autorisation explicite.** Ne crée, ne modifie et
   ne supprime aucun fichier sans que je te l'aie explicitement demandé pour
   cette action précise. Une demande générale ("avance sur le projet") n'est
   pas une autorisation à agir — présente d'abord ce que tu comptes faire et
   attends ma validation.

2. **La sûreté prime sur la vitesse.** Si un bug est identifié, il doit être
   entièrement corrigé et vérifié avant de passer à autre chose — jamais de
   contournement temporaire pour "avancer quand même" pendant qu'un bug
   connu reste ouvert, sauf si je le demande explicitement et en connaissance
   de cause.

3. **Aucune interface générique.** N'invente jamais un composant, une mise en
   page ou un style visuel de toi-même. Utilise exclusivement les modèles
   graphiques (maquettes, écrans, identité visuelle) fournis dans le dossier
   `documentation/` du projet actuellement ouvert. Cette règle s'applique à
   **tous les projets que j'ouvrirai à partir de maintenant**, jusqu'à
   nouvel ordre de ma part — pas seulement au projet en cours. Si un écran
   ou un élément dont j'ai besoin n'est couvert par aucune maquette fournie,
   arrête-toi et demande-moi plutôt que d'en concevoir un par toi-même.

4. **Travail modulaire et méthodique.** Chaque étape doit être vérifiée à la
   lettre avant de passer à la suivante. Avant toute action, produis une
   courte "note d'intention" écrite qui résume : ce qu'on doit faire, ce que
   tu t'apprêtes à faire concrètement, et ce que ça va changer. Cette note
   doit exister et m'être présentée avant l'action, jamais après.

## Règles complémentaires dans le même esprit

5. **Une seule chose à la fois.** Ne regroupe jamais plusieurs changements
   non liés dans une même action. Un module, une fonctionnalité ou un bug à
   la fois — chacun validé avant d'entamer le suivant.

6. **Jamais d'erreur masquée.** N'utilise jamais un `except` silencieux ou
   un `pass` qui avale une exception sans la signaler. Toute erreur doit
   être visible, explicite et accompagnée du contexte qui permet de la
   comprendre.

7. **Aucun bricolage déguisé en solution définitive.** Si un correctif
   temporaire ou une solution de contournement est malgré tout nécessaire,
   signale-le explicitement comme temporaire, explique pourquoi, et précise
   ce qu'il faudrait faire à la place plus tard.

8. **Pas de modification hors du périmètre demandé.** Ne touche à aucun
   fichier, fonction ou style en dehors du périmètre exact de la tâche en
   cours, même si tu identifies une amélioration possible ailleurs —
   signale-la plutôt que de la corriger de ta propre initiative.

9. **Traçabilité écrite continue.** Tiens à jour un fichier de suivi (par
   exemple `PROGRESS.md` à la racine du projet) recensant, à chaque étape :
   ce qui a été fait, ce qui est en cours, ce qui reste à faire. Ce fichier
   doit toujours refléter l'état réel du projet, pas un état théorique.

10. **Aucune nouvelle dépendance sans validation.** N'ajoute jamais une
    librairie, un outil ou un changement de structure de projet non prévu
    sans me le proposer et attendre mon accord au préalable.

11. **Rien n'est "terminé" sans ma confirmation explicite.** Ne déclare
    jamais une tâche achevée de ta propre initiative — présente le résultat,
    ce qui a été vérifié, et attends ma validation avant de considérer
    l'étape close.

12. **Clarté avant élégance.** Privilégie systématiquement un code explicite
    et facile à relire plutôt qu'une solution compacte ou "astucieuse" —
    même si elle est plus courte, si elle est plus difficile à vérifier
    ligne par ligne, ce n'est pas le bon choix ici.

13. **Options avant décision.** Si plusieurs approches d'implémentation sont
    possibles pour une même étape, présente-les avec leurs compromis
    respectifs avant de choisir — ne tranche jamais seul une décision qui
    aurait pu se faire autrement.

14. **Analyse et installation des dépendances avant tout code.** Avant
    d'écrire la moindre ligne de code pour une étape ou un module donné,
    analyse l'ensemble des dépendances dont ce module aura besoin pour
    fonctionner, liste-les explicitement, puis installe-les toutes avant de
    commencer à coder — jamais d'installation au fil de l'eau pendant
    l'écriture du code. Cette analyse et cette liste de dépendances font
    partie de la "note d'intention" prévue par la règle 4, et restent
    soumises à la règle 10 : si une dépendance non encore prévue apparaît
    nécessaire en cours de route, arrête-toi et fais valider son ajout avant
    de l'installer.

## Protocole de collaboration Copilot ↔ agent d'analyse (toutes sessions)

Ce protocole s'applique à **toutes les sessions de ce projet** et définit le
flux de travail quand le code est produit par Copilot dans VS Code puis
analysé et corrigé par un agent d'analyse (DeepSeek Harness) :

1. **Copilot produit, l'agent analyse.** Copilot génère le code dans VS Code
   et le sauvegarde sur disque. L'agent ne voit que les fichiers sauvegardés —
   jamais l'écran de l'éditeur, ni les modifications non enregistrées. Si un
   fichier n'est pas sauvegardé, l'agent ne peut pas l'analyser : demander la
   sauvegarde avant de commencer.

2. **Analyse contre les documents.** Toute analyse compare le code produit
   aux documents de référence du projet (PRD, cahier des charges,
   instructions du projet, présent fichier) et signale explicitement chaque
   écart constaté — y compris les incohérences entre ces documents eux-mêmes.

3. **Rapport structuré avant toute correction.** L'agent remet un rapport :
   ✅ ce qui est conforme / ⚠️ ce qui est douteux / ❌ les bugs avec
   correctif proposé et justification. Aucun correctif n'est appliqué sans
   validation explicite de l'utilisateur (règle 1).

4. **Vérification réelle.** Après application d'un correctif, l'agent exécute
   les vérifications disponibles (build, tests, lint, commandes du projet)
   avant de déclarer quoi que ce soit corrigé — jamais de "ça devrait
   marcher" sans preuve.

5. **Une étape à la fois.** Chaque étape est analysée, corrigée et validée
   avant de passer à la suivante (règle 5). Le périmètre de chaque étape est
   celui que l'utilisateur a défini, rien de plus (règle 8).

6. **Traçabilité.** Chaque cycle (analyse → correctifs appliqués →
   vérifications) est consigné dans le fichier de suivi du projet (règle 9),
   qui reflète l'état réel à tout moment.