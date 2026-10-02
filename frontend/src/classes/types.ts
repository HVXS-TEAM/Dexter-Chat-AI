export interface ClassRead {
  id: number
  nom: string
  professeur_id: number
  code_invitation: string
  created_at: string
}

export interface ClassReadStudent {
  id: number
  nom: string
  professeur_id: number
  created_at: string
}

export type ClassJoinResponse = ClassReadStudent

export interface ClassCreatePayload {
  nom: string
}

export interface ClassJoinPayload {
  code_invitation: string
}
