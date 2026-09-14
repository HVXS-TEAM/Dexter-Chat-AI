export type UserRole = 'etudiant' | 'professeur'

export interface User {
  id: number
  email: string
  role: UserRole
  langue_preferee: string
  filiere: string | null
  annee: string | null
  matieres_enseignees: string[] | null
  etablissement: string | null
  created_at: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}

export interface RegisterPayload {
  email: string
  password: string
  role?: UserRole
  langue_preferee?: string
  filiere?: string
  annee?: string
  matieres_enseignees?: string[]
  etablissement?: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface AuthError {
  message: string
  status?: number
}
