const API_PREFIX = import.meta.env.VITE_API_PREFIX || ''

const pendingRequests = new Map<string, AbortController>()

export function cancelPendingRequest(key: string) {
  const ctrl = pendingRequests.get(key)
  if (ctrl) {
    ctrl.abort()
    pendingRequests.delete(key)
  }
}

export function cancelAllPendingRequests() {
  for (const ctrl of pendingRequests.values()) {
    ctrl.abort()
  }
  pendingRequests.clear()
}

export interface ApiResponse<T = any> {
  data: T
  error?: string
}

function withPrefix(path: string): string {
  if (path.startsWith('/fanqie/')) return path
  if (path.startsWith('/api/')) return API_PREFIX + path
  return path
}


function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, c) => c.toUpperCase())
}

const _preserveKeys = new Set(['modules'])
function shouldConvertKey(_key: string, parentKey: string | null): boolean {
  if (parentKey && _preserveKeys.has(parentKey)) return false
  return true
}

function convertKeys(obj: any, parentKey: string | null = null): any {
  if (Array.isArray(obj)) return obj.map(i => convertKeys(i, parentKey))
  if (obj && typeof obj === 'object') {
    const out: any = {}
    for (const k of Object.keys(obj)) {
      const newKey = shouldConvertKey(k, parentKey) ? snakeToCamel(k) : k
      out[newKey] = convertKeys(obj[k], k)
    }
    return out
  }
  return obj
}

export async function apiGet<T>(path: string, params: Record<string, string> = {}, timeout = 30000): Promise<T> {
  let url = withPrefix(path)
  const qs = Object.keys(params)
    .map(k => encodeURIComponent(k) + '=' + encodeURIComponent(params[k]))
    .join('&')
  if (qs) url += (url.includes('?') ? '&' : '?') + qs
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)
  try {
    const r = await fetch(url, { signal: controller.signal })
    if (!r.ok) {
      const d = await r.json().catch(() => ({}))
      throw new ApiError(formatError(d.error || d.detail || '请求失败 (HTTP ' + r.status + ')', r.status), r.status, d)
    }
    return convertKeys(await r.json())
  } catch (e: any) {
    if (e instanceof ApiError) throw e
    if (e.name === 'AbortError') throw new ApiError('请求超时，请检查网络连接', 0)
    throw new ApiError('网络错误: ' + (e.message || '无法连接到服务器'), 0)
  } finally {
    clearTimeout(timer)
  }
}

export async function apiPost<T>(path: string, data: any, timeout = 120000, dedupKey?: string): Promise<T> {
  if (dedupKey) {
    cancelPendingRequest(dedupKey)
  }
  const controller = new AbortController()
  if (dedupKey) {
    pendingRequests.set(dedupKey, controller)
  }
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
        const msg = r.status === 429 ? 'AI服务响应限流，请稍候重试（约30秒后恢复）' : formatError(d.error || d.detail || '操作失败 (HTTP ' + r.status + ')', r.status)
        throw new ApiError(msg, r.status, d)
      } catch (e: any) {
        if (e instanceof ApiError) throw e
        const msg = r.status === 429 ? 'AI服务响应限流，请稍候重试（约30秒后恢复）' : formatError('操作失败 (HTTP ' + r.status + '): ' + text.slice(0, 200), r.status)
        throw new ApiError(msg, r.status)
      }
    }
    return convertKeys(await r.json())
  } catch (e: any) {
    if (e instanceof ApiError) throw e
    if (e.name === 'AbortError') throw new ApiError('请求超时，请稍后重试或缩小数据量', 0)
    throw new ApiError('网络错误: ' + (e.message || '无法连接到服务器'), 0)
  } finally {
    clearTimeout(timer)
    if (dedupKey) pendingRequests.delete(dedupKey)
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

function statusMessage(status: number): string {
  switch (status) {
    case 400: return '请求参数有误'
    case 401: return '未登录或登录已过期'
    case 403: return '没有操作权限'
    case 404: return '资源不存在'
    case 422: return '数据校验失败'
    case 429: return '请求过于频繁，请稍后重试'
    case 500: return '服务器内部错误'
    case 502: return '上游服务不可用'
    case 503: return '服务暂时不可用'
    case 504: return '上游服务超时'
    default: return ''
  }
}

function formatError(msg: string, status: number): string {
  const prefix = statusMessage(status)
  if (prefix && !msg.includes(prefix)) return prefix + '：' + msg
  return msg
}

export async function apiPostLong<T>(path: string, data: any): Promise<T> {
  return apiPost<T>(path, data, 600000)
}

export async function apiPut<T>(path: string, data: any, timeout = 120000): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)
  try {
    const r = await fetch(withPrefix(path), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      signal: controller.signal,
    })
    if (!r.ok) {
      const text = await r.text()
      try {
        const d = JSON.parse(text)
        throw new ApiError(formatError(d.error || d.detail || '操作失败 (HTTP ' + r.status + ')', r.status), r.status, d)
      } catch (e: any) {
        if (e instanceof ApiError) throw e
        throw new ApiError(formatError('操作失败 (HTTP ' + r.status + '): ' + text.slice(0, 200), r.status), r.status)
      }
    }
    return convertKeys(await r.json())
  } catch (e: any) {
    if (e instanceof ApiError) throw e
    if (e.name === 'AbortError') throw new ApiError('请求超时，请稍后重试', 0)
    throw new ApiError('网络错误: ' + (e.message || '无法连接到服务器'), 0)
  } finally {
    clearTimeout(timer)
  }
}

export async function apiDelete<T>(path: string, timeout = 120000): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)
  try {
    const r = await fetch(withPrefix(path), {
      method: 'DELETE',
      signal: controller.signal,
    })
    if (!r.ok) {
      const text = await r.text()
      try {
        const d = JSON.parse(text)
        throw new ApiError(formatError(d.error || d.detail || '操作失败 (HTTP ' + r.status + ')', r.status), r.status, d)
      } catch (e: any) {
        if (e instanceof ApiError) throw e
        throw new ApiError(formatError('操作失败 (HTTP ' + r.status + '): ' + text.slice(0, 200), r.status), r.status)
      }
    }
    return convertKeys(await r.json())
  } catch (e: any) {
    if (e instanceof ApiError) throw e
    if (e.name === 'AbortError') throw new ApiError('请求超时，请稍后重试', 0)
    throw new ApiError('网络错误: ' + (e.message || '无法连接到服务器'), 0)
  } finally {
    clearTimeout(timer)
  }
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
  step?: number
  updated_at: string
  created_at?: string
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
