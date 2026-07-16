export type Source = { document_id: string; candidate_name: string; page: number; excerpt: string }
export type Message = { id?: string; role: 'user' | 'assistant'; content: string; sources: Source[]; created_at?: string }
export type Conversation = { id: string; title: string; created_at: string; updated_at: string }
const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export function documentPreviewUrl(documentId: string, page: number) {
  return `${API}/api/v1/documents/${encodeURIComponent(documentId)}/file#page=${page}`
}

export function documentDownloadUrl(documentId: string) {
  return `${API}/api/v1/documents/${encodeURIComponent(documentId)}/file?download=true`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers } })
  const body = await response.json()
  if (!response.ok) throw new Error(body.error?.message ?? 'Something went wrong')
  return body as T
}
export async function createConversation() { return request<{id: string}>('/api/v1/conversations', { method: 'POST' }) }
export async function listConversations() { return request<{conversations: Conversation[]}>('/api/v1/conversations') }
export async function getMessages(id: string) { return request<{messages: Message[]}>(`/api/v1/conversations/${id}/messages`) }
export async function ask(id: string, question: string, signal?: AbortSignal) { return request<{answer: string; sources: Source[]}>(`/api/v1/conversations/${id}/messages`, { method: 'POST', body: JSON.stringify({ question }), signal }) }
