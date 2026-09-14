import axios from 'axios'
import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

interface Domain {
  id: string
  label: string
  keywords: string[]
  sous_themes: string[]
  referentiels: string[]
}

const suggestions = [
  { label: 'Résoudre une équation', icon: 'calculate' },
  { label: 'Traduire un texte', icon: 'translate' },
  { label: 'Expliquer la mitose', icon: 'biotech' },
]

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Accueil() {
  const navigate = useNavigate()
  const [question, setQuestion] = useState('')
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
      setErrorMessage('Impossible de charger les matières. Vérifiez la connexion au serveur.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadDomains()
  }, [loadDomains])

  function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmedQuestion = question.trim()

    if (trimmedQuestion) {
      navigate('/chat', { state: { question: trimmedQuestion } })
    }
  }

  function submitSuggestion(suggestion: string) {
    navigate('/chat', { state: { question: suggestion } })
  }

  return (
    <section className="w-full max-w-[1440px] px-0 py-8 text-[var(--text-primary)] md:px-8 md:py-16" aria-labelledby="page-title">
      <div className="mx-auto flex w-full max-w-[1000px] flex-col items-center">
        <div className="mb-10 flex w-full flex-col items-center text-center">
          <div className="mb-6 h-24 w-24 overflow-hidden rounded-full border border-[var(--border-default)] bg-[var(--surface-secondary)]">
            <img
              className="h-full w-full object-cover"
              src="/DexterIcons.ico"
              alt="Mascotte Dexter"
            />
          </div>
          <h1 id="page-title" className="mb-2 text-[32px] font-semibold leading-10 tracking-[-0.01em] text-[var(--text-primary)]">
            Bonjour, David 👋
          </h1>
          <p className="text-lg font-normal leading-7 text-[var(--text-secondary)]">Que souhaites-tu étudier aujourd&apos;hui ?</p>
        </div>

        <form className="w-full max-w-3xl" onSubmit={submitQuestion}>
          <div className="flex items-center gap-2 rounded-[12px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-2 focus-within:border-[var(--primary)] focus-within:ring-1 focus-within:ring-[var(--primary)]">
            <span className="material-symbols-outlined px-3 text-[var(--text-secondary)]" aria-hidden="true">
              search
            </span>
            <input
              className="min-w-0 flex-1 border-0 bg-transparent text-base font-normal leading-6 text-[var(--text-primary)] outline-none placeholder:text-[var(--text-secondary)] focus:ring-0"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Pose ta question à Dexter"
              aria-label="Question à Dexter"
            />
            <button className="flex h-12 w-12 items-center justify-center rounded-[12px] bg-[var(--primary-container)] text-white transition-[filter] hover:brightness-110" type="submit" aria-label="Envoyer la question">
              <span className="material-symbols-outlined" aria-hidden="true">
                send
              </span>
            </button>
          </div>
        </form>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-3" aria-label="Suggestions">
          {suggestions.map((suggestion) => (
            <button
              className="flex items-center gap-2 rounded-full border border-[var(--border-default)] bg-[var(--surface)] px-4 py-2 text-sm font-medium leading-5 text-[var(--text-secondary)] transition-colors hover:border-[var(--primary)] hover:text-[var(--primary)]"
              key={suggestion.label}
              type="button"
              onClick={() => submitSuggestion(suggestion.label)}
            >
              <span className="material-symbols-outlined text-[18px]" aria-hidden="true">
                {suggestion.icon}
              </span>
              {suggestion.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mx-auto mt-10 w-full max-w-[1440px]">
        <div className="mb-6 flex items-center justify-between gap-4">
          <h2 className="text-2xl font-semibold leading-8 text-[var(--text-primary)]">Tes Matières</h2>
        </div>

        {isLoading && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3" aria-label="Chargement des matières" aria-busy="true">
            {Array.from({ length: 7 }, (_, index) => (
              <div className="h-48 animate-pulse rounded-[18px] border border-[var(--border-default)] bg-[var(--surface-secondary)]" key={index} />
            ))}
          </div>
        )}

        {!isLoading && errorMessage && (
          <div className="rounded-[18px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-6 text-center">
            <p className="text-base font-normal leading-6 text-[var(--text-secondary)]">{errorMessage}</p>
            <button className="mt-4 rounded-[12px] bg-[var(--primary-container)] px-4 py-3 text-sm font-medium leading-5 text-white hover:brightness-110" type="button" onClick={() => void loadDomains()}>
              Réessayer
            </button>
          </div>
        )}

        {!isLoading && !errorMessage && domains.length === 0 && (
          <p className="rounded-[18px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-6 text-center text-base font-normal leading-6 text-[var(--text-secondary)]">
            Aucune matière n&apos;est disponible pour le moment.
          </p>
        )}

        {!isLoading && !errorMessage && domains.length > 0 && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {domains.map((domain) => (
              <button
                className="group flex min-h-48 flex-col justify-between rounded-[18px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-6 text-left transition-colors hover:border-[var(--primary)]"
                key={domain.id}
                type="button"
                onClick={() => navigate(`/matiere/${domain.id}`)}
              >
                <div className="flex items-start justify-between gap-4">
                  <span className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--primary)]/10 text-[var(--primary)]">
                    <span className="material-symbols-outlined" aria-hidden="true">
                      auto_stories
                    </span>
                  </span>
                  <span className="material-symbols-outlined text-[var(--text-secondary)] transition-colors group-hover:text-[var(--primary)]" aria-hidden="true">
                    arrow_forward
                  </span>
                </div>
                <div className="mt-8">
                  <h3 className="text-xl font-semibold leading-8 text-[var(--text-primary)]">{domain.label}</h3>
                  <p className="mt-1 text-base font-normal leading-6 text-[var(--text-secondary)]">
                    {domain.sous_themes.length} sous-thèmes
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
