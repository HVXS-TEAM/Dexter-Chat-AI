const GUEST_MODE_KEY = 'dexter-guest'

/**
 * Indique si le visiteur a choisi « Essayer sans connexion » pour cette session.
 * Le mode invité reste limité à la session du navigateur (sessionStorage).
 */
export function isGuestMode(): boolean {
  return sessionStorage.getItem(GUEST_MODE_KEY) === '1'
}

/** Active l'essai sans connexion pour la session en cours. */
export function enableGuestMode(): void {
  sessionStorage.setItem(GUEST_MODE_KEY, '1')
}

/** Quitte l'essai sans connexion (appelé dès qu'une connexion réussit). */
export function disableGuestMode(): void {
  sessionStorage.removeItem(GUEST_MODE_KEY)
}
