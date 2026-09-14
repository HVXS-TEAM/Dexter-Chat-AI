import axios from 'axios'
import { useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

type ChatMode = 'explique_moi' | 'mes_cours' | 'calcul'

interface ChatResponse {
  reponse: string | null
  mode: ChatMode
  domaine: string | null
  sous_theme: string | null
  referentiel: string | null
  clarification_demandee: boolean
  question_sous_themes: string[]
  referentiels_proposes: string[] | null
  conversation_id: number | null
  calcul_result: Record<string, unknown> | null
  champs_manquants: string[]
}

type UserMessage = {
  id: string
  role: 'user'
  content: string
}

type AssistantMessage = {
  id: string
  role: 'assistant'
  content: string
  response: ChatResponse
}

type ChatMessage = UserMessage | AssistantMessage

type LocationState = {
  question?: string
}

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const modeLabels: Record<ChatMode, string> = {
  explique_moi: 'Explication',
  calcul: 'Calcul vérifié',
  mes_cours: 'Mes cours',
}

function formatCalculation(value: Record<string, unknown>): string {
  return JSON.stringify(value, null, 2)
}

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 401 || error.response?.status === 403) {
      return 'Vous devez être connecté pour utiliser le chat Dexter.'
    }

    if (error.response?.status === 502) {
      return 'Dexter ne peut pas répondre pour le moment. Réessayez dans quelques instants.'
    }
  }

  return 'Impossible d’envoyer votre message. Vérifiez la connexion au serveur et réessayez.'
}

export default function Chat() {
  const navigate = useNavigate()
  const location = useLocation()
  const navigationState = location.state as LocationState | null
  const [question, setQuestion] = useState(navigationState?.question ?? '')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  async function sendQuestion(rawQuestion: string) {
    const trimmedQuestion = rawQuestion.trim()

    if (!trimmedQuestion || isLoading) {
      return
    }

    const userMessage: UserMessage = {
      id: `${Date.now()}-user`,
      role: 'user',
      content: trimmedQuestion,
    }
    const assistantMessageId = `${Date.now()}-assistant`
    const assistantMessage: AssistantMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      response: {
        reponse: '',
        mode: 'explique_moi',
        domaine: null,
        sous_theme: null,
        referentiel: null,
        clarification_demandee: false,
        question_sous_themes: [],
        referentiels_proposes: null,
        conversation_id: conversationId,
        calcul_result: null,
        champs_manquants: [],
      },
    }

    setMessages((currentMessages) => [...currentMessages, userMessage, assistantMessage])
    setQuestion('')
    setErrorMessage(null)
    setIsLoading(true)

    try {
      const response = await fetch(`${apiUrl}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: trimmedQuestion, conversation_id: conversationId }),
      })

      if (!response.ok) {
        const message = response.status === 401 || response.status === 403
          ? 'Vous devez être connecté pour utiliser le chat Dexter.'
          : response.status === 502
            ? 'Dexter ne peut pas répondre pour le moment. Réessayez dans quelques instants.'
            : 'Impossible d’envoyer votre message. Vérifiez la connexion au serveur et réessayez.'
        throw new Error(message)
      }

      if (!response.body) {
        throw new Error('Le serveur n’a pas fourni de flux de réponse.')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let bufferedLine = ''
      let streamDone = false

      while (!streamDone) {
        const { value, done } = await reader.read()
        bufferedLine += decoder.decode(value ?? new Uint8Array(), { stream: !done })
        const lines = bufferedLine.split('\n')
        bufferedLine = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) {
            continue
          }

          const event = JSON.parse(line.slice(6)) as {
            type: 'token' | 'done' | 'error'
            content?: string
            message?: string
            conversation_id?: number | null
          }

          if (event.conversation_id !== undefined) {
            setConversationId(event.conversation_id)
          }

          if (event.type === 'token' && event.content) {
            setMessages((currentMessages) => currentMessages.map((message) => (
              message.id === assistantMessageId && message.role === 'assistant'
                ? { ...message, content: message.content + event.content }
                : message
            )))
          }

          if (event.type === 'error') {
            setMessages((currentMessages) => currentMessages.filter((message) => message.id !== assistantMessageId))
            setErrorMessage(event.message ?? 'La génération de la réponse a échoué.')
            streamDone = true
            break
          }

          if (event.type === 'done') {
            streamDone = true
            break
          }
        }

        if (done) {
          streamDone = true
        }
      }
    } catch (error: unknown) {
      setMessages((currentMessages) => currentMessages.filter((message) => message.id !== assistantMessageId))
      setErrorMessage(error instanceof Error ? error.message : getErrorMessage(error))
    } finally {
      setIsLoading(false)
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void sendQuestion(question)
  }

  return (
    <section className="flex min-h-[calc(100vh-80px)] w-full flex-col bg-[var(--background)] text-[var(--text-primary)]" aria-labelledby="chat-title">
      <header className="flex shrink-0 items-center justify-between border-b border-[var(--border-default)] bg-[var(--glass-background)] px-4 py-4 backdrop-blur-[var(--glass-blur)] md:px-8">
        <div>
          <h1 id="chat-title" className="text-2xl font-semibold leading-8 text-[var(--text-primary)]">Chat Dexter</h1>
          <p className="text-sm font-medium leading-5 text-[var(--text-secondary)]">Votre espace de conversation</p>
        </div>
        <button className="rounded-full p-2 text-[var(--text-secondary)] hover:bg-[var(--surface-container)] hover:text-[var(--primary)]" type="button" onClick={() => navigate('/historique')} aria-label="Ouvrir l’historique">
          <span className="material-symbols-outlined" aria-hidden="true">history</span>
        </button>
      </header>

      <div className="flex-1 overflow-y-auto px-4 pb-40 pt-8 md:px-12">
        <div className="mx-auto flex w-full max-w-[1000px] flex-col gap-6">
          {messages.length === 0 && (
            <div className="flex items-end gap-3">
              <img className="h-8 w-8 shrink-0 rounded-full border border-[var(--border-default)] object-cover" src="/DexterIcons.ico" alt="Dexter Assistant Avatar" />
              <div className="max-w-[70%] rounded-[18px] rounded-bl-sm border border-[var(--border-default)] bg-[var(--surface-secondary)] p-6 text-base font-normal leading-6 text-[var(--text-primary)]">
                Bonjour ! Je suis Dexter, ton assistant d&apos;étude. Comment puis-je t&apos;aider aujourd&apos;hui ?
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div className={`flex max-w-[85%] items-end gap-3 md:max-w-[70%] ${message.role === 'user' ? 'self-end flex-row-reverse' : ''}`} key={message.id}>
              {message.role === 'assistant' ? (
                <img className="h-8 w-8 shrink-0 rounded-full border border-[var(--border-default)] object-cover" src="/DexterIcons.ico" alt="Dexter Assistant Avatar" />
              ) : (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--primary-container)] text-xs font-semibold text-white" aria-hidden="true">U</div>
              )}
              <div className={message.role === 'user' ? 'rounded-[18px] rounded-br-sm bg-[var(--accent-gradient)] p-4 text-base font-normal leading-6 text-white' : 'rounded-[18px] rounded-bl-sm border border-[var(--border-default)] bg-[var(--surface-secondary)] p-6 text-base font-normal leading-6 text-[var(--text-primary)]'}>
                <p className="whitespace-pre-wrap">{message.content}</p>
                {message.role === 'assistant' && (
                  <div className="mt-4 flex flex-col gap-3">
                    <span className="w-fit rounded-full bg-[var(--primary)]/10 px-3 py-1 text-xs font-semibold leading-4 text-[var(--primary)]">{modeLabels[message.response.mode]}</span>
                    {message.response.clarification_demandee && (
                      <div className="rounded-[12px] border border-[var(--border-default)] bg-[var(--surface)] p-4 text-sm leading-5 text-[var(--text-secondary)]">
                        <p>Précision nécessaire avant de continuer.</p>
                        {message.response.champs_manquants.length > 0 && <p className="mt-2">Éléments manquants : {message.response.champs_manquants.join(', ')}.</p>}
                        {message.response.referentiels_proposes && <p className="mt-2">Référentiels proposés : {message.response.referentiels_proposes.join(', ')}.</p>}
                      </div>
                    )}
                    {message.response.calcul_result && (
                      <pre className="overflow-x-auto rounded-[12px] bg-[var(--background)] p-4 text-xs leading-5 text-[var(--text-secondary)]">{formatCalculation(message.response.calcul_result)}</pre>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-end gap-3" aria-label="Dexter répond" aria-busy="true">
              <img className="h-8 w-8 shrink-0 rounded-full border border-[var(--border-default)] object-cover" src="/DexterIcons.ico" alt="Dexter Assistant Avatar" />
              <div className="flex h-[42px] items-center gap-1 rounded-[18px] rounded-bl-sm border border-[var(--border-default)] bg-[var(--surface-secondary)] px-4">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--text-secondary)]" />
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--text-secondary)] [animation-delay:75ms]" />
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--text-secondary)] [animation-delay:150ms]" />
              </div>
            </div>
          )}

          {errorMessage && (
            <p className="rounded-[12px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-4 text-sm leading-5 text-[var(--text-secondary)]" role="alert">{errorMessage}</p>
          )}
        </div>
      </div>

      <div className="fixed bottom-0 left-0 right-0 z-20 bg-gradient-to-t from-[var(--background)] via-[var(--background)] to-transparent px-4 pb-4 pt-8 md:left-[280px] md:px-12 md:pb-8">
        <form className="mx-auto flex w-full max-w-3xl items-end gap-2 rounded-[12px] border border-[var(--border-default)] bg-[var(--surface)] p-2 focus-within:border-[var(--primary)] focus-within:ring-1 focus-within:ring-[var(--primary)]" onSubmit={handleSubmit}>
          <span className="material-symbols-outlined px-3 pb-3 text-[var(--text-secondary)]" aria-hidden="true">attach_file</span>
          <textarea className="min-h-11 max-h-32 min-w-0 flex-1 resize-none border-0 bg-transparent px-2 py-3 text-base font-normal leading-6 text-[var(--text-primary)] outline-none placeholder:text-[var(--text-secondary)] focus:ring-0" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Pose ta question à Dexter…" rows={1} aria-label="Message à Dexter" disabled={isLoading} />
          <button className="mb-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-[12px] bg-[var(--primary-container)] text-white hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50" type="submit" aria-label="Envoyer le message" disabled={isLoading || question.trim().length === 0}>
            <span className="material-symbols-outlined" aria-hidden="true">send</span>
          </button>
        </form>
        <p className="mt-2 text-center text-[10px] font-semibold leading-4 text-[var(--text-secondary)]">Dexter peut faire des erreurs. Vérifie les informations importantes.</p>
      </div>
    </section>
  )
}
