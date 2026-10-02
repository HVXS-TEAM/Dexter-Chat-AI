import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'
import { isGuestMode } from './guestMode'

interface ProtectedRouteProps {
  children: ReactNode
  /** Autorise l'acces a un visiteur ayant choisi « Essayer sans connexion ». */
  allowGuest?: boolean
  /** Destination d'un visiteur refuse (par defaut : la page de connexion). */
  redirectTo?: string
}

export default function ProtectedRoute({
  children,
  allowGuest = false,
  redirectTo = '/login',
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center" style={{ background: 'var(--background)' }}>
        <div className="h-8 w-8 animate-spin rounded-full border-2" style={{ borderColor: 'var(--border-default)', borderTopColor: 'var(--primary)' }} />
      </div>
    )
  }

  if (!isAuthenticated && !(allowGuest && isGuestMode())) {
    return <Navigate to={redirectTo} state={{ from: location.pathname }} replace />
  }

  return <>{children}</>
}
