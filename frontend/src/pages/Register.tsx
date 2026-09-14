import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function Register() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [role, setRole] = useState<'etudiant' | 'professeur'>('etudiant')
  const [filiere, setFiliere] = useState('')
  const [annee, setAnnee] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const { register: registerUser } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (password.length < 8) {
      setError('Le mot de passe doit contenir au moins 8 caractères.')
      return
    }
    if (password !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas.')
      return
    }
    setIsLoading(true)
    try {
      await registerUser({ email, password, role, filiere: filiere || undefined, annee: annee || undefined })
      navigate('/', { replace: true })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erreur lors de l'inscription")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4" style={{ background: 'var(--background)' }}>
      <form onSubmit={handleSubmit} className="w-full max-w-md space-y-5 rounded-[18px] p-8"
        style={{ background: 'var(--surface)', border: '1px solid var(--border-default)' }}>
        <div className="space-y-2 text-center">
          <h1 className="text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>Inscription</h1>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Crée ton compte pour accéder à Dexter</p>
        </div>
        {error && (
          <div role="alert" className="rounded-[12px] p-3 text-sm" style={{ background: 'var(--error, #ef4444)', color: '#fff' }}>
            {error}
          </div>
        )}
        <div className="space-y-4">
          <div>
            <label htmlFor="reg-email" className="mb-1 block text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Email</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined" style={{ color: 'var(--text-secondary)', fontSize: '20px' }}>mail</span>
              <input id="reg-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                autoComplete="email" aria-label="Adresse email"
                className="w-full rounded-[12px] py-3 pl-10 pr-4 text-sm outline-none transition-all"
                style={{ background: 'var(--surface-secondary)', border: '1px solid var(--border-default)', color: 'var(--text-primary)' }}
                onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--primary)' }}
                onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--border-default)' }} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="reg-role" className="mb-1 block text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Rôle</label>
              <select id="reg-role" value={role} onChange={(e) => setRole(e.target.value as 'etudiant' | 'professeur')}
                aria-label="Rôle" className="w-full rounded-[12px] px-3 py-3 text-sm outline-none transition-all"
                style={{ background: 'var(--surface-secondary)', border: '1px solid var(--border-default)', color: 'var(--text-primary)' }}>
                <option value="etudiant">Étudiant</option>
                <option value="professeur">Professeur</option>
              </select>
            </div>
            <div>
              <label htmlFor="reg-annee" className="mb-1 block text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Année</label>
              <input id="reg-annee" type="text" value={annee} onChange={(e) => setAnnee(e.target.value)}
                placeholder="L1, L2, M1…" aria-label="Année d'étude"
                className="w-full rounded-[12px] px-3 py-3 text-sm outline-none transition-all"
                style={{ background: 'var(--surface-secondary)', border: '1px solid var(--border-default)', color: 'var(--text-primary)' }}
                onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--primary)' }}
                onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--border-default)' }} />
            </div>
          </div>
          <div>
            <label htmlFor="reg-filiere" className="mb-1 block text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Filière</label>
            <input id="reg-filiere" type="text" value={filiere} onChange={(e) => setFiliere(e.target.value)}
              placeholder="Comptabilité, Finance…" aria-label="Filière"
              className="w-full rounded-[12px] px-3 py-3 text-sm outline-none transition-all"
              style={{ background: 'var(--surface-secondary)', border: '1px solid var(--border-default)', color: 'var(--text-primary)' }}
              onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--primary)' }}
              onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--border-default)' }} />
          </div>
          <div>
            <label htmlFor="reg-password" className="mb-1 block text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Mot de passe</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined" style={{ color: 'var(--text-secondary)', fontSize: '20px' }}>lock</span>
              <input id="reg-password" type={showPassword ? 'text' : 'password'} required value={password}
                onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" aria-label="Mot de passe"
                className="w-full rounded-[12px] py-3 pl-10 pr-10 text-sm outline-none transition-all"
                style={{ background: 'var(--surface-secondary)', border: '1px solid var(--border-default)', color: 'var(--text-primary)' }}
                onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--primary)' }}
                onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--border-default)' }} />
              <button type="button" onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                className="absolute right-3 top-1/2 -translate-y-1/2 material-symbols-outlined"
                style={{ color: 'var(--text-secondary)', fontSize: '20px', background: 'none', border: 'none', cursor: 'pointer' }}>
                {showPassword ? 'visibility_off' : 'visibility'}
              </button>
            </div>
          </div>
          <div>
            <label htmlFor="reg-confirm" className="mb-1 block text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Confirmer le mot de passe</label>
            <input id="reg-confirm" type={showPassword ? 'text' : 'password'} required value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)} autoComplete="new-password" aria-label="Confirmation du mot de passe"
              className="w-full rounded-[12px] py-3 px-4 text-sm outline-none transition-all"
              style={{ background: 'var(--surface-secondary)', border: '1px solid var(--border-default)', color: 'var(--text-primary)' }}
              onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--primary)' }}
              onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--border-default)' }} />
          </div>
        </div>
        <button type="submit" disabled={isLoading}
          className="w-full rounded-[12px] py-3 text-sm font-semibold text-white transition-all hover:opacity-90 disabled:opacity-50"
          style={{ background: 'var(--primary-container)' }}>
          {isLoading ? 'Inscription...' : "S'inscrire"}
        </button>
        <p className="text-center text-sm" style={{ color: 'var(--text-secondary)' }}>
          Déjà un compte ?{' '}
          <Link to="/login" className="font-medium hover:underline" style={{ color: 'var(--primary)' }}>Se connecter</Link>
        </p>
      </form>
    </div>
  )
}