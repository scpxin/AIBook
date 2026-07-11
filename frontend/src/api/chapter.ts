import { apiPost } from './client'

export async function saveChapterApi(data: {
  projectId: string
  chapterNumber: number
  title: string
  content: string
  status: string
  errorMessage?: string
  metadata?: any
}): Promise<{ ok: true }> {
  return apiPost('/api/chapters/save', data)
}

export async function getChaptersApi(projectId: string): Promise<any> {
  return apiPost('/api/chapters/get', { projectId })
}

export async function deleteChapterApi(projectId: string, chapterNumber: number): Promise<{ ok: true }> {
  return apiPost('/api/chapters/delete', { projectId, chapterNumber })
}

export async function startGenerationApi(projectId: string, totalChapters: number): Promise<{ ok: true }> {
  return apiPost('/api/chapters/generation/start', { projectId, totalChapters })
}

export async function pauseGenerationApi(projectId: string): Promise<{ ok: true }> {
  return apiPost('/api/chapters/generation/pause', { projectId })
}

export async function stopGenerationApi(projectId: string): Promise<{ ok: true }> {
  return apiPost('/api/chapters/generation/stop', { projectId })
}

export async function updateGenerationProgressApi(data: {
  projectId: string
  currentChapter: number
  completedChapters?: number
  failedChapters?: number
}): Promise<{ ok: true }> {
  return apiPost('/api/chapters/generation/update', data)
}
