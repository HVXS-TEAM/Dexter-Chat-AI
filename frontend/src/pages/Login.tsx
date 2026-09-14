import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

interface LocationState {
  from?: string
}

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as LocationState)?.from || '/'

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      await login({ email, password })
      navigate(from, { replace: true })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Erreur de connexion'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4" style={{ background: 'var(--background)' }}>
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md space-y-6 rounded-[18px] p-8"
        style={{ background: 'var(--surface)', border: '1px solid var(--border-default)' }}
      >
        <div className="space-y-2 text-center">
          <h1 className="text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>
            Connexion
          </h1>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            Pose tes questions à Dexter
          </p>
        </div>

        {error && (
          <div role="alert" className="rounded-[12px] p-3 text-sm" style={{ background: 'var(--error, #ef4444)', color: '#fff' }}>
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label htmlFor="login-email" className="mb-1 block text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
              Email
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined" style={{ color: 'var(--text-secondary)', fontSize: '20px' }}>
                mail
              </span>
              <input
                id="login-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                aria-label="Adresse email"
                className="w-full rounded-[12px] py-3 pl-10 pr-4 text-sm outline-none transition-all"
                style={{
                  background: 'var(--surface-secondary)',
                  border: '1px solid var(--border-default)',
                  color: 'var(--text-primary)',
                }}
                onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--primary)' }}
                onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--border-default)' }}
              />
            </div>
          </div>

          <div>
            <label htmlFor="login-password" className="mb-1 block text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
              Mot de passe
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined" style={{ color: 'var(--text-secondary)', fontSize: '20px' }}>
                lock
              </span>
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                aria-label="Mot de passe"
                className="w-full rounded-[12px] py-3 pl-10 pr-10 text-sm outline-none transition-all"
                style={{
                  background: 'var(--surface-secondary)',
                  border: '1px solid var(--border-default)',
                  color: 'var(--text-primary)',
                }}
                onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--primary)' }}
                onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--border-default)' }}
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                className="absolute right-3 top-1/2 -translate-y-1/2 material-symbols-outlined"
                style={{ color: 'var(--text-secondary)', fontSize: '20px', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                {showPassword ? 'visibility_off' : 'visibility'}
              </button>
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full rounded-[12px] py-3 text-sm font-semibold text-white transition-all hover:opacity-90 disabled:opacity-50"
          style={{ background: 'var(--primary-container)' }}
        >
          {isLoading ? 'Connexion...' : 'Se connecter'}
        </button>

        <p className="text-center text-sm" style={{ color: 'var(--text-secondary)' }}>
          Pas encore de compte ?{' '}
          <Link to="/register" className="font-medium hover:underline" style={{ color: 'var(--primary)' }}>
            S'inscrire
          </Link>
        </p>
      </form>
    </div>
  )
}
