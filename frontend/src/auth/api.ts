import axios from 'axios'
import type { LoginPayload, RegisterPayload, TokenPair, User } from './types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const authApi = axios.create({
  baseURL: `${API_URL}/auth`,
  headers: { 'Content-Type': 'application/json' },
})

export async function register(payload: RegisterPayload): Promise<User> {
  const { data } = await authApi.post<User>('/register', payload)
  return data
}

export async function login(payload: LoginPayload): Promise<TokenPair> {
  const { data } = await authApi.post<TokenPair>('/login', payload)
  return data
}

export async function refreshToken(refreshToken: string): Promise<TokenPair> {
  const { data } = await authApi.post<TokenPair>('/refresh', {
    refresh_token: refreshToken,
  })
  return data
}
