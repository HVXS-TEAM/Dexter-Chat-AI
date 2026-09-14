import axios from 'axios'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

interface Domain {
  id: string
  label: string
  keywords: string[]
  sous_themes: string[]
  referentiels: string[]
}

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const recentSearches = ['Le bilan comptable et compte de résultat', 'Guerre Froide : Résumé détaillé', 'Équations différentielles de 2…']

export default function Recherche() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [domains, setDomains] = useState<Domain[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const loadDomains = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage(null)

    try {
      const response = await axios.get<Domain[]>(`${apiUrl}/domains`)
      setDomains(response.data)
    } catch {
      setErrorMessage('Impossible de charger les sujets. Vérifiez la connexion au serveur et réessayez.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadDomains()
  }, [loadDomains])

  const filteredDomains = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase('fr')

    if (!normalizedQuery) {
      return domains
    }

    return domains.filter((domain) => [domain.label, ...domain.keywords, ...domain.sous_themes].join(' ').toLocaleLowerCase('fr').includes(normalizedQuery))
  }, [domains, query])

  return (
    <section className="w-full max-w-[1152px] pb-12 text-[var(--text-primary)]" aria-labelledby="page-title">
      <header className="mx-auto flex max-w-[960px] flex-col items-center text-center">
        <h1 id="page-title" className="text-[32px] font-semibold leading-10 tracking-[-0.01em] md:text-5xl md:leading-[56px]">Que souhaitez-vous apprendre ?</h1>
        <p className="mt-4 text-lg font-normal leading-7 text-[var(--text-secondary)]">Explorez des milliers de concepts, résumés et exercices générés par l&apos;IA.</p>
        <label className="mt-12 flex w-full items-center gap-3 rounded-[12px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-2 focus-within:border-[var(--primary)] focus-within:ring-1 focus-within:ring-[var(--primary)]" htmlFor="search-input">
          <span className="material-symbols-outlined px-3 text-[var(--text-secondary)]" aria-hidden="true">search</span>
          <input id="search-input" className="min-w-0 flex-1 border-0 bg-transparent py-3 text-base leading-6 text-[var(--text-primary)] outline-none placeholder:text-[var(--text-secondary)] focus:ring-0" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ex : 'Le bilan comptable', 'Théorème de Pythagore'…" aria-label="Rechercher une matière" />
          <button className="flex h-10 w-10 items-center justify-center rounded-[12px] bg-[var(--surface-container)] text-[var(--text-secondary)] hover:text-[var(--primary)]" type="button" aria-label="Lancer la recherche" onClick={() => setQuery(query.trim())}>
            <span className="material-symbols-outlined" aria-hidden="true">mic</span>
          </button>
        </label>
      </header>

      <section className="mt-16" aria-labelledby="recent-title">
        <div className="mb-6 flex items-center justify-between gap-4">
          <h2 id="recent-title" className="text-2xl font-semibold leading-8">Recherches récentes</h2>
          <button className="text-sm font-medium leading-5 text-[var(--primary)] hover:underline" type="button" onClick={() => setQuery('')}>Tout effacer</button>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {recentSearches.map((search) => (
            <button className="min-h-44 rounded-[18px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-6 text-left hover:border-[var(--primary)]" key={search} type="button" onClick={() => setQuery(search)}>
              <span className="material-symbols-outlined text-[var(--text-secondary)]" aria-hidden="true">history</span>
              <span className="mt-6 block text-base font-medium leading-6 text-[var(--text-primary)]">{search}</span>
              <span className="mt-2 block text-base leading-6 text-[var(--text-secondary)]">Historique de recherche</span>
            </button>
          ))}
        </div>
      </section>

      <section className="mt-16" aria-labelledby="popular-title">
        <h2 id="popular-title" className="mb-6 text-2xl font-semibold leading-8">Sujets populaires</h2>
        {isLoading && <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3" aria-label="Chargement des sujets" aria-busy="true">{Array.from({ length: 3 }, (_, index) => <div className="h-64 animate-pulse rounded-[18px] border border-[var(--border-default)] bg-[var(--surface-secondary)]" key={index} />)}</div>}
        {!isLoading && errorMessage && <div className="rounded-[18px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-6 text-center"><p className="text-base leading-6 text-[var(--text-secondary)]">{errorMessage}</p><button className="mt-4 rounded-[12px] bg-[var(--primary-container)] px-4 py-3 text-sm font-medium leading-5 text-white hover:brightness-110" type="button" onClick={() => void loadDomains()}>Réessayer</button></div>}
        {!isLoading && !errorMessage && filteredDomains.length === 0 && <p className="rounded-[18px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-6 text-center text-base leading-6 text-[var(--text-secondary)]">Aucun résultat pour cette recherche.</p>}
        {!isLoading && !errorMessage && filteredDomains.length > 0 && <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">{filteredDomains.map((domain) => <button className="min-h-64 rounded-[18px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-6 text-left hover:border-[var(--primary)]" key={domain.id} type="button" onClick={() => navigate(`/matiere/${domain.id}`)}><div className="flex items-center gap-4"><span className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--primary)]/10 text-[var(--primary)]"><span className="material-symbols-outlined" aria-hidden="true">auto_stories</span></span><h3 className="text-xl font-semibold leading-8">{domain.label}</h3></div><ul className="mt-8 space-y-4 text-base leading-6 text-[var(--text-secondary)]">{domain.sous_themes.slice(0, 4).map((subTheme) => <li key={subTheme}>{subTheme}</li>)}</ul></button>)}</div>}
      </section>
    </section>
  )
}
