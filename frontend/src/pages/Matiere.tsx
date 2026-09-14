import axios from 'axios'
import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

interface Domain {
  id: string
  label: string
  keywords: string[]
  sous_themes: string[]
  referentiels: string[]
}

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error) && error.response?.status === 404) {
    return 'Cette matière n’existe pas dans le catalogue Dexter.'
  }

  return 'Impossible de charger cette matière. Vérifiez la connexion au serveur et réessayez.'
}

export default function Matiere() {
  const { id } = useParams<{ id: string }>()
  const [domain, setDomain] = useState<Domain | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const loadDomain = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage(null)

    try {
      const response = await axios.get<Domain[]>(`${apiUrl}/domains`)
      const matchingDomain = response.data.find((item) => item.id === id)

      if (!matchingDomain) {
        setDomain(null)
        setErrorMessage('Cette matière n’existe pas dans le catalogue Dexter.')
        return
      }

      setDomain(matchingDomain)
    } catch (error: unknown) {
      setDomain(null)
      setErrorMessage(getErrorMessage(error))
    } finally {
      setIsLoading(false)
    }
  }, [id])

  useEffect(() => {
    void loadDomain()
  }, [loadDomain])

  if (isLoading) {
    return (
      <section className="w-full max-w-[1000px] animate-pulse" aria-labelledby="page-title" aria-busy="true">
        <div className="mb-8 h-8 w-48 rounded-[12px] bg-[var(--surface-secondary)]" />
        <div className="mb-10 h-32 rounded-[18px] border border-[var(--border-default)] bg-[var(--surface-secondary)]" />
        <div className="grid gap-6 md:grid-cols-2">
          {Array.from({ length: 4 }, (_, index) => <div className="h-44 rounded-[18px] border border-[var(--border-default)] bg-[var(--surface-secondary)]" key={index} />)}
        </div>
      </section>
    )
  }

  if (errorMessage || !domain) {
    return (
      <section className="w-full max-w-[1000px] rounded-[18px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-8 text-center" aria-labelledby="page-title">
        <h1 id="page-title" className="text-2xl font-semibold leading-8 text-[var(--text-primary)]">Détail matière</h1>
        <p className="mt-3 text-base leading-6 text-[var(--text-secondary)]">{errorMessage ?? 'Matière introuvable.'}</p>
        <button className="mt-6 rounded-[12px] bg-[var(--primary-container)] px-4 py-3 text-sm font-medium leading-5 text-white hover:brightness-110" type="button" onClick={() => void loadDomain()}>
          Réessayer
        </button>
      </section>
    )
  }

  return (
    <section className="w-full max-w-[1000px] pb-12 text-[var(--text-primary)]" aria-labelledby="page-title">
      <header className="mb-10 flex items-start justify-between gap-6">
        <div>
          <span className="inline-flex rounded-full border border-[var(--border-default)] bg-[var(--surface-secondary)] px-3 py-1 text-xs font-semibold uppercase leading-4 tracking-[0.05em] text-[var(--text-secondary)]">Domaine d&apos;étude</span>
          <h1 id="page-title" className="mt-3 text-[32px] font-semibold leading-10 tracking-[-0.01em] text-[var(--text-primary)]">{domain.label}</h1>
          <div className="mt-4 flex flex-wrap gap-5 text-base leading-6 text-[var(--text-secondary)]">
            <span><span className="material-symbols-outlined mr-1 align-middle text-[20px]" aria-hidden="true">menu_book</span>{domain.sous_themes.length} Chapitres</span>
            <span><span className="material-symbols-outlined mr-1 align-middle text-[20px]" aria-hidden="true">schedule</span>Parcours personnalisé</span>
          </div>
        </div>
        <button className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border border-[var(--border-default)] text-[var(--text-secondary)] hover:bg-[var(--surface-container)] hover:text-[var(--primary)]" type="button" aria-label="Options de la matière">
          <span className="material-symbols-outlined" aria-hidden="true">more_horiz</span>
        </button>
      </header>

      <div className="rounded-[18px] border border-[var(--border-default)] bg-[var(--glass-background)] p-6 backdrop-blur-[var(--glass-blur)]">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase leading-5 tracking-[0.05em] text-[var(--text-secondary)]">Progression globale</p>
            <p className="mt-1 text-[32px] font-semibold leading-10 text-[var(--text-primary)]">Non commencée</p>
          </div>
          <span className="text-sm font-medium leading-5 text-[var(--text-secondary)]">Progression personnelle indisponible</span>
        </div>
        <div className="mt-5 h-2 rounded-full bg-[var(--surface-container)]" role="progressbar" aria-label="Progression globale" aria-valuemin={0} aria-valuemax={100} aria-valuenow={0} />
      </div>

      <div className="mt-10 flex items-center gap-8 border-b border-[var(--border-default)]">
        <div className="border-b-2 border-[var(--primary)] pb-4 text-base font-medium leading-6 text-[var(--primary)]">Chapitres <span className="ml-1 rounded-full bg-[var(--primary)] px-2 py-0.5 text-xs text-white">{domain.sous_themes.length}</span></div>
        <div className="pb-4 text-base font-medium leading-6 text-[var(--text-secondary)]">Référentiels</div>
      </div>

      <div className="mt-8 grid gap-6 md:grid-cols-2">
        {domain.sous_themes.map((subTheme, index) => (
          <button className="group flex min-h-44 flex-col justify-between rounded-[18px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-6 text-left transition-colors hover:border-[var(--primary)]" key={subTheme} type="button" aria-label={`Ouvrir le chapitre ${subTheme}`}>
            <div className="flex items-start gap-4">
              <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border border-[var(--border-default)] bg-[var(--surface-container)] text-[var(--primary)]">
                <span className="material-symbols-outlined" aria-hidden="true">{index === 0 ? 'check_circle' : 'lock'}</span>
              </span>
              <div>
                <p className="text-sm font-semibold leading-5 text-[var(--text-secondary)]">Chapitre {index + 1}</p>
                <h2 className="mt-1 text-xl font-semibold leading-8 text-[var(--text-primary)] group-hover:text-[var(--primary)]">{subTheme}</h2>
              </div>
            </div>
            <span className="mt-6 inline-flex w-fit rounded-full bg-[var(--surface-container)] px-3 py-1 text-xs font-semibold leading-4 text-[var(--text-secondary)]">À découvrir</span>
          </button>
        ))}
      </div>

      {domain.referentiels.length > 0 && (
        <div className="mt-10">
          <h2 className="text-2xl font-semibold leading-8 text-[var(--text-primary)]">Référentiels</h2>
          <div className="mt-4 flex flex-wrap gap-3">
            {domain.referentiels.map((referentiel) => <span className="rounded-full border border-[var(--border-default)] bg-[var(--surface-secondary)] px-4 py-2 text-sm font-medium leading-5 text-[var(--text-secondary)]" key={referentiel}>{referentiel}</span>)}
          </div>
        </div>
      )}
    </section>
  )
}
