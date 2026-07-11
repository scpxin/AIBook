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
  try {
    const r = await fetch(url)
    if (!r.ok) {
      const d = await r.json().catch(() => ({}))
      throw new ApiError(d.error || d.detail || '请求失败 (HTTP ' + r.status + ')', r.status, d)
    }
    return r.json()
  } catch (e: any) {
    if (e instanceof ApiError) throw e
    if (e.name === 'AbortError') throw new ApiError('请求超时，请检查网络连接', 0)
    throw new ApiError('网络错误: ' + (e.message || '无法连接到服务器'), 0)
  }
}

export async function apiPost<T>(path: string, data: any, timeout = 120000): Promise<T> {
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
        throw new ApiError(d.error || d.detail || '操作失败 (HTTP ' + r.status + ')', r.status, d)
      } catch (e: any) {
        if (e instanceof ApiError) throw e
        throw new ApiError('操作失败 (HTTP ' + r.status + '): ' + text.slice(0, 200), r.status)
      }
    }
    return r.json()
  } catch (e: any) {
    if (e instanceof ApiError) throw e
    if (e.name === 'AbortError') throw new ApiError('请求超时，请稍后重试或缩小数据量', 0)
    throw new ApiError('网络错误: ' + (e.message || '无法连接到服务器'), 0)
  } finally {
    clearTimeout(timer)
  }
}

export class ApiError extends Error {
  status: number
  detail: any
  constructor(message: string, status: number = 0, detail: any = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
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
