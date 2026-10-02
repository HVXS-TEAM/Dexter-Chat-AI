import axios from 'axios'

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface ConversationRead {
  id: number
  user_id: number
  titre: string
  referentiel_actif: string | null
  resume_md: string | null
  created_at: string
  updated_at: string
}

export async function createConversation(payload: { titre?: string } = {}): Promise<ConversationRead> {
  const response = await axios.post<ConversationRead>(`${apiUrl}/conversations`, payload)
  return response.data
}

export async function setMessageFeedback(messageId: number, feedback: 'up' | 'down'): Promise<void> {
  await axios.patch(`${apiUrl}/messages/${messageId}/feedback`, { feedback })
}