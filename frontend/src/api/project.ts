import { apiPost, apiGet } from './client'
import type { Project } from './client'

export async function saveProjectApi(data: {
  id?: string
  name: string
  step: number
  data: any
  tags?: string
}): Promise<{ ok: true; id: string; name: string; updated_at: string }> {
  return apiPost('/api/projects/save', data)
}

export async function listProjectsApi(): Promise<{ projects: Project[] }> {
  return apiGet('/api/v2/projects/list')
}

export async function loadProjectApi(id: string): Promise<any> {
  return apiPost('/api/projects/load', { id })
}

export async function deleteProjectApi(id: string): Promise<{ ok: true }> {
  return apiPost('/api/projects/delete', { id })
}

// ==================== V2 项目全量保存/加载 ====================

export async function saveV2Project(data: {
  id?: string
  name: string
  modules: Record<string, any>
  pipeline: any
  templateSelections?: Record<string, string>
  sharedContext?: Record<string, any>
  expectedUpdatedAt?: string
}): Promise<{ ok: true; id: string; name: string; updated_at: string; failedModules?: string[] }> {
  return apiPost('/api/projects/save-v2', data)
}

export async function loadV2Project(id: string): Promise<{
  id: string
  name: string
  updated_at: string
  modules: Record<string, any>
  pipeline: any
  templateSelections: Record<string, string>
  sharedContext: Record<string, any>
}> {
  return apiPost('/api/projects/load-v2', { id })
}

// 5.4-2: Soft delete (move to recycle bin)
export async function softDeleteV2Project(id: string): Promise<{ ok: true }> {
  return apiPost('/api/v2/projects/soft-delete', { project_id: id })
}

// 5.4-2: Restore from recycle bin
export async function restoreV2Project(id: string): Promise<{ ok: true }> {
  return apiPost('/api/v2/projects/restore', { project_id: id })
}
