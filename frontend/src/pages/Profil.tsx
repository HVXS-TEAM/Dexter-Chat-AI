import axios from 'axios'
import { useEffect, useState } from 'react'
import { useTheme } from '../theme/ThemeProvider'

interface UserProfile {
  id: number
  email: string
  role: 'etudiant' | 'professeur'
  langue_preferee: string
  filiere: string | null
  annee: string | null
  matieres_enseignees: string[] | null
  etablissement: string | null
  created_at: string
}

interface QuizProgress {
  total_attempts: number
  submitted_attempts: number
  average_score: number | null
}

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function getInitials(email: string): string {
  const localPart = email.split('@')[0] ?? ''
  const letters = localPart.replace(/[^a-zA-ZÀ-ÿ]/g, '').slice(0, 2)
  return (letters || 'D').toUpperCase()
}

function formatDate(value: string): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return 'Date indisponible'
  }

  return new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' }).format(date)
}

function roleLabel(role: UserProfile['role']): string {
  return role === 'professeur' ? 'Professeur' : 'Étudiant'
}

export default function Profil() {
  const { theme, toggleTheme } = useTheme()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [progress, setProgress] = useState<QuizProgress | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isUnauthorized, setIsUnauthorized] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    async function loadProfile() {
      setIsLoading(true)
      setErrorMessage(null)
      setIsUnauthorized(false)

      try {
        const profileResponse = await axios.get<UserProfile>(`${apiUrl}/users/me`)
        if (!isMounted) return
        setProfile(profileResponse.data)

        try {
          const progressResponse = await axios.get<QuizProgress>(`${apiUrl}/users/me/progress`)
          if (isMounted) setProgress(progressResponse.data)
        } catch {
          if (isMounted) setProgress(null)
        }
      } catch (error: unknown) {
        if (!isMounted) return

        if (axios.isAxiosError(error) && (error.response?.status === 401 || error.response?.status === 403)) {
          setIsUnauthorized(true)
        } else {
          setErrorMessage('Impossible de charger votre profil. Vérifiez la connexion au serveur.')
        }
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    void loadProfile()

    return () => {
      isMounted = false
    }
  }, [])

  if (isLoading) {
    return (
      <section className="w-full max-w-[1100px] animate-pulse" aria-labelledby="page-title" aria-busy="true">
        <div className="mb-8 h-10 w-72 rounded-[12px] bg-[var(--surface-secondary)]" />
        <div className="grid gap-6 lg:grid-cols-8">
          <div className="h-72 rounded-[20px] border border-[var(--border-default)] bg-[var(--surface-secondary)] lg:col-span-5" />
          <div className="h-72 rounded-[20px] border border-[var(--border-default)] bg-[var(--surface-secondary)] lg:col-span-3" />
        </div>
      </section>
    )
  }

  if (isUnauthorized) {
    return (
      <section className="w-full max-w-[560px] rounded-[20px] border border-[var(--border-default)] bg-[var(--glass-background)] p-8 text-center backdrop-blur-[var(--glass-blur)]" aria-labelledby="page-title">
        <span className="material-symbols-outlined text-5xl text-[var(--primary)]" aria-hidden="true">person</span>
        <h1 id="page-title" className="mt-4 text-[32px] font-semibold leading-10 text-[var(--text-primary)]">Connectez-vous pour voir votre profil</h1>
        <p className="mt-3 text-base leading-6 text-[var(--text-secondary)]">Votre profil et votre progression apparaîtront après connexion.</p>
        <button className="mt-6 rounded-[12px] bg-[var(--primary-container)] px-6 py-3 text-sm font-medium leading-5 text-white hover:brightness-110" type="button">Se connecter</button>
      </section>
    )
  }

  if (!profile || errorMessage) {
    return (
      <section className="w-full max-w-[560px] rounded-[20px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-8 text-center" aria-labelledby="page-title">
        <h1 id="page-title" className="text-2xl font-semibold leading-8 text-[var(--text-primary)]">Profil & paramètres</h1>
        <p className="mt-3 text-base leading-6 text-[var(--text-secondary)]">{errorMessage ?? 'Profil indisponible.'}</p>
      </section>
    )
  }

  const metrics = [
    { icon: 'quiz', value: progress ? String(progress.total_attempts) : 'Bientôt disponible', label: 'Questions posées' },
    { icon: 'workspace_premium', value: progress?.average_score !== null && progress ? `${progress.average_score ?? 'Bientôt disponible'}%` : 'Bientôt disponible', label: 'Score moyen' },
    { icon: 'menu_book', value: progress ? String(progress.submitted_attempts) : 'Bientôt disponible', label: 'Quiz complétés' },
  ]

  return (
    <section className="w-full max-w-[1100px] pb-12 text-[var(--text-primary)]" aria-labelledby="page-title">
      <header className="mb-8">
        <p className="text-sm font-semibold uppercase leading-5 tracking-[0.05em] text-[var(--text-secondary)]">Espace personnel</p>
        <h1 id="page-title" className="mt-2 text-[32px] font-semibold leading-10 tracking-[-0.01em]">Profil & paramètres</h1>
      </header>

      <div className="grid gap-6 lg:grid-cols-8">
        <div className="lg:col-span-5">
          <div className="rounded-[20px] border border-[var(--border-default)] bg-[var(--glass-background)] p-6 backdrop-blur-[var(--glass-blur)] md:p-8">
            <div className="flex flex-col items-center gap-6 text-center md:flex-row md:text-left">
              <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-full bg-[var(--primary-container)] text-2xl font-semibold text-white" aria-label={`Avatar de ${profile.email}`}>
                {getInitials(profile.email)}
              </div>
              <div className="min-w-0 flex-1">
                <h2 className="truncate text-2xl font-semibold leading-8 text-[var(--text-primary)]">{profile.email}</h2>
                <div className="mt-3 flex flex-wrap justify-center gap-2 md:justify-start">
                  <span className="inline-flex items-center gap-1 rounded-full border border-[var(--border-default)] bg-[var(--surface-container)] px-3 py-1 text-xs font-semibold leading-4 text-[var(--primary)]"><span className="material-symbols-outlined text-[14px]" aria-hidden="true">person</span>{roleLabel(profile.role)}</span>
                  {profile.filiere && <span className="rounded-full border border-[var(--border-default)] bg-[var(--surface-container)] px-3 py-1 text-xs font-semibold leading-4 text-[var(--text-secondary)]">{profile.filiere}</span>}
                </div>
                <p className="mt-4 text-sm leading-5 text-[var(--text-secondary)]">Membre depuis le {formatDate(profile.created_at)}</p>
              </div>
            </div>
          </div>

          <h2 className="mt-8 text-xs font-semibold uppercase leading-4 tracking-[0.05em] text-[var(--text-secondary)]">Statistiques d&apos;apprentissage</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            {metrics.map((metric) => (
              <div className="rounded-[18px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-5" key={metric.label}>
                <span className="flex h-10 w-10 items-center justify-center rounded-[12px] bg-[var(--surface-container)] text-[var(--primary)]"><span className="material-symbols-outlined" aria-hidden="true">{metric.icon}</span></span>
                <p className="mt-4 min-h-10 text-xl font-semibold leading-8 text-[var(--text-primary)]">{metric.value}</p>
                <p className="mt-1 text-xs font-semibold leading-4 text-[var(--text-secondary)]">{metric.label}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-6 lg:col-span-3">
          <div className="rounded-[20px] bg-[var(--accent-gradient)] p-1">
            <div className="flex h-full flex-col rounded-[18px] bg-[var(--surface)] p-6">
              <div className="flex items-center gap-2"><span className="material-symbols-outlined text-[var(--primary)]" aria-hidden="true">workspace_premium</span><h2 className="text-2xl font-semibold leading-8">Dexter Pro</h2></div>
              <p className="mt-4 flex-1 text-base leading-6 text-[var(--text-secondary)]">Accédez à des explications illimitées, des résumés avancés et une assistance prioritaire.</p>
              <button className="mt-6 w-full rounded-[12px] bg-[var(--primary-container)] px-4 py-3 text-sm font-medium leading-5 text-white hover:brightness-110" type="button">S&apos;abonner — 9,99€/mois</button>
            </div>
          </div>

          <div className="rounded-[20px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-2">
            <div className="flex items-center justify-between rounded-[12px] p-4">
              <div className="flex items-center gap-3"><span className="flex h-8 w-8 items-center justify-center rounded-[12px] bg-[var(--surface-container)] text-[var(--text-secondary)]"><span className="material-symbols-outlined text-[20px]" aria-hidden="true">notifications</span></span><span className="text-sm font-medium leading-5">Notifications</span></div>
              <span className="material-symbols-outlined text-[var(--text-secondary)]" aria-hidden="true">chevron_right</span>
            </div>
            <div className="flex items-center justify-between rounded-[12px] p-4">
              <div className="flex items-center gap-3"><span className="flex h-8 w-8 items-center justify-center rounded-[12px] bg-[var(--surface-container)] text-[var(--text-secondary)]"><span className="material-symbols-outlined text-[20px]" aria-hidden="true">help</span></span><span className="text-sm font-medium leading-5">Aide &amp; Support</span></div>
              <span className="material-symbols-outlined text-[var(--text-secondary)]" aria-hidden="true">chevron_right</span>
            </div>
            <div className="flex items-center justify-between rounded-[12px] p-4">
              <div className="flex items-center gap-3"><span className="flex h-8 w-8 items-center justify-center rounded-[12px] bg-[var(--surface-container)] text-[var(--text-secondary)]"><span className="material-symbols-outlined text-[20px]" aria-hidden="true">dark_mode</span></span><span className="text-sm font-medium leading-5">Apparence</span></div>
              <button className={`relative h-6 w-10 rounded-full ${theme === 'dark' ? 'bg-[var(--primary-container)]' : 'bg-[var(--surface-container)]'}`} type="button" role="switch" aria-checked={theme === 'dark'} aria-label="Basculer le thème" onClick={toggleTheme}><span className={`absolute top-1 h-4 w-4 rounded-full bg-white shadow-sm transition-transform ${theme === 'dark' ? 'translate-x-5' : 'translate-x-1'}`} /></button>
            </div>
          </div>

          <button className="flex w-full items-center justify-center gap-2 rounded-[12px] border border-[var(--error)]/20 bg-[var(--error)]/5 p-4 text-sm font-medium leading-5 text-[var(--error)] hover:bg-[var(--error)]/10" type="button"><span className="material-symbols-outlined text-[20px]" aria-hidden="true">logout</span>Déconnexion</button>
        </div>
      </div>
    </section>
  )
}
