import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import axios from 'axios'
import { login as loginApi, refreshToken as refreshTokenApi, register as registerApi } from './api'
import type { LoginPayload, RegisterPayload, TokenPair, User } from './types'

interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (payload: LoginPayload) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => void
  getAccessToken: () => string | null
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const ACCESS_TOKEN_KEY = 'dexter-access-token'
const REFRESH_TOKEN_KEY = 'dexter-refresh-token'
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function getStoredTokens(): TokenPair | null {
  const access = localStorage.getItem(ACCESS_TOKEN_KEY)
  const refresh = localStorage.getItem(REFRESH_TOKEN_KEY)
  if (!access || !refresh) return null
  return { access_token: access, refresh_token: refresh, token_type: 'bearer' }
}

function storeTokens(tokens: TokenPair): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token)
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
}

function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const refreshPromise = useRef<Promise<TokenPair> | null>(null)

  const getAccessToken = useCallback((): string | null => {
    return localStorage.getItem(ACCESS_TOKEN_KEY)
  }, [])

  const logout = useCallback((): void => {
    clearTokens()
    setUser(null)
    delete axios.defaults.headers.common.Authorization
  }, [])

  const fetchCurrentUser = useCallback(async (token: string): Promise<void> => {
    const { data } = await axios.get<User>(`${API_URL}/users/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    setUser(data)
  }, [])

  const silentRefresh = useCallback(async (): Promise<TokenPair | null> => {
    const stored = getStoredTokens()
    if (!stored) return null

    if (refreshPromise.current) {
      return refreshPromise.current
    }

    refreshPromise.current = refreshTokenApi(stored.refresh_token)
      .then((tokens) => {
        storeTokens(tokens)
        axios.defaults.headers.common.Authorization = `Bearer ${tokens.access_token}`
        return tokens
      })
      .catch(() => {
        clearTokens()
        return null
      })
      .finally(() => {
        refreshPromise.current = null
      })

    return refreshPromise.current
  }, [])

  useEffect(() => {
    let isMounted = true

    async function initialize(): Promise<void> {
      const tokens = getStoredTokens()
      if (!tokens) {
        if (isMounted) setIsLoading(false)
        return
      }

      axios.defaults.headers.common.Authorization = `Bearer ${tokens.access_token}`

      try {
        await fetchCurrentUser(tokens.access_token)
      } catch {
        const newTokens = await silentRefresh()
        if (newTokens && isMounted) {
          try {
            await fetchCurrentUser(newTokens.access_token)
          } catch {
            logout()
          }
        } else if (isMounted) {
          logout()
        }
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    void initialize()

    return () => {
      isMounted = false
    }
  }, [fetchCurrentUser, silentRefresh, logout])

  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config as { _retry?: boolean }

        if (
          axios.isAxiosError(error) &&
          error.response?.status === 401 &&
          !originalRequest._retry
        ) {
          originalRequest._retry = true

          const newTokens = await silentRefresh()
          if (newTokens) {
            originalRequest.headers = {
              ...originalRequest.headers,
              Authorization: `Bearer ${newTokens.access_token}`,
            }
            return axios(originalRequest)
          } else {
            logout()
          }
        }

        return Promise.reject(error)
      }
    )

    return () => {
      axios.interceptors.response.eject(interceptor)
    }
  }, [silentRefresh, logout])

  const login = useCallback(
    async (payload: LoginPayload): Promise<void> => {
      const tokens = await loginApi(payload)
      storeTokens(tokens)
      axios.defaults.headers.common.Authorization = `Bearer ${tokens.access_token}`
      await fetchCurrentUser(tokens.access_token)
    },
    [fetchCurrentUser]
  )

  const register = useCallback(
    async (payload: RegisterPayload): Promise<void> => {
      await registerApi(payload)
      await login({ email: payload.email, password: payload.password })
    },
    [login]
  )

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      register,
      logout,
      getAccessToken,
    }),
    [user, isLoading, login, register, logout, getAccessToken]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return context
}
