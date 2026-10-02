/**
 * Formules d'accueil de l'ecran Accueil (`pages/Accueil.tsx`).
 *
 * - Visiteur en essai gratuit : une seule formule, celle validee par l'utilisateur.
 * - Compte connecte : formule tiree parmi plusieurs variantes, avec le prenom
 *   deduit de l'email (aucun champ « prenom » n'existe en base, cf. PROGRESS.md).
 */

/** Salutation affichee pour l'essai sans connexion (texte valide par l'utilisateur). */
export const GUEST_GREETING = "En quoi puis-je aider aujourd'hui ?"

/** Sous-titre de la maquette `cran_d_accueil_clair_dexter_2` (compte connecte uniquement). */
export const ACCOUNT_SUBTITLE = "Que souhaites-tu étudier aujourd'hui ?"

/** Prefixes d'email qui ne sont pas des prenoms : on utilise alors une formule de repli. */
const NON_NAME_EMAIL_PREFIXES = [
  'contact',
  'info',
  'admin',
  'support',
  'hello',
  'bonjour',
  'etudiant',
  'student',
  'prof',
  'professeur',
  'user',
  'dexter',
]

/** Formules utilisees quand un prenom est disponible (`{prenom}` est remplace). */
const GREETINGS_WITH_NAME = [
  'Bonjour {prenom} 👋',
  'Ravi de te revoir, {prenom}',
  'Salut {prenom}, on continue ?',
  'Content de te revoir, {prenom}',
  'Bonjour {prenom}, prêt à apprendre ?',
  'Rebonjour {prenom} !',
  '{prenom}, prêt pour une nouvelle session ?',
  'Que veux-tu apprendre aujourd\'hui, {prenom} ?',
]

/** Formules de repli quand aucun prenom n'est exploitable. */
const GREETINGS_WITHOUT_NAME = [
  'Bonjour 👋',
  'Ravi de te revoir',
  'Content de te revoir',
  'Prêt à apprendre ?',
  'Que veux-tu apprendre aujourd\'hui ?',
]

/**
 * Prefixe commun aux deux variantes de la formule « Que veux-tu apprendre
 * aujourd'hui » (avec et sans prenom). Sert a detecter la redondance avec le
 * sous-titre de la maquette (« Que souhaites-tu étudier aujourd'hui ? ») :
 * quand la formule tiree est celle-ci, le sous-titre est masque.
 */
export const LEARNING_QUESTION_PREFIX = 'Que veux-tu apprendre aujourd\'hui'

/**
 * Deduit un prenom depuis l'email : `edwin.kouokam@exemple.com` -> « Edwin ».
 * Retourne `null` quand la partie locale n'est pas exploitable (prefixe generique,
 * trop courte, ou composee uniquement de chiffres et de symboles).
 */
export function extractFirstName(email: string | null | undefined): string | null {
  if (!email) {
    return null
  }

  const localPart = email.split('@')[0] ?? ''
  const firstSegment = localPart.split(/[._+-]/)[0] ?? ''
  const lettersOnly = firstSegment.replace(/[^A-Za-zÀ-ÖØ-öø-ÿ]/g, '')

  if (lettersOnly.length < 2 || NON_NAME_EMAIL_PREFIXES.includes(lettersOnly.toLowerCase())) {
    return null
  }

  return lettersOnly.charAt(0).toUpperCase() + lettersOnly.slice(1).toLowerCase()
}

/**
 * Tire une formule d'accueil pour un compte connecte.
 * Le tirage est fait a l'ouverture de l'ecran : deux visites successives peuvent
 * donc afficher deux formules differentes.
 */
export function pickAccountGreeting(firstName: string | null, random: () => number = Math.random): string {
  const pool = firstName ? GREETINGS_WITH_NAME : GREETINGS_WITHOUT_NAME
  const template = pool[Math.floor(random() * pool.length)]

  return firstName ? template.replace('{prenom}', firstName) : template
}

/** Cle de stockage de la formule fige par onglet (stable pendant la session). */
const SESSION_GREETING_KEY = 'dexter:accueil-greeting'

/**
 * Formule d'accueil stable pendant la session de l'onglet : tiree au hasard a
 * la premiere ouverture, puis reutilisee telle quelle jusqu'a fermeture de
 * l'onglet (via `sessionStorage`). En cas de stockage indisponible, repli sur
 * un tirage simple. La cle inclut l'email pour eviter de resservir la formule
 * d'un compte precedent apres un changement d'utilisateur dans le meme onglet.
 */
export function pickStableAccountGreeting(
  firstName: string | null,
  email: string | null | undefined,
  random: () => number = Math.random,
): string {
  try {
    const storageKey = `${SESSION_GREETING_KEY}:${(email ?? '').toLowerCase()}`
    const stored = sessionStorage.getItem(storageKey)
    const pool = firstName ? GREETINGS_WITH_NAME : GREETINGS_WITHOUT_NAME

    if (stored && pool.some((template) => stored === (firstName ? template.replace('{prenom}', firstName) : template))) {
      return stored
    }

    const greeting = pickAccountGreeting(firstName, random)
    sessionStorage.setItem(storageKey, greeting)

    return greeting
  } catch {
    return pickAccountGreeting(firstName, random)
  }
}

/**
 * Indique si la formule tiree est la question « Que veux-tu apprendre
 * aujourd'hui… », redondante avec le sous-titre de la maquette : dans ce cas
 * le sous-titre est masque pour eviter la repetition.
 */
export function isLearningQuestion(greeting: string): boolean {
  return greeting.startsWith(LEARNING_QUESTION_PREFIX)
}
