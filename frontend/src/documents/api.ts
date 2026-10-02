import axios from 'axios'
import type { DocumentRead, DocumentVisibility } from './types'

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function listConversationDocuments(conversationId: number): Promise<DocumentRead[]> {
  const response = await axios.get<DocumentRead[]>(`${apiUrl}/conversations/${conversationId}/documents`)
  return response.data
}

export async function uploadDocument(conversationId: number, file: File): Promise<DocumentRead> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await axios.post<DocumentRead>(`${apiUrl}/conversations/${conversationId}/documents`, formData)
  return response.data
}

export async function updateDocumentVisibility(documentId: number, visibilite: DocumentVisibility): Promise<DocumentRead> {
  const response = await axios.patch<DocumentRead>(`${apiUrl}/documents/${documentId}/visibility`, { visibilite })
  return response.data
}

export async function deleteDocument(documentId: number): Promise<void> {
  await axios.delete(`${apiUrl}/documents/${documentId}`)
}
