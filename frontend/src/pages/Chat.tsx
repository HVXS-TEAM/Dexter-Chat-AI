import axios from 'axios'
import { useEffect, useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import AttachMenu from '../components/AttachMenu'
import ChatMarkdown from '../components/ChatMarkdown'
import { createConversation, setMessageFeedback } from '../conversations/api'
import {
  deleteDocument,
  listConversationDocuments,
  updateDocumentVisibility,
  uploadDocument,
} from '../documents/api'
import type { DocumentRead, DocumentVisibility } from '../documents/types'

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
  sentAt: string
}

type AssistantMessage = {
  id: string
  role: 'assistant'
  content: string
  response: ChatResponse
  messageId?: number
  feedback?: 'up' | 'down'
  sentAt: string
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

function formatLocalTime(): string {
  return new Intl.DateTimeFormat('fr-FR', { hour: '2-digit', minute: '2-digit' }).format(new Date())
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
  const { getAccessToken, user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const navigationState = location.state as LocationState | null
  const [question, setQuestion] = useState(navigationState?.question ?? '')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [documents, setDocuments] = useState<DocumentRead[]>([])
  const [documentsError, setDocumentsError] = useState<string | null>(null)
  const [uploadingDocumentName, setUploadingDocumentName] = useState<string | null>(null)
  const [stagedFiles, setStagedFiles] = useState<Array<{ id: string; file: File }>>([])
  const [attachMenuOpen, setAttachMenuOpen] = useState(false)
  const [guestPromptVisible, setGuestPromptVisible] = useState(false)
  const [feedbackError, setFeedbackError] = useState<string | null>(null)

  useEffect(() => {
    if (conversationId === null) {
      setDocuments([])
      return
    }

    let isMounted = true

    async function loadDocuments() {
      if (conversationId === null) {
        return
      }

      try {
        const response = await listConversationDocuments(conversationId)
        if (isMounted) {
          setDocuments(response)
          setDocumentsError(null)
        }
      } catch (error: unknown) {
        if (!isMounted) {
          return
        }

        if (axios.isAxiosError(error) && error.response?.status === 404) {
          setDocumentsError('Conversation introuvable.')
          return
        }

        setDocumentsError('Impossible de traiter le document. Vérifiez la connexion au serveur et réessayez.')
      }
    }

    void loadDocuments()

    return () => {
      isMounted = false
    }
  }, [conversationId])

  function getDocumentTypeIcon(type: string): string {
    return ['png', 'jpg', 'jpeg'].includes(type.toLowerCase()) ? 'image' : 'description'
  }

  function getDocumentStatusIcon(status: DocumentRead['statut_indexation']): string {
    if (status === 'indexe') {
      return 'check_circle'
    }

    if (status === 'pending') {
      return 'progress_activity'
    }

    return 'error'
  }

  function getDocumentStatusColor(status: DocumentRead['statut_indexation']): string {
    if (status === 'indexe') {
      return 'text-[var(--success)] opacity-80'
    }

    if (status === 'pending') {
      return 'text-[var(--text-secondary)]'
    }

    return 'text-[var(--error)]'
  }

  function getDocumentErrorMessage(status: number | undefined): string {
    switch (status) {
      case 400:
        return 'Type de fichier non supporté (pdf, docx, pptx, png, jpg, jpeg, txt, md).'
      case 422:
        return 'L\'indexation du document a échoué.'
      case 404:
        return 'Conversation introuvable.'
      case 403:
        return 'Seuls les professeurs peuvent partager des documents.'
      default:
        return 'Impossible de traiter le document. Vérifiez la connexion au serveur et réessayez.'
    }
  }

  function handleFilesSelected(files: File[]) {
    setStagedFiles((currentFiles) => [
      ...currentFiles,
      ...files.map((file, index) => ({ id: `${Date.now()}-${index}-${file.name}`, file })),
    ])
    setAttachMenuOpen(false)
    setDocumentsError(null)
  }

  function removeStagedFile(fileId: string) {
    setStagedFiles((currentFiles) => currentFiles.filter(({ id }) => id !== fileId))
  }

  async function handleFeedback(messageId: number, feedback: 'up' | 'down') {
    const previousMessage = messages.find(
      (message): message is AssistantMessage => message.role === 'assistant' && message.messageId === messageId,
    )
    const previousFeedback = previousMessage?.feedback
    setFeedbackError(null)
    setMessages((currentMessages) => currentMessages.map((message) => (
      message.role === 'assistant' && message.messageId === messageId
        ? { ...message, feedback }
        : message
    )))

    try {
      await setMessageFeedback(messageId, feedback)
    } catch {
      setMessages((currentMessages) => currentMessages.map((message) => (
        message.role === 'assistant' && message.messageId === messageId
          ? { ...message, feedback: previousFeedback }
          : message
      )))
      setFeedbackError('Votre feedback n’a pas pu être enregistré.')
    }
  }

  async function handleDeleteDocument(documentId: number, title: string) {
    if (conversationId === null) {
      return
    }

    try {
      await deleteDocument(documentId)
      const refreshedDocuments = await listConversationDocuments(conversationId)
      setDocuments(refreshedDocuments)
    } catch (error: unknown) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        setDocumentsError('Conversation introuvable.')
        return
      }

      setDocumentsError(`Impossible de supprimer le document ${title}. Vérifiez la connexion au serveur et réessayez.`)
    }
  }

  async function handleVisibilityToggle(document: DocumentRead) {
    if (conversationId === null) {
      return
    }

    try {
      const nextVisibility: DocumentVisibility = document.visibilite === 'prive' ? 'partage_classe' : 'prive'
      await updateDocumentVisibility(document.id, nextVisibility)
      const refreshedDocuments = await listConversationDocuments(conversationId)
      setDocuments(refreshedDocuments)
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        setDocumentsError(getDocumentErrorMessage(error.response?.status))
        return
      }

      setDocumentsError('Impossible de traiter le document. Vérifiez la connexion au serveur et réessayez.')
    }
  }

  async function sendQuestion(rawQuestion: string) {
    const trimmedQuestion = rawQuestion.trim()

    if (!trimmedQuestion || isLoading) {
      return
    }

    if (!user) {
      setGuestPromptVisible(true)
      return
    }

    let activeConversationId = conversationId
    const sentAt = formatLocalTime()

    const userMessage: UserMessage = {
      id: `${Date.now()}-user`,
      role: 'user',
      content: trimmedQuestion,
      sentAt,
    }
    const assistantMessageId = `${Date.now()}-assistant`
    const assistantMessage: AssistantMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      sentAt,
      response: {
        reponse: '',
        mode: 'explique_moi',
        domaine: null,
        sous_theme: null,
        referentiel: null,
        clarification_demandee: false,
        question_sous_themes: [],
        referentiels_proposes: null,
        conversation_id: activeConversationId,
        calcul_result: null,
        champs_manquants: [],
      },
    }

    setMessages((currentMessages) => [...currentMessages, userMessage, assistantMessage])
    setQuestion('')
    setErrorMessage(null)
    setIsLoading(true)

    try {
      if (activeConversationId === null) {
        const conversation = await createConversation({ titre: 'Nouvelle conversation' })
        activeConversationId = conversation.id
        setConversationId(conversation.id)
      }

      const pendingFiles = stagedFiles
      for (const stagedFile of pendingFiles) {
        setUploadingDocumentName(stagedFile.file.name)
        try {
          await uploadDocument(activeConversationId, stagedFile.file)
          setStagedFiles((currentFiles) => currentFiles.filter(({ id }) => id !== stagedFile.id))
        } catch (error: unknown) {
          setStagedFiles((currentFiles) => currentFiles.filter(({ id }) => id !== stagedFile.id))
          setDocumentsError(axios.isAxiosError(error)
            ? getDocumentErrorMessage(error.response?.status)
            : 'Impossible de traiter le document. Vérifiez la connexion au serveur et réessayez.')
          setUploadingDocumentName(null)
          const refreshedDocuments = await listConversationDocuments(activeConversationId)
          setDocuments(refreshedDocuments)
          setMessages((currentMessages) => currentMessages.filter((message) => message.id !== assistantMessageId && message.id !== userMessage.id))
          setQuestion(trimmedQuestion)
          setIsLoading(false)
          return
        }
      }
      setUploadingDocumentName(null)
      const refreshedDocuments = await listConversationDocuments(activeConversationId)
      setDocuments(refreshedDocuments)

      const accessToken = getAccessToken()
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (accessToken) {
        headers.Authorization = `Bearer ${accessToken}`
      }

      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ question: trimmedQuestion, conversation_id: activeConversationId }),
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
            type: 'token' | 'done' | 'error' | 'meta'
            content?: string
            message?: string
            conversation_id?: number | null
            message_id?: number
            mode?: ChatMode
            domaine?: string | null
            sous_theme?: string | null
            referentiel?: string | null
            clarification_demandee?: boolean
            question_sous_themes?: string[]
            referentiels_proposes?: string[] | null
            champs_manquants?: string[]
            calcul_result?: Record<string, unknown> | null
          }

          if (event.conversation_id !== undefined) {
            setConversationId(event.conversation_id)
          }

          if (event.type === 'meta') {
            setMessages((currentMessages) => currentMessages.map((message) => (
              message.id === assistantMessageId && message.role === 'assistant'
                ? {
                    ...message,
                    response: {
                      ...message.response,
                      mode: event.mode ?? message.response.mode,
                      domaine: event.domaine ?? message.response.domaine,
                      sous_theme: event.sous_theme ?? message.response.sous_theme,
                      referentiel: event.referentiel ?? message.response.referentiel,
                      clarification_demandee: event.clarification_demandee ?? message.response.clarification_demandee,
                      question_sous_themes: event.question_sous_themes ?? message.response.question_sous_themes,
                      referentiels_proposes: event.referentiels_proposes ?? message.response.referentiels_proposes,
                      champs_manquants: event.champs_manquants ?? message.response.champs_manquants,
                      calcul_result: event.calcul_result ?? message.response.calcul_result,
                    },
                  }
                : message
            )))
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
            setMessages((currentMessages) => currentMessages.map((message) => (
              message.id === assistantMessageId && message.role === 'assistant'
                ? {
                    ...message,
                    messageId: event.message_id,
                    response: { ...message.response, conversation_id: event.conversation_id ?? activeConversationId },
                  }
                : message
            )))
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
              <div>
                <div className={message.role === 'user' ? 'rounded-[18px] rounded-br-sm bg-[var(--accent-gradient)] p-4 text-base font-normal leading-6 text-white' : 'rounded-[18px] rounded-bl-sm border border-[var(--border-default)] bg-[var(--surface-secondary)] p-6 text-base font-normal leading-6 text-[var(--text-primary)]'}>
                  {message.role === 'user' ? <p className="whitespace-pre-wrap">{message.content}</p> : <ChatMarkdown content={message.content} />}
                {message.role === 'assistant' && (
                  <div className="mt-4 flex flex-col gap-3">
                    <span className="w-fit rounded-full bg-[var(--primary)]/10 px-3 py-1 text-xs font-semibold leading-4 text-[var(--primary)]">{modeLabels[message.response.mode]}</span>
                    {message.response.clarification_demandee && (
                      <div className="rounded-[12px] border border-[var(--border-default)] bg-[var(--surface)] p-4 text-sm leading-5 text-[var(--text-secondary)]">
                        <p>Précision nécessaire avant de continuer.</p>
                        {message.response.champs_manquants.length > 0 && <p className="mt-2">Éléments manquants : {message.response.champs_manquants.join(', ')}.</p>}
                        {message.response.question_sous_themes.length > 0 && <p className="mt-2">Pistes possibles : {message.response.question_sous_themes.join(', ')}.</p>}
                        {message.response.referentiels_proposes && <p className="mt-2">Référentiels proposés : {message.response.referentiels_proposes.join(', ')}.</p>}
                      </div>
                    )}
                    {message.response.calcul_result && (
                      <div className="overflow-hidden rounded-[12px] border border-[var(--border-default)] bg-[var(--surface)]">
                        <div className="flex items-center gap-2 border-b border-[var(--border-default)] px-4 py-3 text-sm font-semibold text-[var(--text-primary)]">
                          <span className="material-symbols-outlined text-[var(--primary)]" aria-hidden="true">calculate</span>
                          <span>Calcul vérifié</span>
                        </div>
                        <pre className="overflow-x-auto bg-[var(--background)] p-4 text-xs leading-5 text-[var(--text-secondary)]">{formatCalculation(message.response.calcul_result)}</pre>
                      </div>
                    )}
                  </div>
                )}
                </div>
                {message.role === 'user' ? (
                  <p className="mt-1 text-right text-[10px] text-[var(--text-secondary)]">{message.sentAt}</p>
                ) : (
                  <div className="mt-1 flex items-center justify-end gap-2 text-[10px] text-[var(--text-secondary)]">
                    <span>Dexter • {message.sentAt}</span>
                    {user && message.messageId !== undefined && !isLoading && (
                      <>
                        <button type="button" className={message.feedback === 'up' ? 'text-[var(--primary)]' : 'hover:text-[var(--primary)]'} aria-label="Réponse utile" aria-pressed={message.feedback === 'up'} onClick={() => void handleFeedback(message.messageId as number, 'up')}>
                          <span className="material-symbols-outlined text-base" aria-hidden="true">thumb_up</span>
                        </button>
                        <button type="button" className={message.feedback === 'down' ? 'text-[var(--primary)]' : 'hover:text-[var(--primary)]'} aria-label="Réponse inutile" aria-pressed={message.feedback === 'down'} onClick={() => void handleFeedback(message.messageId as number, 'down')}>
                          <span className="material-symbols-outlined text-base" aria-hidden="true">thumb_down</span>
                        </button>
                      </>
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
        {(stagedFiles.length > 0 || conversationId !== null) && (
          <div className="mx-auto mb-3 flex w-full max-w-3xl flex-wrap gap-2">
            {stagedFiles.map((stagedFile) => (
              <div className="inline-flex items-center gap-2 rounded-full border border-dashed border-[var(--primary)] bg-[var(--surface-secondary)] px-3 py-1.5 text-xs text-[var(--text-primary)]" key={stagedFile.id}>
                <span className="material-symbols-outlined text-[var(--primary)]" aria-hidden="true">attach_file</span>
                <span className="max-w-[160px] truncate" title={stagedFile.file.name}>{stagedFile.file.name}</span>
                <button type="button" aria-label={`Retirer ${stagedFile.file.name}`} onClick={() => removeStagedFile(stagedFile.id)} className="text-[var(--text-secondary)] hover:text-[var(--primary)]">
                  <span className="material-symbols-outlined" aria-hidden="true">close</span>
                </button>
              </div>
            ))}
            {uploadingDocumentName && (
              <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border-default)] bg-[var(--surface-secondary)] px-3 py-1.5 text-xs text-[var(--text-primary)]">
                <span className="material-symbols-outlined animate-pulse text-[var(--text-secondary)]" aria-hidden="true">progress_activity</span>
                <span className="max-w-[160px] truncate" title={uploadingDocumentName}>{uploadingDocumentName}</span>
              </div>
            )}
            {documents.map((document) => (
              <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border-default)] bg-[var(--surface-secondary)] px-3 py-1.5 text-xs text-[var(--text-primary)]" key={document.id}>
                <span className="material-symbols-outlined text-[var(--text-secondary)]" aria-hidden="true">{getDocumentTypeIcon(document.type_fichier)}</span>
                <span className="max-w-[160px] truncate" title={document.titre}>{document.titre}</span>
                <span className={`material-symbols-outlined ${getDocumentStatusColor(document.statut_indexation)}`} aria-hidden="true">{getDocumentStatusIcon(document.statut_indexation)}</span>
                <button type="button" aria-label={`Supprimer le document ${document.titre}`} onClick={() => void handleDeleteDocument(document.id, document.titre)} className="text-[var(--text-secondary)] hover:text-[var(--primary)]" title={`Supprimer le document ${document.titre}`}>
                  <span className="material-symbols-outlined" aria-hidden="true">delete</span>
                </button>
                {user?.role === 'professeur' && (
                  <button type="button" aria-label={`Visibilité du document ${document.titre}`} onClick={() => void handleVisibilityToggle(document)} className="text-[var(--text-secondary)] hover:text-[var(--primary)]" title={`Visibilité du document ${document.titre}`}>
                    <span className="material-symbols-outlined" aria-hidden="true">{document.visibilite === 'prive' ? 'lock' : 'group'}</span>
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {documentsError && (
          <div className="mx-auto mb-3 w-full max-w-3xl rounded-[12px] border border-[var(--border-default)] bg-[var(--surface-secondary)] p-3 text-sm leading-5 text-[var(--text-secondary)]" role="alert">
            {documentsError}
          </div>
        )}

        {feedbackError && <p className="mx-auto mb-2 w-full max-w-3xl text-right text-xs text-[var(--text-secondary)]" role="status">{feedbackError}</p>}

        {guestPromptVisible && !user && (
          <div className="mx-auto mb-3 flex w-full max-w-3xl flex-wrap items-center justify-between gap-3 rounded-[12px] border border-[var(--border-default)] bg-[var(--surface)] p-4" role="alert">
            <p className="text-sm leading-5 text-[var(--text-primary)]">Créez un compte pour envoyer vos documents et recevoir des réponses de Dexter.</p>
            <div className="flex items-center gap-3">
              <button type="button" className="rounded-[8px] bg-[var(--primary-container)] px-3 py-2 text-sm font-semibold text-white" onClick={() => navigate('/register')}>Créer un compte</button>
              <button type="button" className="text-sm font-semibold text-[var(--primary)] hover:underline" onClick={() => navigate('/login')}>J’ai déjà un compte</button>
            </div>
          </div>
        )}

        <form className="relative mx-auto flex w-full max-w-3xl items-end gap-2 rounded-[12px] border border-[var(--border-default)] bg-[var(--surface)] p-2 focus-within:border-[var(--primary)] focus-within:ring-1 focus-within:ring-[var(--primary)]" onSubmit={handleSubmit}>
          <button type="button" className="shrink-0 px-3 pb-3 text-[var(--text-secondary)] disabled:cursor-not-allowed disabled:opacity-50" aria-label="Joindre un document" aria-haspopup="menu" aria-expanded={attachMenuOpen} title={!user ? 'Connectez-vous pour joindre des documents à vos échanges' : uploadingDocumentName ? 'Upload en cours' : 'Joindre un document'} disabled={uploadingDocumentName !== null} onClick={() => setAttachMenuOpen((isOpen) => !isOpen)}>
            <span className="material-symbols-outlined" aria-hidden="true">attach_file</span>
          </button>
          {attachMenuOpen && <AttachMenu onFilesSelected={handleFilesSelected} onClose={() => setAttachMenuOpen(false)} />}
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
