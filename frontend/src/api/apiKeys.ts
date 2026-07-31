import { apiDelete, apiGet, apiPost } from './client'

export interface ApiKeyRecord {
  id: number
  name: string
  description: string
  keyHash: string
  isActive: boolean
  createdAt: string
  expiresAt: string | null
  lastUsedAt: string | null
}

export interface ApiKeyCreateResult extends ApiKeyRecord {
  rawKey?: string
}

export interface ApiKeyCreatePayload {
  name: string
  description?: string
}

export function createApiKey(data: ApiKeyCreatePayload): Promise<ApiKeyCreateResult> {
  return apiPost<ApiKeyCreateResult>('/api/api-keys', data)
}

export function listApiKeys(activeOnly = false): Promise<ApiKeyRecord[]> {
  return apiGet<ApiKeyRecord[]>('/api/api-keys', activeOnly ? { active_only: 'true' } : {})
}

export function revokeApiKey(id: number): Promise<void> {
  return apiDelete<void>(`/api/api-keys/${id}`)
}
