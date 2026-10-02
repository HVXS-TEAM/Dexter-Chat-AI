import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { useAuth } from '../auth'
import { createClass, joinClassByCode, listClasses } from '../classes/api'
import type { ClassRead, ClassReadStudent } from '../classes/types'

function formatDate(value: string): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return 'Date indisponible'
  }

  return new Intl.DateTimeFormat('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(date)
}

type ClassListItem = ClassRead | ClassReadStudent

export default function Classes() {
  const { user } = useAuth()
  const userRole = user?.role
  const [classes, setClasses] = useState<ClassListItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [joinCode, setJoinCode] = useState('')
  const [className, setClassName] = useState('')
  const [joinSuccessMessage, setJoinSuccessMessage] = useState<string | null>(null)
  const [createSuccessMessage, setCreateSuccessMessage] = useState<string | null>(null)

  const loadClasses = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage(null)

    try {
      const response = await listClasses()
      setClasses(response)
    } catch (error: unknown) {
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string } } }
        setErrorMessage(axiosError.response?.data?.detail ?? 'Impossible de charger les classes. Vérifiez la connexion au serveur.')
      } else {
        setErrorMessage('Impossible de charger les classes. Vérifiez la connexion au serveur.')
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadClasses()
  }, [loadClasses])

  const isStudent = userRole === 'etudiant'
  const isProfessor = userRole === 'professeur'

  const classCountLabel = useMemo(() => `${classes.length} ${classes.length <= 1 ? 'classe active' : 'classes actives'}`, [classes.length])

  async function handleJoinClass(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const trimmedCode = joinCode.trim().toUpperCase()
    if (!trimmedCode || !user || isProfessor) {
      return
    }

    setIsSubmitting(true)
    setJoinSuccessMessage(null)
    setErrorMessage(null)

    try {
      const joined = await joinClassByCode({ code_invitation: trimmedCode })
      setJoinSuccessMessage(`Classe « ${joined.nom} » rejointe.`)
      setJoinCode('')
      await loadClasses()
    } catch (error: unknown) {
      const axiosError = error as { response?: { data?: { detail?: string } } }
      const detail = axiosError.response?.data?.detail ?? 'Impossible de rejoindre la classe.'
      setErrorMessage(detail)
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleCreateClass(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmedName = className.trim()

    if (!trimmedName || !isProfessor) {
      return
    }

    setIsSubmitting(true)
    setCreateSuccessMessage(null)
    setErrorMessage(null)

    try {
      const created = await createClass({ nom: trimmedName })
      setClassName('')
      setCreateSuccessMessage(`Classe « ${created.nom} » créée.`)
      await loadClasses()
    } catch (error: unknown) {
      const axiosError = error as { response?: { data?: { detail?: string } } }
      const detail = axiosError.response?.data?.detail ?? 'Impossible de créer la classe.'
      setErrorMessage(detail)
    } finally {
      setIsSubmitting(false)
    }
  }

  async function copyInvitation(code: string) {
    if (!code) {
      return
    }

    try {
      await navigator.clipboard.writeText(code)
    } catch {
      setErrorMessage('Impossible de copier le code d’invitation.')
    }
  }

  if (isLoading) {
    return (
      <section className="w-full max-w-[1100px] animate-pulse" aria-labelledby="page-title" aria-busy="true">
        <div className="mb-6 h-10 w-52 rounded-[12px] bg-[var(--surface-secondary)]" />
        <div className="mb-8 h-6 w-80 rounded-[12px] bg-[var(--surface-secondary)]" />
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }, (_, index) => (
            <div className="h-64 rounded-[20px] border border-[var(--border-default)] bg-[var(--surface-secondary)]" key={index} />
          ))}
        </div>
      </section>
    )
  }

  return (
    <section className="w-full max-w-[1100px] pb-12 text-[var(--text-primary)]" aria-labelledby="page-title">
      <header className="mb-8">
        <h1 id="page-title" className="text-[32px] font-semibold leading-10 tracking-[-0.01em] text-[var(--text-primary)]">
          Mes classes
        </h1>
        <p className="mt-2 text-base leading-6 text-[var(--text-secondary)]">
          {isStudent
            ? 'Rejoignez une classe ou retrouvez celles où vous êtes inscrit.'
            : 'Créez vos classes et partagez le code d’invitation avec vos étudiants.'}
        </p>
      </header>

      {errorMessage && (
        <div className="mb-6 rounded-[12px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-4 text-sm text-[var(--text-secondary)]">
          {errorMessage}
        </div>
      )}

      {joinSuccessMessage && (
        <div className="mb-6 rounded-[12px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-4 text-sm text-[var(--text-primary)]">
          {joinSuccessMessage}
        </div>
      )}

      {createSuccessMessage && (
        <div className="mb-6 rounded-[12px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-4 text-sm text-[var(--text-primary)]">
          {createSuccessMessage}
        </div>
      )}

      {isStudent && (
        <div className="mb-8 rounded-[20px] border border-[var(--primary)]/40 bg-[var(--glass-background)] p-6 backdrop-blur-[var(--glass-blur)]">
          <h2 className="text-xl font-semibold leading-8 text-[var(--text-primary)]">Rejoindre une nouvelle classe</h2>
          <p className="mt-2 text-sm leading-6 text-[var(--text-secondary)]">
            Entrez le code communiqué par votre professeur pour accéder aux cours et travaux.
          </p>

          <form onSubmit={handleJoinClass} className="mt-5 flex flex-col gap-4 md:flex-row">
            <div className="flex-1">
              <label className="mb-2 block text-sm font-medium leading-5 text-[var(--text-secondary)]" htmlFor="join-code">
                Code d’invitation
              </label>
              <input
                id="join-code"
                value={joinCode}
                maxLength={8}
                onChange={(event) => setJoinCode(event.target.value.toUpperCase())}
                placeholder="EX. A7XK2M9P"
                className="w-full rounded-[12px] border border-[var(--border-default)] bg-[var(--surface)] px-4 py-3 text-base text-[var(--text-primary)] outline-none placeholder:text-[var(--text-secondary)] focus:border-[var(--primary)]"
              />
            </div>
            <button
              type="submit"
              disabled={isSubmitting || joinCode.trim().length === 0}
              className="mt-auto rounded-[12px] bg-[var(--primary-container)] px-6 py-3 text-sm font-medium leading-5 text-white hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? '...' : 'Rejoindre'}
            </button>
          </form>
        </div>
      )}

      {isProfessor && (
        <div className="mb-8 rounded-[20px] border border-[var(--primary)]/40 bg-[var(--glass-background)] p-6 backdrop-blur-[var(--glass-blur)]">
          <div className="mb-4 text-[11px] font-semibold uppercase tracking-[0.12em] text-[var(--text-secondary)]">Espace enseignant</div>

          <form onSubmit={handleCreateClass} className="flex flex-col gap-4 md:flex-row md:items-end">
            <div className="flex-1">
              <label className="mb-2 block text-sm font-medium leading-5 text-[var(--text-secondary)]" htmlFor="class-name">
                Nom de la classe
              </label>
              <input
                id="class-name"
                value={className}
                onChange={(event) => setClassName(event.target.value)}
                placeholder="Ex. Terminale — Comptabilité"
                className="w-full rounded-[12px] border border-[var(--border-default)] bg-[var(--surface)] px-4 py-3 text-base text-[var(--text-primary)] outline-none placeholder:text-[var(--text-secondary)] focus:border-[var(--primary)]"
              />
            </div>
            <button
              type="submit"
              disabled={isSubmitting || className.trim().length === 0}
              className="rounded-[12px] bg-[var(--primary-container)] px-6 py-3 text-sm font-medium leading-5 text-white hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <span className="material-symbols-outlined align-middle" aria-hidden="true">add</span>
              <span className="ml-2 align-middle">Créer une classe</span>
            </button>
          </form>
        </div>
      )}

      {isStudent && (
        <div className="mb-6 flex items-center justify-between gap-4">
          <h2 className="text-2xl font-semibold leading-8 text-[var(--text-primary)]">Classes actuelles</h2>
          <span className="inline-flex items-center rounded-full border border-[var(--border-default)] bg-[var(--surface-secondary)] px-3 py-1 text-xs font-semibold uppercase tracking-[0.08em] text-[var(--text-secondary)]">
            {classCountLabel}
          </span>
        </div>
      )}

      {classes.length === 0 ? (
        <div className="rounded-[20px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-6 text-center text-base leading-6 text-[var(--text-secondary)]">
          Aucune classe pour le moment.
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {classes.map((classe) => {
            const isProfessorCard = 'code_invitation' in classe
            const createdAtText = formatDate(classe.created_at)

            return (
              <div
                key={classe.id}
                className="rounded-[20px] border border-[var(--border-default)] bg-[var(--glass-background)] p-5 backdrop-blur-[var(--glass-blur)]"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--surface-secondary)] text-[var(--primary)]">
                    <span className="material-symbols-outlined" aria-hidden="true">groups</span>
                  </div>
                </div>

                <h3 className="mt-5 text-xl font-semibold leading-8 text-[var(--text-primary)]">{classe.nom}</h3>

                {!isProfessorCard && (
                  <div className="mt-4 border-t border-[var(--border-default)] pt-4 text-sm text-[var(--text-secondary)]">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-[18px]" aria-hidden="true">school</span>
                      <span>Professeur</span>
                    </div>
                  </div>
                )}

                {isProfessorCard && (
                  <div className="mt-4 rounded-[12px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-3">
                    <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--text-secondary)]">
                      Code d’invitation
                    </div>
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-mono text-base font-medium text-[var(--text-primary)]">{classe.code_invitation}</span>
                      <button
                        type="button"
                        aria-label="Copier le code d’invitation"
                        onClick={() => void copyInvitation(classe.code_invitation)}
                        className="flex h-9 w-9 items-center justify-center rounded-[12px] bg-[var(--surface)] text-[var(--text-secondary)]"
                      >
                        <span className="material-symbols-outlined text-[18px]" aria-hidden="true">content_copy</span>
                      </button>
                    </div>
                  </div>
                )}

                <div className="mt-4 flex items-center justify-between border-t border-[var(--border-default)] pt-4 text-sm text-[var(--text-secondary)]">
                  <span>Créée le {createdAtText}</span>
                  {!isProfessorCard && (
                    <span className="material-symbols-outlined text-[18px]" aria-hidden="true">check_circle</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}
