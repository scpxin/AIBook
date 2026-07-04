import { apiPost, apiPostLong } from './client'

export async function inspirationTitleApi(data: {
  endpoint: string
  apiKey: string
  model: string
  userInput?: string
  styleProfile?: string
}): Promise<{ options: any[] }> {
  return apiPostLong('/api/novel/inspiration/title', data)
}

export async function inspirationDescriptionApi(data: {
  endpoint: string
  apiKey: string
  model: string
  title: string
  userInput?: string
  styleProfile?: string
}): Promise<{ options: any[] }> {
  return apiPostLong('/api/novel/inspiration/description', data)
}

export async function inspirationThemeApi(data: {
  endpoint: string
  apiKey: string
  model: string
  title: string
  description: string
  styleProfile?: string
}): Promise<{ options: any[] }> {
  return apiPostLong('/api/novel/inspiration/theme', data)
}

export async function inspirationGenreApi(data: {
  endpoint: string
  apiKey: string
  model: string
  title: string
  description: string
  styleProfile?: string
}): Promise<{ options: any[] }> {
  return apiPostLong('/api/novel/inspiration/genre', data)
}

export async function worldbuildingApi(data: {
  endpoint: string
  apiKey: string
  model: string
  title: string
  theme: string
  genre: string
  description: string
  styleProfile?: string
}): Promise<any> {
  return apiPostLong('/api/novel/worldbuilding', data)
}

export async function charactersApi(data: {
  endpoint: string
  apiKey: string
  model: string
  worldData: any
  theme: string
  genre: string
  count: number
  styleProfile?: string
}): Promise<{ characters: any[] }> {
  return apiPostLong('/api/novel/characters', data)
}

export async function outlineApi(data: {
  endpoint: string
  apiKey: string
  model: string
  title: string
  theme: string
  genre: string
  charactersInfo: string
  chapterCount: number
  narrativePerspective: string
  styleProfile?: string
}): Promise<{ outline: any[] }> {
  return apiPostLong('/api/novel/outline', data)
}

export async function generateChapterApi(data: {
  endpoint: string
  apiKey: string
  model: string
  projectTitle: string
  genre: string
  chapterNumber: number | string
  chapterTitle: string
  chapterOutline: string
  continuationPoint?: string
  previousChapterSummary?: string
  chapterCharacters?: string
  targetWordCount: number
  narrativePerspective: string
  useCraft?: boolean
}): Promise<{ content: string }> {
  const path = data.useCraft ? '/api/novel/craft/chapter' : '/api/novel/chapter'
  return apiPostLong(path, data)
}

export async function analyzeStyleApi(data: {
  endpoint: string
  apiKey: string
  model: string
  content: string
}): Promise<{ result: string }> {
  return apiPostLong('/api/novel/analyze-style', data)
}

export async function stepSummarySaveApi(data: {
  projectId: string
  step: string
  summary: any
}): Promise<{ ok: true }> {
  return apiPost('/api/step-summary/save', data)
}

export async function stepSummaryGetApi(projectId: string): Promise<{ summaries: Record<string, any> }> {
  return apiPost('/api/step-summary/get', { projectId })
}

export async function aiAnalyzeApi(data: {
  endpoint: string
  apiKey: string
  model: string
  content: string
}): Promise<{ result: string }> {
  return apiPostLong('/api/ai/analyze', data)
}

export async function aiGenerateApi(data: {
  endpoint: string
  apiKey: string
  model: string
  styleProfile: string
  genre: string
  count: number
  protagonist: string
  world: string
  outline: string
}): Promise<{ result: string }> {
  return apiPostLong('/api/ai/generate', data)
}

export async function testConnectionApi(data: {
  endpoint: string
  apiKey: string
  model: string
}): Promise<{ ok: boolean; error?: string; response?: string }> {
  return apiPost('/api/ai/test-connection', data)
}
