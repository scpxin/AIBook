import { apiGet, apiPost } from './client'
import type { ModelConfig } from './client'

export interface SettingsData {
  models?: ModelConfig[]
  activeModelId?: string
  [key: string]: any
}

export function getSettings(): Promise<SettingsData> {
  return apiGet<SettingsData>('/api/v2/settings')
}

export function saveModelSettings(models: ModelConfig[], activeModelId: string) {
  return apiPost<{ ok: boolean; count: number }>('/api/v2/settings/models', {
    models,
    activeModelId,
  })
}
