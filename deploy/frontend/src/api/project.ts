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
  return apiPost('/api/projects/list', {})
}

export async function loadProjectApi(id: string): Promise<any> {
  return apiPost('/api/projects/load', { id })
}

export async function deleteProjectApi(id: string): Promise<{ ok: true }> {
  return apiPost('/api/projects/delete', { id })
}
