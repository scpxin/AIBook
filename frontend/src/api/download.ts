import { apiGet, apiPost, apiPostLong } from './client'
import type { SavedBook } from './client'

export async function searchBooks(q: string): Promise<{ books: any[] }> {
  return apiGet('/api/search', { q })
}

export async function resolveBook(q: string): Promise<{ book_id: string; count: number; title: string; author: string }> {
  return apiGet('/api/resolve', { q })
}

export async function directoryApi(bookId: string): Promise<{ total: number; ids: string[] }> {
  return apiGet('/api/directory', { book_id: bookId })
}

export async function downloadStart(bookId: string, title: string): Promise<{ session_id: string }> {
  return apiGet('/api/download/start', { book_id: bookId, title })
}

export async function downloadStatus(sessionId: string): Promise<{
  status: string
  total: number
  current: number
  elapsed: number
}> {
  return apiGet('/api/download/status', { session_id: sessionId })
}

export async function downloadPause(sessionId: string): Promise<{ ok: true }> {
  return apiGet('/api/download/pause', { session_id: sessionId })
}

export async function downloadResume(sessionId: string): Promise<{ ok: true }> {
  return apiGet('/api/download/resume', { session_id: sessionId })
}

export function downloadFileUrl(sessionId: string): string {
  return `/api/download/file?session_id=${sessionId}`
}

export async function listSavedBooks(): Promise<{ books: SavedBook[] }> {
  return apiGet('/api/downloads/list', {})
}

export async function getBookContent(bookId: string): Promise<{ content: string; length: number }> {
  return apiGet('/api/downloads/content', { book_id: bookId })
}

export async function craftDetectApi(data: {
  endpoint: string
  apiKey: string
  model: string
  content: string
}): Promise<any> {
  return apiPostLong('/api/novel/craft/detect-ai', data)
}

export async function craftFixApi(data: {
  endpoint: string
  apiKey: string
  model: string
  content: string
  issues: any[]
}): Promise<{ content: string }> {
  return apiPostLong('/api/novel/craft/fix-ai', data)
}

export async function craftGoldenThreeApi(data: {
  endpoint: string
  apiKey: string
  model: string
  content: string
}): Promise<any> {
  return apiPostLong('/api/novel/craft/golden-three', data)
}

export async function craftQualityScoreApi(data: {
  endpoint: string
  apiKey: string
  model: string
  content: string
  title?: string
  genre?: string
}): Promise<any> {
  return apiPostLong('/api/novel/craft/quality-score', data)
}
