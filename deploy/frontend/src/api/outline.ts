import { apiPost } from './client'

export async function saveOutlineApi(data: {
  projectId: string
  chapterNumber: number
  title: string
  summary: string
  scenes?: any
  characters?: any
  key_points?: any
  emotion?: string
  goal?: string
  techniqueFocus?: string
  bookOverview?: string
  chapterHook?: string
  acts?: any
  status?: string
}): Promise<{ ok: true }> {
  return apiPost('/api/outline/save', data)
}

export async function getOutlinesApi(projectId: string): Promise<any> {
  return apiPost('/api/outline/get', { projectId })
}

export async function deleteOutlineApi(projectId: string, chapterNumber: number): Promise<{ ok: true }> {
  return apiPost('/api/outline/delete', { projectId, chapterNumber })
}
