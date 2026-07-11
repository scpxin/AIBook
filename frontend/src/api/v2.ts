// V2 API Service Layer — 所有19模块的API函数
import { apiPost, apiGet, apiPostLong, apiStream } from './client'
import type {
  IdeaCandidate, IdeaScore, IdeaUpgrade, RiskAnalysis,
  NovelPosition, PlatformCompatibility, DerivedFields,
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

// ========== M2: 项目定位 ==========

export function analyzeProject(projectId: string, idea: string, platform?: string) {
  return apiPost<NovelPosition>('/api/v2/projects/analyze', {
    project_id: projectId, idea, platform: platform || 'tomato',
  }, 300000)
}

export function checkProjectCompatibility(projectId: string, idea: string, platform?: string) {
  return apiPost<PlatformCompatibility>('/api/v2/projects/check-compatibility', {
    project_id: projectId, idea, platform: platform || 'tomato',
  })
}

export function deriveProjectFields(projectId: string, projectData: any) {
  return apiPost<DerivedFields>('/api/v2/projects/derive-fields', {
    project_id: projectId, project_data: projectData,
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

// ========== M6: 力量体系 ==========

export function generatePowerSystem(projectId: string, worldRules: any, characterAbilities?: any[]) {
  return apiPost<PowerSystem>('/api/v2/power-system/generate', {
    project_id: projectId, world_rules: worldRules, character_abilities: characterAbilities,
  }, 300000)
}

export function savePowerSystem(projectId: string, data: any) {
  return apiPost<{ saved: boolean }>('/api/v2/power-system/save', {
    project_id: projectId, data,
  })
}

// ========== M7: 势力 ==========

export function generateFactions(projectId: string, civilization: any, characters?: Character[]) {
  return apiPost<{ factions: Faction[]; metaAnalysis: string }>('/api/v2/factions/generate', {
    project_id: projectId, civilization, characters,
  }, 180000)
}

export function saveFactions(projectId: string, factions: Faction[]) {
  return apiPost<{ saved: boolean; count: number }>('/api/v2/factions/save', {
    project_id: projectId, factions,
  })
}

// ========== M8: 时间线 ==========

export function buildTimeline(projectId: string, worldHistory: any, storyEvents: any) {
  return apiPost<Timeline>('/api/v2/timeline/build', {
    project_id: projectId, world_history: worldHistory, story_events: storyEvents,
  }, 300000)
}

export function saveTimeline(projectId: string, data: any) {
  return apiPost<{ saved: boolean }>('/api/v2/timeline/save', {
    project_id: projectId, data,
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

export function getModuleData(projectId: string, moduleName: string) {
  return apiGet<{ module: string; data: any }>(`/api/v2/pipeline/${projectId}/data/${moduleName}`)
}

export function saveModuleData(projectId: string, moduleName: string, data: any) {
  return apiPost<{ success: boolean }>(`/api/v2/pipeline/${projectId}/data/${moduleName}`, data)
}

export function getAllModuleData(projectId: string) {
  return apiGet<{ project_id: string; modules: Record<string, any> }>(`/api/v2/pipeline/${projectId}/data`)
}

export function cleanupPipeline(projectId: string) {
  return apiPost<{ success: boolean }>(`/api/v2/pipeline/${projectId}`, {})
}

export async function confirmIdea(projectId: string, ideaId: string, version: number = 1) {
  return apiPost<{ success: boolean }>(`/api/v2/pipeline/${projectId}/confirm-idea`, { ideaId, version })
}

export async function compatibilityCheck(projectId: string, platform: string) {
  return apiPost<{ success: boolean; results: any[] }>(`/api/v2/pipeline/${projectId}/compatibility-check`, { platform })
}

export async function worldConsistencyCheck(projectId: string) {
  return apiGet<{ passed: boolean; message: string }>(`/api/v2/world/${projectId}/consistency-check`)
}

export async function characterConsistencyCheck(projectId: string) {
  return apiGet<{ passed: boolean; message: string }>(`/api/v2/character/${projectId}/consistency-check`)
}

export async function runConsistencyCheck(projectId: string, chapterNo: string = '1', content?: string, knowledgeState?: any, characters?: any[], world?: any) {
  return apiPost<{ success: boolean }>('/api/v2/consistency/check', {
    project_id: projectId, chapter_no: chapterNo, content,
    knowledge_state: knowledgeState, characters, world,
  })
}

export function getDrafts(projectId: string) {
  return apiGet<any[]>(`/api/v2/pipeline/${projectId}/data/draft_generation`)
}

export function getChapterPlans(projectId: string) {
  return apiGet<any[]>(`/api/v2/pipeline/${projectId}/data/chapter_plan`)
}

export function getPlotNodes(projectId: string) {
  return apiGet<any[]>(`/api/v2/pipeline/${projectId}/data/plot_nodes`)
}

export function testModelConnection(endpoint: string, apiKey: string, model: string) {
  return apiPost<{ ok: boolean; model?: string; response?: string; error?: string }>('/api/ai/test-connection', {
    endpoint, apiKey, model,
  }, 30000)
}

export function getVolumes(projectId: string) {
  return apiGet<any[]>(`/api/v2/pipeline/${projectId}/data/volumes`)
}
