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
