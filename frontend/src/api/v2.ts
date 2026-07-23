// V2 API Service Layer — 所有19模块的API函数
import { apiPost, apiGet, apiPostLong, apiStream, apiPut, apiDelete } from './client'
import type {
  IdeaCandidate, IdeaScore, IdeaUpgrade, RiskAnalysis, IdeaTemplate,
  PlatformCompatibility,
  WorldBuilding, WorldOrigin, WorldRule, WorldConsistencyCheck,
  Character, RelationMap, CharacterConsistencyCheck,
  StoryMaster, VolumeOutline,
  PowerSystem, Faction, Timeline, MasterOutline,
  VolumeDetail, PlotEventDetail, ChapterPlan, ChapterOutline,
  SceneSkeleton, Draft, DraftStreamChunk,
  PolishResult, ContentParseResult,
  KnowledgeState, ConsistencyReport,
  PipelineProgress, ModuleInfo,
} from '../types/v2'

// ========== M1: 灵感 ==========

export function generateIdeas(projectId: string, userInput: string, genreHint?: string, count?: number) {
  return apiPostLong<{ ideas: IdeaCandidate[]; projectId: string }>('/api/v2/ideas/generate', {
    project_id: projectId, user_input: userInput, genre_hint: genreHint, count: count || 5,
  })
}

export function scoreIdeas(projectId: string, ideas: IdeaCandidate[]) {
  return apiPost<{ scoredIdeas: IdeaScore[] }>('/api/v2/ideas/score', {
    project_id: projectId, ideas,
  })
}

export function upgradeIdeas(projectId: string, ideas: IdeaCandidate[]) {
  return apiPost<{ upgraded: IdeaUpgrade[] }>('/api/v2/ideas/upgrade', {
    project_id: projectId, ideas,
  })
}

export function analyzeIdeaRisks(projectId: string, concept: string, extra?: any) {
  return apiPost<RiskAnalysis>('/api/v2/ideas/analyze-risks', {
    project_id: projectId, concept, extra: extra || {},
  })
}

// ========== 灵感离线模板 ==========

export function getTemplates(projectId: string) {
  return apiGet<{ templates: IdeaTemplate[] }>(`/api/v2/templates/${projectId}`)
}

export function createTemplate(data: { project_id: string; name: string; icon?: string; genre: string; prompt: string; reference?: string }) {
  return apiPost<{ ok: boolean; template: IdeaTemplate }>('/api/v2/templates/', data)
}

export function updateTemplate(id: string | number, data: Partial<{ name: string; icon: string; genre: string; prompt: string; reference: string }>) {
  return apiPut<{ ok: boolean; template: IdeaTemplate }>(`/api/v2/templates/${id}`, data)
}

export function deleteTemplate(id: string | number) {
  return apiDelete<{ ok: boolean }>(`/api/v2/templates/${id}`)
}

// ========== M2: 项目定位 ==========

export function analyzeProjectBatch(projectId: string, idea: string, platform: string, batchIndex: number) {
  return apiPost<{ dimensions: any[]; _batch_index: number; _total_batches: number }>(
    '/api/v2/projects/analyze-batch',
    { project_id: projectId, idea, platform, batch_index: batchIndex },
    120000
  )
}

export function checkProjectCompatibility(projectId: string, idea: string, platform?: string) {
  return apiPost<PlatformCompatibility>('/api/v2/projects/check-compatibility', {
    project_id: projectId, idea, platform: platform || 'tomato',
  })
}

export function deriveProjectFields(projectId: string, idea: string) {
  return apiPost<any>('/api/v2/projects/derive-fields', {
    project_id: projectId, idea,
  })
}

// ========== M3: 世界观 ==========

export function generateWorldOrigin(projectId: string, idea: string, genre?: string) {
  return apiPost<WorldOrigin>('/api/v2/world/origin', {
    project_id: projectId, idea, genre: genre || '',
  }, 300000)
}

export function generateWorldRules(projectId: string, origin: any, powerSystem?: any) {
  return apiPost<{ rules: WorldRule[]; metaRule: string }>('/api/v2/world/rules', {
    project_id: projectId, origin, power_system: powerSystem,
  }, 300000)
}

export function generateWorldStructure(projectId: string, origin: any) {
  return apiPost<any>('/api/v2/world/structure', {
    project_id: projectId, origin,
  }, 300000)
}

export function generateWorldCivilization(projectId: string, structure: any) {
  return apiPost<any>('/api/v2/world/civilization', {
    project_id: projectId, structure,
  }, 300000)
}

export function generateWorldHistory(projectId: string, structure: any, civilization: any) {
  return apiPost<any>('/api/v2/world/history', {
    project_id: projectId, structure, civilization,
  }, 300000)
}

export function checkWorldConsistency(projectId: string, worldData: any) {
  return apiPost<WorldConsistencyCheck>('/api/v2/world/check-consistency', {
    project_id: projectId, world_data: worldData,
  })
}

export function saveWorld(projectId: string, worldData: any) {
  return apiPost<{ saved: boolean }>('/api/v2/world/save', {
    project_id: projectId, world_data: worldData,
  })
}

// ========== M4: 角色 ==========

export function generateProtagonist(projectId: string, worldRules: any, storyConcept?: string) {
  return apiPost<Character>('/api/v2/characters/protagonist', {
    project_id: projectId, world_rules: worldRules, story_concept: storyConcept || '',
  }, 300000)
}

export function generateSupporting(projectId: string, protagonist: any, count?: number) {
  return apiPost<{ characters: Character[] }>('/api/v2/characters/supporting', {
    project_id: projectId, protagonist, count: count || 5,
  }, 300000)
}

export function generateAntagonists(projectId: string, protagonist: any, world: any) {
  return apiPost<any>('/api/v2/characters/antagonists', {
    project_id: projectId, protagonist, world,
  }, 300000)
}

export function generateRelations(projectId: string, characters: Character[]) {
  return apiPost<RelationMap>('/api/v2/characters/relations', {
    project_id: projectId, characters,
  }, 300000)
}

export function checkCharacterConsistency(projectId: string, characters: Character[]) {
  return apiPost<CharacterConsistencyCheck>('/api/v2/characters/check-consistency', {
    project_id: projectId, characters,
  })
}

// ========== M5: 故事 ==========

export function generateStoryMaster(projectId: string, protagonist: any, world: any, characters: Character[]) {
  return apiPost<StoryMaster>('/api/v2/story/master', {
    project_id: projectId, protagonist, world, characters,
  }, 300000)
}

export function generateStoryVolumes(projectId: string, masterStory: any, volumeCount?: number) {
  return apiPost<{ volumes: VolumeOutline[] }>('/api/v2/story/volumes', {
    project_id: projectId, master_story: masterStory, volume_count: volumeCount || 5,
  }, 300000)
}

export function checkStoryConsistency(projectId: string, storyData: any, characters: Character[]) {
  return apiPost<any>('/api/v2/story/check-consistency', {
    project_id: projectId, story_data: storyData, characters,
  })
}

// ========== M9: 全书大纲 ==========

export function generateMasterOutline(projectId: string, storySystem: any) {
  return apiPost<MasterOutline>('/api/v2/outline/master', {
    project_id: projectId, story_system: storySystem,
  }, 300000)
}

export function saveMasterOutline(projectId: string, data: any) {
  return apiPost<{ saved: boolean }>('/api/v2/outline/save', {
    project_id: projectId, data,
  })
}

// ========== M10: 卷纲 ==========

export function generateVolume(projectId: string, volumeNo: number, masterOutline: any) {
  return apiPost<VolumeDetail>('/api/v2/volumes/generate', {
    project_id: projectId, volume_no: volumeNo, master_outline: masterOutline,
  }, 300000)
}

export function generateVolumes(projectId: string, count: number, masterOutline: any) {
  return apiPost<any>('/api/v2/volumes/generate-batch', {
    project_id: projectId, count, master_outline: masterOutline,
  }, 300000)
}

export function saveVolume(projectId: string, volumeNo: number, data: any) {
  return apiPost<{ saved: boolean }>('/api/v2/volumes/save', {
    project_id: projectId, volume_no: volumeNo, data,
  })
}

// ========== M11: 剧情节点 ==========

export function generatePlotNodes(projectId: string, chapterPlan: any, masterOutline: any) {
  return apiPost<{ events: PlotEventDetail[] }>('/api/v2/plot-nodes/generate', {
    project_id: projectId, chapter_plan: chapterPlan, master_outline: masterOutline,
  }, 300000)
}

export function savePlotNode(projectId: string, eventId: string, data: any) {
  return apiPost<{ saved: boolean }>('/api/v2/plot-nodes/save', {
    project_id: projectId, event_id: eventId, data,
  })
}

// ========== M12: 章节规划 ==========

export function planChapters(projectId: string, masterOutline: any, plotEvents: any[], targetWordcount?: number) {
  return apiPost<any>('/api/v2/chapters/plan', {
    project_id: projectId, master_outline: masterOutline, plot_events: plotEvents,
    target_wordcount: targetWordcount || 2000,
  }, 300000)
}

export function saveChapterPlan(projectId: string, chapterNo: number | string, data: any) {
  return apiPost<{ saved: boolean }>('/api/v2/chapters/plan-save', {
    project_id: projectId, chapter_no: chapterNo, data,
  })
}

// ========== M13: 章节细纲 ==========

export function generateChapterOutline(projectId: string, chapterNo: number | string, chapterPlan: any) {
  return apiPost<ChapterOutline>('/api/v2/chapters/outline', {
    project_id: projectId, chapter_no: chapterNo, chapter_plan: chapterPlan,
  }, 300000)
}

export function generateChapterOutlines(projectId: string, totalChapters: number, chapterPlan: any) {
  return apiPost<any>('/api/v2/chapters/outline-batch', {
    project_id: projectId, total_chapters: totalChapters, chapter_plan: chapterPlan,
  }, 300000)
}

export function saveChapterOutline(projectId: string, chapterNo: number | string, data: any) {
  return apiPost<{ saved: boolean }>('/api/v2/chapters/outline-save', {
    project_id: projectId, chapter_no: chapterNo, data,
  })
}

// ========== M14: 场景设计 ==========

export function designScenes(projectId: string, chapterOutline: any) {
  return apiPost<{ scenes: SceneSkeleton[] }>('/api/v2/scenes/design', {
    project_id: projectId, chapter_outline: chapterOutline,
  }, 180000)
}

export function saveScene(projectId: string, sceneId: string, data: any) {
  return apiPost<{ saved: boolean }>('/api/v2/scenes/save', {
    project_id: projectId, scene_id: sceneId, data,
  })
}

// ========== M15: 正文生成 (流式) ==========

export function generateDraft(
  projectId: string,
  chapterNo: string,
  sceneSkeleton: any,
  onChunk?: (text: string) => void,
  onDone?: () => void,
  onError?: (err: string) => void
): Promise<void> {
  let buffer = ''
  return apiStream('/api/v2/draft/generate', {
    project_id: projectId,
    chapter_no: chapterNo,
    scene_skeleton: sceneSkeleton,
  }, (rawText: string) => {
    buffer += rawText
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const msg = JSON.parse(line.substring(6))
          if (msg.type === 'chunk' && msg.content) {
            onChunk?.(msg.content)
          } else if (msg.type === 'error') {
            onError?.(msg.message || '生成失败')
          }
        } catch {}
      }
    }
  }, onDone, onError)
}

export function saveDraft(projectId: string, chapterNo: string, content: string) {
  return apiPost<{ saved: boolean }>('/api/v2/draft/save', {
    project_id: projectId, chapter_no: chapterNo, content,
  })
}

// ========== M16: 润色 ==========

export function polishContent(projectId: string, content: string, focus?: string) {
  return apiPost<PolishResult>('/api/v2/polish', {
    project_id: projectId, content, focus: focus || '整体优化',
  })
}

// ========== M17: 内容解析 ==========

export function parseContent(projectId: string, chapterNo: string, content: string, existing_characters?: any[]) {
  return apiPost<ContentParseResult>('/api/v2/content/parse', {
    project_id: projectId, chapter_no: chapterNo, content, existing_characters,
  })
}

// ========== M18: 知识库 ==========

export function updateKnowledge(projectId: string, chapterNo: string, parseResult: any) {
  return apiPost<{ updated: boolean }>('/api/v2/knowledge/update', {
    project_id: projectId, chapter_no: chapterNo, parse_result: parseResult,
  })
}

export function getKnowledgeSnapshot(projectId: string) {
  return apiGet<KnowledgeState>('/api/v2/knowledge/snapshot', { project_id: projectId })
}

export function getForeshadows(projectId: string, status?: string) {
  return apiGet<{ foreshadows: any[]; count: number }>('/api/v2/knowledge/foreshadows',
    status ? { project_id: projectId, status } : { project_id: projectId }
  )
}

// ========== M19: 一致性 ==========

export function checkConsistency(
  projectId: string,
  chapterNo: string,
  content?: string,
  knowledgeState?: any,
  characters?: Character[],
  world?: any,
  powerSystem?: any
) {
  return apiPost<ConsistencyReport>('/api/v2/consistency/check', {
    project_id: projectId, chapter_no: chapterNo, content,
    knowledge_state: knowledgeState, characters, world, power_system: powerSystem,
  })
}

export function getConsistencyReport(projectId: string, chapterNo?: string) {
  return apiGet<{ reports: ConsistencyReport[]; count: number }>('/api/v2/consistency/report',
    chapterNo ? { project_id: projectId, chapter_no: chapterNo } : { project_id: projectId }
  )
}

// ========== 流水线 ==========

export function getPipelineModules() {
  return apiGet<{ modules: ModuleInfo[]; total: number }>('/api/v2/pipeline/modules')
}

export function getPipelineStatus(projectId: string) {
  return apiGet<PipelineProgress>(`/api/v2/pipeline/${projectId}/status`)
}

export function getNextModule(projectId: string) {
  return apiGet<{ nextModule: string | null; moduleInfo: ModuleInfo | null }>(`/api/v2/pipeline/${projectId}/next`)
}

export function updateModuleStatus(projectId: string, moduleName: string, status: string) {
  return apiPost<{ success: boolean; module: string; status: string }>(
    `/api/v2/pipeline/${projectId}/modules/${moduleName}/status`,
    { status }
  )
}

export function getModuleData(projectId: string, moduleName: string) {
  return apiGet<{ module: string; data: any }>(`/api/v2/pipeline/${projectId}/data/${moduleName}`)
}

export function saveModuleData(projectId: string, moduleName: string, data: any) {
  return apiPost<{ success: boolean }>(`/api/v2/pipeline/${projectId}/data/${moduleName}`, data)
}

import { useModuleSaveStore } from '../stores/moduleSave'

export { useModuleSaveStore }

export async function saveModuleDataTracked(projectId: string, moduleName: string, data: any): Promise<boolean> {
  const store = useModuleSaveStore()
  store.markSaving(projectId, moduleName)
  try {
    await saveModuleData(projectId, moduleName, data)
    store.markSaved(projectId, moduleName)
    return true
  } catch (e: any) {
    store.markError(projectId, moduleName, e?.message || '保存失败')
    throw e
  }
}

export function getAllModuleData(projectId: string) {
  return apiGet<{ project_id: string; modules: Record<string, any> }>(`/api/v2/pipeline/${projectId}/data`)
}

export async function confirmIdea(projectId: string, ideaId: string, version: number = 1) {
  return apiPost<{ success: boolean }>(`/api/v2/pipeline/${projectId}/confirm-idea`, { idea_id: ideaId, version })
}

export async function worldConsistencyCheck(projectId: string) {
  return apiGet<{ passed: boolean; score?: number; issues?: string[]; message?: string }>(`/api/v2/world/${projectId}/consistency-check`)
}

export async function characterConsistencyCheck(projectId: string) {
  return apiGet<{ passed: boolean; score?: number; issues?: string[]; message?: string }>(`/api/v2/character/${projectId}/consistency-check`)
}

export function getDrafts(projectId: string) {
  return apiGet<any[]>(`/api/v2/pipeline/${projectId}/data/draft`)
}

export function testModelConnection(endpoint: string, apiKey: string, model: string) {
  return apiPost<{ ok: boolean; model?: string; response?: string; error?: string }>('/api/v2/settings/test-connection', {
    endpoint, api_key: apiKey, model,
  }, 30000)
}

// ========== 生成模板库（全模块模板复用） ==========

export interface GenerationTemplate {
  id: number
  name: string
  module_key: string
  genre: string
  sub_genre: string
  tone: string
  world_type: string
  target_audience: string
  source_project_id: string
  input_fingerprint: string
  output_data: any
  input_context: any
  entity_refs: any
  compatibility_group: string
  usage_count: number
  quality_rating: number
  is_public: number
  created_at: string
  updated_at: string
}

export function listGenerationTemplates(params: {
  module_key?: string
  genre?: string
  world_type?: string
  compatibility_group?: string
  limit?: number
  offset?: number
} = {}) {
  return apiGet<{ templates: GenerationTemplate[]; total: number }>('/api/v2/generation-templates/', params as any)
}

export function getGenerationTemplate(id: number) {
  return apiGet<{ template: GenerationTemplate }>(`/api/v2/generation-templates/${id}`)
}

export function createGenerationTemplate(data: {
  name: string
  module_key: string
  output_data: any
  input_context?: any
  entity_refs?: any
  compatibility_group?: string
  source_project_id?: string
  genre?: string
  sub_genre?: string
  tone?: string
  world_type?: string
  target_audience?: string
  is_public?: boolean
}) {
  return apiPost<{ ok: boolean; template: GenerationTemplate }>('/api/v2/generation-templates/', data)
}

export function updateGenerationTemplate(id: number, data: Partial<{
  name: string
  genre: string
  sub_genre: string
  tone: string
  world_type: string
  target_audience: string
  quality_rating: number
  is_public: boolean
}>) {
  return apiPut<{ ok: boolean; template: GenerationTemplate }>(`/api/v2/generation-templates/${id}`, data)
}

export function deleteGenerationTemplate(id: number) {
  return apiDelete<{ ok: boolean }>(`/api/v2/generation-templates/${id}`)
}

export function matchGenerationTemplates(data: {
  module_key: string
  project_context: Record<string, string>
  selected_templates: Record<string, string>
}) {
  return apiPost<{
    compatible: { template: GenerationTemplate; score: number; is_compatible: boolean; reason?: string }[]
    incompatible: { template: GenerationTemplate; score: number; is_compatible: boolean; reason?: string }[]
    total_candidates: number
  }>('/api/v2/generation-templates/match', data)
}

export function applyGenerationTemplate(templateId: number, projectId: string) {
  return apiPost<{
    success: boolean
    module: string
    data: any
    applied_as: string
  }>(`/api/v2/generation-templates/${templateId}/apply`, { project_id: projectId })
}

export function rateGenerationTemplate(id: number, rating: number) {
  return apiPost<{ ok: boolean }>(`/api/v2/generation-templates/${id}/rate`, { rating })
}

export function autoSaveGenerationTemplate(data: {
  project_id: string
  module_key: string
  module_data: any
  input_context?: any
  compatibility_group?: string
}) {
  return apiPost<{ ok: boolean; template_id?: number; auto_saved: boolean }>(
    '/api/v2/generation-templates/auto-save', data
  )
}


