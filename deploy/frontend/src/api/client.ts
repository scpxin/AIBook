const API_PREFIX = import.meta.env.VITE_API_PREFIX || ''

export interface ApiResponse<T = any> {
  data: T
  error?: string
}

function withPrefix(path: string): string {
  if (path.startsWith('/fanqie/')) return path
  if (path.startsWith('/api/')) return API_PREFIX + path
  return path
}

export async function apiGet<T>(path: string, params: Record<string, string> = {}): Promise<T> {
  let url = withPrefix(path)
  const qs = Object.keys(params)
    .map(k => encodeURIComponent(k) + '=' + encodeURIComponent(params[k]))
    .join('&')
  if (qs) url += (url.includes('?') ? '&' : '?') + qs
  const r = await fetch(url)
  if (!r.ok) {
    const d = await r.json().catch(() => ({}))
    throw new Error(d.error || 'HTTP ' + r.status)
  }
  return r.json()
}

export async function apiPost<T>(path: string, data: any, timeout = 10000): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)
  try {
    const r = await fetch(withPrefix(path), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      signal: controller.signal,
    })
    if (!r.ok) {
      const text = await r.text()
      try {
        const d = JSON.parse(text)
        throw new Error(d.error || 'HTTP ' + r.status)
      } catch (e: any) {
        if (e?.message && e.message.includes('HTTP')) throw e
        throw new Error('HTTP ' + r.status + ': ' + text.slice(0, 200))
      }
    }
    return r.json()
  } finally {
    clearTimeout(timer)
  }
}

export async function apiPostLong<T>(path: string, data: any): Promise<T> {
  return apiPost<T>(path, data, 600000)
}

export async function apiStream(
  path: string,
  data: any,
  onChunk: (text: string) => void,
  onDone?: () => void,
  onError?: (err: string) => void,
  maxRetries = 1
): Promise<void> {
  let lastErr = ''
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), 600000)
      const r = await fetch(withPrefix(path), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        signal: controller.signal,
      })
      clearTimeout(timer)
      if (!r.ok) {
        const text = await r.text()
        try {
          const d = JSON.parse(text)
          lastErr = d.error || 'HTTP ' + r.status
        } catch {
          lastErr = 'HTTP ' + r.status
        }
        if (attempt < maxRetries) continue
        onError?.(lastErr)
        return
      }
      const reader = r.body!.getReader()
      const decoder = new TextDecoder()
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const text = decoder.decode(value, { stream: true })
        if (text) onChunk(text)
      }
      onDone?.()
      return
    } catch (e: any) {
      lastErr = e.message || String(e)
      if (attempt < maxRetries) await new Promise(r => setTimeout(r, 1000))
    }
  }
  onError?.(lastErr)
}

export interface ModelConfig {
  id: string
  name: string
  endpoint: string
  apiKey: string
  model: string
}

export interface Project {
  id: string
  name: string
  step: number
  updated_at: string
  tags?: string
  category?: string
}

export interface Chapter {
  project_id: string
  chapter_number: number
  title: string
  content: string
  word_count: number
  status: string
  version: number
}

export interface OutlineItem {
  project_id: string
  chapter_number: number
  title: string
  summary: string
  scenes?: any
  characters?: any
  key_points?: any
  emotion?: string
  goal?: string
  technique_focus?: string
  book_overview?: string
  chapter_hook?: string
  acts?: any
  status?: string
}

export interface SavedBook {
  book_id: string
  title: string
  total: number
  size: number
  dir: string
}
