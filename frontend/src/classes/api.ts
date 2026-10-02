import axios from 'axios'
import type { ClassCreatePayload, ClassJoinPayload, ClassJoinResponse, ClassRead, ClassReadStudent } from './types'

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function listClasses(): Promise<Array<ClassRead | ClassReadStudent>> {
  const response = await axios.get<Array<ClassRead | ClassReadStudent>>(`${apiUrl}/classes`)
  return response.data
}

export async function createClass(payload: ClassCreatePayload): Promise<ClassRead> {
  const response = await axios.post<ClassRead>(`${apiUrl}/classes`, payload)
  return response.data
}

export async function joinClassByCode(payload: ClassJoinPayload): Promise<ClassJoinResponse> {
  const response = await axios.post<ClassJoinResponse>(`${apiUrl}/classes/join`, payload)
  return response.data
}
